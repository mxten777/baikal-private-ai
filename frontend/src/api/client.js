/**
 * API Client - Axios 인스턴스
 */
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: JWT 토큰 자동 추가
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 응답 인터셉터: 401 시 리프레시 시도
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = res.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch {
          // 리프레시 실패 → 로그아웃
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }

    // 글로벌 에러 토스트 (401 제외 - 이미 처리됨)
    if (!originalRequest._retry) {
      if (!error.response) {
        // 네트워크 오류 (서버 연결 불가)
        toast.error('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.', { id: 'network-error' });
      } else if (error.response.status >= 500) {
        // 서버 내부 오류
        const msg = error.response.data?.detail || '서버 오류가 발생했습니다';
        toast.error(msg, { id: 'server-error' });
      } else if (error.response.status === 503) {
        // Ollama/서비스 비가용
        toast.error('AI 서비스가 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.', { id: 'service-unavailable' });
      }
    }

    return Promise.reject(error);
  }
);

// ---- Auth API ----
export const authAPI = {
  login: (username, password) =>
    client.post('/auth/login', { username, password }),
  me: () => client.get('/auth/me'),
  changePassword: (currentPassword, newPassword) =>
    client.patch('/auth/password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};

// ---- Users API ----
export const usersAPI = {
  list: () => client.get('/users'),
  create: (data) => client.post('/users', data),
  update: (id, data) => client.patch(`/users/${id}`, data),
  delete: (id) => client.delete(`/users/${id}`),
};

// ---- Documents API ----
export const documentsAPI = {
  list: () => client.get('/documents'),
  upload: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    });
  },
  status: (id) => client.get(`/documents/${id}/status`),
  download: (id) =>
    client.get(`/documents/${id}/download`, { responseType: 'blob' }),
  delete: (id) => client.delete(`/documents/${id}`),
};

// ---- Chat API ----
export const chatAPI = {
  sessions: () => client.get('/chat/sessions'),
  createSession: (title) =>
    client.post('/chat/sessions', { title: title || '새 대화' }),
  messages: (sessionId) => client.get(`/chat/sessions/${sessionId}/messages`),
  ask: (sessionId, question) =>
    client.post('/chat/ask', { session_id: sessionId, question }),
  deleteSession: (id) => client.delete(`/chat/sessions/${id}`),

  // 스트리밍 질문응답
  askStream: async function* (sessionId, question) {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_BASE}/chat/ask/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ session_id: sessionId, question }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '스트리밍 요청 실패' }));
      throw new Error(err.detail || '스트리밍 요청 실패');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            // JSON 파싱 실패 무시
          }
        }
      }
    }
  },
};

// ---- Search API ----
export const searchAPI = {
  search: (query) => client.get('/search', { params: { q: query } }),
};

export default client;
