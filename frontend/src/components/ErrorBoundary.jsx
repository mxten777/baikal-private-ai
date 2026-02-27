/**
 * ErrorBoundary - React 에러 바운더리
 * 렌더링 오류를 잡아 사용자 친화적 화면을 표시합니다.
 */
import React from 'react';
import { HiOutlineExclamationTriangle } from 'react-icons/hi2';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-surface-50 p-6">
          <div className="max-w-md w-full text-center">
            {/* 아이콘 */}
            <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-rose-100 to-orange-100 flex items-center justify-center mb-6 shadow-lg shadow-rose-100/50">
              <HiOutlineExclamationTriangle className="w-10 h-10 text-rose-500" />
            </div>

            {/* 제목 */}
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              예기치 않은 오류
            </h1>
            <p className="text-sm text-gray-500 mb-8 leading-relaxed">
              화면을 표시하는 도중 문제가 발생했습니다.<br />
              아래 버튼을 눌러 다시 시도해주세요.
            </p>

            {/* 에러 상세 (개발모드) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-900 rounded-xl text-left overflow-auto max-h-40">
                <p className="text-xs font-mono text-rose-400">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            {/* 버튼 */}
            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleReset}
                className="px-6 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors shadow-sm"
              >
                다시 시도
              </button>
              <button
                onClick={this.handleReload}
                className="px-6 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-baikal-600 to-purple-600 rounded-xl hover:from-baikal-700 hover:to-purple-700 shadow-lg shadow-baikal-500/25 transition-all"
              >
                페이지 새로고침
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
