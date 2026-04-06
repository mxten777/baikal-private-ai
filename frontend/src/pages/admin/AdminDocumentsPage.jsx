/**
 * Admin - AdminDocumentsPage - 프리미엄 관리자 문서 관리
 */
import React, { useState, useEffect, useCallback } from 'react';
import { documentsAPI } from '../../api/client';
import toast from 'react-hot-toast';
import {
  HiOutlineDocumentText,
  HiOutlineTrash,
  HiOutlineArrowPath,
  HiOutlineArrowDownTray,
  HiOutlineCircleStack,
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineExclamationTriangle,
  HiOutlineLockClosed,
  HiOutlineLockOpen,
  HiOutlineShieldCheck,
  HiOutlineXMark,
} from 'react-icons/hi2';

const STATUS_MAP = {
  uploading: { label: '업로드중', dot: 'bg-amber-400', bg: 'bg-amber-500/15 text-amber-400' },
  processing: { label: '분석중', dot: 'bg-blue-400', bg: 'bg-blue-500/15 text-blue-400' },
  completed: { label: '완료', dot: 'bg-emerald-400', bg: 'bg-emerald-500/15 text-emerald-400' },
  failed: { label: '실패', dot: 'bg-red-400', bg: 'bg-red-500/15 text-red-400' },
};

