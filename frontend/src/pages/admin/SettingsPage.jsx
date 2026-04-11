/**
 * Admin - SettingsPage — 5탭 KPI 대시보드 (P2-1/2/3)
 */
import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../api/client';
import toast from 'react-hot-toast';
import {
  HiOutlineCpuChip,
  HiOutlineCheckCircle,
  HiOutlineArrowPath,
  HiOutlineChartBar,
  HiOutlineSignal,
  HiOutlineBolt,
  HiOutlineUsers,
  HiOutlineShieldCheck,
  HiOutlineClipboardDocumentList,
  HiOutlineChartPie,
} from 'react-icons/hi2';

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '—';
  const gb = bytes / (1024 ** 3);
  return gb >= 1 ? gb.toFixed(1) + ' GB' : (bytes / (1024 ** 2)).toFixed(0) + ' MB';
}

/** 인라인 막대 차트 (SVG) — 주간 추이 */
function WeeklyTrendChart({ data }) {
  if (!data || data.length === 0) return null;
  const maxCount = Math.max(...data.map(d => d.count), 1);
  const H = 80;
  const barW = 28;
  const gap = 8;
  const W = data.length * (barW + gap) - gap;

  return (
    <svg viewBox={`0 0 ${W + 20} ${H + 28}`} width="100%" style={{ maxWidth: W + 20 }}>
      {data.map((d, i) => {
        const x = i * (barW + gap);
        const barH = maxCount > 0 ? Math.max((d.count / maxCount) * H, d.count > 0 ? 4 : 0) : 0;
        const y = H - barH;
        const fill = d.count === 0 ? '#2a2a3a' : '#4f8ef7';
        return (
          <g key={i}>
            <rect x={x} y={y} width={barW} height={barH} rx={4} fill={fill} opacity={0.85} />
            {d.count > 0 && (
              <text x={x + barW / 2} y={y - 4} textAnchor="middle" fontSize={9} fill="#9ca3af">{d.count}</text>
            )}
            <text x={x + barW / 2} y={H + 14} textAnchor="middle" fontSize={9} fill="#6b7280">{d.date}</text>
          </g>
        );
      })}
    </svg>
  );
}

/** 신뢰도 분포 — 수평 누적 바 */
function ConfidenceBar({ dist }) {
  const total = (dist?.high || 0) + (dist?.medium || 0) + (dist?.low || 0);
  if (!total) return <div className="h-3 rounded-full bg-white/[0.04]" />;
  const pct = (v) => ((v / total) * 100).toFixed(1);
  return (
    <div className="space-y-1.5">
      <div className="flex h-3 rounded-full overflow-hidden gap-px">
        {dist.high > 0 && <div style={{ width: pct(dist.high) + '%' }} className="bg-emerald-500" title={`High: ${dist.high}`} />}
        {dist.medium > 0 && <div style={{ width: pct(dist.medium) + '%' }} className="bg-amber-400" title={`Medium: ${dist.medium}`} />}
        {dist.low > 0 && <div style={{ width: pct(dist.low) + '%' }} className="bg-red-500" title={`Low: ${dist.low}`} />}
      </div>
      <div className="flex gap-4 text-[10px] text-gray-500">
        <span><span className="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1" />High {pct(dist.high)}%</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-amber-400 mr-1" />Medium {pct(dist.medium)}%</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-red-500 mr-1" />Low {pct(dist.low)}%</span>
      </div>
    </div>
  );
}

