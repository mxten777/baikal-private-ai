/**
 * Sidebar - 프리미엄 사이드바 네비게이션
 */
import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import PasswordChangeModal from './PasswordChangeModal';
import {
  HiOutlineChatBubbleLeftRight,
  HiOutlineDocumentText,
  HiOutlineMagnifyingGlass,
  HiOutlineUsers,
  HiOutlineFolderOpen,
  HiOutlineArrowRightOnRectangle,
  HiOutlineKey,
} from 'react-icons/hi2';

function NavItem({ to, icon: Icon, label }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200 ${
          isActive
            ? 'text-baikal-700 bg-baikal-50/80'
            : 'text-gray-400 hover:text-gray-700 hover:bg-gray-50/80'
        }`
      }
    >
      {({ isActive }) => (
        <>
          {/* 왼쪽 액센트 바 */}
          <div
            className={`absolute left-0 top-1/2 -translate-y-1/2 w-[3px] rounded-full transition-all duration-300 ${
              isActive ? 'h-5 bg-gradient-to-b from-baikal-500 to-purple-500' : 'h-0'
            }`}
          />
          <div
            className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200 ${
              isActive
                ? 'bg-gradient-to-br from-baikal-500 to-baikal-600 text-white shadow-sm shadow-baikal-500/30'
                : 'text-gray-400 group-hover:text-gray-600 group-hover:bg-gray-100/80'
            }`}
          >
            <Icon className="w-[18px] h-[18px]" />
          </div>
          <span className={`transition-colors ${isActive ? 'font-semibold' : ''}`}>
            {label}
          </span>
        </>
      )}
    </NavLink>
  );
}

export default function Sidebar({ onClose }) {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [pwModalOpen, setPwModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.username?.slice(0, 2).toUpperCase() || '??';

  return (
    <aside className="w-[260px] bg-white border-r border-gray-100 flex flex-col h-screen">
      {/* 로고 */}
      <div className="px-5 pt-6 pb-5 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <div className="relative">
            <div className="w-10 h-10 rounded-[14px] bg-gradient-to-br from-baikal-600 via-baikal-500 to-purple-600 flex items-center justify-center shadow-lg shadow-baikal-600/25">
              <span className="text-white font-black text-sm tracking-tighter">B</span>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white" />
          </div>
          <div>
            <h1 className="text-[17px] font-extrabold text-gray-900 tracking-tight leading-none">
              BAIKAL
            </h1>
            <p className="text-[10px] text-gray-400 font-semibold tracking-[0.15em] uppercase mt-0.5">
              Private AI
            </p>
          </div>
        </div>
        {/* 모바일 닫기 버튼 */}
        {onClose && (
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors lg:hidden">
            <HiOutlineArrowRightOnRectangle className="w-5 h-5 rotate-180" />
          </button>
        )}
      </div>

      {/* 구분선 */}
      <div className="mx-5 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />
      
      {/* 메뉴 */}
      <nav className="flex-1 px-3 pt-5 pb-2 space-y-0.5 overflow-y-auto">
        <p className="px-3.5 pb-2 text-[10px] font-bold text-gray-300 uppercase tracking-[0.15em]">
          메인 메뉴
        </p>
        <NavItem to="/chat" icon={HiOutlineChatBubbleLeftRight} label="AI 질문응답" />
        <NavItem to="/documents" icon={HiOutlineDocumentText} label="문서 관리" />
        <NavItem to="/search" icon={HiOutlineMagnifyingGlass} label="문서 검색" />

        {isAdmin && (
          <>
            <div className="pt-5 pb-1">
              <p className="px-3.5 text-[10px] font-bold text-gray-300 uppercase tracking-[0.15em]">
                관리자
              </p>
            </div>
            <NavItem to="/admin/users" icon={HiOutlineUsers} label="사용자 관리" />
            <NavItem to="/admin/documents" icon={HiOutlineFolderOpen} label="문서 관리" />
          </>
        )}
      </nav>

      {/* 하단 구분선 */}
      <div className="mx-5 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />

      {/* 사용자 정보 */}
      <div className="px-3 py-4">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-gray-50 transition-all duration-200 group">
          <div className="relative flex-shrink-0">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-baikal-500 via-purple-500 to-fuchsia-500 flex items-center justify-center text-white text-[11px] font-bold shadow-md shadow-baikal-500/20">
              {initials}
            </div>
            <div className="absolute -bottom-px -right-px w-2.5 h-2.5 rounded-full bg-emerald-400 border-[1.5px] border-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-semibold text-gray-800 truncate leading-tight">
              {user?.username}
            </p>
            <p className="text-[10px] text-gray-400 font-medium mt-0.5">
              {user?.role === 'admin' ? '관리자' : '사용자'}
            </p>
          </div>
          <button
            onClick={() => setPwModalOpen(true)}
            className="p-1.5 text-gray-300 hover:text-baikal-600 hover:bg-baikal-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
            title="비밀번호 변경"
          >
            <HiOutlineKey className="w-4 h-4" />
          </button>
          <button
            onClick={handleLogout}
            className="p-1.5 text-gray-300 hover:text-rose-500 hover:bg-rose-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
            title="로그아웃"
          >
            <HiOutlineArrowRightOnRectangle className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 비밀번호 변경 모달 */}
      <PasswordChangeModal isOpen={pwModalOpen} onClose={() => setPwModalOpen(false)} />
    </aside>
  );
}
