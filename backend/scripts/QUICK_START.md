# 批量导入快速开始指南

## 一句话总结

本地 EEE.txt/TTV.txt → 原始数据导入 → 自动重新计算 → 汇总数据就绪

## 三种使用方式

### 方式 1：最简单（推荐首选）

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 运行快速导入脚本（会提示选择要导入的文件类型）
bash scripts/quick-import.sh
```

然后按照提示选择：
```
选择导入文件类型：
  1) EEE (热度数据)
  2) TTV (交易数据)
  3) 两个都导入
请选择 [1-3]: 1
```

### 方式 2：一行命令导入 EEE

```bash
python3 /Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py --type eee --file /Users/peakom/Downloads/EEE.txt
```

### 方式 3：一行命令导入 TTV

```bash
python3 /Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py --type ttv --file /Users/peakom/Downloads/TTV.txt
```

## 导入过程会做什么？

```
📝 Step 1: 解析文件
  ✓ 读取 EEE.txt/TTV.txt
  ✓ 按照交易日期分组
  ✓ 提取股票代码、日期、数值

💾 Step 2: 导入到数据库
  ✓ 创建导入批次 (import_batches)
  ✓ 存储原始数据 (raw_import_data)
  ✓ 建立数据映射 (raw_data_mapping)

🔄 Step 3: 本地重新计算（默认）
  ✓ 直接在 Python 中执行计算逻辑（无需 API 调用）
  ✓ 计算概念汇总
  ✓ 计算个股排名
  ✓ 计算创新高记录
  ✓ 速度快，无需启动后端服务
```

## 预期输出

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
✓ /Users/peakom/Downloads/EEE.txt 解析完成，包含 150 个交易日期，共 15000 条记录

Step 2: 导入原始数据到数据库...
  ✓ 2024-02-20 (eee): 插入 100 条记录
  ✓ 2024-02-21 (eee): 插入 98 条记录
  ✓ 2024-02-22 (eee): 插入 102 条记录
  ...
  总计插入 15000 条原始数据记录

Step 3: 触发后端重新计算...
  计算中... 2024-02-20 ✓ 完成 | 概念: 156, 排名: 5200, 创新高: 48
  计算中... 2024-02-21 ✓ 完成 | 概念: 154, 排名: 5100, 创新高: 45
  计算中... 2024-02-22 ✓ 完成 | 概念: 158, 排名: 5300, 创新高: 50
  ...

╔════════════════════════════════════════════════════════╗
║                    导入完成！                           ║
╚════════════════════════════════════════════════════════╝

统计:
  文件类型: EEE
  交易日期: 150 个
  总记录数: 15000
  重新计算成功: 150 个日期
  重新计算失败: 0 个日期
```

## 常见场景

### 场景 1：使用 API 进行计算（需要后端服务）

如果您需要通过 API 调用而不是本地执行计算：

```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --use-api
```

**注意**：此模式需要后端服务在 `http://localhost:3007` 运行。

### 场景 2：只导入数据，不立即计算

```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --skip-calc
```

然后稍后手动在 UI 界面点击"重新计算"按钮。

### 场景 3：导入大文件（分批处理）

```bash
# 1. 先分割文件
split -l 50000 /Users/peakom/Downloads/EEE.txt /tmp/eee_part_

# 2. 分别导入（跳过计算）
for file in /tmp/eee_part_*; do
  python3 scripts/batch_import_local_files.py \
    --type eee \
    --file $file \
    --skip-calc
done

# 3. 稍后统一计算（访问导入记录页面点击重新计算）
```

### 场景 4：导入到远程数据库

```bash
python3 scripts/batch_import_local_files.py \
  --type eee \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://user:password@remote-host:5432/stockdb \
  --api-url http://remote-host:3007
```

## 验证导入是否成功

### 方式 1：查看数据库

```bash
# 查看导入批次
psql -U postgres -d stockdb -c \
  "SELECT * FROM import_batches ORDER BY created_at DESC LIMIT 5;"

# 查看原始数据
psql -U postgres -d stockdb -c \
  "SELECT COUNT(*) FROM raw_import_data WHERE source_type='eee';"
```

### 方式 2：查看导入记录页面

访问管理后台 → 导入管理 → 可以看到所有导入的文件和计算结果

