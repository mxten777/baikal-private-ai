/**
 * Admin - SettingsPage - LLM 모델 관리 + 감사 로그
 */
import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../api/client';
import toast from 'react-hot-toast';
import {
  HiOutlineCpuChip,
  HiOutlineCheckCircle,
  HiOutlineArrowPath,
  HiOutlineChartBar,
  HiOutlineClockIcon,
  HiOutlineSignal,
  HiOutlineBolt,
} from 'react-icons/hi2';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '—';
  const gb = bytes / (1024 ** 3);
  return gb >= 1 ? gb.toFixed(1) + ' GB' : (bytes / (1024 ** 2)).toFixed(0) + ' MB';
}

export default function SettingsPage() {
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [activating, setActivating] = useState(null);
  const [loadingModels, setLoadingModels] = useState(true);

  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadingLogs, setLoadingLogs] = useState(true);

  useEffect(() => {
    loadModels();
    loadLogs();
  }, []);

  const loadModels = async () => {
    setLoadingModels(true);
    try {
      const res = await adminAPI.listModels();
      setModels(res.data.models || []);
      setCurrentModel(res.data.current_model || '');
      setEmbeddingModel(res.data.embedding_model || '');
    } catch {
      toast.error('모델 목록 로드 실패');
    } finally {
      setLoadingModels(false);
    }
  };

  const handleActivate = async (modelName) => {
    if (modelName === currentModel) return;
    setActivating(modelName);
    try {
      await adminAPI.activateModel(modelName);
      setCurrentModel(modelName);
      setModels(prev => prev.map(m => ({ ...m, is_current: m.name === modelName })));
      toast.success(`'${modelName}' 모델로 전환되었습니다`);
    } catch (err) {
      toast.error(err.response?.data?.detail || '모델 전환 실패');
    } finally {
      setActivating(null);
    }
  };

  const loadLogs = async () => {
    setLoadingLogs(true);
    try {
      const [logsRes, statsRes] = await Promise.all([
        adminAPI.queryLogs(0, 20),
        adminAPI.queryLogStats(),
      ]);
      setLogs(logsRes.data || []);
      setStats(statsRes.data);
    } catch {
      toast.error('감사 로그 로드 실패');
    } finally {
      setLoadingLogs(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* 헤더 */}
        <div>
          <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-100 tracking-tight">시스템 설정</h1>
          <p className="text-sm text-gray-500 mt-1 font-medium">LLM 모델 관리 및 감사 로그</p>
        </div>

        {/* ── LLM 모델 섹션 ── */}
        <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
          <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center">
                <HiOutlineCpuChip className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="text-[15px] font-bold text-gray-200">LLM 모델</h2>
                <p className="text-[11px] text-gray-500">Ollama에 설치된 모델 목록 · 클릭으로 전환</p>
              </div>
            </div>
            <button onClick={loadModels} disabled={loadingModels} className="p-2 text-gray-500 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all">
              <HiOutlineArrowPath className={`w-4 h-4 ${loadingModels ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="p-4">
            {/* 현재 임베딩 모델 */}
            <div className="mb-4 px-4 py-3 rounded-lg bg-white/[0.02] border border-white/[0.04] flex items-center gap-3">
              <HiOutlineBolt className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span className="text-[12px] text-gray-400">임베딩 모델:</span>
              <span className="text-[12px] font-bold text-amber-300">{embeddingModel || '—'}</span>
              <span className="text-[10px] text-gray-600 ml-1">(변경 불가)</span>
            </div>

            {loadingModels ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <div key={i} className="shimmer-dark h-14 rounded-lg" />
                ))}
              </div>
            ) : models.length === 0 ? (
              <div className="py-10 text-center text-gray-500 text-sm">Ollama에 설치된 모델이 없습니다</div>
            ) : (
              <div className="space-y-2">
                {models.map((model) => (
                  <button
                    key={model.name}
                    onClick={() => handleActivate(model.name)}
                    disabled={activating === model.name}
                    className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                      model.is_current
                        ? 'bg-baikal-600/15 border-baikal-500/40'
                        : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.05] hover:border-white/[0.1]'
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${model.is_current ? 'bg-baikal-400' : 'bg-gray-600'}`} />
                    <div className="flex-1 min-w-0">
                      <p className={`text-[13px] font-semibold truncate ${model.is_current ? 'text-baikal-200' : 'text-gray-300'}`}>
                        {model.name}
                      </p>
                      <p className="text-[11px] text-gray-500">{formatBytes(model.size)}</p>
                    </div>
                    {model.is_current ? (
                      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-baikal-600/30 text-baikal-300 text-[10px] font-bold flex-shrink-0">
                        <HiOutlineCheckCircle className="w-3 h-3" /> 활성
                      </span>
                    ) : activating === model.name ? (
                      <HiOutlineArrowPath className="w-4 h-4 text-gray-500 animate-spin flex-shrink-0" />
                    ) : (
                      <span className="text-[11px] text-gray-600 flex-shrink-0">전환</span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── 감사 로그 통계 ── */}
        {stats && (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: '총 질의 수', value: stats.total_queries.toLocaleString(), icon: HiOutlineChartBar, color: 'text-baikal-400' },
              { label: '평균 신뢰도', value: (stats.avg_confidence * 100).toFixed(1) + '%', icon: HiOutlineSignal, color: 'text-emerald-400' },
              { label: '평균 응답시간', value: stats.avg_latency_ms.toLocaleString() + 'ms', icon: HiOutlineBolt, color: 'text-amber-400' },
            ].map(s => (
              <div key={s.label} className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                <s.icon className={`w-5 h-5 ${s.color} mb-2`} />
                <p className="text-2xl font-black text-gray-100">{s.value}</p>
                <p className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {/* ── 감사 로그 테이블 ── */}
        <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
          <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h2 className="text-[15px] font-bold text-gray-200">최근 질의 로그</h2>
              <span className="px-2 py-0.5 rounded-lg bg-white/[0.06] text-[11px] font-bold text-gray-400">{logs.length}</span>
            </div>
            <button onClick={loadLogs} disabled={loadingLogs} className="p-2 text-gray-500 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all">
              <HiOutlineArrowPath className={`w-4 h-4 ${loadingLogs ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {loadingLogs ? (
            <div className="p-8 text-center text-gray-500 text-sm">로딩 중...</div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-sm">기록된 질의가 없습니다</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[640px]">
                <thead>
                  <tr className="border-b border-white/[0.04]">
                    <th className="px-5 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em]">질문</th>
                    <th className="px-5 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] w-20">신뢰도</th>
                    <th className="px-5 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] w-24">응답시간</th>
                    <th className="px-5 py-3 text-left text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] w-32">시간</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3">
                        <p className="text-[13px] text-gray-300 truncate max-w-xs">{log.query}</p>
                        {log.response_summary && (
                          <p className="text-[11px] text-gray-600 truncate max-w-xs mt-0.5">{log.response_summary}</p>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`text-[12px] font-bold ${
                          (log.confidence_score ?? 0) >= 0.7 ? 'text-emerald-400' :
                          (log.confidence_score ?? 0) >= 0.4 ? 'text-amber-400' : 'text-red-400'
                        }`}>
                          {log.confidence_score != null ? (log.confidence_score * 100).toFixed(0) + '%' : '—'}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-[12px] text-gray-500">
                        {log.latency_ms != null ? log.latency_ms.toLocaleString() + 'ms' : '—'}
                      </td>
                      <td className="px-5 py-3 text-[11px] text-gray-600">
                        {log.created_at ? new Date(log.created_at).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
