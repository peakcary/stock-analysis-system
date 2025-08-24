/**
 * 全局类型定义
 */

// 股票相关类型
export interface Stock {
  id: number;
  stock_code: string;
  stock_name: string;
  industry?: string;
  is_convertible_bond: boolean;
  created_at: string;
  updated_at: string;
}

export interface Concept {
  id: number;
  concept_name: string;
  description?: string;
  created_at: string;
}

export interface StockWithConcepts {
  stock: Stock;
  concepts: Concept[];
}

export interface StockChartData {
  trade_date: string;
  price: number;
  turnover_rate: number;
  net_inflow: number;
  heat_value: number;
  pages_count: number;
  total_reads: number;
}

export interface ConceptWithStocks {
  concept: Concept;
  stocks: Stock[];
}

export interface NewHighConcept {
  concept: Concept;
  total_heat_value: number;
  stock_count: number;
  average_heat_value: number;
  days_checked: number;
  trade_date: string;
}

// API 响应类型
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// 查询参数类型
export interface StockQueryParams {
  skip?: number;
  limit?: number;
  is_bond?: boolean;
}

export interface ChartQueryParams {
  start_date?: string;
  end_date?: string;
  days?: number;
}

export interface ConceptQueryParams {
  skip?: number;
  limit?: number;
}

// 数据导入相关
export interface ImportResult {
  message: string;
  filename: string;
  imported_records: number;
  skipped_records: number;
  errors?: string[];
}

export interface RankingResult {
  message: string;
  trade_date: string;
  processed_concepts: number;
  total_rankings: number;
  new_highs_found: number;
}

// 用户认证相关类型
export interface User {
  id: number;
  username: string;
  email: string;
  phone?: string;
  membership_type: MembershipType;
  membership_expire_date?: string;
  remaining_queries: number;
  max_daily_queries: number;
  is_active: boolean;
  created_at: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  phone?: string;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface UserUpdate {
  username?: string;
  email?: string;
  phone?: string;
}

export type MembershipType = 'free' | 'basic' | 'premium' | 'vip';

export interface UserQuery {
  id: number;
  user_id: number;
  query_type: string;
  query_params: any;
  created_at: string;
}

export interface Payment {
  id: number;
  user_id: number;
  payment_type: PaymentType;
  amount: number;
  status: string;
  created_at: string;
}

// 支付相关类型
export type PaymentType = 'basic' | 'premium' | 'vip';

export interface PaymentCreate {
  payment_type: PaymentType;
  amount: number;
}