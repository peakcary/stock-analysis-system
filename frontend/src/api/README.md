# API 调用指南

## 原则
**❌ 禁止在组件中硬编码 API 路径**
**✅ 所有 API 调用必须使用统一配置**

## 问题案例

### ❌ 错误的做法（已经修复）
```typescript
// 不要这样做！
const response = await adminApiClient.get('/api/v1/universal-import/records');
// 结果: /api/v1 + /api/v1/universal-import/records = /api/v1/api/v1/universal-import/records ❌
```

### ✅ 正确的做法
```typescript
// 方式1: 使用常量
import { API_ENDPOINTS } from '@/api/endpoints';
const response = await adminApiClient.get(API_ENDPOINTS.UNIVERSAL_IMPORT.RECORDS('ttv'));
// 结果: /api/v1 + /universal-import/ttv/records = /api/v1/universal-import/ttv/records ✅

// 方式2: 使用辅助函数
import { getEndpoint } from '@/api/endpoints';
const response = await adminApiClient.get(getEndpoint('UNIVERSAL_IMPORT', 'RECORDS', 'ttv'));
// 结果: 同上 ✅
```

## 为什么要这样做？

### 1. **防止硬编码带来的问题**
   - API 路径写在多个地方，难以维护
   - 容易出现拼写错误
   - 难以统一更改 API 路径

### 2. **集中管理 API 端点**
   - 所有端点定义在一个文件中
   - 修改时只需改一个地方
   - 便于版本升级

### 3. **类型安全**
   - TypeScript 提供自动完成
   - 编译时检查端点是否存在
   - 防止运行时 404 错误

## 如何使用

### 导入端点常量
```typescript
import { API_ENDPOINTS } from '@/api/endpoints';
import { adminApiClient } from 'shared/admin-auth';
```

### 简单端点（无参数）
```typescript
// 获取股票列表
const response = await adminApiClient.get(API_ENDPOINTS.STOCKS.LIST);

// 获取概念列表
const response = await adminApiClient.get(API_ENDPOINTS.CONCEPTS.LIST);
```

### 动态端点（需要参数）
```typescript
// 获取特定股票详情
const stockCode = 'AAPL';
const response = await adminApiClient.get(
  API_ENDPOINTS.STOCKS.DETAIL(stockCode)
);

// 获取通用导入记录
const fileType = 'ttv';
const response = await adminApiClient.get(
  API_ENDPOINTS.UNIVERSAL_IMPORT.RECORDS(fileType)
);
```

### 带查询参数的请求
```typescript
// 注意: baseURL 配置处理 /api/v1 前缀
// 端点处理路由路径
// 查询参数单独通过 params 传递
const response = await adminApiClient.get(
  API_ENDPOINTS.UNIVERSAL_IMPORT.RECORDS(fileType),
  {
    params: {
      limit: 50,
      offset: 0,
    }
  }
);
```

### POST 请求
```typescript
const response = await adminApiClient.post(
  API_ENDPOINTS.STOCKS.CREATE,
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
  }
);
```

## 端点列表

### 认证 (AUTH)
- `LOGIN` - `/auth/login`
- `LOGOUT` - `/auth/logout`
- `ME` - `/auth/me`
- `REGISTER` - `/auth/register`

### 管理员认证 (ADMIN_AUTH)
- `LOGIN` - `/admin/auth/login`
- `LOGOUT` - `/admin/auth/logout`
- `ME` - `/admin/auth/me`
- `REFRESH` - `/admin/auth/refresh`

### 股票 (STOCKS)
- `LIST` - `/stocks`
- `COUNT` - `/stocks/count`
- `SIMPLE` - `/stocks/simple`
- `DETAIL(stockCode)` - `/stocks/{stockCode}`
- `DELETE(stockId)` - `/stocks/{stockId}`
- `BATCH_DELETE` - `/stocks/batch`

### 数据导入 (DATA_IMPORT)
- `STATUS(date)` - `/data/import-status/{date}`
- `IMPORT_CSV` - `/data/import-csv`
- `IMPORT_TXT` - `/data/import-txt`

### 通用导入 (UNIVERSAL_IMPORT)
- `SUPPORTED_TYPES` - `/universal-import/supported-types`
- `RECORDS(fileType)` - `/universal-import/{fileType}/records`
- `STATISTICS(fileType)` - `/universal-import/{fileType}/statistics`
- `IMPORT` - `/universal-import/import`

## 添加新端点

当添加新的 API 端点时，请：

1. **在 `endpoints.ts` 中定义**
```typescript
CATEGORY: {
  ENDPOINT_NAME: '/path/to/endpoint',
  DYNAMIC_ENDPOINT: (param: string) => `/path/${param}/endpoint`,
}
```

2. **在组件中使用**
```typescript
import { API_ENDPOINTS } from '@/api/endpoints';

const response = await adminApiClient.get(
  API_ENDPOINTS.CATEGORY.ENDPOINT_NAME
);
```

3. **禁止硬编码路径**
```typescript
// ❌ 错误
await adminApiClient.get('/new/path');

// ✅ 正确
await adminApiClient.get(API_ENDPOINTS.CATEGORY.ENDPOINT_NAME);
```

## 配置架构

```
Frontend (8006)
  ↓ 使用 adminApiClient
  ↓ baseURL: /api/v1 (来自 auth-config.ts)
  ↓ 端点: /universal-import/records (来自 endpoints.ts)
  ↓ 完整URL: /api/v1/universal-import/records
  ↓ Vite代理拦截 /api
  ↓ 转发到 Backend (3007)
  ↓ /api/v1/universal-import/records
Backend 接收处理 ✓
```

## 调试

如果遇到 404 错误：

1. **检查 baseURL**
   ```typescript
   console.log(adminApiClient.defaults.baseURL); // 应该是 /api/v1
   ```

2. **检查端点**
   ```typescript
   console.log(API_ENDPOINTS.UNIVERSAL_IMPORT.RECORDS('ttv'));
   // 应该输出: /universal-import/ttv/records
   // 完整URL应该是: /api/v1/universal-import/ttv/records
   ```

3. **检查最终URL**
   ```typescript
   // 在浏览器 Network 标签中查看
   // 应该看到: /api/v1/universal-import/...
   // 而不是: /api/v1/api/v1/universal-import/...
   ```

## 最佳实践

1. ✅ 所有 API 调用都通过 `adminApiClient`
2. ✅ 使用 `API_ENDPOINTS` 定义所有端点
3. ✅ 在 `endpoints.ts` 中集中管理
4. ✅ 为新端点添加相应的常量定义
5. ❌ 禁止在组件中硬编码 `/api/v1/`
6. ❌ 禁止直接使用 `fetch()` 或其他 HTTP 客户端
