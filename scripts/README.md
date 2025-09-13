# 🛠️ 股票分析系统 - 脚本中心

## 📋 脚本索引

### 🚀 部署脚本
- [📦 deploy.sh](./deployment/deploy.sh) - 主部署脚本，支持完整部署和迁移模式
- [▶️ start.sh](./deployment/start.sh) - 启动所有服务
- [⏹️ stop.sh](./deployment/stop.sh) - 停止所有服务
- [📊 status.sh](./deployment/status.sh) - 系统状态检查
- [🔨 build.sh](./deployment/build.sh) - 项目构建脚本
- [🏭 production-build.sh](./deployment/production-build.sh) - 生产环境构建
- [🎯 start-frontend-fixed.sh](./deployment/start-frontend-fixed.sh) - 固定端口前端启动

### 🗄️ 数据库脚本
- [📊 init.sql](./database/init.sql) - 数据库初始化SQL
- [⚡ mysql_performance.cnf](./database/mysql_performance.cnf) - MySQL性能优化配置
- [🔍 optimize_indexes.sql](./database/optimize_indexes.sql) - 索引优化SQL
- [💳 payment_tables.sql](./database/payment_tables.sql) - 支付系统表结构
- [📁 simple_import.sql](./database/simple_import.sql) - 简单导入相关表
- [👤 create_admin.py](./database/create_admin.py) - 创建管理员账户
- [👥 create_admin_table.py](./database/create_admin_table.py) - 创建管理员表
- [📊 create_daily_trading_tables.py](./database/create_daily_trading_tables.py) - 创建交易数据表
- [🆔 create_superuser.py](./database/create_superuser.py) - 创建超级用户
- [📋 init_sample_data.py](./database/init_sample_data.py) - 初始化示例数据
- [👥 init_user_tables.py](./database/init_user_tables.py) - 初始化用户表
- [🔄 migrate_stock_codes.py](./database/migrate_stock_codes.py) - 股票代码迁移

### 🔧 开发脚本
- [🔍 deploy-diagnostics.sh](./development/deploy-diagnostics.sh) - 部署诊断脚本
- [🛠️ fix-environment.sh](./development/fix-environment.sh) - 环境修复脚本
- [🔄 test_migration.sh](./development/test_migration.sh) - 迁移测试脚本

## 📁 脚本目录结构

```
scripts/
├── README.md                    # 脚本索引（本文件）
├── deployment/                  # 部署相关脚本
│   ├── deploy.sh                # 主部署脚本
│   ├── start.sh                 # 启动服务
│   ├── stop.sh                  # 停止服务
│   ├── status.sh                # 状态检查
│   ├── build.sh                 # 项目构建
│   ├── production-build.sh      # 生产构建
│   └── start-frontend-fixed.sh  # 固定端口前端启动
├── database/                    # 数据库相关脚本
│   ├── init.sql                 # 数据库初始化
│   ├── *.cnf                    # 配置文件
│   ├── *.sql                    # SQL脚本
│   └── *.py                     # Python数据库脚本
└── development/                 # 开发相关脚本
    ├── deploy-diagnostics.sh    # 部署诊断
    ├── fix-environment.sh       # 环境修复
    └── test_migration.sh        # 迁移测试
```

## 🚀 使用指南

### 首次部署
```bash
# 1. 完整部署（包含环境检查、依赖安装、数据库初始化）
./scripts/deployment/deploy.sh

# 2. 启动所有服务
./scripts/deployment/start.sh

# 3. 检查系统状态
./scripts/deployment/status.sh
```

### 日常运维
```bash
# 启动服务
./scripts/deployment/start.sh

# 停止服务
./scripts/deployment/stop.sh

# 检查状态
./scripts/deployment/status.sh

# 数据库迁移模式部署
./scripts/deployment/deploy.sh --migrate
```

### 开发环境
```bash
# 环境诊断
./scripts/development/deploy-diagnostics.sh

# 环境修复
./scripts/development/fix-environment.sh

# 测试迁移
./scripts/development/test_migration.sh
```

### 数据库管理
```bash
# 创建管理员账户
cd scripts/database && python create_admin.py

# 初始化示例数据
cd scripts/database && python init_sample_data.py

# 股票代码迁移
cd scripts/database && python migrate_stock_codes.py
```

## ⚡ 脚本特性

### 部署脚本特性
- 🔍 **环境检查**: 自动检查Node.js、Python、MySQL等依赖
- 🛡️ **错误处理**: 完善的错误处理和回滚机制
- 📊 **进度显示**: 清晰的部署进度和状态提示
- 🔧 **模式支持**: 支持完整部署、迁移模式等不同场景
- 📝 **日志记录**: 详细的操作日志和错误信息

### 数据库脚本特性
- 🔄 **事务安全**: 数据库操作使用事务保护
- 📊 **性能优化**: 包含索引优化和性能配置
- 🛡️ **数据保护**: 迁移脚本保护现有数据
- 🔧 **灵活配置**: 支持不同环境的配置参数

### 开发脚本特性
- 🔍 **问题诊断**: 自动诊断常见的环境问题
- 🛠️ **自动修复**: 尝试自动修复常见配置问题
- 📋 **详细报告**: 提供详细的诊断和修复报告

## 🔧 脚本使用规范

### 执行权限
```bash
# 给脚本添加执行权限
chmod +x scripts/deployment/*.sh
chmod +x scripts/development/*.sh
```

### 环境要求
- **操作系统**: macOS / Linux
- **Shell**: Bash 4.0+
- **权限**: 当前用户需要有相应的文件和服务操作权限

### 安全注意事项
- 🔐 **敏感信息**: 脚本中不包含硬编码的敏感信息
- 🛡️ **权限控制**: 脚本执行前会检查必要的权限
- 📝 **日志审计**: 重要操作会记录到日志文件
- 🔍 **参数验证**: 脚本会验证输入参数的合法性

## 🆘 故障排除

### 常见问题
1. **权限错误**: 确保脚本有执行权限 `chmod +x script_name.sh`
2. **环境依赖**: 运行诊断脚本检查环境 `./scripts/development/deploy-diagnostics.sh`
3. **端口占用**: 使用停止脚本清理 `./scripts/deployment/stop.sh`
4. **数据库连接**: 检查MySQL服务状态和连接配置

### 获取帮助
```bash
# 查看脚本帮助信息
./scripts/deployment/deploy.sh --help

# 查看系统状态
./scripts/deployment/status.sh

# 运行诊断
./scripts/development/deploy-diagnostics.sh
```

## 📝 脚本开发规范

### 编码规范
- 使用Bash编写，兼容性良好
- 函数命名使用下划线分隔
- 变量使用大写字母
- 添加充分的注释说明

### 错误处理
- 使用`set -e`确保错误时退出
- 重要操作前检查前置条件
- 提供清晰的错误信息
- 支持操作回滚

### 日志记录
- 使用统一的日志格式
- 区分INFO、WARNING、ERROR级别
- 记录关键操作和时间戳
- 日志文件自动轮转

---

**脚本维护**: 技术团队 | **最后更新**: 2025-09-13 | **版本**: v2.6.0