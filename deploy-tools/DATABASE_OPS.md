# 数据库操作指南

本指南涵盖数据库的初始化、备份、恢复和日常维护。

---

## 📋 目录

1. [初始化数据库](#初始化数据库)
2. [备份数据库](#备份数据库)
3. [恢复数据库](#恢复数据库)
4. [日常维护](#日常维护)
5. [常见问题](#常见问题)

---

## 初始化数据库

### 什么是数据库初始化？

初始化数据库会：
- ✅ 创建所有表结构
- ✅ 创建默认管理员用户
- ✅ 初始化数据关系

### 何时初始化？

- 第一次部署到生产环境
- 数据库表结构发生变化（需要重新创建表）
- 需要重置为初始状态

### 如何执行初始化？

#### 方式1: 使用提供的脚本（推荐）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 执行初始化脚本
./db-init.sh
```

**步骤：**
1. 脚本会检查当前数据库状态
2. 提示确认初始化
3. 运行 `init_database.py` 创建表和默认用户
4. 显示创建的表列表

#### 方式2: 手动SSH到服务器

```bash
# SSH连接
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35

# 进入项目目录
cd /opt/stock-analysis-system/backend

# 激活虚拟环境
source venv/bin/activate

# 设置数据库环境变量
export DATABASE_HOST=127.0.0.1
export DATABASE_PORT=3306
export DATABASE_USER=root
export DATABASE_PASSWORD=Pp123456
export DATABASE_NAME=stock_analysis_prod
export DATABASE_URL=mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_prod

# 运行初始化脚本
python3 init_database.py
```

### 初始化后

```bash
# 验证初始化成功
curl https://qwquant.com/api/v1/health

# 查看API文档
# 浏览器打开: https://qwquant.com/api/docs

# 使用默认管理员账户登录
# 用户名: admin
# 密码: admin
```

---

## 备份数据库

### 为什么要备份？

- 🛡️ 保护重要数据
- 🔄 支持快速恢复
- 📊 保存历史数据

### 备份策略

**建议：**
- ✅ 每周自动备份一次
- ✅ 重大更新前手动备份
- ✅ 部署新版本前备份
- ✅ 定期检查备份文件的完整性

### 如何备份？

#### 方式1: 使用脚本（推荐）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 执行备份
./db-backup.sh
```

**输出示例：**
```
💾 数据库备份脚本
================================

📋 备份配置：
   - 数据库: stock_analysis_prod
   - 服务器: 82.157.28.35
   - 本地路径: ./db-backups/stock_analysis_prod_20251023_120000.sql
   - 时间戳: 20251023_120000

确认备份数据库? (y/n) y

📥 下载备份到本地...
   ✅ 下载完成 (245K)

✅ 验证备份文件...
   ✅ 备份文件有效

✅ 备份成功！

📝 备份详情：
   - 文件: ./db-backups/stock_analysis_prod_20251023_120000.sql
   - 大小: 245K
   - 行数: 12345 行

🔄 恢复方式：
   ./db-restore.sh ./db-backups/stock_analysis_prod_20251023_120000.sql
```

#### 方式2: 手动备份

```bash
# SSH到服务器
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35

# 导出数据库
mysqldump -u root -p'Pp123456' stock_analysis_prod > backup.sql

# 退出SSH
exit

# 下载到本地
sshpass -p "chen_188_8_8" scp ubuntu@82.157.28.35:backup.sql ./backup.sql
```

### 备份文件管理

```bash
# 查看所有备份
ls -lh ./db-backups/

# 查看最新备份
ls -lh ./db-backups/ | tail -5

# 计算备份总大小
du -sh ./db-backups/

# 删除旧备份（保留最近10个）
ls -t ./db-backups/ | tail -n +11 | xargs rm -f
```

---

## 恢复数据库

### 何时恢复？

- 🚨 数据意外删除
- 💥 数据库崩溃
- 🔙 需要回滚到之前的版本
- 🧪 恢复到测试状态

### 如何恢复？

#### 方式1: 使用脚本（推荐）

```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 查看可用备份
ls -lh ./db-backups/

# 恢复指定备份
./db-restore.sh ./db-backups/stock_analysis_prod_20251023_120000.sql
```

**脚本会：**
1. ✅ 验证备份文件有效性
2. ✅ 提示二次确认（防止误操作）
3. ✅ 上传备份文件到服务器
4. ✅ 停止应用服务
5. ✅ 删除旧数据库
6. ✅ 导入新数据
7. ✅ 重启应用服务
8. ✅ 验证服务运行正常

#### 方式2: 手动恢复

```bash
# 停止服务
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 "sudo systemctl stop stock-api"

# 删除旧数据库
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'DROP DATABASE stock_analysis_prod;'"

# 创建新数据库
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'CREATE DATABASE stock_analysis_prod DEFAULT CHARACTER SET utf8mb4;'"

# 导入备份
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' stock_analysis_prod < backup.sql"

# 重启服务
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 "sudo systemctl start stock-api"

# 验证
curl https://qwquant.com/api/v1/health
```

---

## 日常维护

### 数据库检查清单

#### 每天
- [ ] 检查服务健康状态：`./check-status.sh`
- [ ] 查看最近的错误日志

#### 每周
- [ ] 执行备份：`./db-backup.sh`
- [ ] 检查磁盘空间
- [ ] 清理旧备份文件

#### 每月
- [ ] 检查数据库大小
- [ ] 优化表结构（如需）
- [ ] 审查访问日志

### 常用的MySQL命令

```bash
# 连接到数据库
mysql -u root -p'Pp123456' stock_analysis_prod

# 查看数据库大小
mysql -u root -p'Pp123456' -e \
  "SELECT table_schema, ROUND(SUM(data_length+index_length)/1024/1024,2) AS size_mb FROM information_schema.tables WHERE table_schema='stock_analysis_prod' GROUP BY table_schema;"

# 查看表列表
SHOW TABLES;

# 查看表结构
DESCRIBE users;

# 查看表大小
SELECT table_name, ROUND(((data_length+index_length)/1024/1024),2) AS size_mb FROM information_schema.tables WHERE table_schema='stock_analysis_prod' ORDER BY size_mb DESC;

# 优化表
OPTIMIZE TABLE users;

# 检查表
CHECK TABLE users;

# 修复表
REPAIR TABLE users;
```

### 定期清理

```bash
# 删除超过30天的备份
find ./db-backups -name "*.sql" -mtime +30 -delete

# 清理所有备份（谨慎！）
rm -rf ./db-backups/*.sql

# 只保留最近5个备份
ls -t ./db-backups/*.sql | tail -n +6 | xargs rm -f
```

---

## 常见问题

### Q1: 数据库初始化失败

**症状：** `ERROR: Access denied for user 'root'@'localhost'`

**解决方案：**
```bash
# 1. 检查MySQL是否运行
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo systemctl status mysql"

# 2. 检查MySQL密码是否正确
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SELECT 1;'"

# 3. 确保数据库存在
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SHOW DATABASES LIKE \"stock%\";'"
```

### Q2: 备份文件太大

**症状：** 备份文件超过可用磁盘空间

**解决方案：**
```bash
# 1. 检查磁盘空间
df -h

# 2. 清理旧备份
ls -lh ./db-backups/

# 3. 删除不需要的备份
rm ./db-backups/old_backup.sql

# 4. 压缩备份文件
gzip ./db-backups/*.sql
```

### Q3: 恢复时间过长

**症状：** 导入大型备份文件需要很长时间

**解决方案：**
```bash
# 1. 在MySQL中禁用日志（加快速度）
SET FOREIGN_KEY_CHECKS=0;
SET UNIQUE_CHECKS=0;
-- 导入数据
SET FOREIGN_KEY_CHECKS=1;
SET UNIQUE_CHECKS=1;

# 2. 使用 -q 参数加快导入
mysql -u root -p'Pp123456' -q stock_analysis_prod < backup.sql

# 3. 分批导入（如果文件太大）
# 先导入前一半，再导入后一半
```

### Q4: 数据库表损坏

**症状：** `Table 'xxx' is marked as crashed and should be repaired`

**解决方案：**
```bash
# 连接到数据库
mysql -u root -p'Pp123456' stock_analysis_prod

# 检查所有表
CHECK TABLE users, admin_users, payments;

# 修复表
REPAIR TABLE users;
REPAIR TABLE admin_users;
REPAIR TABLE payments;

# 优化表
OPTIMIZE TABLE users;
```

### Q5: 忘记备份就删除了数据

**症状：** 重要数据被删除

**解决方案：**
```bash
# 1. 立即停止应用（防止进一步修改）
./rollback.sh

# 2. 检查是否有其他备份
ls -la ./db-backups/

# 3. 如果有备份，执行恢复
./db-restore.sh ./db-backups/latest_backup.sql

# 4. 如果没有备份，联系技术支持
```

---

## 数据库架构

### 表结构

```
stock_analysis_prod
├── users                    # 客户端用户表
├── admin_users              # 管理员用户表
├── payments                 # 支付记录表
├── payment_orders           # 支付订单表
├── payment_packages         # 支付套餐表
├── payment_notifications    # 支付通知表
└── user_queries             # 用户查询历史表
```

### 关键配置

| 配置项 | 值 |
|--------|-----|
| **主机** | 127.0.0.1 |
| **端口** | 3306 |
| **用户** | root |
| **密码** | Pp123456 |
| **数据库** | stock_analysis_prod |
| **字符集** | utf8mb4 |
| **排序规则** | utf8mb4_unicode_ci |

---

## 监控和告警

### 关键指标

```bash
# 查看数据库连接数
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SHOW STATUS LIKE \"Threads_connected\";'"

# 查看慢查询
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SHOW VARIABLES LIKE \"slow_query_log\";'"

# 查看最大连接数
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "mysql -u root -p'Pp123456' -e 'SHOW VARIABLES LIKE \"max_connections\";'"
```

---

## 安全建议

✅ **必做：**
- 定期备份数据库
- 备份文件保存在多个位置
- 定期测试恢复流程
- 使用强密码
- 限制数据库访问

⚠️ **注意：**
- 不要在公网上暴露MySQL端口
- 定期更新MySQL版本
- 监控异常连接
- 审查用户权限

---

## 恢复速查表

| 场景 | 命令 |
|------|------|
| **备份** | `./db-backup.sh` |
| **恢复** | `./db-restore.sh ./db-backups/file.sql` |
| **初始化** | `./db-init.sh` |
| **检查状态** | `./check-status.sh` |
| **查看备份** | `ls -lh ./db-backups/` |

---

**最后更新**: 2025-10-23
**版本**: 1.0
