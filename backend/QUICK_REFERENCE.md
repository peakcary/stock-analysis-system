# ⚡ 快速参考卡

## 🎯 最常用命令

### 本地执行

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 导入EEE数据
python3 scripts/import_eee.py

# 导入TTV数据
python3 scripts/import_ttv.py

# 计算10月数据
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 计算单日期
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```

---

## 🌐 远程执行（推荐）

### 方式1：SSH执行

```bash
# 远程计算10月数据
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF
```

### 方式2：连接远程数据库

```bash
# 本地脚本 → 远程数据库
python3 scripts/import_eee.py \
  --file /Users/peakom/Downloads/EEE.txt \
  --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb

python3 scripts/calculate_rankings.py \
  --month 2024-10 \
  --source eee \
  --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb
```

---

## 📊 完整工作流（一键执行）

### 本地工作流脚本

```bash
#!/bin/bash
# local_work.sh - 本地导入和计算

cd /Users/peakom/work/stock-analysis-system/backend

echo "1️⃣ 导入数据..."
python3 scripts/import_eee.py --file /Users/peakom/Downloads/EEE.txt

echo "2️⃣ 计算排名..."
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

echo "✅ 完成！"
```

执行：
```bash
chmod +x local_work.sh && ./local_work.sh
```

### 远程工作流脚本

```bash
#!/bin/bash
# remote_work.sh - 远程导入和计算

HOST="ubuntu@82.157.28.35"
PASS="chen_188_8_8"

echo "1️⃣ 上传文件..."
sshpass -p "$PASS" scp -o StrictHostKeyChecking=no \
  /Users/peakom/Downloads/EEE.txt $HOST:/tmp/

echo "2️⃣ 远程导入..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $HOST << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/import_eee.py --file /tmp/EEE.txt
EOF

echo "3️⃣ 远程计算..."
sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no $HOST << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF

echo "✅ 完成！"
```

执行：
```bash
chmod +x remote_work.sh && ./remote_work.sh
```

---

## 🔄 常见场景速查

### 场景1：导入新数据并计算

```bash
# 本地
python3 scripts/import_eee.py && \
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 远程
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/import_eee.py --file /tmp/EEE.txt && \
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF
```

### 场景2：重新计算某天数据

```bash
# 本地
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee

# 远程
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
EOF
```

### 场景3：批量计算整月

```bash
# 本地
python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 远程
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt/stock-analysis-system/backend && source venv/bin/activate
  python3 scripts/calculate_rankings.py --month 2024-10 --source eee
EOF
```

---

## 🗄️ 数据库操作速查

### 查看导入数据

```bash
# 查看EEE数据量
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
SELECT COUNT(*) FROM eee_daily_trading;
EOF

# 查看计算结果
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
SELECT COUNT(*) FROM daily_concept_rankings;
SELECT COUNT(*) FROM daily_concept_summaries;
EOF
```

### 清空数据重新计算

```bash
# 清空某日期的计算数据
psql postgresql://postgres:Pp123456@localhost/stockdb << EOF
DELETE FROM daily_concept_rankings WHERE trade_date = '2024-10-16';
DELETE FROM daily_concept_summaries WHERE trade_date = '2024-10-16';
EOF

# 重新计算
python3 scripts/calculate_rankings.py --date 2024-10-16 --source eee
```

---

## 📝 参数速查表

### import_eee.py

```bash
--file PATH              文件路径（默认：~/Downloads/EEE.txt）
--db-url URL             数据库URL（默认：postgresql://postgres:Pp123456@localhost/stockdb）
```

### import_ttv.py

```bash
--file PATH              文件路径（默认：~/Downloads/TTV.txt）
--db-url URL             数据库URL
```

### calculate_rankings.py

```bash
--date YYYY-MM-DD        单日期（2024-10-16）
--range START END        日期范围（2024-10-01 2024-10-31）
--month YYYY-MM          整月（2024-10）
--source eee|ttv         数据源（默认：eee）
--db-url URL             数据库URL
```

---

## ⏰ 定时任务（生产环境）

### 在远程服务器上设置定时计算

```bash
# SSH登录远程服务器
ssh ubuntu@82.157.28.35

# 编辑crontab
crontab -e

# 添加以下行：
# 每天凌晨1点计算前一天
0 1 * * * cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/calculate_rankings.py --date $(date -d '-1 day' +\%Y-\%m-\%d) --source eee >> /tmp/eee_calc.log 2>&1

# 每月1号凌晨2点计算上个月
0 2 1 * * cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/calculate_rankings.py --month $(date -d '-1 month' +\%Y-\%m) --source eee >> /tmp/eee_monthly.log 2>&1
```

查看执行日志：
```bash
tail -f /tmp/eee_calc.log
```

---

## 🔧 故障排除速查

| 问题 | 解决方案 |
|------|--------|
| `ModuleNotFoundError` | `cd /Users/peakom/work/stock-analysis-system/backend` |
| `connection refused` | `pg_isready` 检查数据库是否运行 |
| SSH连接超时 | `ping 82.157.28.35` 检查网络连接 |
| 密码认证失败 | 确认密码：`chen_188_8_8` |
| 脚本执行权限错误 | `chmod +x scripts/*.py` |
| 计算速度慢 | 改为 `--date` 单日期计算，逐日执行 |

---

## 📁 文件位置

```
backend/
├── scripts/
│   ├── import_eee.py              ← EEE导入
│   ├── import_ttv.py              ← TTV导入
│   ├── calculate_rankings.py      ← 计算脚本
│   ├── README.md                  ← 完整文档
│   ├── CALCULATION_GUIDE.md       ← 计算脚本详细指南
│   └── IMPORT_GUIDE.md            ← 导入脚本详细指南
└── QUICK_REFERENCE.md             ← 本文件（快速参考）
```

---

## 🚀 一行命令速查

```bash
# 导入EEE
cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/import_eee.py

# 计算10月
cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/calculate_rankings.py --month 2024-10 --source eee

# 远程计算10月
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 "cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 scripts/calculate_rankings.py --month 2024-10 --source eee"

# 连接远程数据库导入
cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/import_eee.py --file /Users/peakom/Downloads/EEE.txt --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb

# 连接远程数据库计算
cd /Users/peakom/work/stock-analysis-system/backend && python3 scripts/calculate_rankings.py --month 2024-10 --source eee --db-url postgresql://postgres:Pp123456@82.157.28.35/stockdb
```

---

## 📞 获取更多帮助

```bash
# 查看脚本帮助
python3 scripts/import_eee.py --help
python3 scripts/calculate_rankings.py --help

# 查看详细文档
cat scripts/README.md              # 完整指南
cat scripts/CALCULATION_GUIDE.md   # 计算脚本详细说明
```

---

**版本：1.0 | 更新：2024-11-18**
