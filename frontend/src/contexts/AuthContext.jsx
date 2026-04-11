/**
 * Auth Context - 인증 상태 관리
 * P3-4: HttpOnly 쿠키 기반 (localStorage 제거)
 */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../api/client';

const AuthContext = createContext(null);

export { AuthContext };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    // P3-4: localStorage 확인 불필요 — 쿠키가 있으면 /me 성공
    try {
      const res = await authAPI.me();
      setUser(res.data);
    } catch {
      // 쿠키 없음 또는 만료 — 인증 불필요 페이지에서는 정상
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    // P3-4: 서버가 HttpOnly 쿠키를 설정함 — 토큰 수동 저장 불필요
    await authAPI.login(username, password);
    const meRes = await authAPI.me();
    setUser(meRes.data);
    return meRes.data;
  };

  const logout = async () => {
    try {
      // P3-4: 서버에서 쿠키 삭제 + P3-5: refresh 토큰 블랙리스트 등록
      await authAPI.logout();
    } catch {
      // 네트워크 오류 시에도 클라이언트 상태 초기화
    }
    setUser(null);
  };

  const isAdmin = user?.role === 'admin';

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
