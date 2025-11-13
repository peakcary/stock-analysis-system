# PostgreSQL 部署指南

**最后更新**: 2025-11-13
**数据库**: PostgreSQL 17.5
**驱动**: psycopg2-binary

---

## 📋 概述

本指南说明如何使用更新后的部署脚本运行应用。所有脚本已更新为使用 PostgreSQL 而不是 MySQL。

---

## 🔧 已修改的脚本

### 1. `scripts/deployment/deploy.sh` (主部署脚本)

**修改内容**:
- ✅ 移除 MySQL 检查和启动命令
- ✅ 添加 PostgreSQL 服务检查（pg_isready）
- ✅ 使用 `postgresql@17` 或 `postgresql` 服务启动
- ✅ 更新生产环境配置为 PostgreSQL 连接字符串
- ✅ 移除 MySQL 特定的 SQL 表创建命令
- ✅ 更新数据库验证代码使用 PostgreSQL 语法
- ✅ 简化数据库优化部分（PostgreSQL 已内置优化）

**使用方法**:
```bash
# 完整部署
./scripts/deployment/deploy.sh

# 迁移模式（仅更新依赖和数据库）
./scripts/deployment/deploy.sh --migrate

# 生产环境部署
./scripts/deployment/deploy.sh --production
```

### 2. `scripts/database/init_postgresql.sh` (新增)

**功能**:
- 检查 PostgreSQL 服务
- 启动 PostgreSQL 服务（如果需要）
- 配置 postgres 用户密码
- 创建 stockdb 数据库
- 验证数据库连接

**使用方法**:
```bash
chmod +x scripts/database/init_postgresql.sh
./scripts/database/init_postgresql.sh
```

### 3. `scripts/database/verify_postgresql.sh` (新增)

**功能**:
- 验证 PostgreSQL 连接
- 检查 stockdb 数据库
- 统计表数量和行数
- 验证核心表存在
- 检查索引数量
- 显示连接字符串

**使用方法**:
```bash
chmod +x scripts/database/verify_postgresql.sh
./scripts/database/verify_postgresql.sh
```

---

## 🚀 快速启动

### 第一次部署

```bash
# 1. 初始化 PostgreSQL
./scripts/database/init_postgresql.sh

# 2. 验证 PostgreSQL
./scripts/database/verify_postgresql.sh

# 3. 部署应用
./scripts/deployment/deploy.sh

# 4. 启动服务
./start.sh
```

### 后续启动

```bash
# 启动所有服务
./start.sh

# 查看状态
./status.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh
```

---

## 📊 数据库连接信息

### 环境变量

```bash
# 本地开发
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stockdb
```

### psql 连接

```bash
# 交互式连接
psql -U postgres -h localhost -d stockdb

# 执行命令
psql -U postgres -h localhost -d stockdb -c "SELECT * FROM stocks LIMIT 5;"
```

---

## 🔄 迁移检查清单

- [x] PostgreSQL 17.5 安装
- [x] psycopg2-binary 依赖安装
- [x] 部署脚本更新为 PostgreSQL
- [x] 数据库初始化脚本创建
- [x] 数据库验证脚本创建
- [x] 本地 stockdb 数据库创建
- [x] 所有 26 个表创建成功
- [x] 核心数据迁移完成（6987 行）
- [x] 索引优化配置完成
- [x] API 连接 PostgreSQL 验证通过

---

## ⚙️ 生产环境部署

### 在生产服务器上

```bash
# 1. 安装 PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 2. 启动 PostgreSQL
sudo systemctl start postgresql

# 3. 设置 postgres 用户密码
sudo -u postgres psql << EOF
ALTER USER postgres WITH PASSWORD 'YOUR_SECURE_PASSWORD';
EOF

# 4. 创建 stockdb 数据库
sudo -u postgres createdb stockdb

# 5. 更新部署脚本中的密码
# 编辑 backend/.env 或 scripts/deployment/deploy.sh

# 6. 运行部署
./scripts/deployment/deploy.sh --production

# 7. 启动应用
./start.sh
```

---

## 🔍 故障排除

### PostgreSQL 无法连接

```bash
# 检查服务状态
pg_isready -h localhost -p 5432

# 启动服务
brew services start postgresql@17

# 查看日志
tail -f /usr/local/var/log/postgres.log
```

### 数据库不存在

```bash
# 初始化数据库
./scripts/database/init_postgresql.sh

# 或手动创建
psql -U postgres -h localhost << EOF
CREATE DATABASE stockdb ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;
EOF
```

### 连接拒绝

```bash
# 检查密码是否正确
psql -U postgres -h localhost -d stockdb

# 编辑 pg_hba.conf（macOS）
# /usr/local/var/postgres/pg_hba.conf
# 确保有: local   all             postgres                                md5
```

### 表缺失

```bash
# 重新运行初始化
cd backend
source venv/bin/activate
python -c "from app.core.database import Base, engine; Base.metadata.create_all(engine)"
```

---

## 📚 相关文档

- [PostgreSQL 本地开发配置](./POSTGRESQL_LOCAL_DEV_SETUP.md)
- [PostgreSQL 迁移进度](./POSTGRESQL_MIGRATION_PROGRESS.md)
- [PostgreSQL 迁移会话 2](./POSTGRESQL_MIGRATION_SESSION_2.md)

---

## 💡 常用命令

### 数据库操作

```bash
# 列出所有表
psql -U postgres -h localhost -d stockdb -c "\dt"

# 查看表结构
psql -U postgres -h localhost -d stockdb -c "\d stocks"

# 查看表行数
psql -U postgres -h localhost -d stockdb -c "SELECT COUNT(*) FROM stocks;"

# 导出数据
pg_dump -U postgres -d stockdb > backup.sql

# 导入数据
psql -U postgres -d stockdb < backup.sql

# 导出为 CSV
psql -U postgres -d stockdb -c "COPY stocks TO STDOUT WITH CSV HEADER" > stocks.csv
```

### 查询调试

```bash
# 开启 SQL 日志
SQLALCHEMY_ECHO=true python app.main:app

# 查看查询计划
psql -U postgres -h localhost -d stockdb -c "EXPLAIN SELECT * FROM stocks LIMIT 10;"
```

---

## ✅ 验证清单

部署完成后，运行以下检查：

```bash
# 1. 检查 PostgreSQL 连接
./scripts/database/verify_postgresql.sh

# 2. 检查数据库表
psql -U postgres -h localhost -d stockdb -c "\dt"

# 3. 检查核心数据
psql -U postgres -h localhost -d stockdb << EOF
SELECT '### Stocks ###' as table_name, COUNT(*) as row_count FROM stocks
UNION ALL
SELECT '### Concepts ###', COUNT(*) FROM concepts
UNION ALL
SELECT '### Users ###', COUNT(*) FROM users
UNION ALL
SELECT '### Stock Concepts ###', COUNT(*) FROM stock_concepts;
EOF

# 4. 测试 API
curl http://localhost:3007/api/v1/stocks?limit=5

# 5. 查看 API 文档
open http://localhost:3007/docs
```

---

## 🎯 下一步

1. ✅ 本地开发: `./start.sh`
2. ✅ 数据导入: 通过 API 或管理端上传数据
3. ✅ 功能测试: 访问 http://localhost:8006（管理端）
4. ✅ 生产部署: 按照"生产环境部署"部分操作

---

**任何问题？请参考各个 .md 文档或检查脚本的日志输出。**
