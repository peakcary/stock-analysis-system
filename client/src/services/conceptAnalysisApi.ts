// 概念分析API服务
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://your-domain.com/api/v1' 
  : 'http://localhost:3007/api/v1';

class ConceptAnalysisApi {
  // 获取股票在各概念中的排名
  static async getStockRanking(stockCode: string, tradeDate?: string) {
    const url = `${API_BASE_URL}/concept-analysis/stocks/${stockCode}/ranking`;
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${url}${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取概念内股票排名
  static async getConceptRanking(conceptId: number, tradeDate?: string, page = 1, pageSize = 20) {
    const params = new URLSearchParams();
    if (tradeDate) params.append('trade_date', tradeDate);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const response = await fetch(`${API_BASE_URL}/concept-analysis/concepts/${conceptId}/ranking?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取创新高概念列表
  static async getInnovationConcepts(tradeDate?: string, daysBack = 10, page = 1, pageSize = 20) {
    const params = new URLSearchParams();
    if (tradeDate) params.append('trade_date', tradeDate);
    params.append('days_back', daysBack.toString());
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const response = await fetch(`${API_BASE_URL}/concept-analysis/concepts/innovation?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取可转债分析数据
  static async getConvertibleBonds(tradeDate?: string, page = 1, pageSize = 20) {
    const params = new URLSearchParams();
    if (tradeDate) params.append('trade_date', tradeDate);
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    
    const response = await fetch(`${API_BASE_URL}/concept-analysis/convertible-bonds?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 触发每日分析计算
  static async triggerAnalysis(tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/concept-analysis/analysis/trigger${params}`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取分析状态
  static async getAnalysisStatus(tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/concept-analysis/analysis/status${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}

// 图表数据API服务
class ChartDataApi {
  // 获取概念热度趋势
  static async getConceptHeatTrend(conceptId: number, days = 30) {
    const response = await fetch(`${API_BASE_URL}/chart-data/concept/${conceptId}/heat-trend?days=${days}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取每日热门概念
  static async getDailyHotConcepts(tradeDate?: string, topN = 20) {
    const params = new URLSearchParams();
    if (tradeDate) params.append('trade_date', tradeDate);
    params.append('top_n', topN.toString());
    
    const response = await fetch(`${API_BASE_URL}/chart-data/daily-hot-concepts?${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取概念内股票分布
  static async getStockDistribution(conceptId: number, tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/chart-data/concept/${conceptId}/stock-distribution${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取创新高时间线
  static async getInnovationTimeline(days = 30) {
    const response = await fetch(`${API_BASE_URL}/chart-data/innovation-timeline?days=${days}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取可转债分析图表
  static async getConvertibleBondsChart(tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/chart-data/convertible-bonds-analysis${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取概念对比图表
  static async getConceptComparison(conceptIds: number[], days = 30) {
    const idsParam = conceptIds.join(',');
    
    const response = await fetch(`${API_BASE_URL}/chart-data/concept-comparison?concept_ids=${idsParam}&days=${days}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取市场概览
  static async getMarketOverview(tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/chart-data/market-overview${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }

  // 获取股票概念表现
  static async getStockConceptPerformance(stockId: number, tradeDate?: string) {
    const params = tradeDate ? `?trade_date=${tradeDate}` : '';
    
    const response = await fetch(`${API_BASE_URL}/chart-data/stock/${stockId}/concept-performance${params}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  }
}

// 工具函数
export const conceptAnalysisUtils = {
  // 格式化热度值
  formatHeatValue: (value: number) => {
    if (value >= 1000000) {
      return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
      return (value / 1000).toFixed(1) + 'K';
    }
    return value.toFixed(1);
  },

  // 获取热度颜色
  getHeatColor: (value: number) => {
    if (value >= 80) return '#ef4444';
    if (value >= 60) return '#f59e0b';
    if (value >= 40) return '#10b981';
    return '#6b7280';
  },

  // 计算热度等级
  getHeatLevel: (value: number) => {
    if (value >= 80) return '极热';
    if (value >= 60) return '热门';
    if (value >= 40) return '温和';
    return '冷门';
  },

  // 格式化排名显示
  formatRank: (rank: number, total: number) => {
    const percentage = ((rank / total) * 100).toFixed(1);
    return `第${rank}名 (前${percentage}%)`;
  },

  // 格式化日期
  formatDate: (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }
};

export { ConceptAnalysisApi, ChartDataApi };
export type {
  ConceptRankingData,
  StockRankingData,
  InnovationConceptData,
  ConvertibleBondData
} from '../pages/AnalysisPage';