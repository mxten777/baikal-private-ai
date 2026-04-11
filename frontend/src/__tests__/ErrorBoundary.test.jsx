import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorBoundary from '../components/ErrorBoundary';

// 에러를 던지는 테스트용 컴포넌트
function Bomb({ shouldThrow }) {
  if (shouldThrow) throw new Error('Test error');
  return <div>정상 화면</div>;
}

// console.error 억제 (예상된 에러 출력 방지)
beforeEach(() => {
  jest.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  console.error.mockRestore();
});

describe('ErrorBoundary', () => {
  test('자식 컴포넌트를 정상 렌더링', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>
    );
    expect(screen.getByText('정상 화면')).toBeInTheDocument();
  });

  test('에러 발생 시 에러 화면 표시', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('예기치 않은 오류')).toBeInTheDocument();
    expect(screen.getByText(/화면을 표시하는 도중/)).toBeInTheDocument();
  });

  test('"다시 시도" 버튼 클릭 시 에러 상태 초기화', () => {
    const { rerender } = render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('예기치 않은 오류')).toBeInTheDocument();

    fireEvent.click(screen.getByText('다시 시도'));

    // 에러 초기화 후 자식 다시 렌더링 (여전히 shouldThrow=true이면 다시 에러)
    expect(screen.getByText('예기치 않은 오류')).toBeInTheDocument();
  });

  test('"페이지 새로고침" 버튼 존재 확인', () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>
    );
    expect(screen.getByText('페이지 새로고침')).toBeInTheDocument();
  });

  test('여러 자식 컴포넌트 정상 렌더링', () => {
    render(
      <ErrorBoundary>
        <div>첫 번째</div>
        <div>두 번째</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('첫 번째')).toBeInTheDocument();
    expect(screen.getByText('두 번째')).toBeInTheDocument();
  });
});
