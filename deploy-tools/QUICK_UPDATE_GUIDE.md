# ⚡ 快速更新指南

## 📍 所有命令都在这个文件夹执行

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools
```

---

## 🎯 最常用的 3 个操作

### 1️⃣ 部署代码更新（最常用）

```bash
./deploy.sh
```

- 打包代码 → 上传服务器 → 启动服务
- 用时: 2-3 分钟
- 版本信息自动更新

### 2️⃣ 数据库迁移（表结构改变时）

```bash
# 先创建备份（重要！）
./db-backup.sh

# 然后执行迁移
./db-migrate.sh 002 upgrade

# 其中 002 是迁移版本号（从 migrations/ 文件夹查看）
```

- 用时: 1-2 分钟
- 执行前会二次确认

### 3️⃣ 紧急回滚（出问题时）

```bash
# 1. 回滚代码
./rollback.sh

# 2. 恢复数据库
./db-restore.sh ./db-backups/stock_analysis_prod_[date].sql

# 其中 [date] 是备份文件名中的日期
```

- 用时: 3-5 分钟
- 会覆盖当前数据库

---

## 📋 完整的更新流程

```bash
# 步骤 1: 备份当前数据库
./db-backup.sh

# 步骤 2: 部署新代码
./deploy.sh

# 步骤 3: 如果有新的迁移，执行迁移
./db-migrate.sh 002 upgrade

# 步骤 4: 验证服务
curl https://qwquant.com/api/v1/health
```

---

## 🔍 查看版本和状态

```bash
# 查看当前版本
cat ./VERSION

# 查看服务状态
./check-status.sh

# 查看备份列表
ls -lh ./db-backups/

# 查看迁移版本
ls -1 ./migrations/*.py | grep -v TEMPLATE
```

---

## 💡 常见场景

### 场景 A: 只改代码，不改数据库

```bash
./deploy.sh
curl https://qwquant.com/api/v1/health  # 验证
```

### 场景 B: 既改代码又改数据库

```bash
./db-backup.sh              # 1. 备份
./deploy.sh                 # 2. 部署代码
./db-migrate.sh 002 upgrade # 3. 迁移数据库
curl https://qwquant.com/api/v1/health  # 4. 验证
```

### 场景 C: 出错需要回滚

```bash
./rollback.sh               # 回滚代码
./db-restore.sh ./db-backups/stock_analysis_prod_[date].sql  # 恢复数据库
./check-status.sh           # 验证
```

### 场景 D: 只备份，不部署

```bash
./db-backup.sh
```

---

## 🚀 创建新的数据库迁移

当需要添加表或修改表结构时：

### 第1步: 复制迁移模板

```bash
cp ./migrations/TEMPLATE.py ./migrations/002_add_phone_field.py
```

### 第2步: 编辑新的迁移文件

编辑 `002_add_phone_field.py`，在 `upgrade()` 函数中：

```python
def upgrade():
    from sqlalchemy import text
    from app.core.database import engine

    with engine.connect() as conn:
        # 添加新字段
        conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))
        conn.commit()

    return True
```

### 第3步: 执行迁移

```bash
./db-migrate.sh 002 upgrade
```

---

## ⚠️ 重要提示

| 操作 | 风险 | 步骤 |
|------|------|------|
| `./deploy.sh` | 低 | 可以随时运行 |
| `./db-migrate.sh` | 中 | 先备份，再迁移 |
| `./db-restore.sh` | **高** | 会覆盖所有数据 |
| `./rollback.sh` | 中 | 恢复到上一个版本 |

---

## 🆘 故障排查

### 问题: 部署后 API 无法访问

```bash
# 查看错误日志
./check-status.sh

# 详细日志
ssh ubuntu@82.157.28.35 "sudo journalctl -u stock-api -n 50 --no-pager"

# 如果有问题，回滚
./rollback.sh
```

### 问题: 迁移失败

```bash
# 查看错误信息（从上面的输出）
# 检查迁移脚本语法
cat ./migrations/002_*.py

# 从备份恢复
./db-restore.sh ./db-backups/stock_analysis_prod_[date].sql
```

### 问题: 找不到备份文件

```bash
# 查看所有备份
ls -lh ./db-backups/

# 如果没有备份，查看日期格式
# 格式通常是: stock_analysis_prod_YYYYMMDD_HHMMSS.sql
```

---

## 📞 一句话速查

| 需要做什么 | 命令 |
|---------|------|
| 部署代码 | `./deploy.sh` |
| 迁移数据库 | `./db-migrate.sh <版本号> upgrade` |
| 回滚代码 | `./rollback.sh` |
| 恢复数据库 | `./db-restore.sh ./db-backups/file.sql` |
| 备份数据库 | `./db-backup.sh` |
| 检查状态 | `./check-status.sh` |
| 查看版本 | `cat ./VERSION` |
| 查看备份 | `ls -lh ./db-backups/` |
| 查看迁移 | `ls ./migrations/*.py` |

---

## 🎓 完整文档

- **DEPLOYMENT_UPDATES.md** - 详细的更新指南（90% 的问题的答案都在这里）
- **DB-QUICKSTART.md** - 数据库操作快速开始
- **DATABASE_OPS.md** - 完整的数据库操作手册

---

**最后更新**: 2025-10-24

提示：这份文档适合快速查阅。更详细的说明请查看 DEPLOYMENT_UPDATES.md
