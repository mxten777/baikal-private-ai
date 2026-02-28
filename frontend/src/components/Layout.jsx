/**
 * Layout - 통일 다크 테마 레이아웃
 */
import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import { HiOutlineBars3 } from 'react-icons/hi2';

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  return (
    <div className="flex h-screen bg-[#0f0f17]">
      {/* 모바일 오버레이 */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 사이드바 */}
      <div className={`
        fixed inset-y-0 left-0 z-50 transition-transform duration-200 lg:relative lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* 메인 */}
      <main className="flex-1 overflow-y-auto relative min-w-0">
        {/* 모바일 상단바 */}
        <div className="sticky top-0 z-30 flex items-center gap-3 px-4 py-2.5 bg-[#0f0f17]/90 backdrop-blur-md border-b border-white/5 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg transition-colors"
          >
            <HiOutlineBars3 className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-black text-[8px]">B</span>
            </div>
            <span className="text-sm font-bold text-gray-200">BAIKAL</span>
          </div>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