/** 단계별 지연시간 스택 바 */
function LatencyBar({ retrieval, reranking, llm }) {
  const total = (retrieval || 0) + (reranking || 0) + (llm || 0);
  if (!total) return <div className="h-3 rounded-full bg-white/[0.04]" />;
  const pct = (v) => ((v / total) * 100).toFixed(1);
  return (
    <div className="space-y-1.5">
      <div className="flex h-3 rounded-full overflow-hidden gap-px">
        <div style={{ width: pct(retrieval) + '%' }} className="bg-baikal-500" title={`검색: ${retrieval}ms`} />
        <div style={{ width: pct(reranking) + '%' }} className="bg-purple-500" title={`Reranking: ${reranking}ms`} />
        <div style={{ width: pct(llm) + '%' }} className="bg-amber-400" title={`LLM: ${llm}ms`} />
      </div>
      <div className="flex gap-4 text-[10px] text-gray-500">
        <span><span className="inline-block w-2 h-2 rounded-full bg-baikal-500 mr-1" />검색 {retrieval}ms</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-purple-500 mr-1" />Reranking {reranking}ms</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-amber-400 mr-1" />LLM {llm}ms</span>
      </div>
    </div>
  );
}

const TABS = [
  { id: 'executive', label: 'Executive', icon: HiOutlineChartBar },
  { id: 'retrieval', label: 'Retrieval', icon: HiOutlineSignal },
  { id: 'trust', label: 'Trust', icon: HiOutlineChartPie },
  { id: 'ops', label: 'Operations', icon: HiOutlineCpuChip },
  { id: 'governance', label: 'Governance', icon: HiOutlineShieldCheck },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('executive');

  // Executive + Retrieval + Trust 공통 데이터
  const [stats, setStats] = useState(null);
  const [kpiPerf, setKpiPerf] = useState(null);
  const [kpiUsers, setKpiUsers] = useState(null);
  const [kpiTrend, setKpiTrend] = useState(null);
  const [loadingKpi, setLoadingKpi] = useState(true);

  // Ops 데이터
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState('');
  const [embeddingModel, setEmbeddingModel] = useState('');
  const [activating, setActivating] = useState(null);
  const [loadingModels, setLoadingModels] = useState(false);

  // Governance 데이터
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [violations, setViolations] = useState(null);

  useEffect(() => { loadKpiData(); }, []);
  useEffect(() => {
    if (activeTab === 'ops' && models.length === 0) loadModels();
    if (activeTab === 'governance' && logs.length === 0) loadLogs();
  }, [activeTab]);

  const loadKpiData = async () => {
    setLoadingKpi(true);
    try {
      const [statsRes, perfRes, usersRes, trendRes] = await Promise.all([
        adminAPI.queryLogStats(),
        adminAPI.kpiRagPerformance(),
        adminAPI.kpiActiveUsers(),
        adminAPI.kpiWeeklyTrend(),
      ]);
      setStats(statsRes.data);
      setKpiPerf(perfRes.data);
      setKpiUsers(usersRes.data);
      setKpiTrend(trendRes.data?.trends || []);
    } catch {
      toast.error('KPI 데이터 로드 실패');
    } finally {
      setLoadingKpi(false);
    }
  };

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
      const [logsRes, violRes] = await Promise.all([
        adminAPI.queryLogs(),
        adminAPI.kpiPolicyViolations(),
      ]);
      setLogs(logsRes.data || []);
      setViolations(violRes.data);
    } catch {
      toast.error('감사 로그 로드 실패');
    } finally {
      setLoadingLogs(false);
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-100 tracking-tight">KPI 대시보드</h1>
            <p className="text-sm text-gray-500 mt-1 font-medium">RAG 품질 · 성능 · 운영 지표</p>
          </div>
          <button onClick={loadKpiData} disabled={loadingKpi}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] text-[12px] text-gray-400 transition-all">
            <HiOutlineArrowPath className={`w-3.5 h-3.5 ${loadingKpi ? 'animate-spin' : ''}`} />
            새로고침
          </button>
        </div>

        {/* 탭 */}
        <div className="flex gap-1 p-1 bg-white/[0.03] rounded-xl border border-white/[0.04]">
          {TABS.map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-[11px] font-semibold transition-all ${
                activeTab === tab.id
                  ? 'bg-baikal-600/30 text-baikal-300 border border-baikal-500/30'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03]'
              }`}>
              <tab.icon className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* ══ Executive 탭 ══ */}
        {activeTab === 'executive' && (
          <div className="space-y-5">
            {/* KPI 카드 4개 */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                {
                  label: '총 질의 수', icon: HiOutlineChartBar, color: 'text-baikal-400',
                  value: stats ? stats.total_queries.toLocaleString() : '—',
                },
                {
                  label: '평균 신뢰도', icon: HiOutlineSignal, color: 'text-emerald-400',
                  value: stats ? (stats.avg_confidence * 100).toFixed(1) + '%' : '—',
                },
                {
                  label: '평균 응답시간', icon: HiOutlineBolt, color: 'text-amber-400',
                  value: stats ? stats.avg_latency_ms.toLocaleString() + 'ms' : '—',
                },
                {
                  label: '활성 사용자 (7일)', icon: HiOutlineUsers, color: 'text-purple-400',
                  value: kpiUsers ? `${kpiUsers.wau}명 (${kpiUsers.wau_rate}%)` : '—',
                },
              ].map(s => (
                <div key={s.label} className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                  <s.icon className={`w-5 h-5 ${s.color} mb-2`} />
                  <p className="text-2xl font-black text-gray-100 leading-none">{loadingKpi ? '…' : s.value}</p>
                  <p className="text-[9px] text-gray-500 font-semibold uppercase tracking-wider mt-1.5">{s.label}</p>
                </div>
              ))}
            </div>

            {/* 피드백 + 출처 클릭률 */}
            {kpiPerf && (
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-3">Query Success Rate</p>
                  <p className="text-3xl font-black text-emerald-400">{kpiPerf.feedback.success_rate}%</p>
                  <p className="text-[11px] text-gray-600 mt-1">
                    👍 {kpiPerf.feedback.positive} · 👎 {kpiPerf.feedback.negative} · 응답 {kpiPerf.feedback.total}건
                  </p>
                </div>
                <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                  <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-3">Source Click-through Rate</p>
                  <p className="text-3xl font-black text-baikal-400">{kpiPerf.source_click_rate}%</p>
                  <p className="text-[11px] text-gray-600 mt-1">목표: 30% 이상</p>
                </div>
              </div>
            )}

            {/* 주간 추이 차트 */}
            {kpiTrend && kpiTrend.length > 0 && (
              <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-4">주간 질의 추이 (최근 7일)</p>
                <WeeklyTrendChart data={kpiTrend} />
              </div>
            )}
          </div>
        )}

        {/* ══ Retrieval 탭 ══ */}
        {activeTab === 'retrieval' && (
          <div className="space-y-4">
            {loadingKpi ? (
              <div className="py-16 text-center text-gray-500 text-sm">로딩 중...</div>
            ) : kpiPerf ? (
              <>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: '검색 단계', value: kpiPerf.latency.avg_retrieval_ms + 'ms', target: '≤1,500ms', ok: kpiPerf.latency.avg_retrieval_ms <= 1500, color: 'text-baikal-400' },
                    { label: 'Reranking', value: kpiPerf.latency.avg_reranking_ms + 'ms', target: '≤500ms', ok: kpiPerf.latency.avg_reranking_ms <= 500, color: 'text-purple-400' },
                    { label: 'LLM 생성', value: kpiPerf.latency.avg_llm_ms + 'ms', target: '—', ok: null, color: 'text-amber-400' },
                  ].map(s => (
                    <div key={s.label} className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                      <p className={`text-2xl font-black ${s.color}`}>{s.value}</p>
                      <p className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider mt-1">{s.label}</p>
                      <p className={`text-[10px] mt-1 ${s.ok === null ? 'text-gray-600' : s.ok ? 'text-emerald-500' : 'text-red-400'}`}>
                        목표 {s.target} {s.ok === true ? '✓' : s.ok === false ? '✗' : ''}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
                  <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-3">단계별 지연시간 분포</p>
                  <LatencyBar
                    retrieval={kpiPerf.latency.avg_retrieval_ms}
                    reranking={kpiPerf.latency.avg_reranking_ms}
                    llm={kpiPerf.latency.avg_llm_ms}
                  />
                  <div className="mt-3 flex items-center gap-2">
                    <span className="text-[10px] text-gray-500">총 평균:</span>
                    <span className={`text-[13px] font-bold ${kpiPerf.latency.avg_total_ms <= 8000 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {kpiPerf.latency.avg_total_ms.toLocaleString()}ms
                    </span>
                    <span className="text-[10px] text-gray-600">(목표 ≤8,000ms)</span>
                  </div>
                </div>
                <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider">측정 기준</p>
                  <p className="text-[11px] text-gray-400 mt-1">{kpiPerf.latency.sample_count.toLocaleString()}건 질의 평균 (RAG 파이프라인 3단계)</p>
                </div>
              </>
            ) : (
              <div className="py-16 text-center text-gray-500 text-sm">데이터 없음</div>
            )}
          </div>
        )}

        {/* ══ Trust 탭 ══ */}
        {activeTab === 'trust' && (
          <div className="space-y-4">
            {loadingKpi ? (
              <div className="py-16 text-center text-gray-500 text-sm">로딩 중...</div>
            ) : kpiPerf ? (
              <>
                <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-5">
                  <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-4">답변 신뢰도 분포 (P2-3)</p>
                  <ConfidenceBar dist={kpiPerf.confidence_distribution} />
                  <div className="grid grid-cols-3 gap-3 mt-4">
                    {[
                      { label: 'High ≥70%', value: kpiPerf.confidence_distribution.high, color: 'text-emerald-400' },
                      { label: 'Medium 40~70%', value: kpiPerf.confidence_distribution.medium, color: 'text-amber-400' },
                      { label: 'Low <40%', value: kpiPerf.confidence_distribution.low, color: 'text-red-400' },
                    ].map(s => (
                      <div key={s.label} className="text-center">
                        <p className={`text-xl font-black ${s.color}`}>{s.value}</p>
                        <p className="text-[9px] text-gray-500 mt-0.5">{s.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Answer Acceptance Rate</p>
                    <p className="text-3xl font-black text-emerald-400">{kpiPerf.feedback.success_rate}%</p>
                    <p className="text-[10px] text-gray-600 mt-1">목표: 70% 이상</p>
                    <div className="mt-2 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full" style={{ width: Math.min(kpiPerf.feedback.success_rate, 100) + '%' }} />
                    </div>
                  </div>
                  <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">출처 클릭률</p>
                    <p className="text-3xl font-black text-baikal-400">{kpiPerf.source_click_rate}%</p>
                    <p className="text-[10px] text-gray-600 mt-1">목표: 30% 이상</p>
                    <div className="mt-2 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div className="h-full bg-baikal-500 rounded-full" style={{ width: Math.min(kpiPerf.source_click_rate, 100) + '%' }} />
                    </div>
                  </div>
                </div>

                {/* 저신뢰도 리스크 알림 */}
                {kpiPerf.confidence_distribution.low > 0 && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 flex items-start gap-3">
                    <span className="text-red-400 text-lg">⚠</span>
                    <div>
                      <p className="text-[13px] font-bold text-red-300">저신뢰도 답변 {kpiPerf.confidence_distribution.low}건 발생</p>
                      <p className="text-[11px] text-red-400/70 mt-0.5">문서 품질 점검 또는 추가 문서 업로드를 권장합니다.</p>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="py-16 text-center text-gray-500 text-sm">데이터 없음</div>
            )}
          </div>
        )}

        {/* ══ Operations 탭 (기존 LLM 모델 관리) ══ */}
        {activeTab === 'ops' && (
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
            <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center">
                  <HiOutlineCpuChip className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h2 className="text-[15px] font-bold text-gray-200">LLM 모델</h2>
                  <p className="text-[11px] text-gray-500">Ollama 설치 모델 · 클릭으로 전환</p>
                </div>
              </div>
              <button onClick={loadModels} disabled={loadingModels} className="p-2 text-gray-500 hover:text-baikal-400 hover:bg-white/[0.04] rounded-lg transition-all">
                <HiOutlineArrowPath className={`w-4 h-4 ${loadingModels ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="p-4">
              <div className="mb-4 px-4 py-3 rounded-lg bg-white/[0.02] border border-white/[0.04] flex items-center gap-3">
                <HiOutlineBolt className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span className="text-[12px] text-gray-400">임베딩 모델:</span>
                <span className="text-[12px] font-bold text-amber-300">{embeddingModel || '—'}</span>
                <span className="text-[10px] text-gray-600 ml-1">(변경 불가)</span>
              </div>
              {loadingModels ? (
                <div className="space-y-2">{[1, 2, 3].map(i => <div key={i} className="shimmer-dark h-14 rounded-lg" />)}</div>
              ) : models.length === 0 ? (
                <div className="py-10 text-center text-gray-500 text-sm">Ollama에 설치된 모델이 없습니다</div>
              ) : (
                <div className="space-y-2">
                  {models.map((model) => (
                    <button key={model.name} onClick={() => handleActivate(model.name)} disabled={activating === model.name}
                      className={`w-full flex items-center gap-4 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                        model.is_current ? 'bg-baikal-600/15 border-baikal-500/40' : 'bg-white/[0.02] border-white/[0.05] hover:bg-white/[0.05] hover:border-white/[0.1]'
                      }`}>
                      <div className={`w-2 h-2 rounded-full flex-shrink-0 ${model.is_current ? 'bg-baikal-400' : 'bg-gray-600'}`} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-[13px] font-semibold truncate ${model.is_current ? 'text-baikal-200' : 'text-gray-300'}`}>{model.name}</p>
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
        )}

        {/* ══ Governance 탭 (기존 감사 로그) ══ */}
        {activeTab === 'governance' && (
          <div className="space-y-4">
          {/* Policy Violation 카드 */}
          {violations && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">포리시 위반 전체</p>
                <p className={`text-3xl font-black ${violations.total_violations > 0 ? 'text-red-400' : 'text-emerald-400'}`}>{violations.total_violations}</p>
                <p className="text-[11px] text-gray-500 mt-1">Guardrail 에 의해 차단된 질문 합계</p>
              </div>
              <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">오늘 위반</p>
                <p className={`text-3xl font-black ${violations.today_violations > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>{violations.today_violations}</p>
                <p className="text-[11px] text-gray-500 mt-1">오늘(일일) 차단 건수</p>
              </div>
              <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] p-4">
                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">보안 상태</p>
                <p className={`text-3xl font-black ${violations.total_violations === 0 ? 'text-emerald-400' : violations.today_violations > 0 ? 'text-red-400' : 'text-amber-400'}`}>
                  {violations.total_violations === 0 ? '안전' : violations.today_violations > 0 ? '경고' : '양호'}
                </p>
                <p className="text-[11px] text-gray-500 mt-1">목표: 일일 0건</p>
              </div>
            </div>
          )}
          {violations && violations.recent && violations.recent.length > 0 && (
            <div className="bg-white/[0.03] rounded-xl border border-red-500/20 overflow-hidden">
              <div className="px-6 py-4 border-b border-white/[0.04]">
                <h3 className="text-[13px] font-bold text-red-400">최근 정책 위반 내역</h3>
              </div>
              <div className="divide-y divide-white/[0.03]">
                {violations.recent.map((v) => (
                  <div key={v.id} className="px-6 py-3">
                    <p className="text-[12px] text-gray-300 truncate">{v.query}</p>
                    <p className="text-[11px] text-red-400/70 mt-0.5">{v.reason}</p>
                    <p className="text-[10px] text-gray-600 mt-0.5">{v.created_at ? new Date(v.created_at).toLocaleString('ko-KR') : ''}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="bg-white/[0.03] rounded-xl border border-white/[0.06] overflow-hidden">
            <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
              <div className="flex items-center gap-3">
                <HiOutlineClipboardDocumentList className="w-5 h-5 text-baikal-400" />
                <h2 className="text-[15px] font-bold text-gray-200">질의 감사 로그</h2>
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
        )}
      </div>
    </div>
  );
}
