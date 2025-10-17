# Plan 1 架构迁移指南 (v2.7.3)

## 📋 概述

系统已升级到 **Plan 1 完整分离架构**，主要改变包括：

### 数据架构变化

**旧架构 (v2.6.0)**
```
CSV/TXT文件
    ↓
stock_concept_raw_data (单表存储，混合原始和处理后的数据)
```

**新架构 Plan 1 (v2.7.3)**
```
CSV/TXT文件
    ↓
┌─────────────────────────────────┐
│ import_batches                  │ ← 导入批次管理
│ (记录每次导入的元信息)           │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ raw_import_data                 │ ← 原始导入数据
│ (100% 保存原始数据)             │
│ - 支持 CSV 格式                 │
│ - 支持 TXT 格式                 │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ raw_data_mapping                │ ← 原始数据映射
│ (追踪数据处理过程)              │
└─────────────────────────────────┘
    ↓ (数据处理)
┌────────────────────────────────────────┐
│ 业务数据表                            │
│ - stocks                              │
│ - daily_stock_data                    │
│ - stock_concepts                      │
│ - 其他分析表...                       │
└────────────────────────────────────────┘

+ 双写备份
    ↓
stock_concept_raw_data (CSV 备份表)
```

---

## 🔄 升级步骤

### 新安装系统

直接运行部署脚本，Plan 1 表会自动创建：

```bash
cd /path/to/stock-analysis-system
./scripts/deployment/deploy.sh
```

### 现有系统升级

#### 方法 1: 自动迁移 (推荐)

```bash
# 1. 运行迁移脚本 (自动备份 + 创建新表)
./scripts/database/migrate_to_plan1.sh

# 2. 运行部署脚本更新配置
./scripts/deployment/deploy.sh --migrate

# 3. 重启服务
./stop.sh && ./start.sh

# 4. 验证
./status.sh
```

#### 方法 2: 手动迁移 (高级)

```bash
# 1. 备份数据库
mysqldump -u root -p stock_analysis_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 创建新表
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_tables.sql

# 3. 创建 CSV 备份表
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_table.sql

# 4. 重启系统
./deploy.sh --migrate
./stop.sh && ./start.sh
```

---

## 📊 新增表详解

### 1. import_batches - 导入批次管理

记录每次导入的元信息。

**表结构**：
```sql
CREATE TABLE import_batches (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_date DATE,                    -- 导入日期
    import_type VARCHAR(10),             -- csv/txt
    file_name VARCHAR(255),              -- 源文件名
    record_count INT,                    -- 该批次的原始记录数
    status VARCHAR(20),                  -- success/partial/failed
    remark TEXT,                         -- 备注说明
    created_at TIMESTAMP                 -- 创建时间
);
```

**示例数据**：
```
id | import_date | import_type | file_name           | record_count | status | created_at
1  | 2025-10-17  | csv         | stock_20251017.csv  | 150          | success| 2025-10-17 14:30:00
2  | 2025-10-17  | txt         | heat_20251017.txt   | 120          | success| 2025-10-17 14:35:00
```

---

### 2. raw_import_data - 原始导入数据

100% 保存原始导入数据，每行 CSV/TXT 都对应一条记录。

**表结构**：
```sql
CREATE TABLE raw_import_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id INT,                 -- 关联到 import_batches
    row_number INT,                      -- 原始行号
    trade_date DATE,                     -- 交易日期

    -- 股票代码 (三列)
    stock_code_raw VARCHAR(20),          -- 原始代码 (SH600036)
    stock_code_normalized VARCHAR(10),   -- 规范化代码 (600036)
    stock_code_prefix VARCHAR(10),       -- 前缀 (SH/SZ/BJ/HK)

    -- 基本信息
    stock_name VARCHAR(100),
    industry VARCHAR(100),

    -- 交易数据
    price DECIMAL(10, 2),
    turnover_rate DECIMAL(5, 2),
    net_inflow DECIMAL(15, 2),
    pages_count INT,
    total_reads INT,

    -- CSV 专有
    concept VARCHAR(100),                -- 仅 CSV

    -- TXT 专有
    heat_value DECIMAL(15, 2),           -- 仅 TXT

    -- 来源信息
    source_type VARCHAR(10),             -- csv/txt
    source_file VARCHAR(255),            -- 源文件名
    import_created_at TIMESTAMP
);
```

**CSV 示例**：
```
id  | import_batch_id | row_number | trade_date | stock_code_raw | stock_code_normalized | concept | source_type
1   | 1               | 2          | 2025-10-17 | SH600036       | 600036                | 银行    | csv
2   | 1               | 3          | 2025-10-17 | SZ000001       | 000001                | 银行    | csv
```

**TXT 示例**：
```
id  | import_batch_id | row_number | trade_date | stock_code_raw | stock_code_normalized | heat_value | source_type
101 | 2               | 1          | 2025-10-17 | SZ000001       | 000001                | 1250.50    | txt
102 | 2               | 2          | 2025-10-17 | SH600036       | 600036                | 980.30     | txt
```

---

### 3. raw_data_mapping - 原始数据映射

追踪原始数据到业务数据的转换过程。

