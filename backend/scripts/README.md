# 📊 EEE/TTV 数据导入和计算脚本完全指南

本文档汇总了所有数据处理脚本，包括导入、计算、本地执行和远程执行的完整说明。

---

## 📋 脚本总览

### 数据处理流程

```
EEE.txt / TTV.txt 文件
        ↓
   导入脚本
        ↓
eee_daily_trading / ttv_daily_trading（原始数据表）
        ↓
   计算脚本
        ↓
daily_concept_rankings（排名数据）
daily_concept_summaries（汇总数据）
daily_analysis_tasks（任务记录）
```

### 核心脚本列表

| 脚本 | 功能 | 输入 | 输出 | 位置 |
|------|------|------|------|------|
| `import_eee.py` | 导入EEE热度数据 | EEE.txt文件 | eee_daily_trading表 | `scripts/` |
| `import_ttv.py` | 导入TTV交易数据 | TTV.txt文件 | ttv_daily_trading表 | `scripts/` |
| `calculate_rankings.py` | 计算排名和汇总 | eee_daily_trading/ttv_daily_trading表 | daily_concept_rankings、daily_concept_summaries表 | `scripts/` |

---

## 🎯 快速开始

### 本地执行（推荐用于测试）

#### 1. 导入EEE数据

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 导入EEE.txt文件
python3 scripts/import_eee.py \
  --file /Users/peakom/Downloads/EEE.txt

# 或指定数据库
python3 scripts/import_eee.py \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://postgres:Pp123456@localhost/stockdb
```

#### 2. 计算排名（单日期）

```bash
# 计算2024-10-16的数据
python3 scripts/calculate_rankings.py \
  --date 2024-10-16 \
  --source eee
```

#### 3. 批量计算（整月）

```bash
# 计算2024年10月的全部数据
python3 scripts/calculate_rankings.py \
  --month 2024-10 \
  --source eee
```

---

## 📖 详细脚本说明

### 1️⃣ import_eee.py - EEE热度数据导入

**功能：** 从EEE.txt文件导入热度数据到数据库

**文件格式：**
```
SH110064	2024-05-28	6546.000000
SH110064	2024-05-29	9245.000000
```
每行：股票代码[Tab]交易日期[Tab]热度值

**命令格式：**
```bash
python3 scripts/import_eee.py [选项]
```

**可选参数：**
```
--file PATH              EEE.txt文件路径（默认：~/Downloads/EEE.txt）
--db-url DATABASE_URL    数据库URL（默认：postgresql://postgres:Pp123456@localhost/stockdb）
```

**使用示例：**
```bash
# 基础导入（使用默认配置）
python3 scripts/import_eee.py

# 自定义文件路径
python3 scripts/import_eee.py --file /path/to/EEE.txt

# 自定义数据库
python3 scripts/import_eee.py \
  --file /path/to/EEE.txt \
  --db-url postgresql://user:password@host:5432/dbname
```

**输出示例：**
```
╔════════════════════════════════════════════════════════╗
║     EEE 热度数据批量导入脚本                           ║
╚════════════════════════════════════════════════════════╝

配置:
  文件路径: /Users/peakom/Downloads/EEE.txt
  目标表: eee_daily_trading
  数据库: stockdb

Step 1: 计算文件哈希...
✓ 文件哈希: a3f5c8...

Step 2: 解析 EEE.txt 文件...
✓ EEE.txt 解析完成，包含 100 个交易日期，共 5,672 条记录

Step 3: 导入数据到 eee_daily_trading...
  ✓ 2024-05-28: 插入 48 条记录到 eee_daily_trading
  ✓ 2024-05-29: 插入 50 条记录到 eee_daily_trading
  ...
✓ 导入记录已创建

总计插入 5,672 条 EEE 数据到 eee_daily_trading

成功日期: 100, 失败日期: 0
```

**重要说明：**
- ✅ 支持重复导入，相同日期数据会被跳过（防止重复）
- ✅ 生成文件哈希用于追踪数据来源
- ✅ 记录导入元信息（文件名、大小、时间等）
- ❌ 不做任何数据计算，仅存储原始数据

---

### 2️⃣ import_ttv.py - TTV交易数据导入

**功能：** 从TTV.txt文件导入交易数据到数据库

**文件格式：** 与EEE.txt相同
```
BJ920000	2024-07-30	0.000000
BJ920000	2024-07-31	100.000000
```

**命令格式：**
```bash
python3 scripts/import_ttv.py [选项]
```

**可选参数：**
```
--file PATH              TTV.txt文件路径（默认：~/Downloads/TTV.txt）
--db-url DATABASE_URL    数据库URL
```

**使用示例：**
```bash
# 导入TTV数据
python3 scripts/import_ttv.py --file /path/to/TTV.txt
```

---

### 3️⃣ calculate_rankings.py - 排名和汇总计算

**功能：** 计算每个概念的股票排名和汇总统计数据

**计算内容：**
1. 股票在概念内的排名（按热度值排序）
2. 概念的汇总统计（总热度、平均值、最高值、最低值等）

**命令格式：**
```bash
python3 scripts/calculate_rankings.py [必需参数] [可选参数]
```

**必需参数（三选一）：**
```
--date YYYY-MM-DD           计算单个日期
--range START_DATE END_DATE  计算日期范围
--month YYYY-MM              计算整月数据
```

**可选参数：**
```
--source eee|ttv             数据源（默认：eee）
--db-url DATABASE_URL        数据库URL
```

**使用示例：**

```bash
# 单日期计算（最快）
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee

