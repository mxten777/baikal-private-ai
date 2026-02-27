/**
 * LoginPage - 프리미엄 로그인
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
    <div className="min-h-screen flex relative overflow-hidden">
      {/* 왼쪽: 브랜딩 패널 */}
      <div className="hidden lg:flex lg:w-[52%] relative overflow-hidden">
        {/* 메시 그라디언트 배경 */}
        <div className="absolute inset-0 bg-gradient-to-br from-baikal-950 via-baikal-900 to-purple-900" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-baikal-500/30 rounded-full blur-[120px] animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] bg-purple-500/20 rounded-full blur-[100px] animate-float-delayed" />
          <div className="absolute top-1/2 right-1/3 w-[300px] h-[300px] bg-fuchsia-500/15 rounded-full blur-[80px] animate-float-slow" />
        </div>
        <div className="absolute inset-0 grid-pattern opacity-20" />

        {/* 브랜딩 콘텐츠 */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-[14px] bg-white/10 backdrop-blur-sm border border-white/10 flex items-center justify-center">
                <span className="text-white font-black text-sm">B</span>
              </div>
              <span className="text-white/60 text-sm font-medium tracking-wider uppercase">Private AI</span>
            </div>
          </div>

          <div className="space-y-8">
            <div>
              <h1 className="text-6xl font-black text-white leading-[1.1] tracking-tight">
                BAIKAL
                <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-baikal-300 via-purple-300 to-fuchsia-300">
                  Private AI
                </span>
              </h1>
              <p className="mt-5 text-lg text-white/40 leading-relaxed max-w-md font-light">
                폐쇄망 환경에서 안전하게 운영되는
                <br />
                문서 검색 · AI 답변 플랫폼
              </p>
            </div>

            {/* 기능 하이라이트 */}
            <div className="flex gap-6">
              {[
                { num: '100%', label: '폐쇄망 보안' },
                { num: 'RAG', label: '문서 기반 AI' },
                { num: 'Real-time', label: '스트리밍 응답' },
              ].map((item, i) => (
                <div key={i} className="space-y-1">
                  <p className="text-xl font-bold text-white/90">{item.num}</p>
                  <p className="text-[11px] text-white/30 font-medium">{item.label}</p>
                </div>
              ))}
            </div>
          </div>

          <p className="text-[11px] text-white/20 font-medium">
            © 2024 BAIKAL · v1.0.0
          </p>
        </div>
      </div>

      {/* 오른쪽: 로그인 폼 */}
      <div className="flex-1 flex items-center justify-center bg-white relative">
        {/* 미세 장식 */}
        <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-baikal-500 via-purple-500 to-fuchsia-500" />
        
        <div className="w-full max-w-[380px] px-6 animate-fade-in">
          {/* 모바일 로고 */}
          <div className="lg:hidden text-center mb-10">
            <div className="inline-flex w-12 h-12 rounded-2xl bg-gradient-to-br from-baikal-600 to-purple-600 items-center justify-center shadow-glow mb-3">
              <span className="text-white font-black text-lg">B</span>
            </div>
            <h1 className="text-2xl font-black text-gray-900">BAIKAL</h1>
          </div>

          <div className="mb-8">
            <h2 className="text-[28px] font-extrabold text-gray-900 tracking-tight">
              로그인
            </h2>
            <p className="text-sm text-gray-400 mt-1.5 font-medium">
              계정에 로그인하여 시작하세요
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-[11px] font-bold text-gray-400 uppercase tracking-[0.08em] mb-2">
                아이디
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-modern !py-3.5 !rounded-xl"
                placeholder="아이디를 입력하세요"
                autoComplete="username"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-[11px] font-bold text-gray-400 uppercase tracking-[0.08em] mb-2">
                비밀번호
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-modern !py-3.5 !rounded-xl pr-12"
                  placeholder="비밀번호를 입력하세요"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-300 hover:text-gray-500 rounded-lg transition-colors"
                >
                  {showPassword ? <HiOutlineEyeSlash className="w-5 h-5" /> : <HiOutlineEye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 px-4 btn-primary text-[15px] rounded-xl disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2.5">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  로그인 중...
                </span>
              ) : '로그인'}
            </button>
          </form>

          <div className="mt-10 pt-6 border-t border-gray-100 text-center">
            <p className="text-[11px] text-gray-300 font-medium">
              BAIKAL Private AI · 폐쇄망 설치형 플랫폼
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
