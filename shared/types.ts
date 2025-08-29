/**
 * 股票分析系统共享类型定义
 * Shared Type Definitions for Stock Analysis System
 */

// ============ 用户相关类型 ============

export interface User {
  id: number;
  username: string;
  email: string;
  membership_type: 'FREE' | 'PRO' | 'PREMIUM';
  queries_remaining: number;
  membership_expires_at?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserStats {
  total_users: number;
  active_users: number;
  pro_users: number;
  premium_users: number;
  queries_today: number;
  payments_today: number;
}

// ============ 股票相关类型 ============

export interface Stock {
  id: number;
  symbol: string;
  name: string;
  concept: string;
  market_cap?: number;
  price?: number;
  change_percent?: number;
  updated_at: string;
}

export interface StockQuery {
  search?: string;
  concept?: string;
  limit?: number;
  offset?: number;
}

// ============ 支付相关类型 ============

export interface PaymentPackage {
  id: number;
  package_type: string;
  name: string;
  price: number;
  queries_count: number;
  validity_days: number;
  membership_type: 'FREE' | 'PRO' | 'PREMIUM';
  description?: string;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface PaymentOrder {
  id: number;
  out_trade_no: string;
  package_name: string;
  amount: number;
  status: 'PENDING' | 'PAID' | 'FAILED' | 'CANCELLED' | 'EXPIRED';
  payment_method: 'WECHAT_NATIVE' | 'WECHAT_H5' | 'ALIPAY';
  code_url?: string;
  h5_url?: string;
  expire_time: string;
  created_at: string;
}

// ============ API响应类型 ============

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ============ 认证相关类型 ============

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
}

// ============ 管理端专用类型 ============

export interface AdminUserCreate {
  username: string;
  email: string;
  password: string;
  membership_type: 'FREE' | 'PRO' | 'PREMIUM';
  queries_remaining: number;
}

export interface DataImportStatus {
  csv_imported: boolean;
  txt_imported: boolean;
  csv_record?: any;
  txt_record?: any;
  import_date: string;
}

// ============ 系统监控类型 ============

export interface SystemHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  checks: {
    database: HealthCheck;
    cache: HealthCheck;
    database_tables: HealthCheck;
  };
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy' | 'degraded';
  message: string;
}

// ============ 枚举类型 ============

export enum MembershipType {
  FREE = 'FREE',
  PRO = 'PRO', 
  PREMIUM = 'PREMIUM'
}

export enum PaymentStatus {
  PENDING = 'PENDING',
  PAID = 'PAID',
  FAILED = 'FAILED', 
  CANCELLED = 'CANCELLED',
  EXPIRED = 'EXPIRED'
}

export enum PaymentMethod {
  WECHAT_NATIVE = 'WECHAT_NATIVE',
  WECHAT_H5 = 'WECHAT_H5',
  ALIPAY = 'ALIPAY'
}