# 日期范围计算
python3 scripts/calculate_rankings.py \
  --range 2024-10-01 2024-10-31 \
  --source eee

# 整月计算（推荐）
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 使用TTV数据
python3 scripts/calculate_rankings.py --date 2024-10-16 --source ttv
```

**输出示例：**
```
╔════════════════════════════════════════════════════════╗
║         排名和汇总数据计算脚本                         ║
╚════════════════════════════════════════════════════════╝

配置:
  数据源: EEE
  数据库: stockdb

  计算模式: 单日期 (2024-10-16)

开始计算 2024-10-16 的 EEE 数据排名...
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

---

## 🖥️ 本地执行方式

### 前置条件

```bash
# 1. 进入后端目录
cd /Users/peakom/work/stock-analysis-system/backend

# 2. 激活虚拟环境（如果需要）
source venv/bin/activate

# 3. 确保PostgreSQL服务运行
pg_isready  # 应显示 accepting connections
```

### 典型工作流

```bash
# 第1步：导入EEE数据
python3 scripts/import_eee.py --file /Users/peakom/Downloads/EEE.txt

# 第2步：导入TTV数据
python3 scripts/import_ttv.py --file /Users/peakom/Downloads/TTV.txt

# 第3步：计算10月的排名和汇总
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 第4步：验证结果
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
SELECT COUNT(*) FROM eee_daily_trading;
SELECT COUNT(*) FROM daily_concept_rankings;
SELECT COUNT(*) FROM daily_concept_summaries;
EOF
```

---

## 🌐 远程执行方式

### 方式1️⃣：通过SSH在远程服务器执行

#### A. 远程导入

```bash
# 在本地电脑上执行，通过SSH登录远程服务器运行脚本

# 导入EEE数据到远程服务器
sshpass -p "chen_188_8_8" ssh -o StrictHostKeyChecking=no ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate

  # 从本地上传文件到远程
  # 或者从远程URL下载
  python3 scripts/import_eee.py \
    --file /tmp/EEE.txt \
    --db-url postgresql://postgres:Pp123456@localhost/stockdb
EOF
```

#### B. 远程计算

```bash
# 在远程服务器计算
sshpass -p "chen_188_8_8" ssh -o StrictHostKeyChecking=no ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF
```

#### C. 完整远程工作流（推荐）

```bash
#!/bin/bash
# remote_sync.sh - 远程同步和计算脚本

REMOTE_HOST="ubuntu@82.157.28.35"
REMOTE_PASSWORD="chen_188_8_8"
PROJECT_PATH="/opt/stock-analysis-system/backend"

# 1. 上传数据文件到远程服务器
echo "上传数据文件..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
  /Users/peakom/Downloads/EEE.txt \
  $REMOTE_HOST:/tmp/EEE.txt

# 2. 远程导入
echo "远程导入数据..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_HOST << 'REMOTE_EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  python3 scripts/import_eee.py --file /tmp/EEE.txt
  echo "导入完成"
REMOTE_EOF

# 3. 远程计算
echo "远程计算排名..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_HOST << 'REMOTE_EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
  echo "计算完成"
REMOTE_EOF

echo "✅ 远程处理完成！"
```

执行脚本：
```bash
chmod +x remote_sync.sh
./remote_sync.sh
```

---

### 方式2️⃣：通过远程数据库连接

#### A. 连接远程数据库导入

```bash
# 本地脚本连接远程数据库
python3 scripts/import_eee.py \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://postgres:Pp123456@82.157.28.35:5432/stockdb

# 计算数据
python3 scripts/calculate_rankings.py \
  --month 2024-10 \
  --source eee \
  --db-url postgresql://postgres:Pp123456@82.157.28.35:5432/stockdb
```

**前置条件：**
- 远程数据库需要开放网络访问
- 防火墙允许5432端口（PostgreSQL）
- 数据库用户有权限

