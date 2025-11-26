# 时间序列数据导入 API 端点文档

## 📋 概述

本文档描述了新添加的三个 API 端点，用于支持时间序列数据（EEE 热度数据和 TTV 交易量数据）的导入和计算。

**实现位置**: `app/api/api_v1/endpoints/data_import.py`

---

## 🔗 API 端点列表

### 1. EEE 热度数据导入

#### 端点信息
```
POST /api/v1/import-eee
```

#### 功能描述
导入 EEE 热度数据文件，自动规范化股票代码，并保存到 `StockDailyMetrics` 表。

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | File | ✅ | TXT 格式的热度数据文件 |

#### 文件格式
```
股票代码    日期        热度值
SH600000   2025-04-16  1234.56
SZ000001   2025-04-16  5678.90
```

#### 请求示例

**使用 curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/import-eee" \
  -F "file=@eee_data.txt"
```

**使用 Python requests:**
```python
import requests

with open('eee_data.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/import-eee',
        files=files
    )
    print(response.json())
```

**使用 JavaScript fetch:**
```javascript
const formData = new FormData();
formData.append('file', document.getElementById('fileInput').files[0]);

fetch('http://localhost:8000/api/v1/import-eee', {
    method: 'POST',
    body: formData
})
.then(res => res.json())
.then(data => console.log(data))
```

#### 响应示例

**成功 (200):**
```json
{
  "success": true,
  "message": "成功导入 1500 条记录",
  "filename": "eee_data.txt",
  "batch_id": 42,
  "trade_date": "2025-04-16",
  "stats": {
    "imported": 1500,
    "skipped": 10,
    "errors": 5
  },
  "parse_errors": []
}
```

**失败 (400):**
```json
{
  "detail": "文件必须是 TXT 格式"
}
```

#### 错误处理

| 状态码 | 错误信息 | 原因 |
|--------|--------|------|
| 400 | 文件名不能为空 | 未提供文件 |
| 400 | EEE 文件必须是 TXT 格式 | 文件格式不正确 |
| 400 | 文件大小不能超过50MB | 文件过大 |
| 400 | 文件内容为空 | 文件为空 |
| 500 | EEE 导入失败: ... | 处理过程出错 |

---

### 2. TTV 交易量数据导入

#### 端点信息
```
POST /api/v1/import-ttv
```

#### 功能描述
导入 TTV 交易量数据文件，自动规范化股票代码，并保存到 `StockDailyMetrics` 表。

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | File | ✅ | TXT 格式的交易量数据文件 |

#### 文件格式
```
股票代码    日期        交易量
SH600000   2025-04-16  1000000
SZ000001   2025-04-16  2000000
```

#### 请求示例

**使用 curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/import-ttv" \
  -F "file=@ttv_data.txt"
```

**使用 Python requests:**
```python
import requests

with open('ttv_data.txt', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/import-ttv',
        files=files
    )
    print(response.json())
```

#### 响应示例

**成功 (200):**
```json
{
  "success": true,
  "message": "成功导入 2000 条记录",
  "filename": "ttv_data.txt",
  "batch_id": 43,
  "trade_date": "2025-04-16",
  "stats": {
    "imported": 2000,
    "skipped": 20,
    "errors": 3
  },
  "parse_errors": []
}
```

#### 错误处理

同 EEE 端点

---

### 3. 指标计算

#### 端点信息
```
POST /api/v1/calculate-metrics
```

#### 功能描述
计算指定日期的所有时间序列指标，包括：
- 股票排名（按概念分组）
- 概念级汇总
- 创新高检测

#### 请求参数

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| trade_date | string | ✅ | 目标计算日期 (YYYY-MM-DD) |
| metric_type | string | ❌ | 指标类型过滤 (eee_heat 或 ttv_trading_volume) |

#### 请求示例

**使用 curl:**
```bash
# 计算所有指标
curl -X POST "http://localhost:8000/api/v1/calculate-metrics?trade_date=2025-04-16"

# 只计算 EEE 热度
curl -X POST "http://localhost:8000/api/v1/calculate-metrics?trade_date=2025-04-16&metric_type=eee_heat"

# 只计算 TTV 交易量
curl -X POST "http://localhost:8000/api/v1/calculate-metrics?trade_date=2025-04-16&metric_type=ttv_trading_volume"
```

**使用 Python requests:**
```python
import requests

# 计算所有指标
response = requests.post(
    'http://localhost:8000/api/v1/calculate-metrics',
    params={'trade_date': '2025-04-16'}
)
print(response.json())

# 指定指标类型
response = requests.post(
    'http://localhost:8000/api/v1/calculate-metrics',
    params={
        'trade_date': '2025-04-16',
        'metric_type': 'eee_heat'
    }
)
print(response.json())
```

#### 响应示例

**成功 (200):**
```json
{
  "success": true,
  "message": "成功计算 3500/3515 个指标项",
  "target_date": "2025-04-16",
  "task_id": 101,
  "stats": {
    "total_items": 3515,
    "success_items": 3500,
    "failed_items": 15,
    "details": {
      "stock_rankings": {
        "total": 3500,
        "success": 3500
      },
      "concept_summaries": {
        "total": 100,
        "success": 100
      },
      "new_highs": {
        "total": 25,
        "success": 25
      }
    }
  },
  "metric_type": null
}
```

**失败 (400):**
```json
{
  "detail": "日期格式错误，应为 YYYY-MM-DD"
}
```

