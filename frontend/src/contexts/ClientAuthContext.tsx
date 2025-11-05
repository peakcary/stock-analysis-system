import React, { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { message } from 'antd';
import axios, { AxiosInstance } from 'axios';
import { getApiUrl } from '../../../shared/api.config';

// 用户接口定义
export interface ClientUser {
  id: number;
  username: string;
  email: string;
  membership_type: 'free' | 'pro' | 'premium';
  queries_remaining: number;
  queries_count: number;
  membership_expires_at?: string;
  created_at: string;
  updated_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: ClientUser;
}

interface ClientAuthContextType {
  isAuthenticated: boolean;
  user: ClientUser | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  loading: boolean;
  apiClient: AxiosInstance | null;
}

const ClientAuthContext = createContext<ClientAuthContextType | undefined>(undefined);

export const useClientAuth = () => {
  const context = useContext(ClientAuthContext);
  if (context === undefined) {
    throw new Error('useClientAuth must be used within a ClientAuthProvider');
  }
  return context;
};

interface ClientAuthProviderProps {
  children: ReactNode;
}

// 创建 API 客户端
let apiClient: AxiosInstance | null = null;

const createApiClient = (token?: string): AxiosInstance => {
  const client = axios.create({
    baseURL: getApiUrl('/'),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 请求拦截器 - 添加 token
  client.interceptors.request.use(
    (config) => {
      const tokenToUse = token || localStorage.getItem('client_token');
      if (tokenToUse) {
        config.headers.Authorization = `Bearer ${tokenToUse}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 响应拦截器 - 处理 401
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Token 过期，清除认证信息
        localStorage.removeItem('client_token');
        localStorage.removeItem('client_user');
        window.location.reload();
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const ClientAuthProvider: React.FC<ClientAuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<ClientUser | null>(null);
  const [loading, setLoading] = useState(true);

  // 普通用户登录函数
  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await axios.post<AuthResponse>(
        getApiUrl('/auth/login'),
        {
          username,
          password,
        }
      );

      if (response.data && response.data.access_token) {
        const { access_token, user: userData } = response.data;

        // 保存 token 和用户信息
        localStorage.setItem('client_token', access_token);
        localStorage.setItem('client_user', JSON.stringify(userData));

        // 创建 API 客户端
        apiClient = createApiClient(access_token);

        setUser(userData);
        setIsAuthenticated(true);
        message.success(`欢迎 ${userData.username}！`);
        return true;
      }
      return false;
    } catch (error: any) {
      console.error('登录失败:', error);
      const errorMsg = error.response?.data?.detail || '登录失败，请检查用户名和密码';
      message.error(errorMsg);
      return false;
    }
  };

  // 用户注册函数
  const register = async (username: string, email: string, password: string): Promise<boolean> => {
    try {
      const response = await axios.post<AuthResponse>(
        getApiUrl('/auth/register'),
        {
          username,
          email,
          password,
        }
      );

      if (response.data && response.data.access_token) {
        const { access_token, user: userData } = response.data;

        // 保存 token 和用户信息
        localStorage.setItem('client_token', access_token);
        localStorage.setItem('client_user', JSON.stringify(userData));

        // 创建 API 客户端
        apiClient = createApiClient(access_token);

        setUser(userData);
        setIsAuthenticated(true);
        message.success('注册成功！');
        return true;
      }
      return false;
    } catch (error: any) {
      console.error('注册失败:', error);
      const errorMsg = error.response?.data?.detail || '注册失败，请稍后重试';
      message.error(errorMsg);
      return false;
    }
  };

  // 登出
  const logout = () => {
    localStorage.removeItem('client_token');
    localStorage.removeItem('client_user');
    setUser(null);
    setIsAuthenticated(false);
    apiClient = null;
    message.success('已退出登录');
  };

  // 初始化认证状态
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('client_token');
        const userStr = localStorage.getItem('client_user');

        console.log('🔍 ClientAuthContext Debug:', {
          has_token: !!token,
          has_user: !!userStr,
          token_preview: token ? token.substring(0, 50) + '...' : null
        });

        if (token && userStr) {
          const userData = JSON.parse(userStr) as ClientUser;

          console.log('✅ Found existing token and user:', userData.username);

          // 创建 API 客户端
          apiClient = createApiClient(token);

          // 验证 token 是否仍有效
          try {
            const response = await apiClient.get<ClientUser>('/auth/me');
            console.log('✅ Token valid, user authenticated:', response.data.username);
            setUser(response.data);
            setIsAuthenticated(true);
          } catch (error) {
            console.log('❌ Token invalid, clearing storage');
            // Token 无效，清除
            localStorage.removeItem('client_token');
            localStorage.removeItem('client_user');
            apiClient = null;
          }
        } else {
          console.log('ℹ️ No stored token or user, user needs to login');
        }
      } catch (error) {
        console.error('初始化认证失败:', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // 如果没有 API 客户端，创建一个
  if (!apiClient && isAuthenticated) {
    const token = localStorage.getItem('client_token');
    if (token) {
      apiClient = createApiClient(token);
    }
  }

  const value: ClientAuthContextType = {
    isAuthenticated,
    user,
    login,
    logout,
    loading,
    apiClient: apiClient || createApiClient(),
  };

  return <ClientAuthContext.Provider value={value}>{children}</ClientAuthContext.Provider>;
};
