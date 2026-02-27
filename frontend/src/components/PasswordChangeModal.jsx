/**
 * PasswordChangeModal - 비밀번호 변경 모달
 */
import React, { useState, useRef, useEffect } from 'react';
import { HiOutlineKey, HiOutlineXMark, HiOutlineEye, HiOutlineEyeSlash } from 'react-icons/hi2';
import { authAPI } from '../api/client';
import toast from 'react-hot-toast';

export default function PasswordChangeModal({ isOpen, onClose }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const currentRef = useRef(null);

  // 모달 열릴 때 초기화 & 포커스
  useEffect(() => {
    if (isOpen) {
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowCurrent(false);
      setShowNew(false);
      setTimeout(() => currentRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // ESC 키 핸들러
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (newPassword.length < 4) {
      toast.error('새 비밀번호는 4자 이상이어야 합니다');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('새 비밀번호가 일치하지 않습니다');
      return;
    }

    setLoading(true);
    try {
      await authAPI.changePassword(currentPassword, newPassword);
      toast.success('비밀번호가 변경되었습니다');
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || '비밀번호 변경에 실패했습니다';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      {/* 백드롭 */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* 모달 */}
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-2xl shadow-black/10 overflow-hidden animate-in zoom-in-95 duration-200">
        {/* 헤더 */}
        <div className="px-6 pt-6 pb-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center shadow-lg shadow-baikal-500/25">
              <HiOutlineKey className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">비밀번호 변경</h2>
              <p className="text-xs text-gray-400 mt-0.5">새로운 비밀번호를 설정하세요</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <HiOutlineXMark className="w-5 h-5" />
          </button>
        </div>

        {/* 구분선 */}
        <div className="mx-6 h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent" />

        {/* 폼 */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* 현재 비밀번호 */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              현재 비밀번호
            </label>
            <div className="relative">
              <input
                ref={currentRef}
                type={showCurrent ? 'text' : 'password'}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 pr-10 text-sm border border-gray-200 rounded-xl bg-gray-50/50 focus:bg-white focus:border-baikal-400 focus:ring-2 focus:ring-baikal-400/20 outline-none transition-all"
                placeholder="현재 비밀번호 입력"
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showCurrent ? (
                  <HiOutlineEyeSlash className="w-4 h-4" />
                ) : (
                  <HiOutlineEye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* 새 비밀번호 */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              새 비밀번호
            </label>
            <div className="relative">
              <input
                type={showNew ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={4}
                className="w-full px-4 py-2.5 pr-10 text-sm border border-gray-200 rounded-xl bg-gray-50/50 focus:bg-white focus:border-baikal-400 focus:ring-2 focus:ring-baikal-400/20 outline-none transition-all"
                placeholder="새 비밀번호 (4자 이상)"
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showNew ? (
                  <HiOutlineEyeSlash className="w-4 h-4" />
                ) : (
                  <HiOutlineEye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* 비밀번호 확인 */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
              비밀번호 확인
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={4}
              className={`w-full px-4 py-2.5 text-sm border rounded-xl bg-gray-50/50 focus:bg-white outline-none transition-all ${
                confirmPassword && confirmPassword !== newPassword
                  ? 'border-rose-300 focus:border-rose-400 focus:ring-2 focus:ring-rose-400/20'
                  : 'border-gray-200 focus:border-baikal-400 focus:ring-2 focus:ring-baikal-400/20'
              }`}
              placeholder="새 비밀번호 다시 입력"
            />
            {confirmPassword && confirmPassword !== newPassword && (
              <p className="text-xs text-rose-500 mt-1 pl-1">비밀번호가 일치하지 않습니다</p>
            )}
          </div>

          {/* 버튼 */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={loading || !currentPassword || !newPassword || newPassword !== confirmPassword}
              className="flex-1 px-4 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-baikal-600 to-purple-600 hover:from-baikal-700 hover:to-purple-700 rounded-xl shadow-lg shadow-baikal-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  변경 중...
                </span>
              ) : (
                '비밀번호 변경'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