const ROLE_LABELS = { admin: '관리자', manager: '매니저', user: '사용자' };
const ALL_ROLES = ['admin', 'manager', 'user'];

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function PermissionModal({ doc, onClose, onSaved }) {
  const [isPublic, setIsPublic] = useState(doc.is_public ?? true);
  const [allowedRoles, setAllowedRoles] = useState(doc.allowed_roles ?? ['admin', 'manager', 'user']);
  const [saving, setSaving] = useState(false);

  const toggleRole = (role) => {
    setAllowedRoles(prev =>
      prev.includes(role) ? prev.filter(r => r !== role) : [...prev, role]
    );
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await documentsAPI.updatePermissions(doc.id, {
        is_public: isPublic,
        allowed_roles: isPublic ? null : allowedRoles,
      });
      toast.success('권한 설정이 저장되었습니다');
      onSaved();
      onClose();
    } catch {
      toast.error('권한 저장 실패');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#1a1a2e] border border-white/[0.08] rounded-2xl shadow-2xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <HiOutlineShieldCheck className="w-4 h-4 text-baikal-400" />
            <span className="text-[14px] font-bold text-gray-200">접근 권한 설정</span>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg hover:bg-white/[0.05]">
            <HiOutlineXMark className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          <p className="text-[12px] text-gray-400 truncate font-medium">{doc.filename}</p>

          {/* 공개 여부 */}
          <div>
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] mb-2">접근 범위</p>
            <div className="flex gap-2">
              <button
                onClick={() => setIsPublic(true)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12px] font-semibold border transition-all ${isPublic ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-400' : 'bg-white/[0.03] border-white/[0.06] text-gray-500 hover:text-gray-300'}`}
              >
                <HiOutlineLockOpen className="w-3.5 h-3.5" /> 전체 공개
              </button>
              <button
                onClick={() => setIsPublic(false)}
                className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-[12px] font-semibold border transition-all ${!isPublic ? 'bg-amber-500/15 border-amber-500/40 text-amber-400' : 'bg-white/[0.03] border-white/[0.06] text-gray-500 hover:text-gray-300'}`}
              >
                <HiOutlineLockClosed className="w-3.5 h-3.5" /> 역할 제한
              </button>
            </div>
          </div>

          {/* 역할 선택 */}
          {!isPublic && (
            <div>
              <p className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] mb-2">허용 역할</p>
              <div className="flex gap-2">
                {ALL_ROLES.map(role => (
                  <button
                    key={role}
                    onClick={() => toggleRole(role)}
                    className={`flex-1 py-2 rounded-lg text-[11px] font-semibold border transition-all ${
                      allowedRoles.includes(role)
                        ? 'bg-baikal-600/30 border-baikal-500/50 text-baikal-300'
                        : 'bg-white/[0.02] border-white/[0.05] text-gray-600 hover:text-gray-400'
                    }`}
                  >
                    {ROLE_LABELS[role]}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="px-5 pb-5">
          <button
            onClick={handleSave}
            disabled={saving || (!isPublic && allowedRoles.length === 0)}
            className="w-full py-2.5 rounded-lg bg-baikal-600 text-white text-[13px] font-semibold hover:bg-baikal-500 disabled:opacity-40 transition-all"
          >
            {saving ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AdminDocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [permissionDoc, setPermissionDoc] = useState(null);

  const loadDocuments = useCallback(async () => {
    try { const res = await documentsAPI.list(); setDocuments(res.data); }
    catch { toast.error('문서 목록 로드 실패'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  const handleDelete = async (doc) => {
    if (!window.confirm(`"${doc.filename}" 문서를 삭제하시겠습니까?`)) return;
    try { await documentsAPI.delete(doc.id); toast.success('문서 삭제 완료'); loadDocuments(); }
    catch (err) { toast.error(err.response?.data?.detail || '삭제 실패'); }
  };

  const handleDownload = async (doc) => {
    try {
      const res = await documentsAPI.download(doc.id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a'); a.href = url; a.download = doc.filename; a.click();
      window.URL.revokeObjectURL(url);
    } catch { toast.error('다운로드 실패'); }
  };

  const stats = {
    total: documents.length,
    completed: documents.filter((d) => d.status === 'completed').length,
    processing: documents.filter((d) => d.status === 'processing' || d.status === 'uploading').length,
    failed: documents.filter((d) => d.status === 'failed').length,
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-6xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6 sm:mb-8">
          <div>
            <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-100 tracking-tight">문서 관리</h1>
            <p className="text-sm text-gray-500 mt-1 font-medium">전체 시스템 문서 관리 (관리자)</p>
          </div>
          <button onClick={loadDocuments} className="p-2.5 text-gray-500 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all" title="새로고침">
            <HiOutlineArrowPath className="w-5 h-5" />
          </button>
        </div>

        {/* 통계 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {[
            { label: '전체', value: stats.total, icon: HiOutlineCircleStack, gradient: 'from-baikal-600 to-blue-600' },
            { label: '완료', value: stats.completed, icon: HiOutlineCheckCircle, gradient: 'from-emerald-600 to-teal-600' },
            { label: '처리중', value: stats.processing, icon: HiOutlineClock, gradient: 'from-blue-500 to-indigo-600' },
            { label: '실패', value: stats.failed, icon: HiOutlineExclamationTriangle, gradient: 'from-red-500 to-rose-600' },
          ].map((stat) => (
            <div key={stat.label} className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4 hover:bg-white/[0.04] transition-all duration-150">
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.gradient} flex items-center justify-center shadow-lg`}>
                  <stat.icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <p className="text-3xl font-black text-gray-100 tracking-tight">{stat.value}</p>
              <p className="text-[11px] text-gray-500 font-semibold mt-0.5 uppercase tracking-[0.06em]">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* 문서 테이블 */}
        <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
          <div className="px-6 py-4 border-b border-white/[0.04]">
            <div className="flex items-center gap-3">
              <h2 className="text-[15px] font-bold text-gray-200">문서 목록</h2>
              <span className="px-2 py-0.5 rounded-lg bg-white/[0.06] text-[11px] font-bold text-gray-400">{documents.length}</span>
            </div>
          </div>

          {loading ? (
            <div className="p-16 text-center">
              <div className="shimmer-dark w-48 h-4 mx-auto mb-3 rounded" />
              <div className="shimmer-dark w-32 h-4 mx-auto rounded" />
            </div>
          ) : documents.length === 0 ? (
            <div className="p-16 text-center animate-fade-in">
              <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-white/[0.04] flex items-center justify-center">
                <HiOutlineDocumentText className="w-7 h-7 text-gray-600" />
              </div>
              <p className="text-sm text-gray-400 font-semibold">문서가 없습니다</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
            <table className="w-full min-w-[600px]">
              <thead>
                <tr className="border-b border-white/[0.04]">
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em]">파일명</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] hidden sm:table-cell">형식</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] hidden sm:table-cell">크기</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em]">상태</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] hidden md:table-cell">접근권한</th>
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] hidden md:table-cell">업로드일</th>
                  <th className="px-4 sm:px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03]">
                {documents.map((doc) => {
                  const status = STATUS_MAP[doc.status] || STATUS_MAP.uploading;
                  const isPublic = doc.is_public ?? true;
                  const roles = doc.allowed_roles ?? [];
                  return (
                    <tr key={doc.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 sm:px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-baikal-500/10 flex items-center justify-center flex-shrink-0">
                            <HiOutlineDocumentText className="w-4 h-4 text-baikal-400" />
                          </div>
                          <span className="text-[13px] font-semibold text-gray-300 truncate max-w-[120px] sm:max-w-none">{doc.filename}</span>
                        </div>
                      </td>
                      <td className="px-4 sm:px-6 py-4 hidden sm:table-cell">
                        <span className="px-2 py-0.5 rounded-md bg-white/[0.04] text-[10px] font-bold text-gray-500 uppercase tracking-wider">{doc.file_type}</span>
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-[13px] text-gray-500 hidden sm:table-cell">{formatBytes(doc.file_size)}</td>
                      <td className="px-4 sm:px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold ${status.bg}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${status.dot} ${doc.status === 'processing' ? 'animate-pulse' : ''}`} />
                          {status.label}
                        </span>
                        {doc.error_message && <p className="text-[10px] text-red-400 mt-1 max-w-xs truncate">{doc.error_message}</p>}
                      </td>
                      <td className="px-4 sm:px-6 py-4 hidden md:table-cell">
                        {isPublic ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">
                            <HiOutlineLockOpen className="w-3 h-3" /> 전체
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {roles.map(r => (
                              <span key={r} className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-baikal-600/20 text-baikal-300">
                                {ROLE_LABELS[r] || r}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-[13px] text-gray-500 hidden md:table-cell">{new Date(doc.created_at).toLocaleDateString('ko-KR')}</td>
                      <td className="px-4 sm:px-6 py-4">
                        <div className="flex gap-1">
                          <button onClick={() => setPermissionDoc(doc)} className="p-2 text-gray-600 hover:text-amber-400 hover:bg-amber-500/10 rounded-lg transition-all" title="권한 설정">
                            <HiOutlineShieldCheck className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDownload(doc)} className="p-2 text-gray-600 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all" title="다운로드">
                            <HiOutlineArrowDownTray className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDelete(doc)} className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all" title="삭제">
                            <HiOutlineTrash className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </div>

      {permissionDoc && (
        <PermissionModal
          doc={permissionDoc}
          onClose={() => setPermissionDoc(null)}
          onSaved={loadDocuments}
        />
      )}
    </div>
  );
}
