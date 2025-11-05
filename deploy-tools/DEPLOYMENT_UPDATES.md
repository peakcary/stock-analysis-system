# 🚀 版本管理和更新指南

## 📖 概述

当后端代码或数据库结构有变化时，需要按照以下流程更新生产服务器。这个指南确保：
- ✅ 代码和数据库版本同步
- ✅ 更新失败可以快速回滚
- ✅ 所有变化都有版本记录

---

## 🎯 快速流程

### 场景1: 仅更新代码（数据库结构不变）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 1. 执行部署（自动更新版本信息）
./deploy.sh

# 2. 验证服务
curl https://qwquant.com/api/v1/health
```

**所需时间**: 2-3 分钟

### 场景2: 同时更新代码和数据库结构

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 1. 先备份数据库（防止出问题）
./db-backup.sh

# 2. 部署新代码
./deploy.sh

# 3. 执行数据库迁移（如果有新的迁移脚本）
./db-migrate.sh 002 upgrade

# 4. 验证服务
curl https://qwquant.com/api/v1/health
```

**所需时间**: 5-7 分钟

### 场景3: 出现问题需要回滚

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 1. 回滚代码
./rollback.sh

# 2. 如果数据库有问题，从备份恢复
./db-restore.sh ./db-backups/stock_analysis_prod_20251024_120000.sql

# 3. 验证服务
curl https://qwquant.com/api/v1/health
```

**所需时间**: 3-5 分钟

---

## 📋 详细步骤说明

### 第1步: 准备代码更新

**什么时候需要做:**
- 更新了后端代码
- 修改了 FastAPI 路由
- 更新了依赖包（requirements.txt）

**检查清单:**
- [ ] 代码已在本地测试
- [ ] 没有 Python 语法错误
- [ ] requirements.txt 已更新（如果有新依赖）
- [ ] 已备份当前数据库

### 第2步: 检查是否需要数据库迁移

**什么时候需要迁移:**
- 添加了新的表
- 修改了现有表的字段（添加/删除/修改列）
- 需要执行数据转换或初始化数据

**如何创建迁移脚本:**

1. 复制迁移模板:
```bash
cp migrations/TEMPLATE.py migrations/002_your_description.py
```

2. 修改迁移脚本中的 `upgrade()` 和 `downgrade()` 函数

3. 测试迁移脚本（在本地或测试环境）

4. 提交到版本控制

### 第3步: 部署代码

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 执行部署
./deploy.sh
```

**部署过程:**
```
1️⃣  打包代码
   - 清理虚拟环境和缓存
   - 压缩成 tar.gz

2️⃣  上传到服务器
   - 使用 scp 上传

3️⃣  服务器部署
   - 停止当前服务
   - 备份现有代码
   - 解压新代码
   - 安装依赖
   - 启动新服务
   - 验证服务正常

✅ 部署完成
```

### 第4步: 如果需要，执行数据库迁移

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 执行迁移
./db-migrate.sh 002 upgrade
```

**迁移过程:**
```
1. 上传迁移脚本到服务器
2. 执行迁移脚本中的 upgrade() 函数
3. 验证迁移成功
```

### 第5步: 验证部署成功

```bash
# 方式1: 检查服务健康状态
curl https://qwquant.com/api/v1/health

# 方式2: 检查详细状态
./check-status.sh

# 方式3: 查看应用日志
ssh ubuntu@82.157.28.35 "sudo journalctl -u stock-api -n 50 --no-pager"
```

---

## 🔄 版本信息管理

### 查看当前版本

```bash
cat ./VERSION
```

输出示例:
```
# 版本信息文件

# 应用版本 (YYYYMMDD_HHMMSS)
APP_VERSION=20251024_143022

# 数据库版本 (对应 migrations/ 中的版本)
DB_VERSION=001_initial_schema

# 上次更新时间
LAST_UPDATE=2025-10-24

# 上次部署描述
DESCRIPTION="Deployed package: backend_20251024_143022.tar.gz"
```

### 版本号说明

**APP_VERSION (应用版本)**
- 格式: `YYYYMMDD_HHMMSS`
- 例: `20251024_143022` = 2025年10月24日 14:30:22 部署
- 自动生成，无需手动修改

**DB_VERSION (数据库版本)**
- 格式: `NNN_description` 其中 NNN 是三位数字
- 例: `001_initial_schema`, `002_add_phone_field`, `003_create_payment_table`
- 需要手动更新为最新的迁移版本号

---

## 🛡️ 常见情况处理

### 情况1: 部署成功但服务无法启动

**症状**: 部署完成，但 API 无法访问

**解决步骤:**
```bash
# 1. 查看错误日志
ssh ubuntu@82.157.28.35 "sudo journalctl -u stock-api -n 100 --no-pager" | head -50

# 2. 检查 Python 依赖
ssh ubuntu@82.157.28.35 "cd /opt/stock-analysis-system/backend && source venv/bin/activate && python3 -c 'import app'"

# 3. 如果问题严重，执行回滚
./rollback.sh

# 4. 验证回滚后的服务
curl https://qwquant.com/api/v1/health
```

### 情况2: 数据库迁移失败

**症状**: 执行 `db-migrate.sh` 报错

**解决步骤:**
```bash
# 1. 查看迁移错误
# db-migrate.sh 的输出通常包含详细错误信息

# 2. 检查备份
ls -lh ./db-backups/

# 3. 从最后的好状态恢复
./db-restore.sh ./db-backups/stock_analysis_prod_[date].sql

