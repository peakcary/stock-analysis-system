/**
 * API 配置文件
 * 不同环境使用不同的API地址
 */

// 获取开发环境API配置
function getDevConfig() {
  if (typeof window !== 'undefined') {
    return {
      apiBaseUrl: `http://${window.location.hostname}:3007`,
      apiPrefix: '',
    };
  }
  return {
    apiBaseUrl: 'http://localhost:3007',
    apiPrefix: '',
  };
}

// 获取生产环境API配置
function getProdConfig() {
  if (typeof window !== 'undefined') {
    return {
      apiBaseUrl: window.location.origin,
      apiPrefix: '/api/v1',
    };
  }
  return {
    apiBaseUrl: 'https://qwquant.com',
    apiPrefix: '/api/v1',
  };
}

// 获取当前环境的API配置
export function getApiConfig() {
  // 检查是否在浏览器环境
  if (typeof window !== 'undefined') {
    // 如果hostname是localhost或127.0.0.1，使用开发配置
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return getDevConfig();
    }
    // 否则使用生产配置（自动检测当前域名）
    return getProdConfig();
  }

  // Node.js环境，默认使用生产配置
  return getProdConfig();
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
