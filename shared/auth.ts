/**
 * 统一认证工具
 * Unified Authentication Utilities
 */

import axios, { AxiosInstance } from 'axios';

// 统一的token存储key
const TOKEN_KEY = 'app_token';
const USER_KEY = 'app_user';

export interface User {
  id: number;
  username: string;
  email: string;
  membership_type: 'free' | 'pro' | 'premium';
  queries_remaining: number;
  membership_expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export class UnifiedAuthManager {
  private static instance: UnifiedAuthManager;
  private apiClient: AxiosInstance;

  private constructor() {
    this.apiClient = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3007',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 初始化token
    this.initToken();

    // 请求拦截器 - 自动添加token
    this.apiClient.interceptors.request.use((config) => {
      const token = this.getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // 响应拦截器 - 处理401错误
    this.apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token过期或无效，清除认证信息
          this.removeToken();
          // 不自动重试登录，让用户手动重新登录
          window.location.href = '/auth';
        }
        return Promise.reject(error);
      }
    );
  }

  public static getInstance(): UnifiedAuthManager {
    if (!UnifiedAuthManager.instance) {
      UnifiedAuthManager.instance = new UnifiedAuthManager();
    }
    return UnifiedAuthManager.instance;
  }

  // Token管理
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token);
  }

  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  // 用户数据管理
  getUser(): User | null {
    const userData = localStorage.getItem(USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }

  setUser(user: User): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  // 初始化token
  initToken(): void {
    const token = this.getToken();
    if (token && this.apiClient.defaults.headers.common) {
      this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  // 登录
  async login(username: string, password: string): Promise<{ success: boolean; error?: string; user?: User }> {
    try {
      const response = await this.apiClient.post<AuthResponse>('/api/v1/auth/login', {
        username,
        password
      });

      if (response.data.access_token) {
        this.setToken(response.data.access_token);
        this.setUser(response.data.user);
        return {
          success: true,
          user: response.data.user
        };
      }

      return { success: false, error: '登录失败' };
    } catch (error: any) {
      console.error('登录错误:', error);
      return {
        success: false,
        error: error.response?.data?.detail || '登录失败'
      };
    }
  }

  // 检查认证状态
  async checkAuth(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    try {
      const response = await this.apiClient.get<User>('/api/v1/auth/me');
      this.setUser(response.data);
      return true;
    } catch (error) {
      this.removeToken();
      return false;
    }
  }


  // 退出登录
  logout(): void {
    this.removeToken();
  }

  // 获取API客户端
  getApiClient(): AxiosInstance {
    return this.apiClient;
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}

// 导出单例实例
export const authManager = UnifiedAuthManager.getInstance();

// 导出API客户端供其他模块使用
export const apiClient = authManager.getApiClient();

// 兼容性方法
export const tokenManager = {
  getToken: () => authManager.getToken(),
  setToken: (token: string) => authManager.setToken(token),
  removeToken: () => authManager.removeToken(),
  initToken: () => authManager.initToken()
};

export const mockLogin = (username: string, password: string) =>
  authManager.login(username, password);

export const checkAuth = () => authManager.checkAuth();