# 前端集成 API 指南

## 后端API 概览

本文档提供了所有后端API的完整说明，用于前端开发集成。

---

## API基础信息

**Base URL**: `http://localhost:3007/api/v1` 或生产环境对应URL

**认证**: 部分端点需要用户认证token（在请求headers中: `Authorization: Bearer <token>`）

---

## 1. 个股概念查询接口

**功能**: 根据股票代码查询该股票所属的所有概念

### 端点
```
GET /concepts/stocks/{stock_code}/concepts
```

### 参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| stock_code | Path | string | 是 | 股票代码（如：000001 或 SZ000001） |

### 请求示例
```bash
curl "http://localhost:3007/api/v1/concepts/stocks/000001/concepts"
```

### 响应示例
```json
{
  "stock": {
    "id": 1,
    "stock_code": "SZ000001",
    "original_stock_code": "000001",
    "stock_code_prefix": "SZ",
    "stock_name": "平安银行",
    "industry": "银行",
    "is_convertible_bond": false,
    "created_at": "2024-11-14T12:00:00",
    "updated_at": "2024-11-14T12:00:00"
  },
  "concepts": [
    {
      "id": 1,
      "concept_name": "银行",
      "description": "银行类概念股",
      "created_at": "2024-11-14T12:00:00"
    },
    {
      "id": 2,
      "concept_name": "深股通",
      "description": "深股通概念股",
      "created_at": "2024-11-14T12:00:00"
    }
  ]
}
```

### 错误响应
```json
{
  "detail": "股票不存在: 999999"
}
```

### HTTP状态码
- 200: 成功
- 404: 股票不存在
- 403: 查询次数不足（客户端用户）

---

## 2. 概念个股查询接口（分页）

**功能**: 根据概念名称查询该概念下的所有股票，支持分页

### 端点
```
GET /concepts/{concept_name}/stocks
```

### 参数

| 参数 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| concept_name | Path | string | 是 | - | 概念名称 |
| skip | Query | integer | 否 | 0 | 跳过的记录数（用于分页） |
| limit | Query | integer | 否 | 20 | 每页记录数（1-100） |

### 请求示例
```bash
# 获取"银行"概念下的前20只股票
curl "http://localhost:3007/api/v1/concepts/银行/stocks?skip=0&limit=20"

# 获取第二页（跳过前20条）
curl "http://localhost:3007/api/v1/concepts/银行/stocks?skip=20&limit=20"
```

### 响应示例
```json
{
  "concept": {
    "id": 1,
    "concept_name": "银行",
    "description": "银行类概念股",
    "created_at": "2024-11-14T12:00:00"
  },
  "total_count": 150,
  "stocks": [
    {
      "id": 1,
      "stock_code": "SZ000001",
      "original_stock_code": "000001",
      "stock_code_prefix": "SZ",
      "stock_name": "平安银行",
      "industry": "银行",
      "is_convertible_bond": false,
      "created_at": "2024-11-14T12:00:00",
      "updated_at": "2024-11-14T12:00:00"
    }
  ],
  "page_info": {
    "skip": 0,
    "limit": 20,
    "total": 150,
    "has_more": true
  }
}
```

### 参数验证
- limit: 最大值100，超过则限制为100
- skip: 必须 >= 0

---

## 3. 前N概念股查询接口

**功能**: 获取每个概念的前N只股票（按热度值排序）

### 端点
```
GET /concepts/top-stocks/{n}
```

### 参数

| 参数 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| n | Path | integer | 是 | - | 每个概念的前N只股票（1-50） |
| trade_date | Query | string | 否 | 今天 | 交易日期（YYYY-MM-DD格式） |

### 请求示例
```bash
# 获取所有概念的前5只股票
curl "http://localhost:3007/api/v1/concepts/top-stocks/5"

# 指定特定日期
curl "http://localhost:3007/api/v1/concepts/top-stocks/10?trade_date=2024-11-13"
```

### 响应示例
```json
[
  {
    "concept": {
      "id": 1,
      "concept_name": "银行",
      "description": "银行类概念股",
      "created_at": "2024-11-14T12:00:00"
    },
    "top_stocks": [
      {
        "id": 1,
        "stock_code": "SZ000001",
        "original_stock_code": "000001",
        "stock_code_prefix": "SZ",
        "stock_name": "平安银行",
        "industry": "银行",
        "is_convertible_bond": false,
        "created_at": "2024-11-14T12:00:00",
        "updated_at": "2024-11-14T12:00:00"
      },
      {
        "id": 2,
        "stock_code": "SZ000333",
        "original_stock_code": "000333",
        "stock_code_prefix": "SZ",
        "stock_name": "美的集团",
        "industry": "家电",
        "is_convertible_bond": false,
        "created_at": "2024-11-14T12:00:00",
        "updated_at": "2024-11-14T12:00:00"
      }
    ],
    "count": 2
  },
  {
    "concept": {
      "id": 2,
      "concept_name": "深股通",
      "description": "深股通概念股",
      "created_at": "2024-11-14T12:00:00"
    },
    "top_stocks": [
      ...
    ],
    "count": 3
  }
]
```

