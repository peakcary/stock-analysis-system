# 数据库配置总结 (Database Configuration Summary)

## ✅ 连接状态 (Connection Status)

**状态**: ✅ 已连接成功
**数据库版本**: MySQL 8.0.22-txsql (腾讯云)

## 数据库配置信息 (Configuration Details)

| 配置项 | 值 |
|--------|-----|
| 主机 (Host) | bj-cdb-k21a7ijs.sql.tencentcdb.com |
| 端口 (Port) | 27126 |
| 用户名 (User) | root |
| 数据库名 (Database) | mydb |
| 驱动程序 (Driver) | PyMySQL |

## 已更新的文件 (Updated Files)

- ✅ `.env` - 生产环境配置
- ✅ `.env.example` - 配置模板
- ✅ `.env.production` - 生产环境配置

## 连接字符串 (Connection String)

```
DATABASE_URL=mysql+pymysql://root:Pp123456@bj-cdb-k21a7ijs.sql.tencentcdb.com:27126/mydb
```

## 📋 后续步骤 (Next Steps)

### 1. 运行数据库迁移 (Run Database Migrations)

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 检查迁移状态
alembic current

# 执行所有待执行的迁移
alembic upgrade head
```

### 2. 验证表创建 (Verify Tables Created)

```bash
# 查看所有表
python test_db_connection.py

# 或者直接连接数据库查询
mysql -h bj-cdb-k21a7ijs.sql.tencentcdb.com -P 27126 -u root -p mydb
mysql> SHOW TABLES;
```

### 3. 导入初始数据 (Import Initial Data - Optional)

如果需要导入示例数据或参考数据：

```bash
# 使用 API 端点导入数据
# 详见: backend/app/api/api_v1/endpoints/data_import.py

# 或者使用数据库导入工具
# mysql -h bj-cdb-k21a7ijs.sql.tencentcdb.com -P 27126 -u root -p mydb < your_data.sql
```

### 4. 启动后端服务 (Start Backend Service)

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 安装依赖（如果还未安装）
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --host 0.0.0.0 --port 3007 --reload

# 或使用生产环境设置
gunicorn -w 4 -b 0.0.0.0:3007 "app.main:app" -k uvicorn.workers.UvicornWorker
```

## 🔐 安全建议 (Security Recommendations)

### ⚠️ 重要: 保护敏感信息

1. **不要提交密码到版本控制系统**
   - `.env` 文件应添加到 `.gitignore`
   - 使用 `.env.example` 作为模板
   - 生产环境使用秘密管理工具

2. **更改默认密码** (如果可能)
   ```sql
   -- 腾讯云数据库中执行
   ALTER USER 'root'@'%' IDENTIFIED BY 'new_strong_password';
   FLUSH PRIVILEGES;
   ```

3. **创建应用专用用户** (推荐)
   ```sql
   -- 创建应用用户
   CREATE USER 'app_user'@'%' IDENTIFIED BY 'app_strong_password';

   -- 授予权限
   GRANT ALL PRIVILEGES ON mydb.* TO 'app_user'@'%';
   FLUSH PRIVILEGES;

   -- 更新 .env 文件
   DATABASE_USER=app_user
   DATABASE_PASSWORD=app_strong_password
   ```

4. **启用 SSL 连接** (生产环境)
   ```python
   # 在 config.py 中修改连接字符串
   DATABASE_URL = "mysql+pymysql://...?ssl_ca=/path/to/ca.pem&ssl_mode='REQUIRED'"
   ```

## 📊 数据库规划 (Database Planning)

### 预期的表结构 (Expected Tables)

运行迁移后应包含以下表：
- `users` - 客户端用户
- `admin_users` - 管理员用户
- `stocks` - 股票基本信息
- `daily_stock_data` - 每日股票数据
- `concepts` - 概念定义
- `stock_concepts` - 股票-概念关联
- `daily_concept_sums` - 每日概念汇总
- `daily_concept_rankings` - 每日概念排名
- `payment_packages` - 支付套餐
- `payment_orders` - 支付订单
- `payment_notifications` - 支付通知
- `membership_logs` - 会员日志
- `import_batches` - 导入批次
- 及其他相关表...

### 数据库大小预估 (Size Estimation)

- **初始大小**: ~5-10 MB (仅表结构)
- **一年数据**: ~100-500 MB (取决于数据量)
- **备份建议**: 定期备份，建议每日备份

## 🔧 故障排除 (Troubleshooting)

### 连接超时 (Connection Timeout)

**问题**: `Can't connect to MySQL server`

**解决方案**:
1. 检查网络连接
2. 确认数据库实例是否运行
3. 检查防火墙规则
4. 验证主机和端口是否正确

### 认证失败 (Authentication Failed)

**问题**: `Access denied for user 'root'@...`

**解决方案**:
1. 验证用户名和密码
2. 检查用户是否有访问权限
3. 确认主机权限设置（'%' 或特定 IP）

### 缺少表 (No Tables)

**问题**: 运行迁移前数据库为空

**解决方案**:
```bash
# 执行数据库迁移
alembic upgrade head

# 验证迁移
alembic current
alembic history
```

## 📞 相关文档 (Documentation)

- [Alembic 迁移文档](./README_DB_MIGRATIONS.md)
- [FastAPI 配置指南](./README.md)
- [数据模型定义](./app/models/)

---

**最后更新时间**: 2025-11-04
**配置版本**: 2.0 (腾讯云数据库)
