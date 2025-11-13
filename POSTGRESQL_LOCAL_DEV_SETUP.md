# PostgreSQL 本地开发环境配置指南

**日期**: 2025-11-13
**状态**: ✅ 已配置完成

---

## 📊 环境信息

| 配置项 | 值 |
|--------|-----|
| **数据库引擎** | PostgreSQL 17.5 (Homebrew) |
| **主机** | localhost |
| **端口** | 5432 |
| **用户名** | postgres |
| **密码** | Pp123456 |
| **数据库** | stockdb |
| **连接字符串** | `postgresql+psycopg2://postgres:Pp123456@localhost/stockdb` |

---

## 📝 配置文件

### `.env` (开发环境)
```bash
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost/stockdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stockdb
```

### `.env.production` (生产环境)
```bash
DATABASE_URL=postgresql+psycopg2://postgres:Pp123456@localhost:5432/stockdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=stockdb
```

---

## 🗂️ 数据库架构

### 已创建的 26 个表

**核心数据表** (6 个)
- `stocks` - 股票基本信息
- `concepts` - 概念数据
- `stock_concepts` - 股票-概念关联
- `users` - 用户数据
- `daily_stock_data` - 每日股票数据
- `stock_concept_raw_data` - 股票概念原始数据

**数据导入表** (3 个)
- `import_batches` - 导入批次记录
- `raw_import_data` - 原始导入数据
- `raw_data_mapping` - 数据映射关系

**分析统计表** (8 个)
- `daily_concept_rankings` - 每日概念排名
- `daily_concept_summaries` - 每日概念汇总
- `daily_concept_sums` - 每日概念求和
- `daily_analysis_tasks` - 每日分析任务
- `daily_trading` - 每日交易数据
- `concept_daily_summary` - 概念每日汇总
- `stock_concept_ranking` - 股票概念排名
- `concept_high_record` - 概念创新高记录

**支付系统表** (5 个)
- `payment_packages` - 支付套餐
- `payment_orders` - 支付订单
- `payment_notifications` - 支付通知
- `payments` - 支付记录
- `membership_logs` - 会员日志

**其他表** (4 个)
- `user_queries` - 用户查询
- `data_import_records` - 数据导入记录
- `refund_records` - 退款记录
- `txt_import_record` - TXT导入记录

---

## 🔧 常用命令

### 连接数据库
```bash
# 交互式连接
psql -U postgres -d stockdb -h localhost

# 执行单条命令
psql -U postgres -d stockdb -h localhost -c "SELECT * FROM stocks LIMIT 5;"
```

### 查看表结构
```bash
# 列出所有表
psql -U postgres -d stockdb -c "\dt"

# 查看表的详细结构
psql -U postgres -d stockdb -c "\d 表名"

# 查看表的索引
psql -U postgres -d stockdb -c "\di"
```

### 数据操作
```bash
# 查看表的行数
psql -U postgres -d stockdb -c "SELECT COUNT(*) FROM stocks;"

# 导出数据为 SQL
pg_dump -U postgres -d stockdb > backup.sql

# 导入数据
psql -U postgres -d stockdb < backup.sql

# 导出为 CSV
psql -U postgres -d stockdb -c "COPY stocks TO STDOUT WITH CSV HEADER" > stocks.csv
```

### 用户管理
```bash
# 修改密码
psql -U postgres -d postgres -c "ALTER USER postgres WITH PASSWORD 'new_password';"

# 创建新用户
psql -U postgres -c "CREATE USER dev_user WITH PASSWORD 'password';"

# 赋予权限
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE stockdb TO dev_user;"
```

---

## 📊 Python 连接示例

```python
from sqlalchemy import create_engine
from app.core.database import Base

# 读取环境变量
DATABASE_URL = "postgresql+psycopg2://postgres:Pp123456@localhost/stockdb"

# 创建引擎
engine = create_engine(DATABASE_URL, echo=True)

# 创建所有表
Base.metadata.create_all(bind=engine)

# 查询数据
with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM stocks")
    print(result.fetchone())
```

---

## 🚀 启动/停止 PostgreSQL

### macOS (Homebrew)
```bash
# 启动
brew services start postgresql@14

# 停止
brew services stop postgresql@14

# 重启
brew services restart postgresql@14

# 查看状态
brew services list | grep postgresql
```

### 验证是否运行
```bash
pg_isready -h localhost -p 5432
```

---

## 🔐 安全建议

1. **本地开发**: 当前配置适合本地开发，包含密码在 `.env` 文件中
2. **生产环境**:
   - 不要在代码中硬编码密码
   - 使用环境变量管理敏感信息
   - 考虑使用更复杂的密码
   - 定期更改密码

3. **备份数据**:
   ```bash
   # 定期备份
   pg_dump -U postgres -d stockdb > backup_$(date +%Y%m%d).sql
   ```

---

## 📚 相关文档

- `POSTGRESQL_MIGRATION_PROGRESS.md` - 迁移进度报告
- `DATABASE_RECOMMENDATION_SUMMARY.md` - 为什么选择 PostgreSQL
- `DATABASE_ANALYSIS.md` - 详细技术分析
- `POSTGRESQL_MIGRATION_SESSION_2.md` - 第二阶段迁移日志

---

## ✅ 验证清单

- ✅ PostgreSQL 已安装 (17.5)
- ✅ 数据库 stockdb 已创建
- ✅ 26 个表已创建
- ✅ postgres 用户已设置密码
- ✅ 本地应用能正常连接
- ✅ `.env` 配置已更新

---

## 🎯 下一步

现在本地开发环境已完全配置，可以：

1. **启动应用**: `npm run dev` (前端) + 后端启动
2. **运行测试**: `pytest backend/tests/`
3. **进行数据迁移**: 从 MySQL 迁移数据到 PostgreSQL
4. **进行开发**: 开始新的功能开发

---

**最后更新**: 2025-11-13
**状态**: 生产就绪 ✅
