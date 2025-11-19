# EEE/TTV 排名和汇总计算脚本使用指南

## 📋 脚本功能

这个脚本用于计算和汇总 EEE 或 TTV 原始数据，生成以下输出：

1. **排名数据** (`daily_concept_rankings`) - 每个股票在其所属概念内的排名
2. **汇总统计** (`daily_concept_summaries`) - 每个概念的每日统计数据
3. **任务记录** (`daily_analysis_tasks`) - 计算任务的执行记录

这相当于前端"重新计算"按钮的后端逻辑。

---

## 🚀 快速开始

### 脚本位置
```
/Users/peakom/work/stock-analysis-system/backend/scripts/calculate_rankings.py
```

### 三种计算模式

#### 1️⃣ 单日期计算
计算指定日期的数据。最常用的模式，速度快。

```bash
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```

**示例输出：**
```
计算 2024-10-16 的 EEE 数据排名...
  ✓ 读取 5,672 条原始记录
  ✓ 分组到 48 个概念
  ✓ 2024-10-16: 创建 5,672 条排名记录，48 条汇总记录

✅ 计算完成!
统计:
  日期: 2024-10-16
  排名记录: 5,672
  汇总记录: 48
  涉及概念: 48
```

#### 2️⃣ 日期范围计算
批量计算一段时间内的数据。

```bash
# 计算 2024-10-01 到 2024-10-31
python3 scripts/calculate_rankings.py --range 2024-10-01 2024-10-31 --source eee
```

#### 3️⃣ 整月计算
计算整个月份（更简洁的方式）。

```bash
# 计算 2024年10月
python3 scripts/calculate_rankings.py --month 2024-10 --source eee
```

---

## 📝 命令格式

```bash
python3 scripts/calculate_rankings.py [选项]
```

### 必须参数（三选一）

| 参数 | 说明 | 示例 |
|------|------|------|
| `--date YYYY-MM-DD` | 单个日期 | `--date 2024-10-16` |
| `--range START END` | 日期范围 | `--range 2024-10-01 2024-10-31` |
| `--month YYYY-MM` | 整月计算 | `--month 2024-10` |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|-------|
| `--source eee\|ttv` | 数据源 | `eee` |
| `--db-url URL` | 数据库连接 | `postgresql://postgres:Pp123456@localhost/stockdb` |

---

## 💡 使用示例

### 示例 1: 重新计算昨天的 EEE 数据

```bash
cd /Users/peakom/work/stock-analysis-system/backend
python3 scripts/calculate_rankings.py --date 2024-11-17 --source eee
```

### 示例 2: 批量计算整个 10 月的 EEE 数据

```bash
python3 scripts/calculate_rankings.py --month 2024-10 --source eee
```

### 示例 3: 计算最近 7 天的 TTV 数据

```bash
python3 scripts/calculate_rankings.py --range 2024-11-11 2024-11-17 --source ttv
```

### 示例 4: 使用自定义数据库

```bash
python3 scripts/calculate_rankings.py \
  --date 2024-10-16 \
  --source eee \
  --db-url postgresql://user:password@host:5432/dbname
```

---

## ⚙️ 工作流程

### 1. 读取原始数据
从 `eee_daily_trading` 或 `ttv_daily_trading` 表读取指定日期的原始数据。

### 2. 按概念分组
根据股票所属的概念，对热度值数据进行分组。

### 3. 计算排名
在每个概念内，按热度值从高到低排序，生成排名。

### 4. 生成汇总数据
对每个概念计算：
- 总热度值
- 平均热度值
- 最高/最低热度值
- 股票数量

### 5. 更新或插入数据库
- 如果记录已存在，则更新
- 如果不存在，则新建

### 6. 记录任务
在 `daily_analysis_tasks` 表中记录任务执行情况。

---

## 📊 数据说明

### 输入数据

**eee_daily_trading（EEE热度数据表）**
```
stock_code          | trading_date | trading_volume
SH110064           | 2024-10-16   | 714588
SH110064           | 2024-10-17   | 451653
...
```

### 输出数据

**daily_concept_rankings（排名表）**
```
concept_id | stock_id | trade_date   | rank_in_concept | heat_value
12         | 345      | 2024-10-16   | 1               | 714588
12         | 346      | 2024-10-16   | 2               | 451653
...
```

**daily_concept_summaries（汇总表）**
```
concept_id | trade_date   | total_heat_value | stock_count | avg_heat_value | max_heat | min_heat
12         | 2024-10-16   | 2500000          | 25          | 100000         | 714588   | 5000
...
```

---

## 🔄 重新计算场景

### 场景 1: 某个日期的数据导入错误
重新导入正确的数据后，运行：
```bash
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```
脚本会自动更新该日期的所有排名和汇总数据。

### 场景 2: 股票-概念映射关系修改
修改了 `stock_concept` 映射关系后，重新计算该日期的数据：
```bash
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```

### 场景 3: 批量导入大量历史数据后
导入 10 月的所有数据后，批量计算：
```bash
python3 scripts/calculate_rankings.py --month 2024-10 --source eee
```

---

## ⚡ 性能考虑

### 计算时间参考

| 场景 | 数据量 | 预计耗时 |
|------|--------|---------|
| 单日期（~5000条原始数据） | 5,000 | 5-10秒 |
| 一周（7天） | 35,000 | 1-2分钟 |
| 一月（30天） | 150,000 | 5-10分钟 |

### 优化建议

1. **批量导入后再计算** - 先导入所有原始数据，再统一计算
2. **避免重复计算** - 同一日期不需要重复计算多次
3. **利用计划任务** - 可配置 cron 任务定期计算（见下面章节）