#### 错误处理

| 状态码 | 错误信息 | 原因 |
|--------|--------|------|
| 400 | 日期格式错误 | 日期不符合 YYYY-MM-DD 格式 |
| 500 | 计算失败: ... | 计算过程出错 |

---

## 📊 数据流示例

### 完整的导入和计算流程

```bash
#!/bin/bash

# 1. 导入 EEE 数据
echo "📤 导入 EEE 热度数据..."
curl -X POST "http://localhost:8000/api/v1/import-eee" \
  -F "file=@eee_2025-04-16.txt"

# 2. 导入 TTV 数据
echo "📤 导入 TTV 交易量数据..."
curl -X POST "http://localhost:8000/api/v1/import-ttv" \
  -F "file=@ttv_2025-04-16.txt"

# 3. 计算指标
echo "📊 计算指标..."
curl -X POST "http://localhost:8000/api/v1/calculate-metrics?trade_date=2025-04-16"

# 4. 查看结果
echo "✅ 完成！"
```

---

## 🔧 实现细节

### 导入流程

```
1. 文件验证 (格式、大小)
   ↓
2. 读取文件内容
   ↓
3. TimeSeriesImportService.import_timeseries_data()
   ├─ EeeImportHandler.parse_file()     # 解析文件
   ├─ 验证记录
   ├─ 规范化股票代码
   ├─ save_raw_data()                   # 保存原始数据到 RawImportData
   └─ save_normalized_data()            # 保存到 StockDailyMetrics
   ↓
4. 返回导入统计 (JSON 响应)
```

### 计算流程

```
1. 日期验证
   ↓
2. MetricsCalculationService.calculate_daily_metrics()
   ├─ _calculate_stock_rankings()       # 按概念分组排名
   ├─ _calculate_concept_summaries()    # 计算概念汇总
   └─ _detect_new_highs()               # 检测创新高
   ↓
3. 数据库更新
   ├─ StockDailyMetrics (排名、占比)
   ├─ ConceptMetricsSummary (汇总数据)
   └─ ConceptHighRecord (创新高记录)
   ↓
4. 返回计算结果 (JSON 响应)
```

---

## 💾 数据库表关系

### 导入数据保存

```
EEE.txt / TTV.txt
   ↓
RawImportData (原始数据保留用于审计)
   ↓
StockDailyMetrics (统一的指标存储)
   ├─ metric_type: 'eee_heat' 或 'ttv_trading_volume'
   ├─ metric_value: 具体数值
   └─ data_source: 'eee' 或 'ttv'
```

### 计算数据保存

```
StockDailyMetrics (原始数据)
   ↓
计算过程
   ├─ 按概念分组
   ├─ 计算排名
   └─ 计算占比
   ↓
更新结果
├─ StockDailyMetrics.ranking_in_concept (排名)
├─ StockDailyMetrics.percentage_in_concept (占比)
├─ ConceptMetricsSummary (概念汇总)
└─ ConceptHighRecord (创新高记录)
```

---

## 🧪 测试脚本

### Python 测试脚本

```python
#!/usr/bin/env python3

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000/api/v1"

# 测试 EEE 导入
print("测试 EEE 导入...")
with open('eee_data.txt', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/import-eee",
        files={'file': f}
    )
    eee_result = response.json()
    print(json.dumps(eee_result, indent=2, ensure_ascii=False))

# 测试 TTV 导入
print("\n测试 TTV 导入...")
with open('ttv_data.txt', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/import-ttv",
        files={'file': f}
    )
    ttv_result = response.json()
    print(json.dumps(ttv_result, indent=2, ensure_ascii=False))

# 测试指标计算
print("\n测试指标计算...")
response = requests.post(
    f"{BASE_URL}/calculate-metrics",
    params={'trade_date': str(date.today())}
)
calc_result = response.json()
print(json.dumps(calc_result, indent=2, ensure_ascii=False))

print("\n✅ 测试完成！")
```

---

## 📝 注意事项

1. **文件格式**
   - 必须是 TXT 格式
   - 使用制表符 (\t) 分隔列
   - 支持 UTF-8 编码

2. **股票代码**
   - 支持前缀: SH, SZ, BJ, HK
   - 自动规范化为纯数字代码 (6位)
   - 例如: SH600000 → 600000

3. **日期格式**
   - 必须符合 YYYY-MM-DD 格式
   - 例如: 2025-04-16

4. **文件大小限制**
   - EEE/TTV: 最大 50MB
   - 避免上传超大文件导致内存溢出

5. **数据库要求**
   - 确保 `StockDailyMetrics` 表已创建
   - 确保 `stocks` 表包含所需的股票信息
   - 股票代码必须存在，否则记录会被跳过

---

## 🔍 常见问题

### Q: 导入后没有看到数据？
A: 检查以下几点：
1. 文件格式是否正确 (TXT, 制表符分隔)
2. 股票代码是否存在于 stocks 表中
3. 日期格式是否正确

### Q: 计算失败显示什么错误？
A: 检查日志输出，常见原因：
1. 日期不存在数据
2. 数据库连接失败
3. StockDailyMetrics 表不存在

### Q: 导入和计算需要多长时间？
A: 取决于数据量：
- 导入: 通常 10-100 条/秒
- 计算: 取决于股票和概念数量，通常 1-10 秒

---

## 📞 支持

如有问题，请检查：
1. 后端日志输出
2. 数据库表结构
3. 文件格式和编码
4. API 请求参数

