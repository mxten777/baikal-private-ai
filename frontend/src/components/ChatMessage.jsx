/**
 * ChatMessage - 다크 테마 Perplexity-스타일 메시지
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { HiOutlineDocumentText } from 'react-icons/hi2';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

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
      {/* AI 라벨 */}
      <div className="flex items-center gap-2 mb-2">
        <div className="w-5 h-5 rounded-md bg-gradient-to-br from-baikal-500 to-purple-600 flex items-center justify-center">
          <span className="text-white font-black text-[7px]">B</span>
        </div>
        <span className="text-[11px] font-semibold text-gray-500">BAIKAL AI</span>
      </div>

      {/* AI 응답 */}
      <div className="pl-7 prose prose-sm prose-invert max-w-none text-gray-300 leading-[1.75] [&>p]:mb-2.5 [&>ul]:mb-2 [&>ol]:mb-2 [&_li]:mb-0.5 [&_code]:text-baikal-300 [&_code]:bg-white/[0.06] [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded-md [&_code]:text-[12px] [&_pre]:bg-black/40 [&_pre]:text-gray-200 [&_pre]:rounded-lg [&_pre]:p-3 [&_pre]:overflow-x-auto [&_pre]:text-xs [&_strong]:text-gray-100 [&_h1]:text-gray-100 [&_h2]:text-gray-100 [&_h3]:text-gray-200">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      {/* 참고 문서 */}
      {message.sources?.documents?.length > 0 && (
        <div className="pl-7 mt-3 pt-2.5 border-t border-white/[0.05]">
          <p className="text-[9px] font-semibold text-gray-600 uppercase tracking-widest mb-2">참고 문서</p>
          <div className="flex flex-wrap gap-1.5">
            {message.sources.documents.map((src, idx) => (
              <span key={idx} className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-medium bg-white/[0.04] text-gray-400 border border-white/[0.06]">
                <HiOutlineDocumentText className="w-3 h-3 text-gray-500" />
                {src.filename}
                {src.relevance_score && (
                  <span className="ml-0.5 text-[9px] text-baikal-400 font-bold">
                    {(src.relevance_score * 100).toFixed(0)}%
                  </span>
                )}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
