/**
 * Client API 客户端
 * 统一管理所有 API 请求
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { getApiUrl, getApiBaseUrl } from '../../../shared/api.config';

// 导出类型定义，供其他地方使用
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  detail?: string;
}

// 创建 Axios 实例
let apiInstance: AxiosInstance | null = null;

/**
 * 创建 API 客户端实例
 * @param token - 可选的认证令牌
 * @returns Axios 实例
 */
export const createApiInstance = (token?: string): AxiosInstance => {
  const instance = axios.create({
    baseURL: getApiBaseUrl(),
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 请求拦截器 - 添加认证令牌
  instance.interceptors.request.use(
    (config) => {
      const tokenToUse = token || localStorage.getItem('token');
      if (tokenToUse) {
        config.headers.Authorization = `Bearer ${tokenToUse}`;
      }
      return config;
    },
    (error) => {
      console.error('请求拦截器错误:', error);
      return Promise.reject(error);
    }
  );

  // 响应拦截器 - 处理错误和刷新 token
  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError) => {
      // 401 未认证 - 清除 token 并跳转到登录
      if (error.response?.status === 401) {
        console.warn('认证失败 (401)，清除令牌');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        // 可选：跳转到登录页面
        window.location.href = '/login';
      }

      // 403 禁止访问
      if (error.response?.status === 403) {
        console.error('无权访问此资源 (403)');
      }

      // 500 服务器错误
      if (error.response?.status === 500) {
        console.error('服务器错误 (500)');
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

/**
 * 获取 API 实例（如果不存在则创建）
 */
export const getApiInstance = (): AxiosInstance => {
  if (!apiInstance) {
    apiInstance = createApiInstance();
  }
  return apiInstance;
};

/**
 * 更新 API 实例的 token
 * @param token - 新的认证令牌
 */
export const updateApiToken = (token: string): void => {
  apiInstance = createApiInstance(token);
};

/**
 * 清除 API 实例
 */
export const clearApiInstance = (): void => {
  apiInstance = null;
};

/**
 * 支付相关 API
 */
export const paymentAPI = {
  // 创建支付订单
  createOrder: (data: {
    package_type: string;
    payment_method: 'wechat_native' | 'wechat_h5';
  }) => {
    return getApiInstance().post('/payment/v2/orders/create', data);
  },

  // 查询订单状态
  getOrderStatus: (outTradeNo: string) => {
    return getApiInstance().get(`/payment/v2/orders/${outTradeNo}/status`);
  },

  // 取消订单
  cancelOrder: (outTradeNo: string) => {
    return getApiInstance().post(`/payment/v2/orders/${outTradeNo}/cancel`);
  },

  // 模拟支付完成（开发模式）
  mockComplete: (outTradeNo: string) => {
    return getApiInstance().post(`/payment/mock/complete/${outTradeNo}`);
  },

  // 获取支付历史
  getPaymentHistory: (params?: { page?: number; limit?: number }) => {
    return getApiInstance().get('/payment/history', { params });
  },
};

/**
 * 股票分析 API
 */
export const analysisAPI = {
  // 获取可转债概念
  getConvertibleBonds: (params: {
    trading_date: string;
    limit?: number;
  }) => {
    return getApiInstance().get('/stock-analysis/convertible-bonds/concepts', {
      params,
    });
  },

  // 获取股票图表数据
  getStockChartData: (stockCode: string, params?: {
    concept_name?: string;
    days?: number;
  }) => {
    return getApiInstance().get(
      `/stock-analysis/stock/${stockCode}/chart-data`,
      { params }
    );
  },

  // 获取创新高概念
  getNewHighConcepts: (params: {
    days?: number;
    trading_date?: string;
  }) => {
    return getApiInstance().get('/stock-analysis/concepts/new-highs', {
      params,
    });
  },
};

/**
 * 认证相关 API
 */
export const authAPI = {
  // 用户注册
  register: (data: {
    username: string;
    email: string;
    password: string;
  }) => {
    return getApiInstance().post('/auth/register', data);
  },

  // 用户登录
  login: (data: { username: string; password: string }) => {
    return getApiInstance().post('/auth/login', data);
  },

  // 获取当前用户信息
  getMe: () => {
    return getApiInstance().get('/auth/me');
  },

  // 修改密码
  changePassword: (data: {
    old_password: string;
    new_password: string;
  }) => {
    return getApiInstance().post('/auth/change-password', data);
  },
};

/**
 * 用户相关 API
 */
export const userAPI = {
  // 获取用户信息
  getProfile: () => {
    return getApiInstance().get('/users/me');
  },

  // 更新用户信息
  updateProfile: (data: any) => {
    return getApiInstance().put('/users/me', data);
  },

  // 获取用户统计信息
  getStats: () => {
    return getApiInstance().get('/users/stats');
  },
};

export default {
  getApiInstance,
  updateApiToken,
  clearApiInstance,
  paymentAPI,
  analysisAPI,
  authAPI,
  userAPI,
};
