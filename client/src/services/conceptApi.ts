/**
 * Concept Analysis API Service
 * Handles all concept-related API calls
 */

import { apiClient } from '../utils/auth';

// Type definitions
export interface Stock {
  id: number;
  stock_code: string;
  original_stock_code: string;
  stock_code_prefix: string;
  stock_name: string;
  industry: string;
  is_convertible_bond: boolean;
  created_at: string;
  updated_at: string;
}

export interface Concept {
  id: number;
  concept_name: string;
  description: string;
  created_at: string;
}

export interface StockConceptResponse {
  stock: Stock;
  concepts: Concept[];
}

export interface NewHighConcept {
  concept: Concept;
  total_heat_value: number;
  stock_count: number;
  average_heat_value: number;
  days_checked: number;
  trade_date: string;
}

export interface TopStockForConcept {
  stock_code: string;
  stock_name: string;
  heat_value: number;
}

export interface TopConceptData {
  concept: Concept;
  top_stocks: TopStockForConcept[];
}

/**
 * Concept Analysis API Service
 * Provides methods to fetch concept and stock analysis data
 */
export class ConceptAnalysisApi {
  private static baseUrl = '/api/concepts';

  /**
   * Get concepts for a specific stock
   */
  static async getStockConcepts(stockCode: string): Promise<StockConceptResponse> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/stocks/${encodeURIComponent(stockCode)}/concepts`);
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
        `Failed to fetch concepts for stock ${stockCode}`
      );
    }
  }

  /**
   * Get all stocks for a specific concept
   */
  static async getConceptStocks(
    conceptName: string,
    page: number = 1,
    pageSize: number = 50
  ): Promise<{
    concept: Concept;
    stocks: Stock[];
    total: number;
    page: number;
    page_size: number;
  }> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/${encodeURIComponent(conceptName)}/stocks`,
        {
          params: { page, page_size: pageSize }
        }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
        `Failed to fetch stocks for concept ${conceptName}`
      );
    }
  }

  /**
   * Get new high concepts with optional filters
   */
  static async getNewHighConcepts(
    days: number = 1,
    tradeDate?: string
  ): Promise<{
    concepts: NewHighConcept[];
    total_concepts: number;
    total_stocks: number;
    trade_date: string;
  }> {
    try {
      const params: any = { days };
      if (tradeDate) {
        params.trade_date = tradeDate;
      }

      const response = await apiClient.get(
        `${this.baseUrl}/new-highs`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
        'Failed to fetch new high concepts'
      );
    }
  }

  /**
   * Get top N stocks for all concepts
   */
  static async getTopStocksForConcepts(
    n: number = 10,
    tradeDate?: string
  ): Promise<{
    concepts_with_top_stocks: TopConceptData[];
    total_concepts: number;
    total_unique_stocks: number;
    trade_date: string;
  }> {
    try {
      const params: any = { n };
      if (tradeDate) {
        params.trade_date = tradeDate;
      }

      const response = await apiClient.get(
        `${this.baseUrl}/top-stocks/${n}`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
        'Failed to fetch top stocks for concepts'
      );
    }
  }

  /**
   * Get concepts for a convertible bond
   */
  static async getBondConcepts(bondCode: string): Promise<StockConceptResponse> {
    try {
      const response = await apiClient.get(
        `${this.baseUrl}/bonds/${encodeURIComponent(bondCode)}/concepts`
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail ||
        `Failed to fetch concepts for bond ${bondCode}`
      );
    }
  }

  /**
   * Get total concept count
   */
  static async getConceptCount(): Promise<{ total: number }> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/count`);
      return response.data;
    } catch (error: any) {
      throw new Error('Failed to fetch concept count');
    }
  }
}

/**
 * Utility functions for concept data formatting
 */
export const conceptUtils = {
  /**
   * Format large numbers with appropriate units
   */
  formatNumber: (value: number): string => {
    if (value >= 100000000) return `${(value / 100000000).toFixed(2)}亿`;
    if (value >= 10000) return `${(value / 10000).toFixed(2)}万`;
    return value.toString();
  },

  /**
   * Get color for heat value
   */
  getHeatColor: (heat: number): string => {
    if (heat >= 1000) return '#ef4444'; // Red - very hot
    if (heat >= 500) return '#f59e0b'; // Orange - hot
    if (heat >= 100) return '#eab308'; // Yellow - warm
    if (heat >= 10) return '#84cc16'; // Lime - cool
    return '#10b981'; // Green - cold
  },

  /**
   * Get color for rank
   */
  getRankColor: (rank: number): string => {
    if (rank === 1) return '#fbbf24'; // Gold
    if (rank === 2) return '#d1d5db'; // Silver
    if (rank === 3) return '#f8b88b'; // Bronze
    return '#667eea'; // Default
  },

  /**
   * Format date string
   */
  formatDate: (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    } catch {
      return dateString;
    }
  },

  /**
   * Validate stock code format
   */
  validateStockCode: (code: string): boolean => {
    const regex = /^([0-9]{6}|SZ[0-9]{6}|SH[0-9]{6})$/i;
    return regex.test(code.trim());
  },

  /**
   * Validate bond code format
   */
  validateBondCode: (code: string): boolean => {
    const regex = /^(1\d{3}|SZ1\d{3}|SH1\d{3})$/i;
    return regex.test(code.trim());
  }
};

export default ConceptAnalysisApi;
