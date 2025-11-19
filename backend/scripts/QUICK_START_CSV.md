# CSV导入脚本 - 快速开始

## 🚀 一分钟快速上手

### 1. 基础使用

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 导入本地CSV文件
python3 scripts/import_csv_local.py --file /path/to/your/data.csv
```

### 2. 常用命令

```bash
# 覆盖模式（删除当日数据重新导入）
python3 scripts/import_csv_local.py --file data.csv --overwrite

# 指定日期
python3 scripts/import_csv_local.py --file data.csv --date 2024-10-16

# 使用远程MySQL数据库
python3 scripts/import_csv_local.py --file data.csv \
    --db-url mysql+pymysql://root:password@82.157.28.35/stockdb
```

---

## 📄 CSV文件格式

### 最简格式（仅必需字段）

```csv
stock_code,stock_name,concept
SH600000,浦发银行,银行
SH600036,招商银行,银行+消费电子
SZ000001,平安银行,银行+科技
```

### 完整格式（包含所有字段）

```csv
stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow
SH600000,浦发银行,银行+金融科技,金融,2024-10-16,10.52,1.2,5000000
SH600036,招商银行,银行+消费电子,金融,2024-10-16,32.15,0.8,-2000000
SZ000001,平安银行,银行+科技,金融,2024-10-16,12.34,1.5,3000000
```

**说明**：
- 多个概念用 `+` 分隔
- 支持 SH/SZ/BJ/HK 前缀，会自动规范化
- 自动识别转债（1开头的6位代码）

---

## 💡 使用示例

### 示例1：桌面CSV文件导入

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Desktop/stocks_2024-10-16.csv
```

### 示例2：下载文件夹导入

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Downloads/股票数据.csv \
    --overwrite
```

### 示例3：概念匹配表导入

```bash
python3 scripts/import_csv_local.py \
    --file /Users/peakom/Desktop/概念匹配表/stock_concept_mapping.csv \
    --date 2024-10-16
```

### 示例4：批量导入多个文件

```bash
# 创建批量导入脚本
for file in /Users/peakom/Desktop/概念匹配表/*.csv; do
    echo "导入: $(basename $file)"
    python3 scripts/import_csv_local.py --file "$file" --overwrite
done
```

---

## ⚙️ 数据处理规则

### 📊 表处理策略

| 表名 | 新增 | 更新 | 删除 | 说明 |
|------|------|------|------|------|
| **concepts** | ✅ | ❌ | ❌ | 去重插入，只增不改 |
| **stock_concepts** | ✅ | ❌ | ❌ | 累积模式，只增不减 |
| **stocks** | ✅ | ✅ | ❌ | 存在则更新基本信息 |
| **daily_stock_data** | ✅ | ✅ | ✅ | 支持覆盖 |

### 🔄 覆盖模式说明

使用 `--overwrite` 参数时：
- ✅ **会覆盖**：daily_stock_data（每日交易数据）
- ✅ **会更新**：stocks 的名称、行业等基本信息
- ❌ **不会删除**：concepts（概念）
- ❌ **不会删除**：stock_concepts（股票-概念关联）

**概念关联采用累积模式**：
```
首次导入: 600000 → 银行
第二次导入: 600000 → 银行+AI
结果: 600000 → 银行, AI  (两个关联都保留)
```

---

## 🔍 验证导入结果

### 查看导入的股票

```bash
mysql -u root -p stockdb -e "
SELECT stock_code, stock_name, industry,
       original_stock_code, stock_code_prefix
FROM stocks
ORDER BY created_at DESC
LIMIT 10;
"
```

### 查看导入的概念

```bash
mysql -u root -p stockdb -e "
SELECT id, concept_name, created_at
FROM concepts
ORDER BY created_at DESC
LIMIT 10;
"
```

### 查看股票-概念关联

```bash
mysql -u root -p stockdb -e "
SELECT s.stock_code, s.stock_name, c.concept_name
FROM stocks s
JOIN stock_concepts sc ON s.id = sc.stock_id
JOIN concepts c ON sc.concept_id = c.id
WHERE s.stock_code = '600000';
"
```

---

## ❓ 常见问题

### Q: 如何清除某个股票的所有概念关联？

```bash
mysql -u root -p stockdb -e "
DELETE FROM stock_concepts
WHERE stock_id = (SELECT id FROM stocks WHERE stock_code='600000');
"
```

### Q: 如何重新导入某个股票的概念？

```bash
# 1. 先清除旧关联
mysql -u root -p stockdb -e "DELETE FROM stock_concepts WHERE stock_id = (SELECT id FROM stocks WHERE stock_code='600000');"

# 2. 重新导入CSV
python3 scripts/import_csv_local.py --file data.csv --overwrite
```

### Q: 支持哪些CSV格式？

支持两种：
- **英文列名**: `stock_code,stock_name,concept,...`
- **中文列名**: `股票代码,股票名称,概念,...`

脚本会自动识别并转换。

---

## 📚 完整文档

详细说明请查看：
- **完整使用指南**: `scripts/CSV_IMPORT_README.md`
- **示例CSV文件**: `scripts/example_stocks.csv`
- **其他导入脚本**: `scripts/README.md`

---

## 🎯 完整工作流程

```bash
# 第1步：导入CSV（股票+概念）
python3 scripts/import_csv_local.py \
    --file /path/to/stocks_2024-10-16.csv

# 第2步：导入EEE热度数据
python3 scripts/import_eee.py \
    --file /path/to/EEE_2024-10-16.txt

# 第3步：计算排名和汇总
python3 scripts/calculate_rankings.py \
    --date 2024-10-16 \
    --source eee
```

---

创建时间: 2024-11
