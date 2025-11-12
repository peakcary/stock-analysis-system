/**
 * API 端点常量定义
 * 统一管理所有API端点，避免硬编码
 *
 * 使用方式:
 * import { API_ENDPOINTS } from '@/api/endpoints';
 * adminApiClient.get(API_ENDPOINTS.STOCKS.LIST)
 */

export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
    REGISTER: '/auth/register',
  },

  // 管理员认证
  ADMIN_AUTH: {
    LOGIN: '/admin/auth/login',
    LOGOUT: '/admin/auth/logout',
    ME: '/admin/auth/me',
    REFRESH: '/admin/auth/refresh',
  },

  // 股票相关
  STOCKS: {
    LIST: '/stocks',
    COUNT: '/stocks/count',
    SIMPLE: '/stocks/simple',
    DETAIL: (stockCode: string) => `/stocks/${stockCode}`,
    DELETE: (stockId: number) => `/stocks/${stockId}`,
    BATCH_DELETE: '/stocks/batch',
  },

  // 概念相关
  CONCEPTS: {
    LIST: '/concepts',
    COUNT: '/concepts/count',
  },

  // 数据导入
  DATA_IMPORT: {
    STATUS: (date: string) => `/data/import-status/${date}`,
    IMPORT_CSV: '/data/import-csv',
    IMPORT_TXT: '/data/import-txt',
  },

  // 简化导入
  SIMPLE_IMPORT: {
    IMPORT_CSV: '/simple-import/simple-csv',
    IMPORT_TXT: '/simple-import/simple-txt',
  },

  // 通用导入
  UNIVERSAL_IMPORT: {
    SUPPORTED_TYPES: '/universal-import/supported-types',
    RECORDS: (fileType: string) => `/universal-import/${fileType}/records`,
    STATISTICS: (fileType: string) => `/universal-import/${fileType}/statistics`,
    IMPORT: '/universal-import/import',
  },

  // TXT导入
  TXT_IMPORT: {
    CHECK_DATE: '/txt-import/check-date',
    IMPORT: '/txt-import/import',
  },

  // 股票数据
  STOCK_DATA: {
    IMPORT_CSV: '/stock-data/import-csv',
    IMPORT_TXT: '/stock-data/import-txt',
  },

  // 日常分析
  DAILY_ANALYSIS: {
    LIST: '/daily-analysis',
  },

  // 概念分析
  CONCEPT_ANALYSIS: {
    LIST: '/concept-analysis',
  },

  // 图表数据
  CHART_DATA: {
    LIST: '/chart-data',
  },

  // 客户端用户
  CLIENT_USERS: {
    LIST: '/admin/client-users',
    CREATE: '/admin/client-users',
    UPDATE: (userId: number) => `/admin/client-users/${userId}`,
    DELETE: (userId: number) => `/admin/client-users/${userId}`,
  },

  // 管理员
  ADMIN: {
    LIST: '/admin/users',
    CREATE: '/admin/users',
    UPDATE: (adminId: number) => `/admin/users/${adminId}`,
    DELETE: (adminId: number) => `/admin/users/${adminId}`,
  },

  // 支付
  PAYMENT: {
    ORDER_LIST: '/payment/orders',
    CREATE_ORDER: '/payment/orders',
    CANCEL_ORDER: (orderId: number) => `/payment/orders/${orderId}/cancel`,
  },

  // 套餐管理
  PACKAGES: {
    LIST: '/admin/packages',
    CREATE: '/admin/packages',
    UPDATE: (packageId: number) => `/admin/packages/${packageId}`,
    DELETE: (packageId: number) => `/admin/packages/${packageId}`,
  },

  // 模拟支付
  MOCK_PAYMENT: {
    NOTIFY: '/mock/payment/notify',
  },

  // 系统
  SYSTEM: {
    HEALTH: '/system/health',
    STATUS: '/system/status',
  },
} as const;

/**
 * 类型安全的端点获取函数
 * 用于动态生成需要参数的端点
 *
 * 例如:
 * getEndpoint('STOCKS', 'DETAIL', 'AAPL')
 */
export function getEndpoint(
  category: keyof typeof API_ENDPOINTS,
  endpoint: string,
  ...params: (string | number)[]
): string {
  const categoryEndpoints = API_ENDPOINTS[category] as any;
  const endpointFn = categoryEndpoints[endpoint];

  if (typeof endpointFn === 'function') {
    return endpointFn(...params);
  }

  return endpointFn;
}