---

## 🔧 定时任务设置（可选）

### 每天凌晨 1 点自动计算前一天的数据

编辑 crontab：
```bash
crontab -e
```

添加以下行：
```bash
# 每天凌晨 1 点计算前一天的 EEE 数据
0 1 * * * cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/calculate_rankings.py --date $(date -d '-1 day' +\%Y-\%m-\%d) --source eee >> /tmp/eee_calc.log 2>&1
```

### 每月 1 号凌晨 2 点计算上个月的数据

```bash
# 每月 1 号凌晨 2 点计算上个月的全部数据
0 2 1 * * cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/calculate_rankings.py --month $(date -d '-1 month' +\%Y-\%m) --source eee >> /tmp/eee_monthly.log 2>&1
```

---

## 🐛 故障排除

### 问题 1: 找不到 Python 模块

**错误信息：**
```
ModuleNotFoundError: No module named 'app'
```

**解决方案：**
确保在项目根目录运行：
```bash
cd /Users/peakom/work/stock-analysis-system/backend
python3 scripts/calculate_rankings.py --date 2024-10-16
```

### 问题 2: 数据库连接失败

**错误信息：**
```
psycopg2.OperationalError: connection refused
```

**检查清单：**
- PostgreSQL 服务是否运行？`pg_isready`
- 数据库地址正确？
- 用户名密码正确？

### 问题 3: 找不到股票或概念

**警告信息：**
```
⚠️  找不到股票: 600036
```

**原因和解决：**
- 股票还未导入到 `stocks` 表
- 股票-概念映射关系还未建立
- 先确保所有主数据都已导入

### 问题 4: 计算耗时过长

**原因：**
- 日期范围太长（跨越多个月份）
- 数据量太大（百万级记录）

**解决方案：**
- 分批计算：先计算 10 月，再计算 11 月
- 或使用 `--date` 单日期模式，逐天计算

---

## 📈 监控和验证

### 验证计算结果

```sql
-- 查看某日期的排名数据
SELECT * FROM daily_concept_rankings
WHERE trade_date = '2024-10-16'
LIMIT 10;

-- 查看某日期的汇总数据
SELECT * FROM daily_concept_summaries
WHERE trade_date = '2024-10-16';

-- 查看任务执行记录
SELECT * FROM daily_analysis_tasks
WHERE trade_date = '2024-10-16'
ORDER BY created_at DESC;
```

### 检查计算统计

```sql
-- 统计某月的排名数据
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT trade_date) as dates,
  COUNT(DISTINCT concept_id) as concepts
FROM daily_concept_rankings
WHERE trade_date >= '2024-10-01' AND trade_date < '2024-11-01';
```

---

## 💻 完整工作流示例

### 场景：导入和计算 10 月的完整数据

```bash
# 第 1 步: 导入 10 月的所有 EEE 数据
cd /Users/peakom/work/stock-analysis-system/backend
python3 scripts/import_eee.py --file /Users/peakom/Downloads/EEE.txt

# 第 2 步: 验证导入
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
SELECT COUNT(*) FROM eee_daily_trading
WHERE trading_date >= '2024-10-01' AND trading_date < '2024-11-01';
EOF

# 第 3 步: 批量计算整个 10 月的排名和汇总
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 第 4 步: 验证计算结果
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
SELECT COUNT(*) as total_rankings FROM daily_concept_rankings
WHERE trade_date >= '2024-10-01' AND trade_date < '2024-11-01';

SELECT COUNT(*) as total_summaries FROM daily_concept_summaries
WHERE trade_date >= '2024-10-01' AND trade_date < '2024-11-01';
EOF
```

---

## 📞 常见问题

**Q: 能否修改已计算的数据？**
A: 可以。重新运行脚本会自动更新已存在的记录。

**Q: 能否部分重新计算？**
A: 可以。指定 `--date` 或 `--range` 参数即可重新计算部分数据，不影响其他日期。

**Q: 如何清空某日期的计算数据？**
A: 运行清空脚本（见下面的高级用法）。

---

## 🔐 高级用法

### 清空某日期的计算数据

```bash
# 清空 2024-10-16 的所有排名和汇总数据
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
DELETE FROM daily_concept_rankings WHERE trade_date = '2024-10-16';
DELETE FROM daily_concept_summaries WHERE trade_date = '2024-10-16';
DELETE FROM daily_analysis_tasks WHERE trade_date = '2024-10-16';
EOF
```

### 检查计算覆盖情况

```bash
# 查看哪些日期已计算
SELECT DISTINCT trade_date
FROM daily_concept_rankings
ORDER BY trade_date DESC
LIMIT 30;
```

### 导出计算结果

```bash
# 导出排名数据为 CSV
psql postgresql://postgres:Pp123456@localhost/stockdb -c \
  "SELECT * FROM daily_concept_rankings WHERE trade_date = '2024-10-16'" \
  -o ranking_2024-10-16.csv

# 导出汇总数据为 CSV
psql postgresql://postgres:Pp123456@localhost/stockdb -c \
  "SELECT * FROM daily_concept_summaries WHERE trade_date = '2024-10-16'" \
  -o summary_2024-10-16.csv
```

---

## 📚 相关脚本

| 脚本 | 功能 | 使用场景 |
|------|------|---------|
| `import_eee.py` | 导入原始热度数据 | 导入 EEE.txt 文件 |
| `import_ttv.py` | 导入原始交易数据 | 导入 TTV.txt 文件 |
| `calculate_rankings.py` | **计算排名和汇总** | **本脚本** |

---

**最后更新：2024-11-18**