**表结构**：
```sql
CREATE TABLE raw_data_mapping (
    id INT PRIMARY KEY AUTO_INCREMENT,
    raw_import_data_id BIGINT,           -- 关联到 raw_import_data

    -- 业务数据 ID
    stock_id INT,                        -- 对应的 Stock.id
    concept_id INT,                      -- 对应的 Concept.id
    daily_stock_data_id INT,             -- 对应的 DailyStockData.id
    stock_concept_id INT,                -- 对应的 StockConcept.id

    -- 处理状态
    process_status VARCHAR(20),          -- pending/success/error
    error_message TEXT,

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**工作流程**：
```
raw_import_data (id=1)
    ↓ (处理)
stock_concept_raw_data (id=100)  ← CSV 备份

raw_data_mapping (raw_import_data_id=1)
  ├─ stock_id: 50              (Stock 表 id)
  ├─ daily_stock_data_id: 150  (DailyStockData 表 id)
  ├─ concept_id: 10            (Concept 表 id)
  ├─ stock_concept_id: 300     (StockConcept 表 id)
  └─ process_status: success
```

---

## 📝 导入逻辑变化

### CSV 导入

**之前**：
```
CSV 行
  ↓
stocks/concepts/stock_concepts/daily_stock_data
  ↓
stock_concept_raw_data (备份)
```

**现在** (Plan 1)：
```
CSV 行
  ↓
import_batches 创建批次
  ↓
raw_import_data 保存原始数据 ← 核心：100% 保存
  ↓
stocks/concepts/stock_concepts/daily_stock_data 处理业务数据
  ↓
raw_data_mapping 记录映射关系 ← 核心：追踪处理过程
  ↓
stock_concept_raw_data 双写备份
```

### TXT 导入

**之前**：
```
TXT 行
  ↓
daily_stock_data
```

**现在** (Plan 1)：
```
TXT 行
  ↓
import_batches 创建批次
  ↓
raw_import_data 保存原始数据 ← 核心：支持 TXT
  ↓
daily_stock_data 处理热度数据
  ↓
raw_data_mapping 记录映射关系
```

---

## 🚀 部署脚本更新

### deploy.sh 变更

**旧**：
```bash
mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_table.sql
```

**新**：
```bash
# Plan 1 表
mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_tables.sql

# CSV 备份表
mysql -u root -pPp123456 stock_analysis_dev < ../scripts/database/create_raw_data_table.sql
```

### 表验证更新

新增检查项：
```python
'import_batches',        # Plan 1: 导入批次管理
'raw_import_data',       # Plan 1: 原始导入数据
'raw_data_mapping'       # Plan 1: 原始数据到业务数据的映射
```

---

## ✅ 验证迁移成功

```bash
# 1. 检查表是否存在
mysql -u root -p stock_analysis_dev -e "
SHOW TABLES LIKE 'import_batches';
SHOW TABLES LIKE 'raw_import_data';
SHOW TABLES LIKE 'raw_data_mapping';
"

# 2. 检查表结构
mysql -u root -p stock_analysis_dev -e "DESCRIBE import_batches;"
mysql -u root -p stock_analysis_dev -e "DESCRIBE raw_import_data;"
mysql -u root -p stock_analysis_dev -e "DESCRIBE raw_data_mapping;"

# 3. 运行系统状态检查
./status.sh

# 4. 导入测试数据
# 上传 CSV 或 TXT 文件进行测试
```

---

## 🔙 回滚方案

如需回滚到旧架构：

```bash
# 1. 使用备份恢复
mysql -u root -p < backup_20251017_143000.sql

# 2. 清理新表
mysql -u root -p stock_analysis_dev -e "
DROP TABLE IF EXISTS raw_data_mapping;
DROP TABLE IF EXISTS raw_import_data;
DROP TABLE IF EXISTS import_batches;
"

# 3. 重启系统
./stop.sh && ./start.sh
```

---

## 📚 相关文档

- [数据导入逻辑详解](./DATA_IMPORT_LOGIC.md)
- [原始数据查询指南](./RAW_DATA_QUERY.md)
- [性能优化指南](./PERFORMANCE_GUIDE.md)

---

## 🆘 常见问题

**Q1: 迁移需要多久？**
A: 通常 1-2 分钟，取决于现有数据量。

**Q2: 迁移会丢失现有数据吗？**
A: 不会。新表只是添加，不会删除旧数据。stock_concept_raw_data 表仍然保留。

**Q3: 可以跳过迁移吗？**
A: 不建议。Plan 1 架构是必需的，以支持新的导入功能。

**Q4: 迁移后是否需要重新导入数据？**
A: 不需要。旧数据继续有效，新导入的数据会使用 Plan 1 架构保存。

**Q5: 性能会改变吗？**
A: 查询性能不会下降，新的原始数据表可能增加存储空间，但查询速度更快。

---

## 📞 技术支持

如遇到任何问题，请：
1. 查看部署日志: `tail -f logs/backend.log`
2. 检查数据库连接: `mysqladmin ping`
3. 运行状态检查: `./status.sh`
4. 查看本文档的 Q&A 部分

---

**版本**: v2.7.3
**更新日期**: 2025-10-17
**维护者**: 系统开发团队
