# 📊 个股分析功能说明文档

## 📋 文档信息

- **功能名称**: 个股分析 (Stock Analysis)
- **模块路径**: `frontend/src/components/NewStockAnalysisPage.tsx`
- **API 接口**: `/api/v1/stock-analysis/`
- **版本**: v2.6.3
- **更新日期**: 2025-09-13

## 🎯 功能概述

个股分析页面提供以股票为中心的分析模式，用户可以查看指定交易日期的所有股票列表，并深入了解每只股票在各概念中的排名表现。

### 核心特性
- 🔍 **股票列表展示**: 显示选定日期的所有股票及交易量排名
- 📊 **概念深度分析**: 查看单只股票在各概念中的排名和占比
- 🔄 **多日期切换**: 支持历史交易日数据查询
- 🔎 **实时搜索**: 股票代码/名称快速搜索功能

## 🏗️ 页面结构

### 1. 控制面板
```tsx
- 交易日期选择器 (DatePicker)
- 股票搜索输入框 (Input)  
- 数据刷新按钮 (Button)
```

### 2. 股票列表表格
| 列名 | 数据源 | 说明 |
|------|--------|------|
| 排名 | 计算字段 | 基于交易量的排名 |
| 股票代码 | `stock_code` | 股票唯一标识 |
| 股票名称 | `stock_name` | 股票中文名称 |
| 交易日期 | `trading_date` | 数据所属交易日 |
| 交易量 | `trading_volume` | 格式化显示(万/亿) |
| 概念数量 | `concept_count` | 该股票涉及的概念总数 |
| 操作 | - | "查看概念"按钮 |

### 3. 概念信息弹窗
| 列名 | 数据源 | 说明 |
|------|--------|------|
| 排名 | `concept_rank` | 股票在该概念中的排名 |
| 概念名称 | `concept_name` | 概念中文名称 |
| 交易量 | `trading_volume` | 股票在该概念的交易量 |
| 概念总量 | `concept_total_volume` | 该概念的总交易量 |
| 占比 | `volume_percentage` | 股票占概念交易量的百分比 |

## 🔌 API 接口

### 1. 获取股票每日汇总
```http
GET /api/v1/stock-analysis/stocks/daily-summary?trading_date={date}&size={size}
```

**参数说明**:
- `trading_date`: 交易日期 (YYYY-MM-DD)
- `size`: 返回数据量限制 (默认10000)

**响应格式**:
```json
{
  "summaries": [
    {
      "stock_code": "000001",
      "stock_name": "平安银行",
      "trading_volume": 1234567890,
      "concept_count": 8,
      "trading_date": "2025-09-02"
    }
  ]
}
```

### 2. 获取股票概念信息
```http
GET /api/v1/stock-analysis/stock/{stock_code}/concepts?trading_date={date}
```

**参数说明**:
- `stock_code`: 股票代码 (URL编码)
- `trading_date`: 交易日期 (YYYY-MM-DD)

**响应格式**:
```json
{
  "concepts": [
    {
      "concept_name": "银行",
      "trading_volume": 123456789,
      "concept_rank": 1,
      "concept_total_volume": 987654321,
      "volume_percentage": 12.5,
      "trading_date": "2025-09-02"
    }
  ]
}
```

## 💡 使用场景

### 1. 日常股票筛选
- **场景**: 投资者希望找到某日交易活跃的股票
- **操作**: 选择交易日期 → 查看股票列表排名 → 点击感兴趣的股票查看概念

### 2. 概念投资研究
- **场景**: 了解某只股票涉及哪些热门概念
- **操作**: 搜索目标股票 → 点击"查看概念" → 分析概念排名和占比

### 3. 历史数据分析
- **场景**: 对比不同日期的股票表现
- **操作**: 切换日期选择器 → 观察股票排名变化 → 深入分析概念变动

## 🎨 界面设计要点

### 1. 数据可视化
- **交易量格式化**: 自动转换为万/亿单位显示
- **排名标识**: 前3名红色、4-10名橙色、其他蓝色
- **概念数量标签**: 蓝色标签突出显示

### 2. 交互体验
- **搜索即过滤**: 输入框变化立即过滤结果
- **弹窗加载**: 概念数据异步加载，显示loading状态
- **响应式布局**: 支持不同屏幕尺寸

### 3. 性能优化
- **分页显示**: 默认15条/页，支持快速跳转
- **数据缓存**: 避免重复请求相同日期数据
- **懒加载**: 概念数据仅在点击时加载

## 🔧 技术实现细节

### 1. 状态管理
```tsx
// 主要状态
const [stockSummaries, setStockSummaries] = useState<StockSummary[]>([]);
const [loading, setLoading] = useState(false);
const [tradingDate, setTradingDate] = useState<string>();
const [searchText, setSearchText] = useState('');

// 弹窗状态
const [conceptModalVisible, setConceptModalVisible] = useState(false);
const [conceptList, setConceptList] = useState<ConceptInfo[]>([]);
const [conceptLoading, setConceptLoading] = useState(false);
```

### 2. 数据处理
```tsx
// 搜索过滤
summaries = summaries.filter((item: StockSummary) =>
  item.stock_code.toLowerCase().includes(searchText.toLowerCase()) ||
  item.stock_name.toLowerCase().includes(searchText.toLowerCase())
);

// 交易量排序
summaries = summaries.sort((a: StockSummary, b: StockSummary) => 
  b.trading_volume - a.trading_volume
);
```

### 3. 数字格式化
```tsx
const formatNumber = (num: number): string => {
  if (num >= 100000000) {
    return `${(num / 100000000).toFixed(2)}亿`;
  } else if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}万`;
  } else {
    return num.toLocaleString();
  }
};
```

## ⚠️ 注意事项

### 1. 数据依赖
- **TXT导入**: 页面数据依赖TXT文件导入的预计算结果
- **日期有效性**: 只有TXT导入过的日期才有数据
- **股票代码**: 需要与TXT文件中的股票代码格式一致

### 2. 性能考虑
- **大数据量**: 10000+股票列表需要考虑前端渲染性能
- **频繁搜索**: 搜索功能可能需要防抖处理
- **API超时**: 大量数据查询需要适当的超时设置

### 3. 错误处理
- **网络异常**: 显示友好的错误提示
- **数据为空**: 提供引导性的空状态提示
- **日期无效**: 自动回退到有数据的最近日期

## 🚀 未来优化方向

### 1. 功能增强
- [ ] 添加股票收藏功能
- [ ] 支持多股票对比分析
- [ ] 增加概念热力图显示
- [ ] 导出分析报告功能

### 2. 性能优化
- [ ] 虚拟滚动支持大列表
- [ ] 数据预加载和缓存
- [ ] 搜索防抖和高亮
- [ ] 图表可视化展示

### 3. 用户体验
- [ ] 添加数据更新时间显示
- [ ] 支持自定义列显示
- [ ] 快捷键操作支持
- [ ] 移动端适配优化

---

**文档维护**: 开发团队 | **最后更新**: 2025-09-13 | **版本**: v2.6.3