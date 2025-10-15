/**
 * 设计 Token 系统
 * 统一的设计变量，确保整个应用的视觉一致性
 */

export const designTokens = {
  // ============================================
  // 间距系统 (基于 4px 网格)
  // ============================================
  spacing: {
    xxs: '2px',
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
    xxxl: '64px'
  },

  // ============================================
  // 字体系统 (1.25 比例)
  // ============================================
  fontSize: {
    tiny: '10px',      // 最小字体 (标签、徽章)
    xs: '12px',        // 辅助文本
    sm: '14px',        // 次要文本
    base: '16px',      // 正文
    lg: '20px',        // 小标题
    xl: '24px',        // 中标题
    xxl: '32px',       // 大标题
    xxxl: '40px',      // 特大标题
    display: '48px'    // 展示标题
  },

  // 字重
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },

  // 行高
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.6,
    loose: 1.8
  },

  // ============================================
  // 颜色系统
  // ============================================
  colors: {
    // 品牌色
    primary: {
      50: '#f5f7ff',
      100: '#ebf0ff',
      200: '#dce4ff',
      300: '#c3d1ff',
      400: '#a3b5ff',
      500: '#667eea',    // 主色
      600: '#5568d3',
      700: '#4553b8',
      800: '#3a4694',
      900: '#2d3670'
    },

    // 市场指示器 (股票专用)
    market: {
      bullish: '#10b981',      // 涨/买入 - 绿色
      bearish: '#ef4444',      // 跌/卖出 - 红色
      neutral: '#6b7280',      // 中性 - 灰色
      bullishBg: '#d1fae5',    // 涨背景
      bearishBg: '#fee2e2',    // 跌背景
      neutralBg: '#f3f4f6'     // 中性背景
    },

    // 状态色
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',

    // 成功色渐变
    successShades: {
      50: '#ecfdf5',
      100: '#d1fae5',
      500: '#10b981',
      700: '#047857'
    },

    // 警告色渐变
    warningShades: {
      50: '#fffbeb',
      100: '#fef3c7',
      500: '#f59e0b',
      700: '#b45309'
    },

    // 错误色渐变
    errorShades: {
      50: '#fef2f2',
      100: '#fee2e2',
      500: '#ef4444',
      700: '#b91c1c'
    },

    // 背景色
    background: {
      primary: '#ffffff',
      secondary: '#f8fafc',
      tertiary: '#f1f5f9',
      elevated: '#ffffff',
      overlay: 'rgba(0, 0, 0, 0.5)',
      disabled: '#f3f4f6'
    },

    // 文本色 (已优化对比度以符合 WCAG AA)
    text: {
      primary: '#111827',        // 16.7:1 对比度
      secondary: '#4b5563',      // 8.6:1 对比度 (之前是 #6b7280)
      tertiary: '#6b7280',       // 4.6:1 对比度 (之前是 #9ca3af)
      disabled: '#9ca3af',       // 仅用于禁用状态
      inverse: '#ffffff',        // 反色文本
      link: '#667eea',           // 链接色
      linkHover: '#5568d3'       // 链接悬停
    },

    // 边框色
    border: {
      light: '#e5e7eb',
      medium: '#d1d5db',
      strong: '#9ca3af',
      focus: '#667eea',
      error: '#ef4444',
      success: '#10b981'
    },

    // 热度等级色 (金融数据专用)
    heat: {
      cold: '#3b82f6',      // 冷门 - 蓝色
      warm: '#f59e0b',      // 温热 - 橙色
      hot: '#ef4444',       // 热门 - 红色
      extreme: '#dc2626'    // 极热 - 深红
    },

    // 排名色 (金融数据专用)
    rank: {
      top1: '#f59e0b',      // 第1名 - 金色
      top3: '#f59e0b',      // 前3名 - 金色
      top10: '#10b981',     // 前10名 - 绿色
      normal: '#6b7280'     // 其他 - 灰色
    }
  },

  // ============================================
  // 圆角
  // ============================================
  borderRadius: {
    none: '0',
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    xxl: '24px',
    full: '9999px'
  },

  // ============================================
  // 阴影 (层级)
  // ============================================
  elevation: {
    none: 'none',
    xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
    xxl: '0 25px 50px -12px rgba(0, 0, 0, 0.25)'
  },

  // ============================================
  // 过渡动画
  // ============================================
  transition: {
    fast: '150ms',
    base: '200ms',
    slow: '300ms',
    slower: '500ms'
  },

  // 缓动函数
  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
  },

  // ============================================
  // Z-Index 层级
  // ============================================
  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
    notification: 1080
  },

  // ============================================
  // 断点 (响应式)
  // ============================================
  breakpoints: {
    xs: '480px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    xxl: '1536px'
  },

  // ============================================
  // 组件特定 Token
  // ============================================
  components: {
    // 按钮
    button: {
      minHeight: {
        desktop: '40px',
        mobile: '44px'     // Touch-friendly
      },
      padding: {
        sm: '0 12px',
        md: '0 16px',
        lg: '0 24px'
      }
    },

    // 卡片
    card: {
      padding: {
        desktop: '24px',
        mobile: '16px'
      },
      gap: '16px'
    },

    // 输入框
    input: {
      minHeight: {
        desktop: '40px',
        mobile: '44px'     // 防止 iOS 自动缩放
      },
      fontSize: {
        desktop: '14px',
        mobile: '16px'     // 防止 iOS 自动缩放
      }
    },

    // 表格
    table: {
      cellPadding: {
        desktop: '12px 16px',
        mobile: '8px 6px'
      },
      rowHeight: {
        desktop: '48px',
        mobile: '56px'     // Touch-friendly
      }
    }
  }
};

// ============================================
// 辅助函数
// ============================================

/**
 * 根据数值获取市场涨跌颜色
 */
export const getMarketColor = (value: number): string => {
  if (value > 0) return designTokens.colors.market.bullish;
  if (value < 0) return designTokens.colors.market.bearish;
  return designTokens.colors.market.neutral;
};

/**
 * 根据数值获取市场涨跌背景色
 */
export const getMarketBgColor = (value: number): string => {
  if (value > 0) return designTokens.colors.market.bullishBg;
  if (value < 0) return designTokens.colors.market.bearishBg;
  return designTokens.colors.market.neutralBg;
};

/**
 * 根据热度值获取颜色
 */
export const getHeatColor = (heatValue: number): string => {
  if (heatValue >= 10000) return designTokens.colors.heat.extreme;
  if (heatValue >= 5000) return designTokens.colors.heat.hot;
  if (heatValue >= 1000) return designTokens.colors.heat.warm;
  return designTokens.colors.heat.cold;
};

/**
 * 根据排名获取颜色
 */
export const getRankColor = (rank: number): string => {
  if (rank === 1) return designTokens.colors.rank.top1;
  if (rank <= 3) return designTokens.colors.rank.top3;
  if (rank <= 10) return designTokens.colors.rank.top10;
  return designTokens.colors.rank.normal;
};

/**
 * 获取响应式间距
 */
export const getResponsiveSpacing = (isMobile: boolean, desktopSize: keyof typeof designTokens.spacing, mobileSize: keyof typeof designTokens.spacing) => {
  return isMobile ? designTokens.spacing[mobileSize] : designTokens.spacing[desktopSize];
};

// 导出类型
export type DesignTokens = typeof designTokens;
export type SpacingKey = keyof typeof designTokens.spacing;
export type FontSizeKey = keyof typeof designTokens.fontSize;
export type ColorKey = keyof typeof designTokens.colors;

export default designTokens;
