/**
 * 统一认证配置
 * Unified Authentication Configuration
 */

export interface AuthEndpoints {
  login: string;
  register?: string;
  logout: string;
  refresh?: string;
  me: string;
}

export interface AuthStorage {
  tokenKey: string;
  userKey: string;
  refreshTokenKey?: string;
}

export interface AuthConfig {
  apiBaseUrl: string;
  endpoints: AuthEndpoints;
  storage: AuthStorage;
  tokenExpireTime: number; // 毫秒
  refreshThreshold: number; // 毫秒，在token过期前多久开始刷新
  maxRetryAttempts: number;
  autoRefresh: boolean;
}

// 获取API基础URL的统一方法 - 智能检测环境并自动路由
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    // 浏览器环境 - 运行时环境检测
    const env = (import.meta as any)?.env?.VITE_API_URL ||
                (window as any).REACT_APP_API_URL;

    if (env) {
      // 如果明确设置了环境变量，使用它
      return env;
    }

    // 自动检测环境
    const hostname = window.location.hostname;

    // 开发环境检测
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://${hostname}:3007/api/v1`;
    }

    // 生产环境 - 使用当前域名 + Nginx代理路径
    return `${window.location.origin}/api/v1`;
  } else {
    // Node.js 环境
    return process.env.REACT_APP_API_URL ||
           process.env.VITE_API_URL ||
           '/api/v1';
  }
};

// 普通用户认证配置
export const USER_AUTH_CONFIG: AuthConfig = {
  apiBaseUrl: getApiBaseUrl(),
  endpoints: {
    login: '/auth/login',
    register: '/auth/register',
    logout: '/auth/logout',
    me: '/auth/me'
  },
  storage: {
    tokenKey: 'app_token',
    userKey: 'app_user'
  },
  tokenExpireTime: 24 * 60 * 60 * 1000, // 24小时
  refreshThreshold: 5 * 60 * 1000, // 5分钟前刷新
  maxRetryAttempts: 3,
  autoRefresh: false // 暂时关闭，因为后端没有refresh端点
};

// 管理员认证配置
export const ADMIN_AUTH_CONFIG: AuthConfig = {
  apiBaseUrl: getApiBaseUrl(),
  endpoints: {
    login: '/admin-auth/login',
    logout: '/admin-auth/logout',
    refresh: '/admin-auth/refresh',
    me: '/admin-auth/me'
  },
  storage: {
    tokenKey: 'admin_token',
    userKey: 'admin_user',
    refreshTokenKey: 'admin_refresh_token'
  },
  tokenExpireTime: 24 * 60 * 60 * 1000, // 24小时
  refreshThreshold: 5 * 60 * 1000, // 5分钟前刷新
  maxRetryAttempts: 3,
  autoRefresh: true // 现在启用自动刷新
};

// 错误代码映射
export const AUTH_ERROR_CODES = {
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  NETWORK_ERROR: 'NETWORK_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
} as const;

export type AuthErrorCode = typeof AUTH_ERROR_CODES[keyof typeof AUTH_ERROR_CODES];

// 错误信息映射
export const AUTH_ERROR_MESSAGES: Record<AuthErrorCode, string> = {
  [AUTH_ERROR_CODES.INVALID_CREDENTIALS]: '用户名或密码错误',
  [AUTH_ERROR_CODES.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [AUTH_ERROR_CODES.TOKEN_INVALID]: '登录状态无效，请重新登录',
  [AUTH_ERROR_CODES.NETWORK_ERROR]: '网络连接失败，请检查网络设置',
  [AUTH_ERROR_CODES.SERVER_ERROR]: '服务器错误，请稍后重试',
  [AUTH_ERROR_CODES.UNKNOWN_ERROR]: '未知错误，请稍后重试'
};

// HTTP状态码到错误代码的映射
export const mapHttpStatusToErrorCode = (status: number): AuthErrorCode => {
  switch (status) {
    case 401:
      return AUTH_ERROR_CODES.TOKEN_EXPIRED;
    case 403:
      return AUTH_ERROR_CODES.TOKEN_INVALID;
    case 400:
      return AUTH_ERROR_CODES.INVALID_CREDENTIALS;
    case 500:
    case 502:
    case 503:
    case 504:
      return AUTH_ERROR_CODES.SERVER_ERROR;
    default:
      if (status >= 400 && status < 500) {
        return AUTH_ERROR_CODES.INVALID_CREDENTIALS;
      }
      return AUTH_ERROR_CODES.UNKNOWN_ERROR;
  }
};

// 网络错误到错误代码的映射
export const mapNetworkErrorToErrorCode = (error: any): AuthErrorCode => {
  if (error.code === 'NETWORK_ERROR' || !error.response) {
    return AUTH_ERROR_CODES.NETWORK_ERROR;
  }
  if (error.response?.status) {
    return mapHttpStatusToErrorCode(error.response.status);
  }
  return AUTH_ERROR_CODES.UNKNOWN_ERROR;
};