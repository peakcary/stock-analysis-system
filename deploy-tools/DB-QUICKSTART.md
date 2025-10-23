# 🗄️ 数据库操作快速开始

## 文件夹中的数据库脚本

```
deploy-tools/
├── db-init.sh              ← 初始化数据库（首次部署时使用）
├── db-backup.sh            ← 备份数据库（定期执行）
├── db-restore.sh           ← 恢复数据库（紧急情况）
├── DATABASE_OPS.md         ← 完整操作指南
└── DB-QUICKSTART.md        ← 这个文件
```

---

## ⚡ 快速命令

### 初始化（首次部署）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 初始化数据库（创建表、默认用户等）
./db-init.sh
```

**执行时间**: 2-3 分钟
**输出**: 创建的表列表

### 备份（定期执行）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 备份数据库到本地
./db-backup.sh
```

**执行时间**: 1-2 分钟（取决于数据量）
**输出**: `./db-backups/stock_analysis_prod_YYYYMMDD_HHMMSS.sql`

### 恢复（紧急情况）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 从备份恢复
./db-restore.sh ./db-backups/stock_analysis_prod_20251023_120000.sql
```

**执行时间**: 2-5 分钟（取决于数据量）
**警告**: 会覆盖现有数据库！

---

## 📋 日常操作流程

### 每次部署代码

```bash
# 1. 部署代码
./deploy.sh

# 2. 检查状态
./check-status.sh

# 3. 数据库无需改动（自动处理依赖）
```

### 每周维护

```bash
# 周一：备份数据库
./db-backup.sh

# 周五：检查备份和服务状态
ls -lh ./db-backups/
./check-status.sh
```

### 更新数据库结构

```bash
# 修改 ORM 模型后，运行初始化（会覆盖！）
./db-init.sh

# 或者从备份恢复（推荐）
./db-restore.sh ./db-backups/before_structure_change.sql
```

---

## 🎯 常见场景

### 场景1: 第一次部署到生产环境

```bash
# 步骤：
1. 运行部署脚本
   ./deploy.sh

2. 初始化数据库
   ./db-init.sh

3. 验证
   curl https://qwquant.com/api/v1/health

4. 创建备份（防备）
   ./db-backup.sh
```

### 场景2: 定期备份

```bash
# 推荐：每周执行一次
./db-backup.sh

# 查看备份列表
ls -lh ./db-backups/

# 自动删除30天前的备份
find ./db-backups -name "*.sql" -mtime +30 -delete
```

### 场景3: 数据丢失恢复

```bash
# 1. 查看备份
ls -lh ./db-backups/

# 2. 恢复最近的备份
./db-restore.sh ./db-backups/stock_analysis_prod_20251023_120000.sql

# 3. 验证恢复成功
./check-status.sh
```

### 场景4: 测试数据库

```bash
# 1. 备份当前生产数据
./db-backup.sh

# 2. 初始化测试数据（会删除现有数据！）
./db-init.sh

# 3. 做完测试后，恢复生产数据
./db-restore.sh ./db-backups/stock_analysis_prod_before_test.sql
```

---

## ⚠️ 危险操作

| 操作 | 命令 | 结果 | 风险 |
|------|------|------|------|
| 初始化 | `./db-init.sh` | 删除所有表，创建新表 | 🔴 高 |
| 恢复 | `./db-restore.sh` | 覆盖所有数据 | 🔴 高 |
| 备份 | `./db-backup.sh` | 创建备份文件 | 🟢 安全 |

**安全建议：**
- ✅ 初始化前备份
- ✅ 恢复前二次确认
- ✅ 定期测试备份恢复
- ✅ 保存多个备份副本

---

## 📊 数据库配置参考

```
主机:         127.0.0.1
端口:         3306
用户:         root
密码:         Pp123456
数据库:       stock_analysis_prod
字符集:       utf8mb4
表前缀:       无
```

---

## 🔍 故障排查

### 问题: 初始化失败

```bash
# 检查MySQL是否运行
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo systemctl status mysql"

# 检查连接
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SELECT 1;'"
```

### 问题: 备份很慢

```bash
# 查看数据库大小
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e \
   'SELECT SUM(data_length+index_length) FROM information_schema.tables WHERE table_schema=\"stock_analysis_prod\";'"
```

### 问题: 恢复失败

```bash
# 检查备份文件完整性
head -5 ./db-backups/stock_analysis_prod_*.sql
tail -5 ./db-backups/stock_analysis_prod_*.sql

# 查看备份文件大小
ls -lh ./db-backups/
```

---

## 📚 完整文档

详细的操作指南和FAQ，请查看：

```bash
cat DATABASE_OPS.md
```

---

## 🚀 与部署流程的配合

```
日常工作流程：
┌─────────────────┐
│ 修改代码        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ ./deploy.sh     │ ← 部署新代码
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 验证 API        │ ← ./check-status.sh
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 检查数据库      │ ← 无需手动操作
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 定期备份        │ ← ./db-backup.sh（每周）
└─────────────────┘

紧急恢复流程：
┌──────────────────┐
│ 发现问题         │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ ./rollback.sh    │ ← 代码回滚
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ ./db-restore.sh  │ ← 数据恢复
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ ./check-status.sh│ ← 验证恢复
└──────────────────┘
```

---

## ✅ 检查清单

### 第一次设置

- [ ] 运行 `./deploy.sh` 部署代码
- [ ] 运行 `./db-init.sh` 初始化数据库
- [ ] 运行 `./db-backup.sh` 创建初始备份
- [ ] 验证: `curl https://qwquant.com/api/v1/health`

### 定期维护

- [ ] 每周: `./db-backup.sh`
- [ ] 每月: 检查备份文件 `ls -lh ./db-backups/`
- [ ] 每月: 清理旧备份 `find ./db-backups -mtime +30 -delete`

### 代码更新

- [ ] 更改代码
- [ ] 运行 `./deploy.sh`
- [ ] 验证 `./check-status.sh`
- [ ] 如有问题: `./rollback.sh` + `./db-restore.sh`

---

## 📞 快速命令速查

```bash
# 初始化
./db-init.sh

# 备份
./db-backup.sh

# 恢复
./db-restore.sh ./db-backups/filename.sql

# 检查备份
ls -lh ./db-backups/

# 检查服务
./check-status.sh

# 部署代码
./deploy.sh

# 回滚代码
./rollback.sh

# 清理旧备份（30天前）
find ./db-backups -name "*.sql" -mtime +30 -delete

# 手动备份（使用 MySQL 命令）
mysqldump -u root -p'Pp123456' stock_analysis_prod > backup_manual.sql
```

---

**版本**: 1.0
**最后更新**: 2025-10-23
**相关文件**: DATABASE_OPS.md, deploy.sh, rollback.sh, check-status.sh
