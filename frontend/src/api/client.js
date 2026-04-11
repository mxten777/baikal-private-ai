/**
 * API Client - Axios 인스턴스
 * P3-4: HttpOnly 쿠키 기반 인증 (withCredentials, localStorage 제거)
 */
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = process.env.REACT_APP_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // P3-4: HttpOnly 쿠키 자동 전송
});

// 응답 인터셉터: 401 시 쿠키 기반 리프레시 시도
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // P3-4: refresh_token은 HttpOnly 쿠키로 자동 전송
        await axios.post(`${API_BASE}/auth/refresh`, {}, { withCredentials: true });
        return client(originalRequest);
      } catch {
        // 리프레시 실패 → 로그인 페이지로 (이미 /login 이면 무시)
        if (!window.location.pathname.startsWith('/login')) {
          window.location.replace('/login');
        }
      }
    }

    // 글로벌 에러 토스트 (401 제외 - 이미 처리됨)
    if (!originalRequest._retry) {
      if (!error.response) {
        toast.error('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.', { id: 'network-error' });
      } else if (error.response.status >= 500) {
        const msg = error.response.data?.detail || '서버 오류가 발생했습니다';
        toast.error(msg, { id: 'server-error' });
      } else if (error.response.status === 503) {
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
  logout: () => client.post('/auth/logout', {}),
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
  updatePermissions: (id, data) => client.patch(`/documents/${id}/permissions`, data),
};

// ---- Chat API ----
export const chatAPI = {
  sessions: () => client.get('/chat/sessions'),
  createSession: (title) =>
    client.post('/chat/sessions', { title: title || '새 대화' }),
  messages: (sessionId) => client.get(`/chat/sessions/${sessionId}/messages`),
  ask: (sessionId, question, documentIds = null, useHyde = false) =>
    client.post('/chat/ask', { session_id: sessionId, question, document_ids: documentIds, use_hyde: useHyde }),
  deleteSession: (id) => client.delete(`/chat/sessions/${id}`),

  // 스트리밍 질문응답
  askStream: async function* (sessionId, question, documentIds = null, useHyde = false) {
    // P3-4: SSE는 Axios 인터셉터를 우회하므로 credentials 직접 설정
    const doFetch = () => fetch(`${API_BASE}/chat/ask/stream`, {
      method: 'POST',
      credentials: 'include', // HttpOnly 쿠키 자동 전송
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, question, document_ids: documentIds, use_hyde: useHyde }),
    });

    let response = await doFetch();

    // 401: 쿠키 기반 토큰 갱신 후 1회 재시도
    if (response.status === 401) {
      try {
        await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: '{}',
        });
        response = await doFetch();
      } catch {
        window.location.href = '/login';
        return;
      }
    }

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
  search: (query, mode = 'hybrid') => client.get('/search', { params: { q: query, mode } }),
};

// ---- Admin API ----
export const adminAPI = {
  listModels: () => client.get('/admin/models'),
  activateModel: (modelName) => client.post(`/admin/models/activate?model_name=${encodeURIComponent(modelName)}`),
  queryLogs: (skip = 0, limit = 50) => client.get('/admin/query-logs', { params: { skip, limit } }),
  queryLogStats: () => client.get('/admin/query-logs/stats'),
  // P2-7 KPI APIs
  kpiActiveUsers: () => client.get('/admin/kpi/active-users'),
  kpiRagPerformance: () => client.get('/admin/kpi/rag-performance'),
  kpiWeeklyTrend: () => client.get('/admin/kpi/weekly-trend'),
  // P3-1 Guardrail
  kpiPolicyViolations: () => client.get('/admin/kpi/policy-violations'),
};

export default client;
