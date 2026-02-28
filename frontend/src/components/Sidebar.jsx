/**
 * Sidebar - 전문 RAG 시스템 네비게이션
 * 미니멀 다크 테마
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
        `group flex items-center gap-3 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150 ${
          isActive
            ? 'text-white bg-white/10'
            : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <Icon className={`w-[18px] h-[18px] ${isActive ? 'text-baikal-400' : ''}`} />
          <span>{label}</span>
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
    <aside className="w-[220px] bg-[#13131d] border-r border-white/[0.04] flex flex-col h-screen">
      {/* 로고 */}
      <div className="px-4 pt-5 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-black text-[11px]">B</span>
          </div>
          <div>
            <h1 className="text-[15px] font-bold text-white leading-none">BAIKAL</h1>
            <p className="text-[9px] text-gray-500 font-medium tracking-[0.15em] uppercase mt-0.5">Private AI</p>
          </div>
        </div>
        {onClose && (
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg transition-colors lg:hidden">
            <HiOutlineArrowRightOnRectangle className="w-4 h-4 rotate-180" />
          </button>
        )}
      </div>

      {/* 구분선 */}
      <div className="mx-4 h-px bg-gray-800/60" />

      {/* 메뉴 */}
      <nav className="flex-1 px-3 pt-4 pb-2 space-y-0.5 overflow-y-auto">
        <p className="px-3 pb-2 text-[9px] font-semibold text-gray-600 uppercase tracking-widest">
          메뉴
        </p>
        <NavItem to="/chat" icon={HiOutlineChatBubbleLeftRight} label="AI 질문응답" />
        <NavItem to="/documents" icon={HiOutlineDocumentText} label="문서 관리" />
        <NavItem to="/search" icon={HiOutlineMagnifyingGlass} label="문서 검색" />

        {isAdmin && (
          <>
            <div className="pt-4 pb-1">
              <p className="px-3 text-[9px] font-semibold text-gray-600 uppercase tracking-widest">관리자</p>
            </div>
            <NavItem to="/admin/users" icon={HiOutlineUsers} label="사용자 관리" />
            <NavItem to="/admin/documents" icon={HiOutlineFolderOpen} label="문서 관리" />
          </>
        )}
      </nav>

      {/* 구분선 */}
      <div className="mx-4 h-px bg-gray-800/60" />

      {/* 사용자 정보 */}
      <div className="px-3 py-3">
        <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg hover:bg-white/5 transition-colors group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center text-white text-[9px] font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[12px] font-medium text-gray-300 truncate leading-tight">{user?.username}</p>
            <p className="text-[9px] text-gray-600 mt-0.5">{user?.role === 'admin' ? '관리자' : '사용자'}</p>
          </div>
          <button
            onClick={() => setPwModalOpen(true)}
            className="p-1 text-gray-600 hover:text-gray-300 rounded transition-all opacity-0 group-hover:opacity-100"
            title="비밀번호 변경"
          >
            <HiOutlineKey className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleLogout}
            className="p-1 text-gray-600 hover:text-rose-400 rounded transition-all opacity-0 group-hover:opacity-100"
            title="로그아웃"
          >
            <HiOutlineArrowRightOnRectangle className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <PasswordChangeModal isOpen={pwModalOpen} onClose={() => setPwModalOpen(false)} />
    </aside>
  );
}
