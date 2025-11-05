# 🚀 快速参考卡 (Quick Reference)

## 📌 数据库连接信息速查

```
主机 (Host):      bj-cdb-k21a7ijs.sql.tencentcdb.com
端口 (Port):      27126
用户 (User):      root
密码 (Password):  Pp123456
数据库 (DB):      mydb
```

## 🔗 连接字符串

**Python (SQLAlchemy)**:
```
mysql+pymysql://root:Pp123456@bj-cdb-k21a7ijs.sql.tencentcdb.com:27126/mydb
```

**MySQL CLI**:
```bash
mysql -h bj-cdb-k21a7ijs.sql.tencentcdb.com -P 27126 -u root -p mydb
```

**JDBC (Java)**:
```
jdbc:mysql://bj-cdb-k21a7ijs.sql.tencentcdb.com:27126/mydb
```

---

## ⚡ 常用命令

### 启动后端服务

```bash
cd backend/
uvicorn app.main:app --host 0.0.0.0 --port 3007 --reload
```

### 测试数据库连接

```bash
cd backend/
PYTHONPATH=./:$PYTHONPATH python test_db_connection.py
```

### 执行数据库迁移

```bash
cd backend/
PYTHONPATH=./:$PYTHONPATH alembic upgrade head
```

### 查看迁移历史

```bash
cd backend/
PYTHONPATH=./:$PYTHONPATH alembic history
```

### 直接连接数据库

```bash
mysql -h bj-cdb-k21a7ijs.sql.tencentcdb.com -P 27126 -u root -p
# 密码: Pp123456
```

---

## 📁 关键文件

| 文件 | 位置 | 用途 |
|------|------|------|
| 配置 | `.env` | 生产环境配置 |
| 配置 | `.env.example` | 配置模板 |
| 配置 | `.env.production` | 生产环境配置 |
| 脚本 | `test_db_connection.py` | 连接测试 |
| 脚本 | `setup_database.sh` | 初始化脚本 |
| 文档 | `SETUP_COMPLETE.md` | 完整说明 |
| 文档 | `DATABASE_CONFIG_SUMMARY.md` | 配置说明 |

---

## 🎯 API 访问

**Swagger UI**: http://localhost:3007/docs
**ReDoc**: http://localhost:3007/redoc

---

## 🗄️ 数据库表列表

```
✅ users                       - 用户表
✅ admin_users                 - 管理员表
✅ payment_packages            - 支付套餐
✅ payment_orders              - 支付订单
✅ payment_notifications       - 支付通知
✅ payments                    - 支付记录
✅ refund_records              - 退款记录
✅ membership_logs             - 会员日志
✅ user_queries                - 查询记录
✅ daily_trading               - 每日交易数据
✅ stock_concept_ranking       - 股票概念排名
✅ concept_daily_summary       - 概念每日汇总
✅ concept_high_record         - 概念创高记录
✅ txt_import_record           - TXT导入记录
✅ alembic_version             - 迁移版本
```

---

## 🔑 环境变量

### 必需配置

```bash
# 数据库
DATABASE_URL=mysql+pymysql://root:Pp123456@bj-cdb-k21a7ijs.sql.tencentcdb.com:27126/mydb
DATABASE_HOST=bj-cdb-k21a7ijs.sql.tencentcdb.com
DATABASE_PORT=27126
DATABASE_USER=root
DATABASE_PASSWORD=Pp123456
DATABASE_NAME=mydb

# JWT
SECRET_KEY=your-secret-key-32-chars-min
ADMIN_SECRET_KEY=admin-secret-key-32-chars-min
```

### 支付配置 (可选)

```bash
WECHAT_APPID=your_appid
WECHAT_MCH_ID=merchant_id
WECHAT_API_KEY=api_key
PAYMENT_MOCK_MODE=true  # 开发时使用
```

---

## ⚙️ 配置优先级

1. **环境变量** (最高优先级)
2. **.env 文件**
3. **代码中的默认值**

---

## 🚨 常见问题速解

| 问题 | 解决方案 |
|------|---------|
| `ModuleNotFoundError: app` | `PYTHONPATH=./:$PYTHONPATH` |
| 无法连接数据库 | 检查网络、主机、端口、凭证 |
| 端口被占用 | `uvicorn app.main:app --port 3008` |
| 权限被拒绝 | 检查数据库用户权限 |
| 迁移失败 | 运行 `PYTHONPATH=./:$PYTHONPATH alembic upgrade head` |

---

## 📊 性能指标

- **连接池大小**: 10
- **最大溢出**: 20
- **连接超时**: 30 秒
- **连接回收**: 3600 秒

---

## 🔒 安全提示

⚠️ **不要**:
- ❌ 提交 `.env` 文件到 Git
- ❌ 在代码中硬编码密码
- ❌ 使用弱密码
- ❌ 在生产环境使用 `root` 用户

✅ **应该**:
- ✅ 使用环境变量管理敏感信息
- ✅ 定期备份数据库
- ✅ 启用 SSL 连接
- ✅ 创建专用应用用户

---

## 🔄 迁移快速参考

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade 20251009_000001

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看历史记录
alembic history

# 创建新迁移
alembic revision --autogenerate -m "description"
```

---

## 📞 调试技巧

### 启用 SQL 日志

```python
# 在 core/database.py 中
engine = create_engine(DATABASE_URL, echo=True)  # 打印所有 SQL
```

### 查询性能分析

```bash
# 连接数据库后执行
SET SESSION sql_mode='TRADITIONAL';
EXPLAIN SELECT * FROM users WHERE id = 1;
```

### 检查连接状态

```bash
mysql -h bj-cdb-k21a7ijs.sql.tencentcdb.com -P 27126 -u root -p -e "SHOW PROCESSLIST;"
```

---

## 📈 数据库优化建议

1. **定期检查慢查询日志**
2. **维护表索引**
3. **定期执行 OPTIMIZE TABLE**
4. **监控连接数和内存使用**
5. **定期备份数据**

---

## 🎓 学习资源

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [MySQL 官方文档](https://dev.mysql.com/doc/)

---

**最后更新**: 2025-11-04
**状态**: ✅ 可用
