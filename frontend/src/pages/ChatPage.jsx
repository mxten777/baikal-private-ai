/**
 * ChatPage - 전문 RAG 시스템 UI
 * 중앙 집중형 + 다크 세션 패널
 */
import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../api/client';
import ChatMessage from '../components/ChatMessage';
import toast from 'react-hot-toast';
import {
  HiOutlinePaperAirplane,
  HiOutlinePlusCircle,
  HiOutlineTrash,
  HiOutlineChatBubbleLeftRight,
  HiOutlineDocumentText,
  HiOutlineLightBulb,
  HiOutlineSparkles,
  HiOutlineChevronLeft,
  HiOutlineMagnifyingGlass,
  HiOutlineArrowPath,
} from 'react-icons/hi2';

export default function ChatPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [showSessions, setShowSessions] = useState(false);

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { if (activeSession) loadMessages(activeSession); }, [activeSession]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const loadSessions = async () => {
    try {
      const res = await chatAPI.sessions();
      setSessions(res.data);
      if (res.data.length > 0 && !activeSession) setActiveSession(res.data[0].id);
    } catch { toast.error('세션 로드 실패'); }
  };

  const loadMessages = async (sessionId) => {
    try { const res = await chatAPI.messages(sessionId); setMessages(res.data); }
    catch { toast.error('메시지 로드 실패'); }
  };

  const createSession = async () => {
    try {
      const res = await chatAPI.createSession('새 대화');
      setSessions([res.data, ...sessions]);
      setActiveSession(res.data.id);
      setMessages([]);
    } catch { toast.error('세션 생성 실패'); }
  };

  const deleteSession = async (id) => {
    try {
      await chatAPI.deleteSession(id);
      const updated = sessions.filter((s) => s.id !== id);
      setSessions(updated);
      if (activeSession === id) { setActiveSession(updated.length > 0 ? updated[0].id : null); setMessages([]); }
    } catch { toast.error('세션 삭제 실패'); }
  };

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;
    if (!activeSession) {
      try {
        const res = await chatAPI.createSession('새 대화');
        setSessions([res.data, ...sessions]);
        setActiveSession(res.data.id);
        await askQuestion(res.data.id, question.trim());
      } catch { toast.error('세션 생성 실패'); }
      return;
    }
    await askQuestion(activeSession, question.trim());
  };

  const askQuestion = async (sessionId, q) => {
    setLoading(true);
    const userMsg = { role: 'user', content: q, id: 'user-' + Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setQuestion('');
    const streamingMsgId = 'streaming-' + Date.now();
    let fullAnswer = '';
    let sources = [];

    try {
      setMessages((prev) => [...prev, { role: 'assistant', content: '', sources: null, id: streamingMsgId }]);
      for await (const event of chatAPI.askStream(sessionId, q)) {
        if (event.type === 'sources') { sources = event.sources || []; }
        else if (event.type === 'token') {
          fullAnswer += event.content;
          setMessages((prev) => prev.map((m) => m.id === streamingMsgId ? { ...m, content: fullAnswer } : m));
        } else if (event.type === 'done') {
          setMessages((prev) => prev.map((m) => m.id === streamingMsgId ? { ...m, content: fullAnswer || event.content, sources: { documents: sources } } : m));
        } else if (event.type === 'error') {
          toast.error(event.content || 'AI 응답 오류');
          setMessages((prev) => prev.filter((m) => m.id !== streamingMsgId));
        }
      }
      loadSessions();
    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== streamingMsgId));
      try {
        const res = await chatAPI.ask(sessionId, q);
        setMessages((prev) => [...prev, { role: 'assistant', content: res.data.answer, sources: { documents: res.data.sources }, id: res.data.message_id }]);
        loadSessions();
      } catch (fallbackErr) {
        toast.error(fallbackErr.response?.data?.detail || fallbackErr.message || 'AI 답변 생성 실패');
      }
    } finally { setLoading(false); }
  };

  const handleQuickQuestion = (q) => {
    setQuestion(q);
    inputRef.current?.focus();
  };

  return (
    <div className="flex h-full relative">
      {/* 모바일 세션 오버레이 */}
      {showSessions && (
        <div className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm md:hidden" onClick={() => setShowSessions(false)} />
      )}

      {/* ── 세션 패널 ── */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-[260px] bg-[#13131d] border-r border-white/[0.04] flex flex-col transition-transform duration-300 ease-in-out
        md:relative md:w-[240px] md:translate-x-0 md:z-auto
        ${showSessions ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between p-3 pb-0 md:hidden">
          <p className="text-xs font-semibold text-gray-400 px-1">대화 목록</p>
          <button onClick={() => setShowSessions(false)} className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg">
            <HiOutlineChevronLeft className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3">
          <button
            onClick={() => { createSession(); setShowSessions(false); }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-[13px] font-medium text-gray-400 border border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1] transition-all duration-200"
          >
            <HiOutlinePlusCircle className="w-4 h-4" />
            새 대화
          </button>
        </div>

        <div className="px-4 py-1.5">
          <p className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider">최근 대화</p>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
          {sessions.map((session) => {
            const isActive = activeSession === session.id;
            return (
              <div
                key={session.id}
                className={`group flex items-center gap-2 px-2.5 py-2 cursor-pointer rounded-lg transition-all duration-150 ${
                  isActive ? 'bg-white/[0.06] text-gray-200' : 'text-gray-500 hover:bg-white/[0.03] hover:text-gray-300'
                }`}
                onClick={() => { setActiveSession(session.id); setShowSessions(false); }}
              >
                <HiOutlineChatBubbleLeftRight className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                <p className="text-[12px] truncate flex-1">{session.title}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  className="p-1 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all rounded"
                >
                  <HiOutlineTrash className="w-3 h-3" />
                </button>
              </div>
            );
          })}
          {sessions.length === 0 && (
            <div className="px-3 py-10 text-center">
              <HiOutlineChatBubbleLeftRight className="w-6 h-6 text-gray-700 mx-auto mb-2" />
              <p className="text-[11px] text-gray-600">대화가 없습니다</p>
            </div>
          )}
        </div>
      </div>

      {/* ── 메인 채팅 영역 ── */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0f0f17]">
        {/* 상단 바 */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.04] bg-[#0f0f17]/80 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <button onClick={() => setShowSessions(true)} className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg hover:bg-white/[0.05] transition-colors md:hidden">
              <HiOutlineChatBubbleLeftRight className="w-4.5 h-4.5" />
            </button>
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-[12px] font-medium text-gray-500">
                {sessions.find(s => s.id === activeSession)?.title || 'BAIKAL AI'}
              </span>
            </div>
          </div>
          <span className="text-[10px] text-gray-600 font-medium hidden sm:block">RAG Engine v1.0</span>
        </div>

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center w-full max-w-[580px] px-6 animate-fade-in">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-baikal-500 to-purple-600 mb-6 shadow-lg shadow-baikal-500/20">
                  <HiOutlineSparkles className="w-7 h-7 text-white" />
                </div>
                <h2 className="text-2xl sm:text-[28px] font-extrabold text-gray-100 tracking-tight mb-2">
                  무엇을 알고 싶으세요?
                </h2>
                <p className="text-[14px] text-gray-500 mb-8">
                  업로드된 문서를 기반으로 정확한 답변을 제공합니다
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-8">
                  {[
                    { icon: HiOutlineDocumentText, text: '연차휴가 규정을 알려주세요', color: 'text-blue-500' },
                    { icon: HiOutlineLightBulb, text: '이 문서를 요약해주세요', color: 'text-amber-500' },
                    { icon: HiOutlineMagnifyingGlass, text: '복리후생 제도는 어떻게 되나요?', color: 'text-emerald-500' },
                    { icon: HiOutlineSparkles, text: '2025년 총 매출 현황은?', color: 'text-purple-500' },
                  ].map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuickQuestion(item.text)}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl border border-white/[0.06] hover:border-white/[0.12] hover:bg-white/[0.03] text-left transition-all duration-200 group"
                    >
                      <item.icon className={`w-4 h-4 ${item.color} flex-shrink-0`} />
                      <span className="text-[13px] text-gray-500 group-hover:text-gray-300 transition-colors">{item.text}</span>
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  {['PDF', 'DOCX', 'XLSX', '시맨틱 검색', '실시간 스트리밍'].map((tag) => (
                    <span key={tag} className="px-2.5 py-1 rounded-full text-[10px] font-semibold bg-white/[0.04] text-gray-500">{tag}</span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto w-full px-4 sm:px-6 pt-5">
              {messages.map((msg, idx) => (
                <ChatMessage key={msg.id || idx} message={msg} />
              ))}
              {loading && (
                <div className="px-5 py-6">
                  <div className="flex gap-3 items-start">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-bold text-[9px]">AI</span>
                    </div>
                    <div className="pt-0.5">
                      <div className="flex items-center gap-2 mb-2">
                        <HiOutlineArrowPath className="w-3.5 h-3.5 text-baikal-500 animate-spin" />
                        <span className="text-[12px] text-gray-400 font-medium">분석 및 답변 생성 중...</span>
                      </div>
                      <div className="space-y-2">
                        <div className="h-3 bg-white/[0.06] rounded-full w-72 animate-pulse" />
                        <div className="h-3 bg-white/[0.06] rounded-full w-56 animate-pulse" style={{ animationDelay: '150ms' }} />
                        <div className="h-3 bg-white/[0.06] rounded-full w-64 animate-pulse" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} className="h-4" />
            </div>
          )}
        </div>

        {/* ── 입력 영역 ── */}
        <div className="border-t border-white/[0.04] bg-[#0f0f17] px-4 py-3 sm:px-6 sm:py-4">
          <form onSubmit={handleAsk} className="max-w-3xl mx-auto">
            <div className="relative flex items-center">
              <input
                ref={inputRef}
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="질문을 입력하세요..."
                className="w-full pl-4 pr-12 py-3 bg-white/[0.04] border border-white/[0.06] rounded-xl text-[14px] text-gray-200 placeholder:text-gray-600 focus:outline-none focus:bg-white/[0.06] focus:border-baikal-500/40 focus:ring-2 focus:ring-baikal-500/10 transition-all duration-200"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="absolute right-1.5 p-2 rounded-lg bg-baikal-600 text-white hover:bg-baikal-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-200"
              >
                <HiOutlinePaperAirplane className="w-4 h-4" />
              </button>
            </div>
            <p className="text-center text-[10px] text-gray-600 mt-2 font-medium">
              BAIKAL AI · 문서 기반 RAG 답변 · 정확하지 않을 수 있습니다
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
