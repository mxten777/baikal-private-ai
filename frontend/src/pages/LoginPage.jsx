/**
 * LoginPage - 미니멀 다크 로그인
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { HiOutlineEye, HiOutlineEyeSlash } from 'react-icons/hi2';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error('아이디와 비밀번호를 입력하세요');
      return;
    }

    setLoading(true);
    try {
      await login(username, password);
      toast.success('로그인 성공');
      navigate('/chat');
    } catch (err) {
      const msg = err.response?.data?.detail || '로그인에 실패했습니다';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-gray-950">
      {/* 왼쪽 브랜딩 */}
      <div className="hidden lg:flex lg:w-[50%] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-baikal-950 to-gray-950" />
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-1/3 left-1/4 w-[400px] h-[400px] bg-baikal-500/30 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/3 right-1/4 w-[300px] h-[300px] bg-purple-500/20 rounded-full blur-[100px]" />
        </div>

        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
              <span className="text-white font-black text-[10px]">B</span>
            </div>
            <span className="text-white/30 text-[11px] font-medium tracking-widest uppercase">Private AI</span>
          </div>

          <div>
            <h1 className="text-5xl font-black text-white leading-[1.1] tracking-tight">
              BAIKAL
              <br />
              <span className="text-baikal-400">Private AI</span>
            </h1>
            <p className="mt-4 text-[15px] text-white/30 leading-relaxed max-w-sm">
              폐쇄망 환경에서 안전하게 운영되는
              <br />문서 검색 · AI 답변 플랫폼
            </p>

            <div className="flex gap-8 mt-8">
              {[
                { num: '100%', label: '폐쇄망 보안' },
                { num: 'RAG', label: '문서 기반 AI' },
                { num: 'Real-time', label: '스트리밍' },
              ].map((item, i) => (
                <div key={i}>
                  <p className="text-lg font-bold text-white/80">{item.num}</p>
                  <p className="text-[10px] text-white/25 mt-0.5">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          <p className="text-[10px] text-white/15">© 2025 BAIKAL · v1.0.0</p>
        </div>
      </div>

      {/* 오른쪽 로그인 폼 */}
      <div className="flex-1 flex items-center justify-center bg-[#0f0f17] relative">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-baikal-500 to-purple-500" />

        <div className="w-full max-w-[360px] px-6">
          {/* 모바일 로고 */}
          <div className="lg:hidden text-center mb-8">
            <div className="inline-flex w-10 h-10 rounded-xl bg-gradient-to-br from-baikal-500 to-purple-600 items-center justify-center mb-2">
              <span className="text-white font-black text-sm">B</span>
            </div>
            <h1 className="text-xl font-black text-gray-100">BAIKAL</h1>
          </div>

          <div className="mb-7">
            <h2 className="text-2xl font-bold text-gray-100">로그인</h2>
            <p className="text-sm text-gray-500 mt-1">계정에 로그인하여 시작하세요</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-gray-500 mb-1.5">아이디</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-baikal-500/40 focus:ring-1 focus:ring-baikal-500/20 transition-all"
                placeholder="아이디를 입력하세요"
                autoComplete="username"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-gray-500 mb-1.5">비밀번호</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-lg border border-white/[0.06] bg-white/[0.03] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-baikal-500/40 focus:ring-1 focus:ring-baikal-500/20 transition-all pr-10"
                  placeholder="비밀번호를 입력하세요"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400 transition-colors"
                >
                  {showPassword ? <HiOutlineEyeSlash className="w-4 h-4" /> : <HiOutlineEye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-baikal-600 hover:bg-baikal-500 text-white text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-1"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  로그인 중...
                </span>
              ) : '로그인'}
            </button>
          </form>

          <div className="mt-8 pt-5 border-t border-white/[0.04] text-center">
            <p className="text-[10px] text-gray-600">BAIKAL Private AI · 폐쇄망 설치형 플랫폼</p>
          </div>
        </div>
      </div>
    </div>
  );
}