# 4. 修复迁移脚本并重新执行
# 编辑 migrations/XXX_description.py
# 然后重新运行 db-migrate.sh
```

### 情况3: 需要紧急回滚到上一个版本

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 1. 回滚代码
./rollback.sh

# 2. 查看可用的数据库备份
ls -lh ./db-backups/ | tail -10

# 3. 恢复数据库到上一个稳定版本
./db-restore.sh ./db-backups/stock_analysis_prod_[last_good_date].sql

# 4. 验证
./check-status.sh
```

---

## 📊 迁移版本管理

### 查看所有可用的迁移版本

```bash
ls -1 ./migrations/*.py | grep -v TEMPLATE | sort
```

输出示例:
```
./migrations/001_initial_schema.py
./migrations/002_add_user_fields.py
./migrations/003_create_payment_tables.py
```

### 创建新的迁移版本

#### 第1步: 创建迁移文件

```bash
# 复制模板
cp ./migrations/TEMPLATE.py ./migrations/002_your_description.py
```

#### 第2步: 编辑迁移脚本

编辑 `002_your_description.py`，修改 `upgrade()` 和 `downgrade()` 函数:

```python
def upgrade():
    """升级到此版本"""
    from sqlalchemy import text
    from app.core.database import engine

    with engine.connect() as conn:
        # 添加新字段示例:
        # conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)"))

        # 创建新表示例:
        # conn.execute(text("""
        #     CREATE TABLE payments (
        #         id INT PRIMARY KEY AUTO_INCREMENT,
        #         user_id INT NOT NULL,
        #         amount DECIMAL(10,2),
        #         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     )
        # """))

        conn.commit()

    print("✅ 升级完成")
    return True

def downgrade():
    """回滚此版本"""
    from sqlalchemy import text
    from app.core.database import engine

    with engine.connect() as conn:
        # 删除添加的字段
        # conn.execute(text("ALTER TABLE users DROP COLUMN phone_number"))

        # 删除创建的表
        # conn.execute(text("DROP TABLE IF EXISTS payments"))

        conn.commit()

    print("✅ 回滚完成")
    return True
```

#### 第3步: 测试迁移脚本（可选）

```bash
# 在本地测试环境
python3 ./migrations/002_your_description.py upgrade

# 测试回滚
python3 ./migrations/002_your_description.py downgrade
```

#### 第4步: 部署和执行迁移

```bash
# 部署新代码
./deploy.sh

# 执行迁移
./db-migrate.sh 002 upgrade
```

---

## ✅ 完整的更新检查清单

### 代码更新前
- [ ] 在本地开发环境测试通过
- [ ] 没有 Python 语法错误
- [ ] requirements.txt 已更新
- [ ] 没有硬编码的密钥或敏感信息

### 数据库迁移准备
- [ ] 创建了迁移脚本（如果需要）
- [ ] 迁移脚本在本地测试过（可选但推荐）
- [ ] 确认 upgrade() 和 downgrade() 都正确

### 执行部署
- [ ] 执行备份: `./db-backup.sh`
- [ ] 执行部署: `./deploy.sh`
- [ ] 检查部署日志是否有错误

### 执行数据库迁移（如果需要）
- [ ] 执行迁移: `./db-migrate.sh X upgrade`
- [ ] 检查迁移日志

### 验证部署
- [ ] 健康检查: `curl https://qwquant.com/api/v1/health`
- [ ] 详细状态: `./check-status.sh`
- [ ] 检查应用日志: `ssh ubuntu@82.157.28.35 "sudo journalctl -u stock-api -n 20"`

### 更新版本信息
- [ ] VERSION 文件已自动更新
- [ ] 更新 DB_VERSION（如果执行了迁移）

---

## 🚨 紧急情况

### 完全回滚到上一个版本

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 1. 回滚代码
./rollback.sh

# 2. 恢复数据库
./db-restore.sh ./db-backups/stock_analysis_prod_[date].sql

# 3. 验证
./check-status.sh
```

### 数据库修复

```bash
# SSH 到服务器
ssh ubuntu@82.157.28.35

# 进入 MySQL
mysql -u root -p'Pp123456' stock_analysis_prod

# 查看表
SHOW TABLES;

# 检查表结构
DESCRIBE users;

# 检查表状态
CHECK TABLE users;

# 修复表（如果损坏）
REPAIR TABLE users;
```

---

## 📚 相关文件

```
deploy-tools/
├── VERSION                    ← 当前版本信息
├── deploy.sh                  ← 部署脚本（已改进）
├── db-migrate.sh              ← 新增：数据库迁移脚本
├── db-backup.sh               ← 数据库备份
├── db-restore.sh              ← 数据库恢复
├── rollback.sh                ← 代码回滚
├── check-status.sh            ← 状态检查
├── migrations/                ← 新增：数据库迁移脚本文件夹
│   ├── 001_initial_schema.py  ← 初始化迁移
│   ├── TEMPLATE.py            ← 迁移模板
│   └── 002_*.py               ← 您将来添加的迁移
└── DEPLOYMENT_UPDATES.md      ← 这个文件
```

---

## 🎓 工作流程图

```
修改代码或数据库结构
    ↓
备份数据库（./db-backup.sh）
    ↓
部署新代码（./deploy.sh）
    ↓
是否需要数据库迁移？
    ├─ 是 → 执行迁移（./db-migrate.sh X upgrade）
    └─ 否 → 跳过迁移
    ↓
验证服务（curl 或 ./check-status.sh）
    ↓
服务正常？
    ├─ 是 → 完成！
    └─ 否 → 回滚（./rollback.sh + ./db-restore.sh）
```

---

**最后更新**: 2025-10-24
**版本**: 1.0
