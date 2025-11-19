# CSV本地文件导入使用指南

## 📋 脚本说明

`import_csv_local.py` 用于从本地CSV文件批量导入股票、概念和关联数据到数据库。

## ✨ 功能特性

### 1. 自动处理三个核心表
- **stocks** - 股票基础信息（创建/更新）
- **concepts** - 概念信息（去重插入）
- **stock_concepts** - 股票-概念关联（增量添加）

### 2. 智能数据处理
- ✅ 股票代码规范化（自动去除 SH/SZ/BJ/HK 前缀）
- ✅ 转债自动识别（1开头的6位数字）
- ✅ 概念增量关联（只增不减）
- ✅ 股票信息更新（名称、行业等）
- ✅ 支持中英文CSV格式

### 3. 数据覆盖策略
| 表名 | 新增 | 更新 | 删除（覆盖模式）| 说明 |
|------|------|------|----------------|------|
| concepts | ✅ | ❌ | ❌ | 去重插入，只增不改 |
| stock_concepts | ✅ | ❌ | ❌ | 累积模式，只增不减 |
| stocks | ✅ | ✅ | ❌ | 存在则更新基本信息 |
| daily_stock_data | ✅ | ✅ | ✅ | 完全覆盖模式 |

**重要**: 即使使用 `--overwrite` 参数，概念关联也不会被删除！

---

## 📝 CSV文件格式

### 格式1：英文列名（推荐）

```csv
stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow
SH600000,浦发银行,银行,金融,2024-10-16,10.52,1.2,5000000
SH600036,招商银行,银行+消费电子,金融,2024-10-16,32.15,0.8,-2000000
SZ000001,平安银行,银行+科技,金融,2024-10-16,12.34,1.5,3000000
```

### 格式2：中文列名

```csv
股票代码,股票名称,概念,行业,价格,换手,净流入,全部页数,热帖首页页阅读总数
SH600000,浦发银行,银行,金融,10.52,1.2,5000000,100,5000
SH600036,招商银行,银行+消费电子,金融,32.15,0.8,-2000000,150,8000
SZ000001,平安银行,银行+科技,金融,12.34,1.5,3000000,120,6000
```

### 必需字段
- ✅ `stock_code` / `股票代码` - 股票代码（支持SH/SZ前缀）
- ✅ `stock_name` / `股票名称` - 股票名称
- ✅ `concept` / `概念` - 概念名称（多个概念用+分隔）

### 可选字段
- `industry` / `行业` - 行业分类
- `date` - 交易日期（格式: YYYY-MM-DD）
- `price` / `价格` - 股价
- `turnover_rate` / `换手` - 换手率
- `net_inflow` / `净流入` - 资金净流入
- `pages_count` / `全部页数` - 页数统计
- `total_reads` / `热帖首页页阅读总数` - 阅读数

---

## 🚀 使用方法

### 1. 基础导入

```bash
python3 scripts/import_csv_local.py --file /path/to/data.csv
```

**效果**：
- 创建新股票、新概念
- 添加新的股票-概念关联
- 更新已存在股票的基本信息
- 如果数据已存在，会提示但不覆盖

### 2. 覆盖导入

```bash
python3 scripts/import_csv_local.py --file /path/to/data.csv --overwrite
```

**效果**：
- 覆盖当日的 `daily_stock_data` 记录
- 更新股票基本信息
- **不会删除**概念关联

### 3. 指定交易日期

```bash
python3 scripts/import_csv_local.py --file /path/to/data.csv --date 2024-10-16
```

**效果**：
- 强制使用指定日期
- 不从文件名解析日期

### 4. 使用远程数据库

```bash
# MySQL
python3 scripts/import_csv_local.py \
    --file /path/to/data.csv \
    --db-url mysql+pymysql://user:password@host:3306/dbname

# PostgreSQL
python3 scripts/import_csv_local.py \
    --file /path/to/data.csv \
    --db-url postgresql://user:password@host:5432/dbname
```

---

## 📊 实际示例

### 示例1：首次导入

```bash
cd /Users/peakom/work/stock-analysis-system/backend

python3 scripts/import_csv_local.py \
    --file /Users/peakom/Downloads/stocks_2024-10-16.csv
```

**输出**：
```
======================================================================
📊 CSV本地文件导入脚本
======================================================================
📁 文件路径: /Users/peakom/Downloads/stocks_2024-10-16.csv
📋 文件名称: stocks_2024-10-16.csv
📦 文件大小: 125,486 bytes (122.55 KB)
📅 指定日期: None
🔄 覆盖模式: 否
======================================================================

✅ 文件读取成功，大小: 125,486 bytes

🚀 开始导入CSV数据...
----------------------------------------------------------------------
📊 第一步：分析CSV文件中的股票和概念关系...
📈 CSV中包含 50 只股票，150 个股票-概念关系
📦 创建导入批次: ID=1, 记录数=50
✨ 创建新股票: 600000 - 浦发银行
✨ 创建新概念: 银行
🔗 添加关联: 600000 -> 银行
...
----------------------------------------------------------------------

✅ 导入完成！

📈 导入统计:
   📅 导入日期: 2024-10-16
   ✅ 成功记录: 150 条
   ⏭️  跳过记录: 0 条

📊 详细信息:
   🏢 股票: 50 新增, 0 更新
   🏷️  概念: 20 新增
   🔗 关联: 150 新增
   📈 每日数据: 50 新增, 0 更新
   💾 原始数据: 150 条

======================================================================
```

### 示例2：重复导入（不覆盖）

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Downloads/stocks_2024-10-16.csv
```

**输出**：
```
⚠️  数据已存在
   📅 导入日期: 2024-10-16
   📊 已导入记录: 150 条
   ⏭️  跳过记录: 0 条
   💡 提示: 使用 --overwrite 参数可以覆盖已存在的数据
