/**
 * ChatPage - 프리미엄 AI 채팅
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
} from 'react-icons/hi2';

export default function ChatPage() {
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
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

  return (
    <div className="flex h-full relative">
      {/* 모바일 세션 오버레이 */}
      {showSessions && (
        <div className="fixed inset-0 z-30 bg-black/30 backdrop-blur-sm md:hidden" onClick={() => setShowSessions(false)} />
      )}

      {/* ── 세션 목록 사이드바 ── */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-[280px] bg-white border-r border-gray-100/80 flex flex-col transition-transform duration-300 ease-in-out
        md:relative md:w-[260px] md:translate-x-0 md:z-auto
        ${showSessions ? 'translate-x-0' : '-translate-x-full'}
      `}>
        {/* 모바일 헤더 */}
        <div className="flex items-center justify-between p-3 pb-0 md:hidden">
          <p className="text-sm font-bold text-gray-700 px-1">대화 목록</p>
          <button onClick={() => setShowSessions(false)} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg">
            <HiOutlineChevronLeft className="w-5 h-5" />
          </button>
        </div>
        <div className="p-3 pb-2">
          <button onClick={() => { createSession(); setShowSessions(false); }} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-baikal-600 to-baikal-700 hover:from-baikal-700 hover:to-baikal-800 shadow-sm hover:shadow-md transition-all duration-200">
            <HiOutlinePlusCircle className="w-4.5 h-4.5" />
            새 대화
          </button>
        </div>

        <div className="px-3 py-2">
          <p className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.1em]">대화 목록</p>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
          {sessions.map((session) => {
            const isActive = activeSession === session.id;
            return (
              <div
                key={session.id}
                className={`group flex items-center gap-2.5 px-3 py-2.5 cursor-pointer rounded-xl transition-all duration-200 ${
                  isActive ? 'bg-baikal-50/80 shadow-sm' : 'hover:bg-gray-50/80'
                }`}
                onClick={() => { setActiveSession(session.id); setShowSessions(false); }}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${
                  isActive ? 'bg-baikal-600 text-white' : 'bg-gray-100 text-gray-400'
                }`}>
                  <HiOutlineChatBubbleLeftRight className="w-3.5 h-3.5" />
                </div>
                <p className={`text-[13px] truncate flex-1 ${isActive ? 'font-semibold text-gray-800' : 'text-gray-500'}`}>
                  {session.title}
                </p>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteSession(session.id); }}
                  className="p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all rounded-lg hover:bg-red-50"
                >
                  <HiOutlineTrash className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
          {sessions.length === 0 && (
            <div className="px-4 py-12 text-center">
              <div className="w-10 h-10 rounded-xl bg-gray-50 flex items-center justify-center mx-auto mb-3">
                <HiOutlineChatBubbleLeftRight className="w-5 h-5 text-gray-300" />
              </div>
              <p className="text-xs text-gray-400 font-medium">대화가 없습니다</p>
              <p className="text-[10px] text-gray-300 mt-0.5">새 대화를 시작해보세요</p>
            </div>
          )}
        </div>
      </div>

      {/* ── 채팅 영역 ── */}
      <div className="flex-1 flex flex-col bg-gray-50/50 min-w-0">
        {/* 모바일 채팅 헤더 */}
        <div className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-100 bg-white md:hidden">
          <button onClick={() => setShowSessions(true)} className="p-1.5 -ml-1 text-gray-500 hover:text-baikal-600 rounded-lg hover:bg-baikal-50 transition-colors">
            <HiOutlineChatBubbleLeftRight className="w-5 h-5" />
          </button>
          <p className="text-sm font-semibold text-gray-700 truncate">
            {sessions.find(s => s.id === activeSession)?.title || '새 대화'}
          </p>
        </div>
        {/* 메시지 */}
        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full animate-fade-in">
              <div className="text-center max-w-lg px-4 sm:px-0">
                {/* 로고 영역 */}
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-baikal-50 via-purple-50 to-fuchsia-50 mb-7 relative">
                  <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-baikal-200/30 via-transparent to-purple-200/30 animate-glow-pulse" />
                  <HiOutlineSparkles className="w-9 h-9 text-baikal-600 relative z-10" />
                </div>

                <h2 className="text-xl sm:text-[28px] font-black text-gray-900 tracking-tight mb-1.5">
                  무엇이든 물어보세요
                </h2>
                <p className="text-sm text-gray-400 font-medium mb-10">
                  업로드된 문서를 기반으로 AI가 정확한 답변을 제공합니다
                </p>

                {/* 기능 팁 카드 */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
                  {[
                    { icon: HiOutlineDocumentText, title: '문서 질문', desc: '업로드한 문서 내용으로 질문하세요', gradient: 'from-baikal-500 to-blue-600' },
                    { icon: HiOutlineLightBulb, title: '요약 요청', desc: '"이 문서를 요약해줘" 형식을 사용하세요', gradient: 'from-amber-500 to-orange-500' },
                    { icon: HiOutlineSparkles, title: '구체적 질문', desc: '구체적인 질문일수록 정확한 답변을 받아요', gradient: 'from-purple-500 to-fuchsia-500' },
                  ].map((tip, idx) => (
                    <div key={idx} className="group p-4 rounded-2xl bg-white border border-gray-100 hover:border-gray-200 hover:shadow-soft transition-all duration-200 cursor-default">
                      <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${tip.gradient} flex items-center justify-center mb-3 shadow-sm group-hover:shadow-md transition-shadow`}>
                        <tip.icon className="w-4.5 h-4.5 text-white" />
                      </div>
                      <p className="text-[13px] font-bold text-gray-800 mb-1">{tip.title}</p>
                      <p className="text-[11px] text-gray-400 leading-relaxed">{tip.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              {messages.map((msg, idx) => (
                <ChatMessage key={msg.id || idx} message={msg} />
              ))}
              {loading && (
                <div className="px-6 py-5">
                  <div className="flex gap-3 items-start">
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <span className="text-white font-black text-[10px]">AI</span>
                    </div>
                    <div className="flex items-center gap-3 pt-1.5">
                      <div className="flex gap-1">
                        {[0, 1, 2].map((i) => (
                          <div key={i} className="w-2 h-2 bg-baikal-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
                        ))}
                      </div>
                      <p className="text-sm text-gray-400 font-medium animate-pulse-soft">답변 생성 중...</p>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* ── 입력 영역 ── */}
        <div className="border-t border-gray-100 bg-white p-3 sm:p-4">
          <form onSubmit={handleAsk} className="max-w-4xl mx-auto">
            <div className="flex gap-2.5 items-end">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="문서 내용에 대해 질문하세요..."
                  className="w-full px-4 py-3.5 bg-gray-50 border border-gray-200 rounded-2xl text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:bg-white focus:border-baikal-300 focus:ring-4 focus:ring-baikal-500/10 transition-all duration-200"
                  disabled={loading}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !question.trim()}
                className="p-3.5 rounded-2xl bg-gradient-to-r from-baikal-600 to-baikal-700 text-white hover:from-baikal-700 hover:to-baikal-800 shadow-sm hover:shadow-md disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
              >
                <HiOutlinePaperAirplane className="w-5 h-5" />
              </button>
            </div>
            <p className="text-center text-[10px] text-gray-300 mt-2.5 font-medium">
              AI 답변은 문서 기반이며, 정확하지 않을 수 있습니다
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}
