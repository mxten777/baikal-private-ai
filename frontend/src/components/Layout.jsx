/**
 * Layout - 프리미엄 레이아웃 (모바일 반응형)
 */
import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { HiOutlineBars3, HiOutlineXMark } from 'react-icons/hi2';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // 페이지 이동 시 모바일 사이드바 닫기
  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  return (
    <div className="flex h-screen bg-surface-50">
      {/* 모바일 오버레이 */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 사이드바 - 데스크탑 고정, 모바일 슬라이드 */}
      <div className={`
        fixed inset-y-0 left-0 z-50 transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 overflow-y-auto relative bg-surface-50 min-w-0">
        {/* 모바일 상단바 */}
        <div className="sticky top-0 z-30 flex items-center gap-3 px-4 py-3 bg-white/80 backdrop-blur-md border-b border-gray-100 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 -ml-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <HiOutlineBars3 className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center">
              <span className="text-white font-black text-[9px]">B</span>
            </div>
            <span className="text-sm font-bold text-gray-800">BAIKAL</span>
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
