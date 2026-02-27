/**
 * ChatMessage - 프리미엄 채팅 메시지
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { HiOutlineUser, HiOutlineDocumentText } from 'react-icons/hi2';

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`px-4 py-4 sm:px-6 sm:py-5 ${isUser ? '' : 'bg-white/60'}`}>
      <div className="flex gap-3 sm:gap-3.5 items-start">
        {/* 아바타 */}
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
          isUser
            ? 'bg-gray-100 text-gray-500'
            : 'bg-gradient-to-br from-baikal-600 to-purple-600 text-white shadow-sm'
        }`}>
          {isUser ? (
            <HiOutlineUser className="w-4 h-4" />
          ) : (
            <span className="font-black text-[10px]">AI</span>
          )}
        </div>

        {/* 메시지 */}
        <div className="flex-1 min-w-0 pt-0.5">
          <p className={`text-[11px] font-bold uppercase tracking-[0.08em] mb-1.5 ${
            isUser ? 'text-gray-400' : 'text-baikal-600'
          }`}>
            {isUser ? '나' : 'BAIKAL AI'}
          </p>
          <div className="prose prose-sm max-w-none text-gray-700 leading-relaxed [&>p]:mb-2 [&>ul]:mb-2 [&>ol]:mb-2 [&_code]:text-baikal-700 [&_code]:bg-baikal-50 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded-md [&_code]:text-[13px] [&_pre]:bg-gray-900 [&_pre]:text-gray-100 [&_pre]:rounded-xl [&_pre]:p-3 [&_pre]:sm:p-4 [&_pre]:overflow-x-auto [&_pre]:text-xs [&_pre]:sm:text-sm">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>

          {/* 참고 문서 */}
          {!isUser && message.sources?.documents?.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100/80">
              <p className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.1em] mb-2.5">
                참고 문서
              </p>
              <div className="flex flex-wrap gap-1.5">
                {message.sources.documents.map((src, idx) => (
                  <span key={idx} className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold bg-gray-50 border border-gray-100 text-gray-600 hover:bg-white hover:border-gray-200 transition-colors">
                    <HiOutlineDocumentText className="w-3 h-3 text-gray-400" />
                    {src.filename}
                    {src.relevance_score && (
                      <span className="ml-0.5 px-1.5 py-0.5 rounded-md bg-baikal-50 text-baikal-600 text-[9px] font-bold">
                        {(src.relevance_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
