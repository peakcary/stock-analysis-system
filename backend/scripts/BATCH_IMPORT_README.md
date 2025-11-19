# 本地文件批量导入脚本使用说明

## 概述

这个脚本用于将本地的 EEE.txt 和 TTV.txt 文件中的原始数据批量导入到数据库，然后自动触发后端的重新计算逻辑，生成汇总数据。

## 文件格式

### EEE.txt 格式
```
股票代码(原始)    交易日期        热度值
SH110062         2024-02-20      33082.000000
SH110062         2024-02-21      32293.000000
```

### TTV.txt 格式
```
股票代码(原始)    交易日期        数值
BJ920000         2024-07-30      0.000000
BJ920000         2024-07-31      0.000000
```

## 工作流程

```
本地TXT文件
    ↓
[Step 1] 解析文件，按日期分组
    ↓
[Step 2] 导入原始数据到数据库表 (raw_import_data)
    ├─ import_batches (导入批次)
    ├─ raw_import_data (原始数据)
    └─ raw_data_mapping (数据映射)
    ↓
[Step 3] 本地或 API 重新计算（默认本地计算）
    ├─ perform_calculations()
    ├─ 概念汇总
    ├─ 个股排名
    └─ 创新高记录
    ↓
业务表更新（concept_daily_summary, stock_concept_ranking 等）
```

## 使用方法

### 基础使用

#### 导入 EEE 文件（含重新计算）
```bash
cd /Users/peakom/work/stock-analysis-system/backend

python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt
```

#### 导入 TTV 文件（含重新计算）
```bash
python3 scripts/batch_import_local_files.py \
  --type ttv \
  --file /Users/peakom/Downloads/TTV.txt
```

### 高级选项

#### 跳过重新计算（仅导入数据）
```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --skip-calc
```

#### 指定数据库连接
```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://postgres:Pp123456@localhost/stockdb
```

#### 指定API地址
```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --api-url http://localhost:3007
```

### 命令参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--type` | 文件类型 (eee/ttv) | - | `eee` |
| `--file` | 文件路径 | - | `/Users/peakom/Downloads/EEE.txt` |
| `--db-url` | 数据库连接串 | `postgresql://postgres:Pp123456@localhost/stockdb` | - |
| `--api-url` | API基础URL | `http://localhost:3007` | `http://192.168.1.100:3007` |
| `--skip-calc` | 跳过重新计算步骤 | false | - |
| `--use-api` | 使用 API 进行重新计算（默认使用本地计算） | false | - |

## 输出示例

```
╔════════════════════════════════════════════════════════╗
║          本地文件批量导入脚本                           ║
╚════════════════════════════════════════════════════════╝

配置:
  文件类型: EEE
  文件路径: /Users/peakom/Downloads/EEE.txt
  数据库: stockdb
  API: http://localhost:3007

Step 1: 解析本地文件...
✓ /Users/peakom/Downloads/EEE.txt 解析完成，包含 100 个交易日期，共 10000 条记录

Step 2: 导入原始数据到数据库...
  ✓ 2024-02-20 (eee): 插入 100 条记录
  ✓ 2024-02-21 (eee): 插入 98 条记录
  ...
  总计插入 10000 条原始数据记录

Step 3: 触发后端重新计算...
  计算中... 2024-02-20 ✓ 完成 | 概念: 150, 排名: 5000, 创新高: 45
  计算中... 2024-02-21 ✓ 完成 | 概念: 148, 排名: 4950, 创新高: 42
  ...

╔════════════════════════════════════════════════════════╗
║                    导入完成！                           ║
╚════════════════════════════════════════════════════════╝

统计:
  文件类型: EEE
  交易日期: 100 个
  总记录数: 10000
  重新计算成功: 100 个日期
  重新计算失败: 0 个日期
```

## 关键特性

✅ **自动日期提取** - 从文件中自动提取所有交易日期

✅ **按日期分组** - 按照交易日期分组处理数据

✅ **数据标准化** - 自动处理股票代码前缀 (SH/SZ/BJ 等)

✅ **批量导入** - 支持大数据量的批量导入

