/**
 * 数字格式化工具
 * 提供一致的数字、货币、百分比格式化
 */

import React from 'react';
import { designTokens, getMarketColor } from '../styles/designTokens';

/**
 * 格式化货币
 * @param value 数值
 * @param decimals 小数位数
 * @returns 格式化后的货币字符串
 */
export const formatCurrency = (value: number, decimals: number = 2): string => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

/**
 * 格式化大数字 (万/亿)
 * @param value 数值
 * @returns 格式化后的字符串
 */
export const formatLargeNumber = (value: number): string => {
  if (value >= 100000000) {
    return (value / 100000000).toFixed(2) + '亿';
  }
  if (value >= 10000) {
    return (value / 10000).toFixed(2) + '万';
  }
  if (value >= 1000) {
    return value.toLocaleString('zh-CN');
  }
  return value.toString();
};

/**
 * 格式化百分比
 * @param value 数值 (如 5.67 表示 5.67%)
 * @param decimals 小数位数
 * @param showSign 是否显示正号
 * @returns 格式化后的百分比字符串
 */
export const formatPercentage = (
  value: number,
  decimals: number = 2,
  showSign: boolean = false
): string => {
  const sign = showSign && value > 0 ? '+' : '';
  return sign + value.toFixed(decimals) + '%';
};

/**
 * 格式化涨跌幅 (带颜色和箭头)
 * @param value 涨跌幅
 * @param decimals 小数位数
 * @returns React 元素
 */
export const formatChange = (value: number, decimals: number = 2): React.ReactElement => {
  const color = getMarketColor(value);
  const arrow = value > 0 ? '▲' : value < 0 ? '▼' : '';
  const sign = value > 0 ? '+' : '';

  return (
    <span style={{ color, fontWeight: 600 }}>
      {arrow} {sign}{value.toFixed(decimals)}%
    </span>
  );
};

/**
 * 格式化涨跌额 (带颜色和箭头)
 * @param value 涨跌额
 * @param decimals 小数位数
 * @returns React 元素
 */
export const formatChangeAmount = (value: number, decimals: number = 2): React.ReactElement => {
  const color = getMarketColor(value);
  const arrow = value > 0 ? '▲' : value < 0 ? '▼' : '';
  const sign = value > 0 ? '+' : '';

  return (
    <span style={{ color, fontWeight: 600 }}>
      {arrow} {sign}{value.toFixed(decimals)}
    </span>
  );
};

/**
 * 格式化紧凑数字 (用于移动端)
 * @param value 数值
 * @returns 格式化后的字符串
 */
export const formatCompact = (value: number): string => {
  return new Intl.NumberFormat('zh-CN', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 1
  }).format(value);
};

/**
 * 格式化净流入 (带单位)
 * @param value 净流入金额
 * @returns 格式化后的字符串
 */
export const formatNetInflow = (value: number): string => {
  const absValue = Math.abs(value);

  if (absValue >= 100000000) {
    return (value / 100000000).toFixed(2) + '亿';
  }
  if (absValue >= 10000) {
    return (value / 10000).toFixed(2) + '万';
  }
  return value.toFixed(2);
};

/**
 * 格式化热度值
 * @param value 热度值
 * @returns 格式化后的字符串
 */
export const formatHeatValue = (value: number): string => {
  if (value >= 10000) {
    return (value / 10000).toFixed(1) + 'w';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'k';
  }
  return value.toFixed(0);
};

/**
 * 格式化日期
 * @param date 日期字符串或 Date 对象
 * @param format 格式类型
 * @returns 格式化后的日期字符串
 */
export const formatDate = (
  date: string | Date,
  format: 'full' | 'short' | 'time' = 'full'
): string => {
  const d = typeof date === 'string' ? new Date(date) : date;

  if (format === 'full') {
    return new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(d);
  }

  if (format === 'short') {
    return new Intl.DateTimeFormat('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    }).format(d);
  }

  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(d);
};

/**
 * 格式化排名
 * @param rank 排名
 * @param total 总数
 * @returns 格式化后的字符串
 */
export const formatRank = (rank: number, total?: number): string => {
  if (total) {
    const percentage = ((rank / total) * 100).toFixed(1);
    return `第${rank}名 (前${percentage}%)`;
  }
  return `第${rank}名`;
};

/**
 * 格式化股票代码 (添加市场标识)
 * @param code 股票代码
 * @returns 格式化后的股票代码
 */
export const formatStockCode = (code: string): string => {
  if (code.startsWith('6')) {
    return `SH${code}`;  // 上海
  }
  if (code.startsWith('0') || code.startsWith('3')) {
    return `SZ${code}`;  // 深圳
  }
  return code;
};

/**
 * 格式化成交量
 * @param volume 成交量
 * @returns 格式化后的字符串
 */
export const formatVolume = (volume: number): string => {
  if (volume >= 100000000) {
    return (volume / 100000000).toFixed(2) + '亿手';
  }
  if (volume >= 10000) {
    return (volume / 10000).toFixed(2) + '万手';
  }
  return volume.toLocaleString('zh-CN') + '手';
};

/**
 * 格式化成交额
 * @param amount 成交额
 * @returns 格式化后的字符串
 */
export const formatTurnover = (amount: number): string => {
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(2) + '亿元';
  }
  if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万元';
  }
  return amount.toLocaleString('zh-CN') + '元';
};

/**
 * 格式化换手率
 * @param rate 换手率 (小数形式，如 0.0567)
 * @returns 格式化后的字符串
 */
export const formatTurnoverRate = (rate: number): string => {
  return (rate * 100).toFixed(2) + '%';
};

/**
 * 获取热度等级标签
 * @param heatValue 热度值
 * @returns 热度等级标签
 */
export const getHeatLevel = (heatValue: number): string => {
  if (heatValue >= 10000) return '🔥 极热';
  if (heatValue >= 5000) return '🔥 很热';
  if (heatValue >= 1000) return '⭐ 温热';
  return '💤 冷门';
};

/**
 * 格式化时间段 (如 "30天", "7天")
 * @param days 天数
 * @returns 格式化后的字符串
 */
export const formatTimePeriod = (days: number): string => {
  if (days >= 365) {
    return Math.floor(days / 365) + '年';
  }
  if (days >= 30) {
    return Math.floor(days / 30) + '个月';
  }
  if (days >= 7) {
    return Math.floor(days / 7) + '周';
  }
  return days + '天';
};

/**
 * 数字千分位格式化
 * @param value 数值
 * @returns 格式化后的字符串
 */
export const formatThousands = (value: number): string => {
  return value.toLocaleString('zh-CN');
};

// 导出所有格式化函数
export const formatters = {
  currency: formatCurrency,
  largeNumber: formatLargeNumber,
  percentage: formatPercentage,
  change: formatChange,
  changeAmount: formatChangeAmount,
  compact: formatCompact,
  netInflow: formatNetInflow,
  heatValue: formatHeatValue,
  date: formatDate,
  rank: formatRank,
  stockCode: formatStockCode,
  volume: formatVolume,
  turnover: formatTurnover,
  turnoverRate: formatTurnoverRate,
  heatLevel: getHeatLevel,
  timePeriod: formatTimePeriod,
  thousands: formatThousands
};

export default formatters;
