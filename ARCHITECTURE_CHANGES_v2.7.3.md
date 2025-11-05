# 架构变更总结 - v2.7.3 (Plan 1 完整分离)

## 🎯 核心改变

### 数据架构

**三表设计 (Plan 1 完整分离架构)**

```
┌────────────────────────────────┐
│ 导入批次管理                   │
│ import_batches                │
│ - 记录每次导入的元信息         │
└────────────────────────────────┘
           ↓
┌────────────────────────────────┐
│ 原始导入数据                   │
│ raw_import_data               │
│ - 100% 保存原始数据           │
│ - 支持 CSV 和 TXT             │
│ - 包含原始代码和规范化代码    │
└────────────────────────────────┘
           ↓
┌────────────────────────────────┐
│ 原始数据映射                   │
│ raw_data_mapping              │
│ - 追踪处理过程                │
│ - 支持审计追踪                │
└────────────────────────────────┘
```

### 导入逻辑

**CSV 导入流程**

```
CSV 文件 (150 行)
    ↓
1. ImportBatch 创建
2. raw_import_data 批量保存 (150 条)
3. 业务数据处理 (stocks/concepts/etc.)
4. raw_data_mapping 创建映射
5. stock_concept_raw_data 双写备份
```

**TXT 导入流程**

```
TXT 文件 (120 行)
    ↓
1. ImportBatch 创建
2. raw_import_data 批量保存 (120 条)
3. DailyStockData 处理热度数据
4. raw_data_mapping 创建映射
```

---

## 📝 改动清单

### 1. 数据模型 (app/models/stock.py)

**新增**：
- ✅ `ImportBatch` - 导入批次管理表
- ✅ `RawImportData` - 原始导入数据表
- ✅ `RawDataMapping` - 原始数据映射表

**改动细节**：
```python
class ImportBatch:
    import_date: date
    import_type: str          # csv/txt
    file_name: str
    record_count: int         # 原始记录数
    status: str              # success/partial/failed

class RawImportData:
    import_batch_id: int     # 关联批次
    row_number: int          # 原始行号
    stock_code_raw: str      # 原始代码 (SH600036)
    stock_code_normalized: str # 规范化代码 (600036)
    stock_code_prefix: str   # 前缀 (SH/SZ/etc.)
    concept: str             # CSV only
    heat_value: float        # TXT only
    source_type: str         # csv/txt

class RawDataMapping:
    raw_import_data_id: int  # 原始数据 ID
    stock_id: int
    concept_id: int
    daily_stock_data_id: int
    stock_concept_id: int
    process_status: str      # pending/success/error
```

---

### 2. 数据导入逻辑 (app/services/data_import.py)

**CSV 导入改动**：

```python
# 第 180-189 行: 创建 ImportBatch
import_batch = ImportBatch(
    import_date=import_date,
    import_type='csv',
    file_name=filename,
    record_count=len(df),
    status='pending'
)
self.db.add(import_batch)
self.db.flush()

# 第 193 行: 初始化原始数据收集列表
raw_import_records = []

# 第 302-320 行: 为每行 CSV 创建 RawImportData
raw_import_record = RawImportData(
    import_batch_id=import_batch.id,
    row_number=index + 2,
    stock_code_raw=stock_code_raw,
    stock_code_normalized=stock_code,
    stock_code_prefix=stock_code_prefix,
    concept=concept_name,
    source_type='csv',
    source_file=filename
)
raw_import_records.append(raw_import_record)

# 第 398-402 行: 批量保存原始数据
if raw_import_records:
    self.db.bulk_save_objects(raw_import_records)
    stats['raw_import_records'] = len(raw_import_records)

# 第 404-406 行: 更新批次状态
import_batch.record_count = len(raw_import_records)
import_batch.status = 'success' if not errors else 'partial'
```

**TXT 导入改动**：

```python
# 第 548-558 行: 创建 ImportBatch (TXT)
import_batch = ImportBatch(
    import_date=target_date,
    import_type='txt',
    file_name=filename,
    record_count=len(valid_lines),
    status='pending'
)
self.db.add(import_batch)
self.db.flush()

# 第 561 行: 初始化原始数据收集列表
raw_import_records = []

# 第 685-705 行: 为每行 TXT 创建 RawImportData
raw_import_record = RawImportData(
    import_batch_id=import_batch.id,
    row_number=line_num,
    trade_date=target_date,
    stock_code_raw=stock_code_with_prefix,
    stock_code_normalized=stock_code,
    stock_code_prefix=stock_code_prefix,
    heat_value=heat_value,
    source_type='txt',
    source_file=filename
)
raw_import_records.append(raw_import_record)

# 第 716-720 行: 批量保存原始数据
if raw_import_records:
    self.db.bulk_save_objects(raw_import_records)
    stats['raw_import_records'] = len(raw_import_records)

# 第 722-724 行: 更新批次状态
import_batch.record_count = len(raw_import_records)
import_batch.status = 'success' if not errors else 'partial'
```

---

### 3. 数据库脚本

**新增**：

