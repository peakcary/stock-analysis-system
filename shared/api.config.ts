/**
 * API 配置文件
 * 不同环境使用不同的API地址
 */

// 开发环境
const DEV_CONFIG = {
  apiBaseUrl: 'http://localhost:3007',
  apiPrefix: '',
};

// 生产环境
const PROD_CONFIG = {
  apiBaseUrl: 'https://qwquant.com',
  apiPrefix: '/api/v1',
};

// 获取当前环境的API配置
export function getApiConfig() {
  // 检查是否在浏览器环境
  if (typeof window !== 'undefined') {
    // 如果hostname是localhost，使用开发配置
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return DEV_CONFIG;
    }
    // 否则使用生产配置
    return PROD_CONFIG;
  }

  // Node.js环境，默认使用生产配置
  return PROD_CONFIG;
}

/**
 * 获取完整的API URL
 * @param endpoint - API端点，如 '/auth/login'
 * @returns 完整的API URL
 */
export function getApiUrl(endpoint: string): string {
  const config = getApiConfig();
  return `${config.apiBaseUrl}${config.apiPrefix}${endpoint}`;
}

/**
 * 获取API基础URL
 */
export function getApiBaseUrl(): string {
  const config = getApiConfig();
  if (config.apiPrefix) {
    return `${config.apiBaseUrl}${config.apiPrefix}`;
  }
  return config.apiBaseUrl;
}
