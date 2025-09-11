/**
 * 统一认证工具
 * Unified Authentication Utilities
 */

import axios, { AxiosInstance } from 'axios';
import { 
  USER_AUTH_CONFIG, 
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
const config = USER_AUTH_CONFIG;

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

export interface LoginResult {
  success: boolean;
  user?: User;
  error?: AuthError;
}

export class UnifiedAuthManager {
  private static instance: UnifiedAuthManager;
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

    // 请求拦截器 - 自动添加token
    this.apiClient.interceptors.request.use((requestConfig) => {
      const token = this.getToken();
      if (token) {
        requestConfig.headers.Authorization = `Bearer ${token}`;
      }
      return requestConfig;
    });

    // 响应拦截器 - 统一错误处理
    this.apiClient.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token过期或无效，清除认证信息
          this.removeToken();
          
          // 只有在不是认证页面时才跳转
          if (typeof window !== 'undefined') {
            const currentPath = window.location.pathname;
            const isAuthPage = currentPath === '/auth' || currentPath.includes('/login');
            
            if (!isAuthPage) {
              console.log('用户认证失效，准备跳转到登录页面');
              setTimeout(() => {
                if (!window.location.pathname.includes('/auth')) {
                  window.location.href = '/auth';
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

  public static getInstance(): UnifiedAuthManager {
    if (!UnifiedAuthManager.instance) {
      UnifiedAuthManager.instance = new UnifiedAuthManager();
    }
    return UnifiedAuthManager.instance;
  }

  // Token管理 - 使用安全存储
  getToken(): string | null {
    return secureStorage.getItem(config.storage.tokenKey);
  }

  setToken(token: string): void {
    secureStorage.setItem(config.storage.tokenKey, token);
  }

  removeToken(): void {
    secureStorage.removeItem(config.storage.tokenKey);
    secureStorage.removeItem(config.storage.userKey);
  }

  // 用户数据管理 - 使用安全存储
  getUser(): User | null {
    const userData = secureStorage.getItem(config.storage.userKey);
    try {
      return userData ? JSON.parse(userData) : null;
    } catch {
      console.warn('Failed to parse user data from storage');
      return null;
    }
  }

  setUser(user: User): void {
    secureStorage.setItem(config.storage.userKey, JSON.stringify(user));
  }

  // 初始化token
  initToken(): void {
    const token = this.getToken();
    if (token && this.apiClient.defaults.headers.common) {
      this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }

  // 登录 - 使用统一错误处理和重试机制
  async login(username: string, password: string): Promise<LoginResult> {
    try {
      const loginRequest = () => this.apiClient.post<AuthResponse>(
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
        this.setUser(response.data.user);
        
        return {
          success: true,
          user: response.data.user
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
      console.error('用户登录错误:', error);
      
      // 如果已经是 AuthError，直接使用
      const authError = error.code ? error : createAuthErrorFromNetworkError(error);
      
      return {
        success: false,
        error: authError
      };
    }
  }

  // 检查认证状态 - 增强版本
  async checkAuth(): Promise<boolean> {
    const token = this.getToken();
    if (!token) return false;

    // 检查token是否已过期
    if (isTokenExpired(token)) {
      console.log('用户token已过期');
      this.removeToken();
      return false;
    }

    try {
      const response = await this.apiClient.get<User>(config.endpoints.me);
      this.setUser(response.data);
      return true;
    } catch (error: any) {
      console.error('用户认证检查失败:', error);
      this.removeToken();
      return false;
    }
  }


  // 退出登录
  logout(): void {
    this.removeToken();
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