import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatMessage from '../components/ChatMessage';

// apiClient mock
jest.mock('../api/client', () => ({
  __esModule: true,
  default: {
    post: jest.fn().mockResolvedValue({ data: {} }),
  },
}));

// react-icons mock
jest.mock('react-icons/hi2', () => ({
  HiOutlineDocumentText: () => <span data-testid="icon-doc" />,
  HiOutlineXMark: () => <span data-testid="icon-x" />,
  HiOutlineSignal: () => <span data-testid="icon-signal" />,
  HiOutlineHandThumbUp: () => <span data-testid="icon-thumb-up" />,
  HiOutlineHandThumbDown: () => <span data-testid="icon-thumb-down" />,
  HiOutlineExclamationTriangle: () => <span data-testid="icon-warning" />,
}));

// react-markdown mock (단순 텍스트 출력)
jest.mock('react-markdown', () => ({ children }) => <>{children}</>);

// createPortal mock (jsdom은 body 렌더링 지원)
jest.mock('react-dom', () => ({
  ...jest.requireActual('react-dom'),
  createPortal: (node) => node,
}));

const userMessage = {
  role: 'user',
  content: '안녕하세요',
};

const aiMessage = {
  id: 'msg-001',
  role: 'assistant',
  content: 'BAIKAL Private AI는 폐쇄망 전용 AI입니다.',
  confidence_score: 0.85,
  sources: { documents: [] },
};

const lowConfMessage = {
  id: 'msg-002',
  role: 'assistant',
  content: '잘 모르겠습니다.',
  confidence_score: 0.25,
  sources: { documents: [] },
};

const messageWithSources = {
  id: 'msg-003',
  role: 'assistant',
  content: '답변입니다.',
  confidence_score: 0.9,
  sources: {
    documents: [
      { filename: '취업규칙.pdf', chunk_id: 'chunk-1', relevance_score: 0.92, page_number: 5 },
      { filename: '내규.hwpx', chunk_id: 'chunk-2', relevance_score: 0.75, page_number: null },
    ],
  },
};

describe('ChatMessage', () => {
  test('사용자 메시지 렌더링', () => {
    render(<ChatMessage message={userMessage} />);
    expect(screen.getByText('안녕하세요')).toBeInTheDocument();
  });

  test('AI 메시지 렌더링', () => {
    render(<ChatMessage message={aiMessage} />);
    expect(screen.getByText('BAIKAL AI')).toBeInTheDocument();
    expect(screen.getByText(/BAIKAL Private AI는/)).toBeInTheDocument();
  });

  test('신뢰도 높은 경우 신뢰도 배지 표시', () => {
    render(<ChatMessage message={aiMessage} />);
    expect(screen.getByText(/신뢰도 85%/)).toBeInTheDocument();
  });

  test('신뢰도 < 0.4 시 "근거 부족" 경고 배지 표시', () => {
    render(<ChatMessage message={lowConfMessage} />);
    expect(screen.getByText(/근거 부족 25%/)).toBeInTheDocument();
    // 경고 아이콘 표시
    expect(screen.getByTestId('icon-warning')).toBeInTheDocument();
  });

  test('신뢰도 없으면 배지 없음', () => {
    render(<ChatMessage message={{ ...aiMessage, confidence_score: null }} />);
    expect(screen.queryByText(/신뢰도/)).not.toBeInTheDocument();
    expect(screen.queryByText(/근거 부족/)).not.toBeInTheDocument();
  });

  test('출처 문서 배지 표시 (페이지 번호 포함)', () => {
    render(<ChatMessage message={messageWithSources} />);
    expect(screen.getByText(/취업규칙\.pdf/)).toBeInTheDocument();
    expect(screen.getByText('p.5')).toBeInTheDocument();
    expect(screen.getByText(/내규\.hwpx/)).toBeInTheDocument();
  });

  test('출처 배지 클릭 시 미리보기 모달 열림', async () => {
    render(<ChatMessage message={messageWithSources} />);
    const badge = screen.getByText(/취업규칙\.pdf/).closest('button');
    fireEvent.click(badge);
    // 모달의 "닫기" 아이콘(X) 표시 확인
    await waitFor(() => {
      expect(screen.getByTestId('icon-x')).toBeInTheDocument();
    });
  });

  test('피드백 버튼 표시 (message.id 있을 때)', () => {
    render(<ChatMessage message={aiMessage} />);
    expect(screen.getByTitle('도움이 됐어요')).toBeInTheDocument();
    expect(screen.getByTitle('도움이 안 됐어요')).toBeInTheDocument();
  });

  test('피드백 없으면 버튼 없음 (message.id 없을 때)', () => {
    render(<ChatMessage message={{ ...aiMessage, id: null }} />);
    expect(screen.queryByTitle('도움이 됐어요')).not.toBeInTheDocument();
  });

  test('👍 피드백 클릭 시 API 호출 및 버튼 비활성화', async () => {
    const apiClient = require('../api/client').default;
    render(<ChatMessage message={aiMessage} />);
    fireEvent.click(screen.getByTitle('도움이 됐어요'));
    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/chat/messages/msg-001/feedback',
        { score: 1 }
      );
    });
    expect(screen.getByText('피드백 감사합니다')).toBeInTheDocument();
  });

  test('피드백 한 번 클릭 후 재클릭 무시 (중복 방지)', async () => {
    const apiClient = require('../api/client').default;
    apiClient.post.mockClear();
    render(<ChatMessage message={aiMessage} />);
    fireEvent.click(screen.getByTitle('도움이 됐어요'));
    await waitFor(() => expect(screen.getByText('피드백 감사합니다')).toBeInTheDocument());
    // 두 번째 클릭 시도
    fireEvent.click(screen.getByTitle('도움이 안 됐어요'));
    // API는 한 번만 호출되어야 함
    expect(apiClient.post).toHaveBeenCalledTimes(1);
  });
});
