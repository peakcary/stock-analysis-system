import axios from 'axios';

// API基础URL - 从环境变量或使用默认值
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://qwquant.com/api/v1';

// 创建axios实例
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 请求拦截器 - 添加token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('client_system_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('client_system_token');
      localStorage.removeItem('client_system_user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export default api;
