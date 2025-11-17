/**
 * 概念分析API调用工具
 */

import { apiClient } from './auth';

// ==================== 类型定义 ====================

export interface ConceptRanking {
  concept_id: number;
  concept_name: string;
  rank: number;
  total_stocks: number;
  heat_value: number;
}

export interface StockConceptData {
  stock_code: string;
  stock_name: string;
  trade_date: string;
  heat_value: number;
  concept_rankings: ConceptRanking[];
  total_concepts: number;
}

export interface StockRanking {
  stock_id: number;
  stock_code: string;
  stock_name: string;
  rank: number;
  heat_value: number;
}

export interface ConceptSummary {
  total_heat_value: number;
  stock_count: number;
  avg_heat_value: number;
  is_new_high: boolean;
  new_high_days: number;
}

export interface ConceptRankingData {
  concept_id: number;
  concept_name: string;
  trade_date: string;
  summary: ConceptSummary;
  rankings: StockRanking[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface InnovationConcept {
  concept_id: number;
  concept_name: string;
  total_heat_value: number;
  stock_count: number;
  avg_heat_value: number;
  new_high_days: number;
  top_stocks: Array<{
    stock_code: string;
    stock_name: string;
    heat_value: number;
  }>;
}

export interface InnovationConceptsData {
  trade_date: string;
  days_back: number;
  innovation_concepts: InnovationConcept[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export interface ConvertibleBond {
  stock_id: number;
  stock_code: string;
  stock_name: string;
  heat_value: number;
  concepts: string[];
}

export interface ConvertibleBondsData {
  trade_date: string;
  statistics: {
    total_bonds: number;
    avg_heat_value: number;
    max_heat_value: number;
    total_heat_value: number;
  };
  convertible_bonds: ConvertibleBond[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

// ==================== API调用函数 ====================

/**
 * 查询单只股票在各概念中的排名
 */
export const getStockConceptRanking = async (
  stockCode: string,
  tradeDate?: string
): Promise<StockConceptData> => {
  const params: any = {};
  if (tradeDate) {
    params.trade_date = tradeDate;
  }

  const response = await apiClient.get(
    `/concept-analysis/stocks/${stockCode}/ranking`,
    { params }
  );

  return response.data;
};

/**
 * 查询概念内股票排名（支持分页）
 */
export const getConceptStockRanking = async (
  conceptId: number,
  page: number = 1,
  pageSize: number = 10,
  tradeDate?: string
): Promise<ConceptRankingData> => {
  const params: any = {
    page,
    page_size: pageSize,
  };

  if (tradeDate) {
    params.trade_date = tradeDate;
  }

  const response = await apiClient.get(
    `/concept-analysis/concepts/${conceptId}/ranking`,
    { params }
  );

  return response.data;
};

/**
 * 获取创新高概念列表
 */
export const getInnovationConcepts = async (
  daysBack: number = 10,
  page: number = 1,
  pageSize: number = 20,
  tradeDate?: string
): Promise<InnovationConceptsData> => {
  const params: any = {
    days_back: daysBack,
    page,
    page_size: pageSize,
  };

  if (tradeDate) {
    params.trade_date = tradeDate;
  }

  const response = await apiClient.get(
    `/concept-analysis/concepts/innovation`,
    { params }
  );

  return response.data;
};

/**
 * 获取可转债分析数据
 */
export const getConvertibleBonds = async (
  page: number = 1,
  pageSize: number = 20,
  tradeDate?: string
): Promise<ConvertibleBondsData> => {
  const params: any = {
    page,
    page_size: pageSize,
  };

  if (tradeDate) {
    params.trade_date = tradeDate;
  }

  const response = await apiClient.get(
    `/concept-analysis/convertible-bonds`,
    { params }
  );

  return response.data;
};

/**
 * 获取股票图表数据
 */
export const getStockChartData = async (stockCode: string) => {
  const response = await apiClient.get(
    `/stock-analysis/stock/${stockCode}/chart-data`
  );

  return response.data;
};

/**
 * 获取前N概念股（从stock-analysis端点）
 */
export const getTopConceptsStocks = async (topN: number, tradeDate?: string) => {
  const params: any = {};

  if (tradeDate) {
    params.trade_date = tradeDate;
  }

  const response = await apiClient.get(
    `/stock-analysis/concepts/top/${topN}`,
    { params }
  );

  return response.data;
};
