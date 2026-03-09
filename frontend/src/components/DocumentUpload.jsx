/**
 * DocumentUpload - 프리미엄 파일 업로드
 */
import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { documentsAPI } from '../api/client';
import { HiOutlineCloudArrowUp, HiOutlineDocument } from 'react-icons/hi2';
import toast from 'react-hot-toast';

const ACCEPTED = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/x-hwp': ['.hwp'],
  'application/haansofthwp': ['.hwp'],
  'application/vnd.hancom.hwp': ['.hwp'],
  'application/vnd.hancom.hwpx': ['.hwpx'],
};

export default function DocumentUpload({ onUploaded }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      for (const file of acceptedFiles) {
        setUploading(true); setProgress(0);
        try {
          await documentsAPI.upload(file, (e) => { if (e.total) setProgress(Math.round((e.loaded * 100) / e.total)); });
          toast.success(`${file.name} 업로드 완료`);
          onUploaded?.();
        } catch (err) { toast.error(`${file.name}: ${err.response?.data?.detail || '업로드 실패'}`); }
        finally { setUploading(false); setProgress(0); }
      }
    }, [onUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: ACCEPTED, maxSize: 100 * 1024 * 1024, disabled: uploading });

  return (
    <div
      {...getRootProps()}
      className={`relative rounded-2xl p-5 sm:p-8 text-center cursor-pointer transition-all duration-300 overflow-hidden ${
        isDragActive
          ? 'bg-baikal-500/10 border-2 border-baikal-500/40 shadow-lg shadow-baikal-500/10'
          : uploading
          ? 'bg-white/[0.02] border-2 border-white/[0.06] cursor-not-allowed'
          : 'bg-white/[0.03] border-2 border-dashed border-white/[0.08] hover:border-baikal-500/30 hover:bg-white/[0.05]'
      }`}
    >
      <input {...getInputProps()} />

      {uploading ? (
        <div className="animate-fade-in">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center">
            <HiOutlineDocument className="w-6 h-6 text-white animate-pulse" />
          </div>
          <p className="text-sm font-semibold text-gray-300 mb-1">업로드 중...</p>
          <p className="text-3xl font-black text-gray-100 mb-3">{progress}%</p>
          <div className="w-56 mx-auto bg-white/[0.06] rounded-full h-1.5 overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-baikal-600 to-purple-600 transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
        </div>
      ) : (
        <div>
          <div className={`w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-all duration-300 ${
            isDragActive ? 'bg-gradient-to-br from-baikal-600 to-purple-600 scale-110' : 'bg-white/[0.06]'
          }`}>
            <HiOutlineCloudArrowUp className={`w-6 h-6 transition-colors ${isDragActive ? 'text-white' : 'text-gray-500'}`} />
          </div>
          <p className="text-sm font-semibold text-gray-300 mb-0.5">
            {isDragActive ? '여기에 놓으세요!' : '파일을 드래그하거나 클릭하여 업로드'}
          </p>
          <p className="text-[11px] text-gray-500 font-medium">PDF, DOCX, XLSX, HWP, HWPX · 최대 100MB</p>
          <div className="flex items-center justify-center gap-2 mt-4">
            {['PDF', 'DOCX', 'XLSX', 'HWP', 'HWPX'].map((ext) => (
              <span key={ext} className="px-2 py-1 rounded-lg bg-white/[0.04] text-[10px] font-bold text-gray-500 tracking-wider">.{ext}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
