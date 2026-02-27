/**
 * SearchPage - 프리미엄 문서 검색
 */
import React, { useState } from 'react';
import { searchAPI } from '../api/client';
import toast from 'react-hot-toast';
import {
  HiOutlineMagnifyingGlass,
  HiOutlineDocumentText,
  HiOutlineSparkles,
  HiOutlineArrowTrendingUp,
} from 'react-icons/hi2';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true); setSearched(true);
    try { const res = await searchAPI.search(query.trim()); setResults(res.data); }
    catch { toast.error('검색 실패'); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
      <div className="max-w-4xl mx-auto">
        {/* 헤더 */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-xl sm:text-[28px] font-extrabold text-gray-900 tracking-tight">문서 검색</h1>
          <p className="text-sm text-gray-400 mt-1 font-medium">업로드된 문서에서 의미 기반 검색</p>
        </div>

        {/* 검색창 */}
        <form onSubmit={handleSearch} className="mb-6 sm:mb-8">
          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="flex-1 relative">
              <HiOutlineMagnifyingGlass className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="파일명 또는 내용으로 검색..."
                className="w-full pl-12 pr-4 py-3.5 rounded-2xl border border-gray-200 bg-white text-sm text-gray-700 placeholder:text-gray-400 focus:outline-none focus:border-baikal-300 focus:ring-4 focus:ring-baikal-500/10 transition-all duration-200"
              />
            </div>
            <button type="submit" disabled={loading} className="px-7 py-3.5 rounded-2xl bg-gradient-to-r from-baikal-600 to-baikal-700 text-white text-sm font-semibold hover:from-baikal-700 hover:to-baikal-800 disabled:opacity-50 shadow-sm hover:shadow-md transition-all duration-200 w-full sm:w-auto">
              {loading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              ) : '검색'}
            </button>
          </div>
        </form>

        {/* 결과 */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white rounded-2xl border border-gray-100 p-5">
                <div className="shimmer w-48 h-5 rounded mb-3" />
                <div className="shimmer w-full h-4 rounded mb-2" />
                <div className="shimmer w-3/4 h-4 rounded" />
              </div>
            ))}
          </div>
        ) : searched && results.length === 0 ? (
          <div className="text-center py-16 animate-fade-in">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gray-50 flex items-center justify-center">
              <HiOutlineMagnifyingGlass className="w-7 h-7 text-gray-300" />
            </div>
            <p className="text-sm font-semibold text-gray-400">검색 결과가 없습니다</p>
            <p className="text-[11px] text-gray-300 mt-1">다른 키워드로 시도해보세요</p>
          </div>
        ) : results.length > 0 ? (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <HiOutlineSparkles className="w-4 h-4 text-baikal-500" />
              <p className="text-[13px] font-bold text-gray-500">{results.length}개 결과</p>
            </div>
            <div className="space-y-3">
              {results.map((result, idx) => (
                <div key={idx} className="group bg-white rounded-2xl border border-gray-100 p-5 hover:border-gray-200 hover:shadow-soft transition-all duration-200 animate-fade-in-up" style={{ animationDelay: `${idx * 60}ms` }}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 rounded-xl bg-baikal-50 flex items-center justify-center flex-shrink-0">
                      <HiOutlineDocumentText className="w-4 h-4 text-baikal-600" />
                    </div>
                    <h3 className="text-[14px] font-bold text-gray-800 group-hover:text-baikal-600 transition-colors">{result.filename}</h3>
                    {result.score && (
                      <div className="flex items-center gap-1 ml-auto">
                        <HiOutlineArrowTrendingUp className="w-3 h-3 text-emerald-500" />
                        <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-lg">{(result.score * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                  <p className="text-[13px] text-gray-500 leading-relaxed bg-gray-50/80 rounded-xl p-3.5">...{result.content_snippet}...</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-16 animate-fade-in">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-baikal-50 to-purple-50 flex items-center justify-center">
              <HiOutlineMagnifyingGlass className="w-7 h-7 text-baikal-600" />
            </div>
            <p className="text-sm font-semibold text-gray-400">검색어를 입력하여 문서를 찾아보세요</p>
            <p className="text-[11px] text-gray-300 mt-1">벡터 검색으로 의미적으로 유사한 내용을 찾습니다</p>
          </div>
        )}
      </div>
    </div>
  );
}
