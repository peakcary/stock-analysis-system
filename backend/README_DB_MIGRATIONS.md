# 数据库迁移（Alembic）使用说明

本项目后端使用 Alembic 管理“核心表结构”的演进（用户、管理员、支付、交易与概念汇总等）。动态文件类型（如 `ttv`、`eee`）由运行时的动态表管理器维护，不纳入 Alembic 迁移。

## 目录布局
- `backend/alembic.ini`：Alembic 配置文件（从 `backend/` 目录执行命令）
- `backend/alembic/`：迁移脚本目录
  - `env.py`：运行环境配置，自动读取 `DATABASE_URL`
  - `versions/`：迁移版本目录

## 准备
1. 复制环境变量文件并配置数据库连接：
   ```bash
   cp backend/.env.example backend/.env
   # 设置 DATABASE_URL，例如：
   # DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/stock_analysis_dev
   ```
2. 安装后端依赖（已包含 Alembic）：
   ```bash
   cd backend && pip install -r requirements.txt
   ```

## 常用命令（在 backend/ 目录下执行）
- 升级到最新版本：
  ```bash
  alembic upgrade head
  ```
- 回滚上一个版本：
  ```bash
  alembic downgrade -1
  ```
- 新增迁移（自动检测模型变更，需确保 `app.models.*` 正确导入到 `Base`）：
  ```bash
  alembic revision --autogenerate -m "描述本次变更"
  ```

## 说明
- 首次迁移脚本：`versions/20251009_000001_initial_core_tables.py`，创建核心表与主要索引。
- 动态文件类型：仍由应用在启动时通过 `FileTypeRegistry` 初始化（不在 Alembic 管理范围内）。
- 生产部署：建议在部署脚本中加入 `alembic upgrade head`，确保表结构与版本一致。

## 常见问题
- 连接失败：检查 `DATABASE_URL` 是否可连、数据库用户权限是否足够（建表/索引）。
- 自动生成失败：确认 `env.py` 的 `target_metadata` 指向 `app.core.database.Base.metadata`，且相关模型已被导入。
- 动态表缺失：动态表不由 Alembic 管理，需通过应用启动的生命周期钩子或专用脚本初始化。