---

### 方式3️⃣：在远程服务器定时运行（推荐用于生产）

#### 通过Cron设置定时任务

```bash
# SSH登录远程服务器
ssh -i ~/.ssh/key.pem ubuntu@82.157.28.35

# 编辑crontab
crontab -e

# 添加以下任务：
```

**每天凌晨1点计算前一天的EEE数据**
```bash
0 1 * * * cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/calculate_rankings.py --date $(date -d '-1 day' +\%Y-\%m-\%d) --source eee >> /tmp/eee_calc.log 2>&1
```

**每月1号凌晨2点计算上个月的全部数据**
```bash
0 2 1 * * cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/calculate_rankings.py --month $(date -d '-1 month' +\%Y-\%m) --source eee >> /tmp/eee_monthly.log 2>&1
```

**每天凌晨3点从远程导入数据**
```bash
0 3 * * * cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/import_eee.py --file /tmp/EEE.txt >> /tmp/eee_import.log 2>&1
```

查看日志：
```bash
tail -f /tmp/eee_calc.log
```

---

## 🔧 常用命令速查表

### 本地执行

```bash
# 导入
python3 scripts/import_eee.py --file /path/to/EEE.txt
python3 scripts/import_ttv.py --file /path/to/TTV.txt

# 单日期计算
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee

# 整月计算
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 日期范围计算
python3 scripts/calculate_rankings.py --range 2024-10-01 2024-10-31 --source eee
```

### 远程执行（SSH）

```bash
# 导入
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/import_eee.py --file /tmp/EEE.txt
EOF

# 计算
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF
```

### 远程执行（数据库连接）

```bash
# 导入到远程数据库
python3 scripts/import_eee.py \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb

# 从远程数据库计算
python3 scripts/calculate_rankings.py \
  --month 2024-10 \
  --source eee \
  --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb
```

---

## 📊 数据库表说明

### 输入表

#### eee_daily_trading（EEE热度数据）
```sql
SELECT * FROM eee_daily_trading LIMIT 5;
```
| 字段 | 说明 | 类型 |
|------|------|------|
| id | 主键 | Integer |
| stock_code | 股票代码（含前缀） | String(20) |
| normalized_stock_code | 规范化代码 | String(10) |
| trading_date | 交易日期 | Date |
| trading_volume | 热度值 | Integer |
| created_at | 创建时间 | DateTime |

#### ttv_daily_trading（TTV交易数据）
```sql
SELECT * FROM ttv_daily_trading LIMIT 5;
```
结构与eee_daily_trading相同

### 输出表

#### daily_concept_rankings（排名数据）
```sql
SELECT * FROM daily_concept_rankings WHERE trade_date = '2024-10-16' LIMIT 10;
```
| 字段 | 说明 | 类型 |
|------|------|------|
| id | 主键 | Integer |
| concept_id | 概念ID | Integer |
| stock_id | 股票ID | Integer |
| trade_date | 交易日期 | Date |
| rank_in_concept | 排名 | Integer |
| heat_value | 热度值 | Decimal |

#### daily_concept_summaries（汇总数据）
```sql
SELECT * FROM daily_concept_summaries WHERE trade_date = '2024-10-16';
```
| 字段 | 说明 | 类型 |
|------|------|------|
| id | 主键 | Integer |
| concept_id | 概念ID | Integer |
| trade_date | 交易日期 | Date |
| total_heat_value | 总热度值 | Decimal |
| stock_count | 股票数量 | Integer |
| avg_heat_value | 平均热度值 | Decimal |
| max_heat_value | 最高热度值 | Decimal |
| min_heat_value | 最低热度值 | Decimal |

---

## 🐛 常见问题

### Q1: 脚本找不到Python模块

**错误：** `ModuleNotFoundError: No module named 'app'`

**解决：**
```bash
# 确保在正确的目录
cd /Users/peakom/work/stock-analysis-system/backend

# 验证目录结构
ls -la app/  # 应该有models.py等文件

# 重新运行脚本
python3 scripts/import_eee.py
```

---

### Q2: 数据库连接失败

**错误：** `psycopg2.OperationalError: connection refused`

**解决：**
```bash
# 检查PostgreSQL是否运行
pg_isready

# 验证连接字符串
psql postgresql://postgres:Pp123456@localhost/stockdb

# 检查远程连接
psql -h 82.157.28.35 -U postgres -d stockdb
```

---

### Q3: 导入重复数据

**现象：** 导入时显示"已存在"，跳过了某些日期

**说明：** 这是正常的**防重复机制**，脚本会自动跳过已存在的日期