```

### 示例3：覆盖导入

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Downloads/stocks_2024-10-16.csv \
    --overwrite
```

**输出**：
```
🗑️ 已删除 50 只股票在 2024-10-16 的 50 条数据记录
✅ 导入完成！
   📅 导入日期: 2024-10-16
   ✅ 成功记录: 150 条
   🏢 股票: 0 新增, 50 更新
   🏷️  概念: 0 新增
   🔗 关联: 0 新增
   📈 每日数据: 50 新增, 0 更新
```

### 示例4：使用远程数据库

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Downloads/stocks.csv \
    --db-url mysql+pymysql://root:Pp123456@82.157.28.35/stockdb \
    --overwrite
```

---

## 🔍 常见问题

### Q1: 如何完全重新导入某个股票的概念关联？

**A**: 当前脚本采用增量模式，旧关联不会自动删除。如需完全重置：

```bash
# 方法1：手动清理数据库
mysql -u user -p stockdb -e "
DELETE FROM stock_concepts
WHERE stock_id = (SELECT id FROM stocks WHERE stock_code='600000');
"

# 然后重新导入
python3 scripts/import_csv_local.py --file data.csv --overwrite
```

```bash
# 方法2：SQL批量清理
mysql -u user -p stockdb -e "
DELETE FROM stock_concepts
WHERE stock_id IN (
    SELECT id FROM stocks WHERE stock_code IN ('600000','600036','600050')
);
"
```

### Q2: 如何查看已导入的概念关联？

```bash
# 查看某个股票的所有概念
mysql -u user -p stockdb -e "
SELECT s.stock_code, s.stock_name, c.concept_name
FROM stocks s
JOIN stock_concepts sc ON s.id = sc.stock_id
JOIN concepts c ON sc.concept_id = c.id
WHERE s.stock_code = '600000';
"
```

### Q3: CSV文件中概念格式是什么？

**A**: 多个概念用 `+` 分隔：

```csv
stock_code,stock_name,concept
600000,浦发银行,银行+金融科技+AI
600036,招商银行,银行+消费电子+支付
```

### Q4: 覆盖模式到底覆盖什么？

**A**:
- ✅ **会覆盖**: daily_stock_data（每日交易数据）
- ✅ **会更新**: stocks 的基本信息（名称、行业）
- ❌ **不会删除**: concepts（概念）
- ❌ **不会删除**: stock_concepts（股票-概念关联）

### Q5: 如何批量导入多个CSV文件？

```bash
# Bash脚本批量导入
for file in /path/to/csv/*.csv; do
    echo "导入: $file"
    python3 scripts/import_csv_local.py --file "$file" --overwrite
done
```

### Q6: 导入失败怎么办？

**A**: 检查以下几点：
1. CSV文件编码是否为 UTF-8
2. 必需字段是否完整（stock_code, stock_name, concept）
3. 日期格式是否正确（YYYY-MM-DD）
4. 数据库连接是否正常
5. 查看详细错误信息进行调试

---

## 📚 相关脚本

| 脚本 | 用途 | 数据源 |
|------|------|--------|
| `import_csv_local.py` | CSV文件导入（本脚本） | 本地CSV文件 |
| `import_eee.py` | EEE热度数据导入 | 本地EEE.txt文件 |
| `import_ttv.py` | TTV交易数据导入 | 本地TTV.txt文件 |
| `calculate_rankings.py` | 排名和汇总计算 | 已导入的数据库数据 |

---

## 🎯 最佳实践

### 1. 日常导入流程

```bash
# 第1步：导入CSV（股票+概念）
python3 scripts/import_csv_local.py --file stocks_2024-10-16.csv

# 第2步：导入EEE热度
python3 scripts/import_eee.py --file EEE_2024-10-16.txt

# 第3步：计算排名和汇总
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```

### 2. 数据纠正流程

```bash
# 发现数据有误，重新导入覆盖
python3 scripts/import_csv_local.py \
    --file stocks_2024-10-16_corrected.csv \
    --overwrite
```

### 3. 远程服务器导入

```bash
# SSH到服务器
ssh user@82.157.28.35

# 上传CSV文件
scp stocks.csv user@82.157.28.35:/tmp/

# 在服务器上执行导入
cd /path/to/stock-analysis-system/backend
python3 scripts/import_csv_local.py --file /tmp/stocks.csv --overwrite
```

---

## ⚙️ 技术细节

### 数据流程

```
CSV文件
  ↓
读取并解析（支持中英文格式）
  ↓
规范化股票代码（去除SH/SZ前缀）
  ↓
┌─────────────────┬─────────────────┬──────────────────┐
↓                 ↓                 ↓                  ↓
concepts表        stocks表         stock_concepts表   daily_stock_data表
(去重插入)        (创建/更新)      (增量添加)         (创建/更新)
  ↓                 ↓                 ↓                  ↓
只增不改          更新基本信息      只增不减           支持覆盖
```

### 事务处理

- ✅ 使用数据库事务保证数据一致性
- ✅ 失败自动回滚
- ✅ 批量操作提高性能

### 性能优化

- 使用 `bulk_save_objects()` 批量插入
- 两遍扫描：先收集关系，再批量处理
- 避免重复查询，缓存已处理的实体

---

## 📞 技术支持

如有问题，请查看：
1. 本文档的"常见问题"部分
2. 脚本源代码注释
3. 相关文档: `backend/scripts/README.md`
4. 数据库架构文档

---

创建时间: 2024-11
最后更新: 2024-11
