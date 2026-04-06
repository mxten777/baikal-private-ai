/**
 * DocumentsPage - 프리미엄 문서 관리
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { documentsAPI } from '../api/client';
import DocumentUpload from '../components/DocumentUpload';
import toast from 'react-hot-toast';
import {
  HiOutlineDocumentText,
  HiOutlineArrowDownTray,
  HiOutlineArrowPath,
  HiOutlineCircleStack,
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineTrash,
  HiOutlineExclamationTriangle,
} from 'react-icons/hi2';

const STATUS_MAP = {
  uploading: { label: '업로드중', dot: 'bg-amber-400', bg: 'bg-amber-500/15 text-amber-400' },
  processing: { label: '분석중', dot: 'bg-blue-400', bg: 'bg-blue-500/15 text-blue-400' },
  processing_stuck: { label: '응답없음', dot: 'bg-orange-400', bg: 'bg-orange-500/15 text-orange-400' },
  completed: { label: '완료', dot: 'bg-emerald-400', bg: 'bg-emerald-500/15 text-emerald-400' },
  failed: { label: '실패', dot: 'bg-red-400', bg: 'bg-red-500/15 text-red-400' },
};

const STUCK_THRESHOLD_MS = 5 * 60 * 1000; // 5분

function getElapsedLabel(createdAt) {
  const elapsed = Date.now() - new Date(createdAt).getTime();
  const secs = Math.floor(elapsed / 1000);
  if (secs < 60) return `${secs}초 경과`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}분 경과`;
  return `${Math.floor(mins / 60)}시간 경과`;
}

function isStuck(doc) {
  if (doc.status !== 'processing' && doc.status !== 'uploading') return false;
  return Date.now() - new Date(doc.created_at).getTime() > STUCK_THRESHOLD_MS;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);

  const loadDocuments = useCallback(async () => {
    try { const res = await documentsAPI.list(); setDocuments(res.data); }
    catch { toast.error('문서 목록 로드 실패'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { loadDocuments(); }, [loadDocuments]);

  // 폴링: 처리 중 문서 있으면 3초마다 새로고침
  useEffect(() => {
    const processing = documents.filter((d) => d.status === 'uploading' || d.status === 'processing');
    if (processing.length === 0) return;
    const interval = setInterval(() => { loadDocuments(); }, 3000);
    return () => clearInterval(interval);
  }, [documents, loadDocuments]);

  // 경과 시간 표시 갱신 (1초마다)
  useEffect(() => {
    const hasActive = documents.some((d) => d.status === 'processing' || d.status === 'uploading');
    if (!hasActive) return;
    const t = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(t);
  }, [documents]);

  const handleDelete = async (doc) => {
    if (!window.confirm(`"${doc.filename}" 를 삭제하시겠습니까?`)) return;
    try {
      await documentsAPI.delete(doc.id);
      toast.success('문서가 삭제되었습니다');
      loadDocuments();
    } catch { toast.error('삭제 실패'); }
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
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-5xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6 sm:mb-8">
          <div>
            <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-100 tracking-tight">문서 관리</h1>
            <p className="text-sm text-gray-500 mt-1 font-medium">문서를 업로드하고 AI 분석을 시작하세요</p>
          </div>
          <button onClick={loadDocuments} className="p-2.5 text-gray-500 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all" title="새로고침">
            <HiOutlineArrowPath className="w-5 h-5" />
          </button>
        </div>

        {/* 통계 카드 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {[
            { label: '전체 문서', value: stats.total, icon: HiOutlineCircleStack, gradient: 'from-baikal-600 to-blue-600' },
            { label: '분석 완료', value: stats.completed, icon: HiOutlineCheckCircle, gradient: 'from-emerald-600 to-teal-600' },
            { label: '처리 중', value: stats.processing, icon: HiOutlineClock, gradient: 'from-amber-500 to-orange-500' },
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

        {/* 업로드 */}
        <div className="mb-6 sm:mb-8">
          <DocumentUpload onUploaded={loadDocuments} />
        </div>

        {/* 문서 목록 */}
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
              <p className="text-sm text-gray-400 font-semibold">업로드된 문서가 없습니다</p>
              <p className="text-[11px] text-gray-600 mt-1">위 영역에 파일을 드래그하여 시작하세요</p>
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
                  <th className="px-4 sm:px-6 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] hidden md:table-cell">업로드일</th>
                  <th className="px-4 sm:px-6 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.03]">
                {documents.map((doc) => {
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
                        {(() => {
                          const stuck = isStuck(doc);
                          const displayStatus = stuck ? STATUS_MAP.processing_stuck : (STATUS_MAP[doc.status] || STATUS_MAP.uploading);
                          const isActive = doc.status === 'processing' || doc.status === 'uploading';
                          return (
                            <div>
                              <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold ${displayStatus.bg}`}>
                                {stuck
                                  ? <HiOutlineExclamationTriangle className="w-3 h-3" />
                                  : <span className={`w-1.5 h-1.5 rounded-full ${displayStatus.dot} ${isActive && !stuck ? 'animate-pulse' : ''}`} />}
                                {displayStatus.label}
                              </span>
                              {isActive && (
                                <p className={`text-[10px] mt-1 ${stuck ? 'text-orange-400 font-semibold' : 'text-gray-500'}`}>
                                  {stuck ? '⚠ 응답 없음 — 삭제 후 재업로드 하세요' : getElapsedLabel(doc.created_at)}
                                </p>
                              )}
                              {doc.status === 'failed' && doc.error_message && (
                                <p className="text-[10px] text-red-400 mt-1 max-w-[200px] truncate" title={doc.error_message}>{doc.error_message}</p>
                              )}
                            </div>
                          );
                        })()}
                      </td>
                      <td className="px-4 sm:px-6 py-4 text-[13px] text-gray-500 hidden md:table-cell">{new Date(doc.created_at).toLocaleDateString('ko-KR')}</td>
                      <td className="px-4 sm:px-6 py-4">
                        <div className="flex items-center gap-1">
                          {doc.status === 'completed' && (
                            <button onClick={() => handleDownload(doc)} className="p-2 text-gray-600 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all" title="다운로드">
                              <HiOutlineArrowDownTray className="w-4 h-4" />
                            </button>
                          )}
                          {(doc.status === 'failed' || isStuck(doc)) && (
                            <button onClick={() => handleDelete(doc)} className="p-2 text-gray-600 hover:text-red-400 hover:bg-red-500/[0.08] rounded-lg transition-all" title="삭제">
                              <HiOutlineTrash className="w-4 h-4" />
                            </button>
                          )}
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
    </div>
  );
}
