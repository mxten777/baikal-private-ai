import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth, AuthContext } from '../contexts/AuthContext';
import { authAPI } from '../api/client';

// authAPI mock
jest.mock('../api/client', () => ({
  authAPI: {
    me: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
  },
}));

// useAuth를 소비하는 테스트용 컴포넌트
function AuthConsumer() {
  const { user, loading, isAdmin } = useAuth();
  if (loading) return <div>로딩중</div>;
  if (!user) return <div>미인증</div>;
  return (
    <div>
      <span>사용자: {user.username}</span>
      <span>관리자: {isAdmin ? 'yes' : 'no'}</span>
    </div>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('초기 로딩 상태 표시', async () => {
    // me가 느린 경우 시뮬레이션
    authAPI.me.mockImplementation(() => new Promise(() => {}));
    render(<AuthProvider><AuthConsumer /></AuthProvider>);
    expect(screen.getByText('로딩중')).toBeInTheDocument();
  });

  test('인증 쿠키 있을 때 사용자 로드', async () => {
    authAPI.me.mockResolvedValue({ data: { username: 'admin', role: 'admin' } });
    render(<AuthProvider><AuthConsumer /></AuthProvider>);
    await waitFor(() => {
      expect(screen.getByText('사용자: admin')).toBeInTheDocument();
      expect(screen.getByText('관리자: yes')).toBeInTheDocument();
    });
  });

  test('쿠키 없을 때 미인증 상태', async () => {
    authAPI.me.mockRejectedValue(new Error('401'));
    render(<AuthProvider><AuthConsumer /></AuthProvider>);
    await waitFor(() => {
      expect(screen.getByText('미인증')).toBeInTheDocument();
    });
  });

  test('일반 사용자 isAdmin = false', async () => {
    authAPI.me.mockResolvedValue({ data: { username: 'user1', role: 'user' } });
    render(<AuthProvider><AuthConsumer /></AuthProvider>);
    await waitFor(() => {
      expect(screen.getByText('관리자: no')).toBeInTheDocument();
    });
  });

  test('login() 호출 시 authAPI.login + authAPI.me 순서대로 호출', async () => {
    authAPI.me
      .mockResolvedValueOnce({ data: null }) // 초기 checkAuth (미인증)
      .mockResolvedValueOnce({ data: { username: 'admin', role: 'admin' } }); // login 후 me
    authAPI.login.mockResolvedValue({});

    let loginFn;
    function LoginTrigger() {
      const { login } = useAuth();
      loginFn = login;
      return null;
    }

    await act(async () => {
      render(<AuthProvider><LoginTrigger /></AuthProvider>);
    });

    await act(async () => {
      await loginFn('admin', 'password');
    });

    expect(authAPI.login).toHaveBeenCalledWith('admin', 'password');
    expect(authAPI.me).toHaveBeenCalledTimes(2);
  });

  test('logout() 호출 시 authAPI.logout 호출 + user = null', async () => {
    authAPI.me.mockResolvedValue({ data: { username: 'admin', role: 'admin' } });
    authAPI.logout.mockResolvedValue({});

    let logoutFn;
    function LogoutTrigger() {
      const { logout, user } = useAuth();
      logoutFn = logout;
      return <div>{user ? '인증됨' : '미인증'}</div>;
    }

    render(<AuthProvider><LogoutTrigger /></AuthProvider>);
    await waitFor(() => expect(screen.getByText('인증됨')).toBeInTheDocument());

    await act(async () => {
      await logoutFn();
    });

    expect(authAPI.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByText('미인증')).toBeInTheDocument();
  });

  test('logout() 네트워크 오류 시에도 user = null', async () => {
    authAPI.me.mockResolvedValue({ data: { username: 'admin', role: 'admin' } });
    authAPI.logout.mockRejectedValue(new Error('network error'));

    let logoutFn;
    function LogoutTrigger() {
      const { logout, user } = useAuth();
      logoutFn = logout;
      return <div>{user ? '인증됨' : '미인증'}</div>;
    }

    render(<AuthProvider><LogoutTrigger /></AuthProvider>);
    await waitFor(() => expect(screen.getByText('인증됨')).toBeInTheDocument());

    await act(async () => {
      await logoutFn();
    });

    // 에러여도 클라이언트 상태는 초기화됨
    expect(screen.getByText('미인증')).toBeInTheDocument();
  });

  test('useAuth를 AuthProvider 밖에서 사용하면 에러', () => {
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    function BareConsumer() {
      useAuth();
      return null;
    }
    expect(() => render(<BareConsumer />)).toThrow('useAuth must be used within AuthProvider');
    consoleError.mockRestore();
  });
});
