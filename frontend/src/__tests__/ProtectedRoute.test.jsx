import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import { AuthContext } from '../contexts/AuthContext';

// AuthContext를 직접 값으로 주입하는 헬퍼
function renderWithAuth(ui, authValue) {
  return render(
    <AuthContext.Provider value={authValue}>
      <MemoryRouter initialEntries={['/protected']}>
        <Routes>
          <Route path="/protected" element={ui} />
          <Route path="/login" element={<div>로그인 페이지</div>} />
          <Route path="/chat" element={<div>채팅 페이지</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>
  );
}

describe('ProtectedRoute', () => {
  test('로딩 중일 때 스피너 표시', () => {
    renderWithAuth(
      <ProtectedRoute><div>보호 콘텐츠</div></ProtectedRoute>,
      { user: null, loading: true }
    );
    // 스피너는 animate-spin 클래스를 가진 div
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    expect(screen.queryByText('보호 콘텐츠')).not.toBeInTheDocument();
  });

  test('비인증 사용자는 /login으로 리다이렉트', () => {
    renderWithAuth(
      <ProtectedRoute><div>보호 콘텐츠</div></ProtectedRoute>,
      { user: null, loading: false }
    );
    expect(screen.getByText('로그인 페이지')).toBeInTheDocument();
    expect(screen.queryByText('보호 콘텐츠')).not.toBeInTheDocument();
  });

  test('일반 사용자는 보호 콘텐츠 접근 가능', () => {
    renderWithAuth(
      <ProtectedRoute><div>보호 콘텐츠</div></ProtectedRoute>,
      { user: { role: 'user' }, loading: false }
    );
    expect(screen.getByText('보호 콘텐츠')).toBeInTheDocument();
  });

  test('requireAdmin=true인 경우 일반 사용자는 /chat으로 리다이렉트', () => {
    renderWithAuth(
      <ProtectedRoute requireAdmin><div>관리자 콘텐츠</div></ProtectedRoute>,
      { user: { role: 'user' }, loading: false }
    );
    expect(screen.getByText('채팅 페이지')).toBeInTheDocument();
    expect(screen.queryByText('관리자 콘텐츠')).not.toBeInTheDocument();
  });

  test('requireAdmin=true인 경우 admin 사용자는 접근 가능', () => {
    renderWithAuth(
      <ProtectedRoute requireAdmin><div>관리자 콘텐츠</div></ProtectedRoute>,
      { user: { role: 'admin' }, loading: false }
    );
    expect(screen.getByText('관리자 콘텐츠')).toBeInTheDocument();
  });

  test('requireAdmin 없이 admin 사용자도 일반 보호 라우트 접근 가능', () => {
    renderWithAuth(
      <ProtectedRoute><div>보호 콘텐츠</div></ProtectedRoute>,
      { user: { role: 'admin' }, loading: false }
    );
    expect(screen.getByText('보호 콘텐츠')).toBeInTheDocument();
  });
});
