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
          ? 'bg-baikal-50 border-2 border-baikal-300 shadow-lg shadow-baikal-100/50'
          : uploading
          ? 'bg-gray-50 border-2 border-gray-200 cursor-not-allowed'
          : 'bg-white border-2 border-dashed border-gray-200 hover:border-baikal-300 hover:bg-baikal-50/30'
      }`}
    >
      <input {...getInputProps()} />

      {uploading ? (
        <div className="animate-fade-in">
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-baikal-600 to-purple-600 flex items-center justify-center">
            <HiOutlineDocument className="w-6 h-6 text-white animate-pulse" />
          </div>
          <p className="text-sm font-semibold text-gray-700 mb-1">업로드 중...</p>
          <p className="text-3xl font-black text-gray-900 mb-3">{progress}%</p>
          <div className="w-56 mx-auto bg-gray-100 rounded-full h-1.5 overflow-hidden">
            <div className="h-full rounded-full bg-gradient-to-r from-baikal-600 to-purple-600 transition-all duration-300" style={{ width: `${progress}%` }} />
          </div>
        </div>
      ) : (
        <div>
          <div className={`w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-all duration-300 ${
            isDragActive ? 'bg-gradient-to-br from-baikal-600 to-purple-600 scale-110' : 'bg-gray-100'
          }`}>
            <HiOutlineCloudArrowUp className={`w-6 h-6 transition-colors ${isDragActive ? 'text-white' : 'text-gray-400'}`} />
          </div>
          <p className="text-sm font-semibold text-gray-700 mb-0.5">
            {isDragActive ? '여기에 놓으세요!' : '파일을 드래그하거나 클릭하여 업로드'}
          </p>
          <p className="text-[11px] text-gray-400 font-medium">PDF, DOCX, XLSX · 최대 100MB</p>
          <div className="flex items-center justify-center gap-2 mt-4">
            {['PDF', 'DOCX', 'XLSX'].map((ext) => (
              <span key={ext} className="px-2 py-1 rounded-lg bg-gray-50 text-[10px] font-bold text-gray-400 tracking-wider">.{ext}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
