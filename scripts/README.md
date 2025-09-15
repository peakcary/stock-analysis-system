# 脚本说明

## 部署脚本 (scripts/deployment/)

### 主要脚本
- `deploy.sh` - 系统部署（首次安装和更新）
- `start.sh` - 启动所有服务
- `stop.sh` - 停止所有服务
- `status.sh` - 检查服务状态

### 使用方法
```bash
# 首次部署
./scripts/deployment/deploy.sh

# 仅更新数据库
./scripts/deployment/deploy.sh --migrate

# 启动服务
./scripts/deployment/start.sh
```

## 数据库脚本 (scripts/database/)

### 核心脚本
- `sync_model_definitions.py` - 自动同步SQLAlchemy模型定义
- `deploy_optimization.sh` - 数据库性能优化部署
- `create_daily_trading_tables.py` - 创建核心数据表

### 其他脚本
大部分为内部使用，由部署脚本自动调用，无需手动执行。

## 快速参考

```bash
# 问题修复
./scripts/deployment/deploy.sh --migrate

# 服务管理
./scripts/deployment/start.sh
./scripts/deployment/stop.sh
./scripts/deployment/status.sh

# 帮助信息
./scripts/deployment/deploy.sh --help
```