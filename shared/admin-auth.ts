/**
 * 管理员认证工具
 * Admin Authentication Utilities
 */

import axios, { AxiosInstance } from 'axios';

// 管理员token存储key
const ADMIN_TOKEN_KEY = 'admin_token';
const ADMIN_USER_KEY = 'admin_user';

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  last_login?: string;
}

export interface AdminAuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin_info: AdminUser;
}

export class AdminAuthManager {
  private static instance: AdminAuthManager;
  private apiClient: AxiosInstance;

  private constructor() {
    // 获取API基础URL
    const getApiBaseUrl = () => {
      if (typeof window !== 'undefined') {
        return (import.meta as any)?.env?.VITE_API_URL || 
               (window as any).REACT_APP_API_URL || 
               'http://localhost:3007';
      } else {
        return process.env.REACT_APP_API_URL || 
               process.env.VITE_API_URL || 
               'http://localhost:3007';
      }
    };

    this.apiClient = axios.create({
      baseURL: getApiBaseUrl(),
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // 初始化token
    this.initToken();

    // 请求拦截器 - 自动添加admin token
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
          // Admin token过期或无效，清除认证信息
          this.removeToken();
          // 跳转到管理员登录页
          window.location.href = '/';
        }
        return Promise.reject(error);
      }
    );
  }

  public static getInstance(): AdminAuthManager {
    if (!AdminAuthManager.instance) {
      AdminAuthManager.instance = new AdminAuthManager();
    }
    return AdminAuthManager.instance;
  }

  // Token管理
  getToken(): string | null {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  }

  setToken(token: string): void {
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
  }

  removeToken(): void {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    localStorage.removeItem(ADMIN_USER_KEY);
  }

  // 管理员数据管理
  getUser(): AdminUser | null {
    const userData = localStorage.getItem(ADMIN_USER_KEY);
    return userData ? JSON.parse(userData) : null;
  }

  setUser(user: AdminUser): void {
    localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(user));
  }

  // 初始化token
  initToken(): void {
    const token = this.getToken();
    if (token && this.apiClient.defaults.headers.common) {
      this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  // 管理员登录
  async login(username: string, password: string): Promise<{ success: boolean; error?: string; user?: AdminUser }> {
    try {
      const response = await this.apiClient.post<AdminAuthResponse>('/api/v1/admin/auth/login', {
        username,
        password
      });

      if (response.data.access_token) {
        this.setToken(response.data.access_token);
        this.setUser(response.data.admin_info);
        return {
          success: true,
          user: response.data.admin_info
        };
      }

      return { success: false, error: '登录失败' };
    } catch (error: any) {
      console.error('管理员登录错误:', error);
      return {
        success: false,
        error: error.response?.data?.detail || '登录失败'
      };
    }
  }

  // 检查管理员认证状态
  async checkAuth(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    try {
      const response = await this.apiClient.get<AdminUser>('/api/v1/admin/auth/me');
      this.setUser(response.data);
      return true;
    } catch (error) {
      this.removeToken();
      return false;
    }
  }

  // 管理员退出登录
  async logout(): Promise<void> {
    try {
      await this.apiClient.post('/api/v1/admin/auth/logout');
    } catch (error) {
      console.error('登出请求失败:', error);
    } finally {
      this.removeToken();
    }
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
export const adminAuthManager = AdminAuthManager.getInstance();

// 导出API客户端供其他模块使用
export const adminApiClient = adminAuthManager.getApiClient();