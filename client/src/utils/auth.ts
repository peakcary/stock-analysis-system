/**
 * 客户端认证工具
 * Client Authentication Utilities
 */

import axios from 'axios';

// Token管理
export const tokenManager = {
  getToken: (): string | null => {
    return localStorage.getItem('client_token');
  },

  setToken: (token: string): void => {
    localStorage.setItem('client_token', token);
    // 设置axios默认认证头
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  },

  removeToken: (): void => {
    localStorage.removeItem('client_token');
    delete axios.defaults.headers.common['Authorization'];
  },

  // 初始化token（应用启动时调用）
  initToken: (): void => {
    const token = tokenManager.getToken();
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }
};

// 模拟登录（用于测试）
export const mockLogin = async (username: string = 'testuser', password: string = 'test123') => {
  try {
    const response = await axios.post('/api/v1/auth/login', {
      username,
      password
    });

    if (response.data.access_token) {
      tokenManager.setToken(response.data.access_token);
      return {
        success: true,
        user: response.data.user,
        token: response.data.access_token
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
};

// 检查认证状态
export const checkAuth = async (): Promise<boolean> => {
  const token = tokenManager.getToken();
  if (!token) return false;

  try {
    await axios.get('/api/v1/auth/me');
    return true;
  } catch (error) {
    // Token无效，清除
    tokenManager.removeToken();
    return false;
  }
};