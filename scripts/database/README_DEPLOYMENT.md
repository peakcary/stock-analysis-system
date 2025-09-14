# 🚀 数据库优化部署指南

## 📋 概述

本目录包含完整的数据库优化部署脚本和工具，支持一键部署和分步骤部署。

## 🛠️ 工具列表

### 1. 主要部署脚本

| 脚本名称 | 功能描述 | 使用场景 |
|---------|---------|----------|
| `deploy_optimization.sh` | **一键部署脚本** | 生产环境完整部署 |
| `database_manager.py` | **Python管理工具** | 开发环境和精细化管理 |
| `enable_optimization.py` | 优化功能开关 | 启用/禁用优化功能 |
| `smooth_migration_service.py` | 数据迁移工具 | 零停机数据迁移 |

### 2. SQL脚本

| 脚本名称 | 功能描述 |
|---------|----------|
| `create_optimized_tables.sql` | 创建优化表结构 |
| `create_views_and_indexes.sql` | 创建高性能视图和索引 |

## 🚀 快速部署（推荐）

### 方式一：Shell脚本一键部署

```bash
# 进入项目目录
cd /Users/cary/work/other/stock-analysis-system

# 执行一键部署
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev"
```

#### 高级选项

```bash
# 仅创建表结构（不迁移数据）
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --mode tables-only

# 仅迁移数据（表结构已存在）
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --mode migrate-only

# 强制执行（跳过确认）
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --force

# 跳过备份（加快部署速度）
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --skip-backup
```

### 方式二：Python工具部署

```bash
# 完整部署
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  deploy

# 查看详细状态报告
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  report
```

## 📊 分步骤部署

### 第一步：检查当前状态

```bash
# Shell方式
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --dry-run

# Python方式 
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  status
```

### 第二步：创建优化表结构

```bash
# Shell方式
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --mode tables-only

# Python方式
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  create-tables
```

### 第三步：迁移数据

```bash
# Shell方式
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --mode migrate-only

# Python方式（支持日期范围）
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  migrate --start-date "2025-09-01" --end-date "2025-09-13"
```

### 第四步：启用优化功能

```bash
# Shell方式
./scripts/database/deploy_optimization.sh \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --mode enable-only

# Python方式
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  enable --mode optimized

# 直接使用优化开关工具
python3 scripts/database/enable_optimization.py enable --mode optimized
```

### 第五步：性能测试和验证

```bash
# 性能测试
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  test --date "2025-09-02"

# 生成状态报告
python3 scripts/database/database_manager.py \
  --db-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  report
```

## 🔧 数据库管理命令

### 优化功能管理

```bash
# 检查优化状态
python3 scripts/database/enable_optimization.py status

# 启用优化（不同模式）
python3 scripts/database/enable_optimization.py enable --mode testing    # 测试模式
python3 scripts/database/enable_optimization.py enable --mode optimized  # 优化模式
python3 scripts/database/enable_optimization.py enable --mode production # 生产模式

# 禁用优化
python3 scripts/database/enable_optimization.py disable
```

### 数据迁移管理

```bash
# 完整数据迁移
python3 scripts/database/smooth_migration_service.py \
  --database-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev"

# 按日期范围迁移
python3 scripts/database/smooth_migration_service.py \
  --database-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --start-date "2025-09-01" --end-date "2025-09-13"

# 仅验证数据一致性
python3 scripts/database/smooth_migration_service.py \
  --database-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --verify-only

# 从中断点继续迁移
python3 scripts/database/smooth_migration_service.py \
  --database-url "mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev" \
  --resume
```

## 📊 API监控和测试

### 部署完成后的验证

```bash
# 检查优化状态API
curl "http://localhost:8000/api/v1/optimization/status"

# 性能对比测试API
curl "http://localhost:8000/api/v1/optimization/test"

# 查看迁移状态API
curl "http://localhost:8000/api/v1/optimization/migration-status"
```

## ⚠️ 常见问题和解决方案

### 1. 数据库连接失败

**问题**: `数据库连接失败`
**解决**: 检查数据库URL格式和权限

```bash
# 正确的URL格式
mysql+pymysql://用户名:密码@主机:端口/数据库名

# 示例
mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev
```

### 2. 迁移过程中断

**问题**: 迁移过程中断或失败
**解决**: 使用恢复模式继续迁移

```bash
python3 scripts/database/smooth_migration_service.py \
  --database-url "your-db-url" \
  --resume
```

### 3. 表已存在错误

**问题**: `Table 'xxx' already exists`
**解决**: 脚本会自动处理，或手动删除重新创建

```bash
# 查看现有表
mysql -u root -pPp123456 stock_analysis_dev -e "SHOW TABLES LIKE '%unified%'"

# 如需重新创建，先删除
mysql -u root -pPp123456 stock_analysis_dev -e "DROP TABLE IF EXISTS daily_trading_unified"
```

### 4. 性能提升不明显

**问题**: 部署后性能提升不明显
**解决**: 检查优化是否正确启用

```bash
# 检查环境变量
python3 scripts/database/enable_optimization.py status

# 确保USE_OPTIMIZED_TABLES=true
export USE_OPTIMIZED_TABLES=true

# 重启后端服务
```

## 📈 预期效果

### 性能提升指标

| 查询类型 | 优化前 | 优化后 | 提升倍数 |
|---------|--------|--------|----------|
| **股票列表查询** | 5-10秒 | 50-100ms | **50-200倍** |
| **概念排行查询** | 2-3秒 | 20-50ms | **60-150倍** |
| **分页查询** | 1-2秒 | 5-10ms | **100-400倍** |
| **股票概念查询** | 500ms | 10-20ms | **25-50倍** |

### 功能增强

- ✅ **预计算排名**: 数据导入时自动计算排名
- ✅ **创新高识别**: 自动识别创新高概念
- ✅ **内存缓存**: 当天数据缓存在内存中
- ✅ **趋势分析**: 交易量变化百分比计算
- ✅ **性能监控**: 查询性能自动记录

## 🔄 回滚方案

### 如需回滚到原始状态

```bash
# 禁用优化功能
python3 scripts/database/enable_optimization.py disable

# 重启后端服务
# 系统将自动使用原始表查询

# 如需完全清理优化表（可选）
mysql -u root -pPp123456 stock_analysis_dev << EOF
DROP TABLE IF EXISTS daily_trading_unified;
DROP TABLE IF EXISTS concept_daily_metrics;
DROP TABLE IF EXISTS stock_concept_daily_snapshot;
DROP TABLE IF EXISTS today_trading_cache;
EOF
```

## 📞 技术支持

### 日志文件位置

- 部署日志: `optimization_deployment.log`
- 迁移日志: `migration_state.json`
- 管理日志: `database_manager.log`

### 常用调试命令

```bash
# 查看详细状态
python3 scripts/database/database_manager.py \
  --db-url "your-db-url" report

# 测试性能对比
python3 scripts/database/database_manager.py \
  --db-url "your-db-url" test

# 检查环境配置
python3 scripts/database/enable_optimization.py status
```

---

**部署成功后，记得重启后端服务以加载新配置！** 🚀