### 方式 3：查看汇总数据

访问概念分析页面 → 查看各个概念的数据是否已更新

## 关键概念

### 原始表 vs 汇总表

| 表名 | 用途 | 数据示例 |
|------|------|---------|
| `raw_import_data` | 存储导入的**原始数据** | 每条 CSV 行 |
| `import_batches` | 记录**导入批次** | 导入元信息 |
| `concept_daily_summary` | **概念汇总** | 每个概念的交易总量 |
| `stock_concept_ranking` | **个股排名** | 每个概念下的排名 |
| `daily_new_high_concept` | **创新高概念** | 新创新高的概念 |

### 重新计算做了什么

```
原始数据 (raw_import_data)
    ↓
  perform_calculations()
    ├─ 概念汇总: 聚合所有股票的交易数据
    ├─ 个股排名: 计算每个概念下的排名
    └─ 创新高: 检测新创新高的概念
    ↓
汇总表更新
```

## 故障排查

### 问题 1：数据库连接失败

**症状**：
```
错误: 无法连接到数据库 postgresql://postgres:Pp123456@localhost/stockdb
```

**解决**：
```bash
# 检查 PostgreSQL 是否运行
brew services list | grep postgres

# 手动启动
brew services start postgresql

# 测试连接
psql -U postgres -h localhost -d stockdb -c "SELECT 1"
```

### 问题 2：后端服务未响应

**症状**：
```
警告: 后端服务未响应，将跳过重新计算步骤
```

**解决**：
```bash
# 检查后端是否运行
curl http://localhost:3007/health

# 如果失败，需要启动后端
# 在另一个终端运行：
cd /Users/peakom/work/stock-analysis-system/backend
python3 -m uvicorn app.main:app --reload --port 3007
```

### 问题 3：文件格式问题

**症状**：
```
警告: 第N行解析失败
```

**检查文件格式**：
```bash
# 查看文件格式
head -3 /Users/peakom/Downloads/EEE.txt

# 应该是：股票代码 [Tab] 日期 [Tab] 数值
# 例如：
# SH110062	2024-02-20	33082.000000

# 检查是否为 Tab 分隔
file /Users/peakom/Downloads/EEE.txt  # 应该显示 ASCII text
od -c /Users/peakom/Downloads/EEE.txt | head -1  # 检查分隔符是否为 \t
```

### 问题 4：导入速度慢

如果文件超过 100,000 行，可能很慢。建议：

1. 使用 `--skip-calc` 先导入数据
2. 等待导入完成后，再手动触发重新计算
3. 或分批导入（见场景 2）

## 下一步

导入完成后：

1. **访问管理后台**
   - 查看导入记录
   - 验证数据是否正确

2. **查看汇总数据**
   - 概念分析页面
   - 个股排名
   - 创新高概念列表

3. **监控重新计算**
   - 每个日期的计算结果
   - 概念数、排名数、创新高数

## 文件位置速查

| 内容 | 路径 |
|------|------|
| 导入脚本 | `/Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py` |
| 快速脚本 | `/Users/peakom/work/stock-analysis-system/backend/scripts/quick-import.sh` |
| 详细文档 | `/Users/peakom/work/stock-analysis-system/backend/scripts/BATCH_IMPORT_README.md` |
| EEE 文件 | `/Users/peakom/Downloads/EEE.txt` |
| TTV 文件 | `/Users/peakom/Downloads/TTV.txt` |

## 一键导入命令

复制粘贴运行：

```bash
# 导入 EEE
python3 /Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py --type eee --file /Users/peakom/Downloads/EEE.txt

# 导入 TTV
python3 /Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py --type ttv --file /Users/peakom/Downloads/TTV.txt

# 两个都导入
bash /Users/peakom/work/stock-analysis-system/backend/scripts/quick-import.sh
```

## 需要帮助？

查看详细文档：
```bash
cat /Users/peakom/work/stock-analysis-system/backend/scripts/BATCH_IMPORT_README.md
```

或查看脚本帮助：
```bash
python3 /Users/peakom/work/stock-analysis-system/backend/scripts/batch_import_local_files.py --help
```

---

**祝你导入顺利！** 如有问题，检查日志并参考详细文档。