---

## 4. 创新高概念查询接口

**功能**: 获取在指定天数内创新高的概念

### 端点
```
GET /concepts/new-highs
```

### 参数

| 参数 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|------|--------|------|
| days | Query | integer | 否 | 10 | 检查创新高的天数 |
| trade_date | Query | string | 否 | 今天 | 交易日期（YYYY-MM-DD格式） |

### 请求示例
```bash
# 获取过去10天内创新高的概念（默认）
curl "http://localhost:3007/api/v1/concepts/new-highs"

# 获取过去30天内创新高的概念
curl "http://localhost:3007/api/v1/concepts/new-highs?days=30"

# 指定特定日期查询
curl "http://localhost:3007/api/v1/concepts/new-highs?days=5&trade_date=2024-11-13"
```

### 响应示例
```json
[
  {
    "concept": {
      "id": 1,
      "concept_name": "AI芯片",
      "description": "人工智能芯片相关概念",
      "created_at": "2024-11-14T12:00:00"
    },
    "total_heat_value": 1250.5,
    "stock_count": 25,
    "average_heat_value": 50.02,
    "days_checked": 10,
    "trade_date": "2024-11-14"
  },
  {
    "concept": {
      "id": 2,
      "concept_name": "新能源",
      "description": "新能源相关概念",
      "created_at": "2024-11-14T12:00:00"
    },
    "total_heat_value": 980.3,
    "stock_count": 18,
    "average_heat_value": 54.46,
    "days_checked": 10,
    "trade_date": "2024-11-14"
  }
]
```

---

## 5. 转债概念查询接口

**功能**: 查询可转债所属的所有概念

### 端点
```
GET /concepts/bonds/{bond_code}/concepts
```

### 参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| bond_code | Path | string | 是 | 转债代码（如：123456 或 SZ123456） |

### 请求示例
```bash
curl "http://localhost:3007/api/v1/concepts/bonds/123456/concepts"
```

### 响应示例
```json
{
  "stock": {
    "id": 50,
    "stock_code": "SZ123456",
    "original_stock_code": "123456",
    "stock_code_prefix": "SZ",
    "stock_name": "平安转债",
    "industry": null,
    "is_convertible_bond": true,
    "created_at": "2024-11-14T12:00:00",
    "updated_at": "2024-11-14T12:00:00"
  },
  "concepts": [
    {
      "id": 1,
      "concept_name": "银行转债",
      "description": "银行类可转债",
      "created_at": "2024-11-14T12:00:00"
    }
  ]
}
```

### 错误响应
```json
{
  "detail": "转债不存在: 999999"
}
```

---

## 常见错误处理

### 401 Unauthorized
表示认证失效，需要重新登录。

### 403 Forbidden
客户端用户查询次数不足，需要升级会员或购买查询包。

### 404 Not Found
- 股票不存在
- 转债不存在
- 概念不存在

### 500 Internal Server Error
服务器内部错误，可从响应中的 `detail` 字段获取具体错误信息。

---

## 前端集成要点

### 1. 错误处理
```typescript
try {
  const response = await fetch(url);
  if (!response.ok) {
    if (response.status === 401) {
      // 处理认证失效 - 跳转到登录
    } else if (response.status === 403) {
      // 处理查询次数不足
      message.error('查询次数不足，请升级会员');
    } else if (response.status === 404) {
      // 处理资源不存在
      message.error('搜索的资源不存在');
    } else {
      // 其他错误
    }
  }
} catch (error) {
  // 网络错误处理
}
```

### 2. 分页实现
```typescript
const [skip, setSkip] = useState(0);
const [limit, setLimit] = useState(20);
const [hasMore, setHasMore] = useState(false);

const loadMore = async () => {
  const response = await fetch(
    `...?skip=${skip + limit}&limit=${limit}`
  );
  const data = await response.json();
  setSkip(skip + limit);
  setHasMore(data.page_info.has_more);
};
```

### 3. 日期格式
所有日期参数都使用 YYYY-MM-DD 格式：
```typescript
const today = new Date().toISOString().split('T')[0]; // 2024-11-14
```

### 4. 股票代码规范化
API支持多种股票代码格式：
- 仅代码: `000001`
- 带前缀: `SZ000001` 或 `SH600000`

API会自动添加前缀，但建议前端也实现规范化逻辑以提供更好的用户体验。

---

## 总结

这5个API端点共同构成了一个完整的股票概念分析系统：
1. **个股概念** - 查看单只股票属于哪些概念
2. **概念个股** - 查看单个概念包含哪些股票（分页）
3. **前N概念股** - 全局视图，查看所有概念的热门股票
4. **创新高概念** - 发现最近表现强劲的概念
5. **转债概念** - 专门针对可转债的概念查询

前端可根据这些API组织4个主要页面的展示和交互。
