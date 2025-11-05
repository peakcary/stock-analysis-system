/**
 * 每日分析API服务
 */

import { apiClient } from '../utils/auth';

// 类型定义
export interface ConceptSummary {
  concept: string;
  concept_rank: number;
  stock_count: number;
  total_net_inflow: number;
  avg_net_inflow: number;
  avg_price: number;
  avg_turnover_rate: number;
  total_reads: number;
  total_pages: number;
}

export interface ConceptRanking {
  concept: string;
  stock_code: string;
  stock_name: string;
  net_inflow_rank: number;
  price_rank: number;
  turnover_rate_rank: number;
  total_reads_rank: number;
  net_inflow: number;
  price: number;
  turnover_rate: number;
  total_reads: number;
  industry: string;
}

export interface TopConcept {
  rank: number;
  concept: string;
  stock_count: number;
  total_net_inflow: number;
  avg_net_inflow: number;
}

export interface AnalysisTask {
  task_type: string;
  status: string;
  processed_concepts: number;
  processed_stocks: number;
  source_data_count: number;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  error_message: string | null;
}

export interface ConceptDetail {
  analysis_date: string;
  concept_summary: ConceptSummary;
  stock_rankings: ConceptRanking[];
}

// API服务类
export class DailyAnalysisApi {
  private static baseUrl = '/api/v1/daily-analysis';

  /**
   * 生成每日分析报告
   */
  static async generateAnalysis(analysisDate?: string) {
    const params = analysisDate ? { analysis_date: analysisDate } : {};
    const response = await apiClient.post(`${this.baseUrl}/generate-analysis`, null, { params });
    return response.data;
  }

  /**
   * 获取概念汇总排名
   */
  static async getConceptSummaries(analysisDate?: string, limit: number = 50): Promise<{
    success: boolean;
    data: {
      analysis_date: string;
      total_count: number;
      summaries: ConceptSummary[];
    };
  }> {
    const params: any = { limit };
    if (analysisDate) params.analysis_date = analysisDate;

    const response = await apiClient.get(`${this.baseUrl}/concept-summaries`, { params });
    return response.data;
  }

  /**
   * 获取概念内个股排名
   */
  static async getConceptRankings(
    analysisDate?: string,
    concept?: string,
    limit: number = 50
  ): Promise<{
    success: boolean;
    data: {
      analysis_date: string;
      concept: string | null;
      total_count: number;
      rankings: ConceptRanking[];
    };
  }> {
    const params: any = { limit };
    if (analysisDate) params.analysis_date = analysisDate;
    if (concept) params.concept = concept;

    const response = await apiClient.get(`${this.baseUrl}/concept-rankings`, { params });
    return response.data;
  }

  /**
   * 获取顶部概念
   */
  static async getTopConcepts(analysisDate?: string, limit: number = 10): Promise<{
    success: boolean;
    data: {
      analysis_date: string;
      top_concepts: TopConcept[];
    };
  }> {
    const params: any = { limit };
    if (analysisDate) params.analysis_date = analysisDate;

    const response = await apiClient.get(`${this.baseUrl}/top-concepts`, { params });
    return response.data;
  }

  /**
   * 获取概念详情
   */
  static async getConceptDetail(
    concept: string,
    analysisDate?: string
  ): Promise<{
    success: boolean;
    data: ConceptDetail;
  }> {
    const params = analysisDate ? { analysis_date: analysisDate } : {};
    const response = await apiClient.get(`${this.baseUrl}/concept-detail/${encodeURIComponent(concept)}`, { params });
    return response.data;
  }

  /**
   * 获取分析任务状态
   */
  static async getAnalysisStatus(analysisDate?: string): Promise<{
    success: boolean;
    data: {
      analysis_date: string;
      overall_status: string;
      tasks: AnalysisTask[];
    };
  }> {
    const params = analysisDate ? { analysis_date: analysisDate } : {};
    const response = await apiClient.get(`${this.baseUrl}/analysis-status`, { params });
    return response.data;
  }
}

// 辅助函数
export const analysisUtils = {
  /**
   * 格式化净流入金额
   */
  formatNetInflow: (value: number): string => {
    if (Math.abs(value) >= 100000000) {
      return `${(value / 100000000).toFixed(2)}亿`;
    } else if (Math.abs(value) >= 10000) {
      return `${(value / 10000).toFixed(2)}万`;
    }
    return value.toFixed(2);
  },

  /**
   * 获取涨跌幅颜色
   */
  getChangeColor: (value: number): string => {
    if (value > 0) return '#10b981';
    if (value < 0) return '#ef4444';
    return '#6b7280';
  },

  /**
   * 格式化百分比
   */
  formatPercent: (value: number): string => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  },

  /**
   * 计算热度评分
   */
  calculateHeatScore: (summary: ConceptSummary): number => {
    // 基于净流入、股票数量、阅读量等计算综合热度评分
    const netInflowScore = Math.min(Math.abs(summary.total_net_inflow) / 10000000, 50);
    const stockCountScore = Math.min(summary.stock_count, 30);
    const readsScore = Math.min(summary.total_reads / 1000000, 20);
    
    return Math.round(netInflowScore + stockCountScore + readsScore);
  },

  /**
   * 格式化日期显示
   */
  formatAnalysisDate: (dateStr: string): string => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (dateStr === today.toISOString().split('T')[0]) {
      return '今日';
    } else if (dateStr === yesterday.toISOString().split('T')[0]) {
      return '昨日';
    }
    return dateStr;
  }
};