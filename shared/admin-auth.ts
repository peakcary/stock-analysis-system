/**
 * 管理员认证工具
 * Admin Authentication Utilities
 */

import axios, { AxiosInstance } from 'axios';
import { 
  ADMIN_AUTH_CONFIG, 
  AuthConfig, 
  AuthErrorCode 
} from './auth-config';
import { 
  AuthError, 
  createAuthErrorFromNetworkError, 
  withRetry, 
  isTokenExpired, 
  isTokenExpiringSoon, 
  secureStorage,
  formatErrorForUser
} from './auth-utils';

// 使用统一配置
const config = ADMIN_AUTH_CONFIG;

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
  refresh_token: string;
  token_type: string;
  expires_in: number;
  admin_info: AdminUser;
}

export interface AdminLoginResult {
  success: boolean;
  user?: AdminUser;
  error?: AuthError;
}

export class AdminAuthManager {
  private static instance: AdminAuthManager;
  private apiClient: AxiosInstance;

  private constructor() {
    this.apiClient = axios.create({
      baseURL: config.apiBaseUrl,
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 10000 // 10秒超时
    });

    // 初始化token
    this.initToken();

    // 请求拦截器 - 自动添加admin token和检查刷新
    this.apiClient.interceptors.request.use(async (requestConfig) => {
      const token = this.getToken();
      
      // 检查是否需要刷新token
      if (config.autoRefresh && this.shouldRefreshToken()) {
        console.log('Token即将过期，尝试自动刷新...');
        await this.refreshTokens();
      }
      
      // 使用最新的token
      const currentToken = this.getToken();
      if (currentToken) {
        requestConfig.headers.Authorization = `Bearer ${currentToken}`;
      }
      
      return requestConfig;
    });

    // 响应拦截器 - 统一错误处理和自动刷新
    this.apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // 如果是401错误且还没有重试过
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          // 尝试刷新token
          if (config.autoRefresh && this.getRefreshToken()) {
            console.log('收到401错误，尝试刷新token...');
            const refreshed = await this.refreshTokens();
            
            if (refreshed) {
              // 刷新成功，重试原请求
              const newToken = this.getToken();
              if (newToken) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return this.apiClient(originalRequest);
              }
            }
          }
          
          // 刷新失败或没有refresh token，清除认证信息
          this.removeToken();
          
          // 只有在当前不是登录页面时才跳转
          if (typeof window !== 'undefined') {
            const currentPath = window.location.pathname;
            const isLoginPage = currentPath === '/' || currentPath.includes('/login');
            
            if (!isLoginPage) {
              console.log('管理员认证失效，准备跳转到登录页面');
              setTimeout(() => {
                if (!window.location.pathname.includes('/login') && window.location.pathname !== '/') {
                  window.location.href = '/';
                }
              }, 100);
            }
          }
        }
        
        // 创建统一的错误对象
        const authError = createAuthErrorFromNetworkError(error);
        return Promise.reject(authError);
      }
    );
  }

  public static getInstance(): AdminAuthManager {
    if (!AdminAuthManager.instance) {
      AdminAuthManager.instance = new AdminAuthManager();
    }
    return AdminAuthManager.instance;
  }

  // Token管理 - 使用安全存储
  getToken(): string | null {
    return secureStorage.getItem(config.storage.tokenKey);
  }

  setToken(token: string): void {
    secureStorage.setItem(config.storage.tokenKey, token);
  }

  getRefreshToken(): string | null {
    return config.storage.refreshTokenKey ? 
      secureStorage.getItem(config.storage.refreshTokenKey) : null;
  }

  setRefreshToken(token: string): void {
    if (config.storage.refreshTokenKey) {
      secureStorage.setItem(config.storage.refreshTokenKey, token);
    }
  }

  removeToken(): void {
    secureStorage.removeItem(config.storage.tokenKey);
    secureStorage.removeItem(config.storage.userKey);
    if (config.storage.refreshTokenKey) {
      secureStorage.removeItem(config.storage.refreshTokenKey);
    }
  }

  // 管理员数据管理 - 使用安全存储
  getUser(): AdminUser | null {
    const userData = secureStorage.getItem(config.storage.userKey);
    try {
      return userData ? JSON.parse(userData) : null;
    } catch {
      console.warn('Failed to parse user data from storage');
      return null;
    }
  }

  setUser(user: AdminUser): void {
    secureStorage.setItem(config.storage.userKey, JSON.stringify(user));
  }

  // 初始化token
  initToken(): void {
    const token = this.getToken();
    if (token && this.apiClient.defaults.headers.common) {
      this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  // 管理员登录 - 使用统一错误处理和重试机制
  async login(username: string, password: string): Promise<AdminLoginResult> {
    try {
      const loginRequest = () => this.apiClient.post<AdminAuthResponse>(
        config.endpoints.login,
        { username, password }
      );

      // 使用重试机制
      const response = await withRetry(loginRequest, {
        maxAttempts: config.maxRetryAttempts,
        delay: 1000,
        backoff: 2
      });

      if (response.data.access_token) {
        this.setToken(response.data.access_token);
        if (response.data.refresh_token) {
          this.setRefreshToken(response.data.refresh_token);
        }
        this.setUser(response.data.admin_info);
        
        return {
          success: true,
          user: response.data.admin_info
        };
      }

      return { 
        success: false, 
        error: {
          code: 'INVALID_CREDENTIALS',
          message: '登录失败：服务器未返回有效令牌'
        }
      };
    } catch (error: any) {
      console.error('管理员登录错误:', error);
      
      // 如果已经是 AuthError，直接使用
      const authError = error.code ? error : createAuthErrorFromNetworkError(error);
      
      return {
        success: false,
        error: authError
      };
    }
  }

  // 检查管理员认证状态 - 增强版本
  async checkAuth(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    // 检查token是否已过期
    if (isTokenExpired(token)) {
      console.log('管理员token已过期');
      this.removeToken();
      return false;
    }

    try {
      const response = await this.apiClient.get<AdminUser>(config.endpoints.me);
      this.setUser(response.data);
      return true;
    } catch (error: any) {
      console.error('管理员认证检查失败:', error);
      this.removeToken();
      return false;
    }
  }

  // 管理员退出登录
  async logout(): Promise<void> {
    try {
      await this.apiClient.post(config.endpoints.logout);
    } catch (error) {
      console.error('登出请求失败:', error);
      // 即使请求失败也要清除本地状态
    } finally {
      this.removeToken();
    }
  }

  // 刷新Token
  async refreshTokens(): Promise<boolean> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken || !config.endpoints.refresh) {
      return false;
    }

    try {
      const response = await this.apiClient.post<AdminAuthResponse>(
        config.endpoints.refresh,
        { refresh_token: refreshToken }
      );

      if (response.data.access_token) {
        this.setToken(response.data.access_token);
        if (response.data.refresh_token) {
          this.setRefreshToken(response.data.refresh_token);
        }
        this.setUser(response.data.admin_info);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Token刷新失败:', error);
      this.removeToken(); // 刷新失败，清除所有token
      return false;
    }
  }

  // 检查是否需要刷新token
  private shouldRefreshToken(): boolean {
    const token = this.getToken();
    return token ? isTokenExpiringSoon(token, config.refreshThreshold) : false;
  }

  // 获取用户友好的错误信息
  getErrorMessage(error: AuthError): string {
    return formatErrorForUser(error);
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