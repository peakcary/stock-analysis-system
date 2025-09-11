/**
 * 认证工具函数
 * Authentication Utility Functions
 */

import { 
  AuthErrorCode, 
  AUTH_ERROR_MESSAGES, 
  mapNetworkErrorToErrorCode,
  AuthConfig 
} from './auth-config';

export interface AuthError {
  code: AuthErrorCode;
  message: string;
  originalError?: any;
}

export interface RetryConfig {
  maxAttempts: number;
  delay: number;
  backoff: number;
}

// 创建认证错误
export const createAuthError = (code: AuthErrorCode, originalError?: any): AuthError => ({
  code,
  message: AUTH_ERROR_MESSAGES[code],
  originalError
});

// 从网络错误创建认证错误
export const createAuthErrorFromNetworkError = (error: any): AuthError => {
  const code = mapNetworkErrorToErrorCode(error);
  return createAuthError(code, error);
};

// 重试机制
export const withRetry = async <T>(
  fn: () => Promise<T>,
  retryConfig: RetryConfig
): Promise<T> => {
  let lastError: any;
  
  for (let attempt = 1; attempt <= retryConfig.maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // 如果是最后一次尝试，直接抛出错误
      if (attempt === retryConfig.maxAttempts) {
        break;
      }
      
      // 如果是认证错误（401, 403），不要重试
      if (error.response?.status === 401 || error.response?.status === 403) {
        break;
      }
      
      // 等待后重试
      const delay = retryConfig.delay * Math.pow(retryConfig.backoff, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

// Token 有效性检查
export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch {
    return true; // 如果无法解析，认为已过期
  }
};

// Token 是否即将过期
export const isTokenExpiringSoon = (token: string, thresholdMs: number): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    const thresholdSeconds = thresholdMs / 1000;
    return payload.exp - currentTime < thresholdSeconds;
  } catch {
    return true;
  }
};

// 安全的localStorage操作
export const secureStorage = {
  getItem: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch {
      console.warn('localStorage access failed');
      return null;
    }
  },
  
  setItem: (key: string, value: string): void => {
    try {
      localStorage.setItem(key, value);
    } catch {
      console.warn('localStorage write failed');
    }
  },
  
  removeItem: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch {
      console.warn('localStorage remove failed');
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear();
    } catch {
      console.warn('localStorage clear failed');
    }
  }
};

// 防抖函数，用于避免重复的认证请求
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T => {
  let timeoutId: NodeJS.Timeout;
  
  return ((...args: any[]) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  }) as T;
};

// 生成设备指纹（简单版本）
export const generateDeviceFingerprint = (): string => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);
  }
  
  const fingerprint = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    new Date().getTimezoneOffset(),
    canvas.toDataURL()
  ].join('|');
  
  // 简单hash
  let hash = 0;
  for (let i = 0; i < fingerprint.length; i++) {
    const char = fingerprint.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // 转换为32位整数
  }
  
  return Math.abs(hash).toString(16);
};

// 验证密码强度
export interface PasswordStrength {
  score: number; // 0-4
  suggestions: string[];
}

export const checkPasswordStrength = (password: string): PasswordStrength => {
  const suggestions: string[] = [];
  let score = 0;
  
  if (password.length >= 8) {
    score++;
  } else {
    suggestions.push('密码长度至少8位');
  }
  
  if (/[a-z]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含小写字母');
  }
  
  if (/[A-Z]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含大写字母');
  }
  
  if (/[0-9]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含数字');
  }
  
  if (/[^a-zA-Z0-9]/.test(password)) {
    score++;
  } else {
    suggestions.push('包含特殊字符');
  }
  
  return { score: Math.min(score, 4), suggestions };
};

// 格式化错误信息用于显示
export const formatErrorForUser = (error: AuthError): string => {
  // 根据错误类型返回用户友好的提示
  switch (error.code) {
    case 'NETWORK_ERROR':
      return '网络连接失败，请检查您的网络连接后重试';
    case 'INVALID_CREDENTIALS':
      return '登录信息有误，请检查用户名和密码';
    case 'TOKEN_EXPIRED':
      return '登录已过期，正在为您重新登录...';
    case 'SERVER_ERROR':
      return '服务暂时不可用，请稍后重试';
    default:
      return error.message;
  }
};