**清空数据重新导入：**
```bash
# 清空EEE表
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
DELETE FROM eee_daily_trading WHERE trading_date = '2024-10-16';
EOF

# 重新导入
python3 scripts/import_eee.py --file /Users/peakom/Downloads/EEE.txt
```

---

### Q4: 计算速度慢

**原因：** 日期范围太长或数据量太大

**解决：**
```bash
# 分批计算：先算10月，再算11月
python3 scripts/calculate_rankings.py --month 2024-10 --source eee
python3 scripts/calculate_rankings.py --month 2024-11 --source eee

# 或单日期计算
for day in {01..31}; do
  python3 scripts/calculate_rankings.py --date 2024-10-$day --source eee
done
```

---

### Q5: 远程执行失败

**问题1：** SSH连接超时
```bash
# 检查服务器IP和端口
ping 82.157.28.35
ssh -p 22 ubuntu@82.157.28.35  # 默认22端口
```

**问题2：** 密码认证失败
```bash
# 确保密码正确：chen_188_8_8
# 使用key认证代替密码
ssh -i ~/.ssh/key.pem ubuntu@82.157.28.35
```

**问题3：** 文件权限错误
```bash
# 远程服务器上检查权限
ssh ubuntu@82.157.28.35 << EOF
  ls -la /opt/stock-analysis-system/backend/scripts/
  # 确保*.py文件可执行或有读权限
EOF
```

---

## 📚 完整示例

### 示例1：本地导入和计算10月数据

```bash
#!/bin/bash
# local_process.sh

set -e  # 遇到错误即停止

PROJECT_DIR="/Users/peakom/work/stock-analysis-system/backend"
DATA_DIR="/Users/peakom/Downloads"

cd "$PROJECT_DIR"

echo "════════════════════════════════════════"
echo "  本地数据处理流程"
echo "════════════════════════════════════════"

# 1. 导入EEE数据
echo ""
echo "[1/3] 导入EEE数据..."
python3 scripts/import_eee.py --file "$DATA_DIR/EEE.txt"

# 2. 导入TTV数据
echo ""
echo "[2/3] 导入TTV数据..."
python3 scripts/import_ttv.py --file "$DATA_DIR/TTV.txt"

# 3. 计算排名
echo ""
echo "[3/3] 计算10月排名和汇总..."
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

echo ""
echo "════════════════════════════════════════"
echo "✅ 处理完成！"
echo "════════════════════════════════════════"
```

执行：
```bash
chmod +x local_process.sh
./local_process.sh
```

---

### 示例2：远程导入并计算

```bash
#!/bin/bash
# remote_process.sh

REMOTE_HOST="ubuntu@82.157.28.35"
PASSWORD="chen_188_8_8"
LOCAL_FILE="/Users/peakom/Downloads/EEE.txt"

echo "════════════════════════════════════════"
echo "  远程数据处理流程"
echo "════════════════════════════════════════"

# 1. 上传文件
echo ""
echo "[1/3] 上传EEE.txt到远程服务器..."
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no \
  "$LOCAL_FILE" \
  $REMOTE_HOST:/tmp/EEE.txt

# 2. 远程导入
echo ""
echo "[2/3] 远程导入数据..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_HOST << 'EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  python3 scripts/import_eee.py --file /tmp/EEE.txt
EOF

# 3. 远程计算
echo ""
echo "[3/3] 远程计算排名..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_HOST << 'EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF

echo ""
echo "════════════════════════════════════════"
echo "✅ 远程处理完成！"
echo "════════════════════════════════════════"
```

执行：
```bash
chmod +x remote_process.sh
./remote_process.sh
```

---

## 📞 技术支持

### 脚本文件位置

```
/Users/peakom/work/stock-analysis-system/backend/
├── scripts/
│   ├── import_eee.py              # EEE导入脚本
│   ├── import_ttv.py              # TTV导入脚本
│   ├── calculate_rankings.py      # 排名计算脚本
│   ├── README.md                  # 本文档
│   ├── CALCULATION_GUIDE.md       # 计算脚本详细指南
│   └── IMPORT_GUIDE.md            # 导入脚本详细指南
```

### 查看帮助

```bash
# 查看脚本参数
python3 scripts/import_eee.py --help
python3 scripts/import_ttv.py --help
python3 scripts/calculate_rankings.py --help
```

### 查看脚本日志

```bash
# 查看导入日志
tail -f /tmp/import_eee.log

# 查看计算日志
tail -f /tmp/calculate.log

# 远程日志
ssh ubuntu@82.157.28.35 tail -f /tmp/eee_calc.log
```

---

## 📝 更新记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2024-11-18 | 1.0 | 初版，包含导入和计算脚本 |

---

**最后更新：2024-11-18**

