/**
 * ChatMessage - 다크 테마 Perplexity-스타일 메시지
 */
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { HiOutlineDocumentText, HiOutlineXMark, HiOutlineSignal } from 'react-icons/hi2';

function ChunkPreviewModal({ source, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-[#1a1a2e] border border-white/[0.08] rounded-2xl shadow-2xl max-w-lg w-full max-h-[70vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <HiOutlineDocumentText className="w-4 h-4 text-baikal-400" />
            <span className="text-[13px] font-semibold text-gray-200 truncate max-w-[280px]">{source.filename}</span>
            <span className="text-[10px] text-gray-500">청크 {(source.chunk_index ?? 0) + 1}</span>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-500 hover:text-gray-300 rounded-lg hover:bg-white/[0.05] transition-colors">
            <HiOutlineXMark className="w-4 h-4" />
          </button>
        </div>
        <div className="p-4 overflow-y-auto flex-1">
          <p className="text-[13px] text-gray-300 leading-relaxed whitespace-pre-wrap">
            {source.chunk_content || '내용 미리보기 없음'}
          </p>
        </div>
        <div className="px-4 py-2.5 border-t border-white/[0.06] flex items-center gap-2">
          <HiOutlineSignal className="w-3.5 h-3.5 text-baikal-400" />
          <span className="text-[11px] text-gray-500">관련도:</span>
          <span className="text-[11px] font-bold text-baikal-400">{source.relevance_score ? (source.relevance_score * 100).toFixed(0) + '%' : 'N/A'}</span>
        </div>
      </div>
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const [previewSource, setPreviewSource] = useState(null);

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[85%] px-4 py-2.5 rounded-2xl rounded-tr-md bg-baikal-600 text-white text-[14px] leading-relaxed shadow-lg shadow-baikal-600/10">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      {/* AI 라벨 + 신뢰도 점수 */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center">
          <span className="text-white font-black text-[7px]">B</span>
        </div>
        <span className="text-[11px] font-semibold text-gray-500">BAIKAL AI</span>
        {message.confidence_score != null && message.confidence_score > 0 && (
          <span className="flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-baikal-600/20 border border-baikal-500/30">
            <HiOutlineSignal className="w-2.5 h-2.5 text-baikal-400" />
            <span className="text-[9px] font-bold text-baikal-400">
              신뢰도 {(message.confidence_score * 100).toFixed(0)}%
            </span>
          </span>
        )}
      </div>

      {/* AI 응답 */}
      <div className="pl-7 prose prose-sm prose-invert max-w-none text-gray-300 leading-[1.75] [&>p]:mb-2.5 [&>ul]:mb-2 [&>ol]:mb-2 [&_li]:mb-0.5 [&_code]:text-baikal-300 [&_code]:bg-white/[0.06] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded-md [&_code]:text-[12px] [&_pre]:bg-black/40 [&_pre]:text-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_pre]:overflow-x-auto [&_pre]:text-xs [&_strong]:text-gray-100 [&_h1]:text-gray-100 [&_h2]:text-gray-100 [&_h3]:text-gray-200">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      {/* 참고 문서 (클릭 시 청크 미리보기) */}
      {message.sources?.documents?.length > 0 && (
        <div className="pl-7 mt-3 pt-2.5 border-t border-white/[0.05]">
          <p className="text-[9px] font-semibold text-gray-600 uppercase tracking-widest mb-2">참고 문서</p>
          <div className="flex flex-wrap gap-1.5">
            {message.sources.documents.map((src, idx) => (
              <button
                key={idx}
                onClick={() => setPreviewSource(src)}
                className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium bg-white/[0.04] text-gray-400 border border-white/[0.06] transition-all duration-150 hover:bg-white/[0.08] hover:text-gray-200 hover:border-white/[0.12] cursor-pointer"
                title="클릭하여 내용 미리보기"
              >
                <HiOutlineDocumentText className="w-3 h-3 text-gray-500" />
                {src.filename}
                {src.relevance_score && (
                  <span className="ml-0.5 text-[9px] text-baikal-400 font-bold">
                    {(src.relevance_score * 100).toFixed(0)}%
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {previewSource && <ChunkPreviewModal source={previewSource} onClose={() => setPreviewSource(null)} />}
    </div>
  );
}