✅ `/scripts/database/create_raw_data_tables.sql`
- 包含 `import_batches` 表定义
- 包含 `raw_import_data` 表定义
- 包含 `raw_data_mapping` 表定义

✅ `/scripts/database/migrate_to_plan1.sh`
- 自动迁移脚本
- 包含备份功能
- 包含验证逻辑

**修改**：

📝 `/scripts/database/create_raw_data_table.sql`
- 保持不变（用于 CSV 备份表）

---

### 4. 部署脚本

**修改 deploy.sh**：

```bash
# 第 130-136 行: 更新表创建逻辑
echo "💾 创建原始数据表 (Plan 1)..."
mysql < ../scripts/database/create_raw_data_tables.sql

echo "💾 创建CSV备份表..."
mysql < ../scripts/database/create_raw_data_table.sql

# 第 262-272 行: 新增表验证
tables_to_check = [
    ...
    'import_batches',        # Plan 1
    'raw_import_data',       # Plan 1
    'raw_data_mapping'       # Plan 1
]

# 第 419-450 行: 更新完成提示
echo "🎉 完整部署成功！(包含Plan 1完整分离架构 + 数据库优化 v2.7.3)"
# 新增架构升级信息
```

**修改 init_database.sh**：

```bash
# 第 105-109 行: 更新表创建顺序
execute_sql_file "create_raw_data_tables.sql" "创建Plan 1原始数据表"
execute_sql_file "create_raw_data_table.sql" "创建CSV备份表"

# 第 129-144 行: 更新完成信息
# 按分类显示所有表
```

---

### 5. 文档

**新增**：

📄 `PLAN1_MIGRATION.md` - 完整迁移指南
📄 `ARCHITECTURE_CHANGES_v2.7.3.md` - 此文件

---

## 🔄 迁移路径

### 新安装

```bash
./deploy.sh
# Plan 1 表自动创建
```

### 现有系统

```bash
# 方法 1: 自动迁移
./scripts/database/migrate_to_plan1.sh
./deploy.sh --migrate
./stop.sh && ./start.sh

# 方法 2: 手动迁移
# 见 PLAN1_MIGRATION.md
```

---

## 📊 性能影响

| 指标 | 变化 |
|------|------|
| 存储空间 | ↑ 增加 (新增 raw_import_data) |
| CSV 导入速度 | ≈ 相同 (批量操作) |
| TXT 导入速度 | ≈ 相同 (批量操作) |
| 查询性能 | ↑ 提升 (Plan 1 优化) |
| 数据完整性 | ↑ 提升 (100% 保存) |

---

## ✅ 验证清单

在生产环境部署前，请确认：

- [ ] SQL 脚本正确 (create_raw_data_tables.sql 包含所有三个表)
- [ ] deploy.sh 引用了正确的 SQL 文件
- [ ] data_import.py 正确保存 raw_import_data
- [ ] 数据库验证包含了新表检查
- [ ] 迁移脚本可以正确执行
- [ ] 部署后所有表都已创建
- [ ] 新导入的数据在 raw_import_data 中存在
- [ ] raw_data_mapping 中有正确的映射记录

---

## 🔍 检查命令

```bash
# 1. 检查表结构
mysql -u root -p stock_analysis_dev << EOF
DESCRIBE import_batches;
DESCRIBE raw_import_data;
DESCRIBE raw_data_mapping;
EOF

# 2. 检查数据量
mysql -u root -p stock_analysis_dev << EOF
SELECT 'import_batches' as table_name, COUNT(*) as count FROM import_batches
UNION ALL
SELECT 'raw_import_data', COUNT(*) FROM raw_import_data
UNION ALL
SELECT 'raw_data_mapping', COUNT(*) FROM raw_data_mapping;
EOF

# 3. 检查最新导入
mysql -u root -p stock_analysis_dev << EOF
SELECT * FROM import_batches ORDER BY created_at DESC LIMIT 1;
SELECT * FROM raw_import_data ORDER BY import_created_at DESC LIMIT 5;
EOF

# 4. 系统检查
./status.sh
```

---

## 📞 故障排除

**问题**: 部署失败，提示表不存在
**解决**: 确认 SQL 脚本路径正确，手动执行:
```bash
mysql -u root -p stock_analysis_dev < scripts/database/create_raw_data_tables.sql
```

**问题**: 导入后 raw_import_data 为空
**解决**: 检查 data_import.py 中的 raw_import_records 是否正确添加

**问题**: raw_data_mapping 的 process_status 都是 pending
**解决**: 这是预期行为，可手动更新或创建后台任务处理

---

## 📈 后续优化方向

1. **自动映射处理**
   - 创建后台任务自动处理 raw_data_mapping
   - 自动创建业务数据关联

2. **数据质量检查**
   - 添加数据验证规则
   - 自动检测异常数据

3. **审计日志**
   - 记录每次数据变更
   - 完整的审计追踪

4. **API 优化**
   - 新增原始数据查询接口
   - 支持映射关系查询

---

**版本**: v2.7.3
**发布日期**: 2025-10-17
**状态**: ✅ 已完成