✅ **自动重新计算** - 导入后自动触发后端的重新计算

✅ **错误处理** - 完整的错误处理和日志记录

✅ **跳过重复** - 自动检测并跳过已导入的日期

## 可能遇到的问题

### 问题 1: 数据库连接失败
```
错误: 无法连接到数据库
```

**解决方案**：
- 确保数据库运行中：`brew services list | grep postgres`
- 检查连接字符串是否正确
- 检查数据库用户权限

```bash
# 测试数据库连接
psql -U postgres -h localhost -d stockdb -c "SELECT 1"
```

### 问题 2: API 连接超时
```
错误: 重新计算超时
```

**解决方案**：
- 确保后端服务运行中：`curl http://localhost:3007/health`
- 如果数据量大，可能需要增加超时时间
- 可以先用 `--skip-calc` 跳过计算，稍后手动触发

```bash
# 检查后端是否运行
ps aux | grep uvicorn
```

### 问题 3: 日期格式不正确
```
错误: 第N行解析失败
```

**解决方案**：
- 确保日期格式为 `YYYY-MM-DD`
- 检查文件编码是否为 UTF-8
- 检查分隔符是否为 Tab 而不是空格

### 问题 4: 股票代码无法识别
```
警告: 第N行数据不完整
```

**解决方案**：
- 确保文件有三列：股票代码、日期、数值
- 检查是否有空行或注释行

## 数据库表说明

### import_batches（导入批次表）
```
id                   - 主键
import_date          - 导入日期
import_type          - 导入类型 (eee/ttv)
file_name            - 源文件名
record_count         - 记录数
status               - 导入状态 (success/partial/failed)
created_at           - 创建时间
```

### raw_import_data（原始导入数据表）
```
id                   - 主键
import_batch_id      - 导入批次ID
row_number           - 原始行号
trade_date           - 交易日期
stock_code_raw       - 原始股票代码 (SH600000)
stock_code_normalized - 规范化代码 (600000)
stock_code_prefix    - 代码前缀 (SH/SZ 等)
stock_name           - 股票名称
heat_value           - 热度值 (EEE 特有)
source_type          - 来源类型 (eee/ttv)
source_file          - 来源文件
import_created_at    - 导入时间
```

## 性能优化建议

### 大数据量导入

如果文件包含超过 100,000 条记录，建议分批处理：

```bash
# 先分割文件为多个小文件
split -l 50000 EEE.txt EEE_part_

# 分别导入
for file in EEE_part_*; do
  python3 scripts/batch_import_local_files.py \
    --type eee \
    --file $file \
    --skip-calc
done

# 最后统一重新计算
python3 scripts/batch_import_local_files.py \
  --type eee \
  --skip-calc  # 手动触发或调用 API
```

### 内存使用优化

脚本按日期分组，即使对大文件也能保持内存占用较低。

## 后续步骤

导入完成后，你可以：

1. **查看导入统计**：访问导入记录管理界面
2. **验证数据**：检查原始表中的数据是否正确
3. **触发重新计算**：在导入记录列表中点击"重新计算"按钮
4. **查看汇总结果**：在概念分析页面查看计算结果

## 常用命令速查表

```bash
# EEE 文件导入（完整流程）
python3 scripts/batch_import_local_files.py --type eee --file /Users/peakom/Downloads/EEE.txt

# TTV 文件导入（完整流程）
python3 scripts/batch_import_local_files.py --type ttv --file /Users/peakom/Downloads/TTV.txt

# 仅导入数据，跳过计算
python3 scripts/batch_import_local_files.py --type eee --file /Users/peakom/Downloads/EEE.txt --skip-calc

# 查看导入批次
psql -U postgres -d stockdb -c "SELECT * FROM import_batches ORDER BY created_at DESC LIMIT 10;"

# 查看原始数据
psql -U postgres -d stockdb -c "SELECT COUNT(*) FROM raw_import_data WHERE source_type='eee';"
```

## 支持

如有问题，请查看日志输出或检查以下日志文件：
- 后端日志：`/tmp/gunicorn-error.log`
- 应用日志：检查脚本的日志输出

## 许可证

内部脚本，仅供项目使用。
