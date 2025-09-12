# 📊 股票分析系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

一个功能完整的股票分析系统，支持股票数据查询、概念分析、用户管理和支付系统。

## 🚀 快速开始

### 💡 只需3步，开箱即用：

```bash
# 1️⃣ 环境部署（首次使用）
./deploy.sh

# 2️⃣ 启动服务
./start.sh

# 3️⃣ 访问系统
# 管理端：http://localhost:8006 (admin/admin123)
# 客户端：http://localhost:8005
```

### 🔧 环境要求

**必需软件**：
- **Node.js** 16+ (JavaScript运行环境)
- **Python** 3.8+ (推荐3.10-3.12，兼容性最佳)
- **MySQL** 8.0+ (数据库服务)

**一键安装 (macOS)**：
```bash
# 安装Node.js和MySQL
brew install node mysql
brew services start mysql

# 克隆项目并部署
git clone <your-repo>
cd stock-analysis-system
./deploy.sh
```

### ⚡ 快速故障排除

**常见问题解决**：
- **部署卡住**: Python版本过新/过老，建议使用Python 3.10-3.12
- **MySQL连接失败**: 运行 `mysqladmin ping` 检查MySQL服务状态
- **端口占用**: 运行 `./stop.sh` 清理进程后重新启动

## 🛠️ 核心功能

### 📈 股票分析 ⭐ v2.4.1增强
- 🔍 **个股分析**: 支持SH/SZ/BJ前缀格式，概念按交易量排序
- 📊 **概念分析**: 全新卡片式界面，支持展开查看股票排名
- 📋 **数据导入**: TXT文件批量导入，支持股票代码标准化
- 📱 **智能界面**: 响应式设计，数字格式化，优雅错误处理

### 👥 用户系统
- 🔐 用户注册、登录、JWT认证
- 👑 会员等级管理（免费/付费用户）
- 🎫 查询次数限制和套餐购买
- 📊 用户行为统计

### 💳 支付系统
- 💸 微信支付集成
- 📦 4个套餐配置（10次/100次/1000次/无限次）
- 🔄 自动会员升级和权限管理
- 📝 支付记录和退款管理

### 👨‍💼 管理系统 ⭐ v2.4.2重构
- 🏠 独立管理端后台 (端口8006)
- 🔐 **统一认证架构**: JWT自动刷新，token安全管理
- 👥 **用户管理分离**: 客户端用户 vs 管理员账户
- 🛡️ **权限级控制**: 超级管理员权限，角色管理
- 📊 数据管理、系统监控

## 🏗️ 技术架构

```
前端架构：
├── 管理端 (8006) - React + Ant Design - 管理员后台
├── 客户端 (8005) - React + Ant Design - 用户端界面
└── 共享组件 - TypeScript + 响应式设计

后端架构：
├── FastAPI + SQLAlchemy - REST API 服务 (3007)
├── MySQL 8.0 - 关系型数据库
├── JWT 认证 - 安全认证系统
└── 微信支付API - 第三方支付集成
```

## 📋 系统管理

### 🔧 可用脚本

| 脚本 | 功能 | 使用方式 |
|------|------|----------|
| `deploy.sh` | 环境部署 | `./deploy.sh` (完整部署)<br>`./deploy.sh --migrate` (仅迁移) |
| `start.sh` | 启动服务 | `./start.sh` |
| `stop.sh` | 停止服务 | `./stop.sh` |
| `status.sh` | 状态检查 | `./status.sh` |

### 🌐 服务地址

| 服务 | 端口 | 地址 | 说明 |
|------|------|------|------|
| API服务 | 3007 | http://localhost:3007 | 后端API接口 |
| 管理端 | 8006 | http://localhost:8006 | 管理员后台 |
| 客户端 | 8005 | http://localhost:8005 | 用户前端界面 |

### 👤 默认账号

- **管理员**: `admin` / `admin123` (管理端登录，无查询限制)
- **客户端**: 需要注册新账号 (有查询限制，需购买套餐)

## 📚 详细文档

### 🔗 快速导航
- [📖 脚本使用指南](./docs/SCRIPTS_GUIDE.md) - 部署脚本详细说明
- [📥 TXT导入指南](./docs/TXT_IMPORT_GUIDE.md) - 数据导入功能使用
- [💳 支付系统配置](./docs/PAYMENT_CONFIG.md) - 微信支付配置指南

## 🔧 开发环境

### 📋 环境要求
- Node.js 16+
- Python 3.8+
- MySQL 8.0+

### 🚀 首次部署
```bash
# 克隆项目
git clone <your-repo>
cd stock-analysis-system

# 环境检查和部署
./deploy.sh

# 启动服务
./start.sh
```

### 🔄 现有环境升级
```bash
# 数据库迁移（保留现有数据）
./deploy.sh --migrate

# 重启服务
./start.sh
```

## 🆕 版本更新

### v2.5.0 (2025-09-12) ⭐ 最新版本
- 📊 **页面功能重新规划**: 明确三个分析页面的功能定位和使用场景
- 🔍 **股票查询**: 输入单个股票代码，查看其在所有概念中的表现和排名
- 📈 **个股分析**: 展示指定日期所有股票列表，可查看每只股票的概念信息
- 🎯 **概念分析**: 展示指定日期所有概念列表，可查看每个概念的股票构成
- 🛠️ **新增调试API**: 添加概念交易量分析接口，便于数据验证和问题排查
- 📋 **概念排序优化**: 所有概念列表严格按总交易量排序，提升数据可读性
- 🔧 **数据一致性**: 统一股票代码匹配逻辑，确保概念汇总和排名数据准确

### v2.4.2 (2025-09-11)
- 🔐 **登录系统重构**: 解决401认证错误，实现JWT自动刷新机制
- 👥 **用户管理分离**: 明确区分客户端用户和管理员账户
- 🛡️ **权限控制增强**: 超级管理员权限，防止误操作自己账户
- 🔧 **管理员管理**: 完整的CRUD操作，密码重置，状态切换
- 🎨 **界面优化**: 管理后台菜单重构，用户友好的操作界面

### v2.4.1 (2025-09-08)
- 🚀 **个股分析增强**: 支持SH/SZ/BJ前缀股票代码，概念按交易量排序
- 🎨 **概念分析重构**: 全新卡片式界面，展开式股票排名查看
- 🛡️ **错误处理优化**: 优雅处理概念排名表缺失，智能股票代码转换
- 📊 **数据展示优化**: 数字格式化，彩色标签，响应式设计
- 🔧 **API接口增强**: 新增概念汇总和股票排名API接口

### v2.3.0 (2025-09-07)
- ✅ 集成migrate_database.sh到deploy.sh，简化部署流程
- ✅ 支持迁移模式 `./deploy.sh --migrate`
- ✅ 优化脚本使用体验

### v2.2.0 (2025-09-06)
- ✅ TXT文件导入功能
- ✅ 概念数据分析和排名
- ✅ 管理员认证系统
- ✅ 界面优化和用户体验提升

### v2.1.0 (2025-08-30)
- ✅ 完善支付系统数据库结构
- ✅ 双前端架构优化
- ✅ 安全性增强和性能优化

## 🚨 故障排除

### 🔧 部署问题

**deploy.sh卡在设置后端**：
```bash
# 原因：Python版本兼容性或网络问题
# 解决方案：
python3 --version  # 检查Python版本(推荐3.10-3.12)

# 手动创建虚拟环境(如果需要)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**MySQL相关问题**：
```bash
# 检查MySQL状态
brew services list | grep mysql
mysqladmin ping -h127.0.0.1

# 启动MySQL服务
brew services start mysql

# 设置root密码(首次安装)
mysql_secure_installation
```

### 🚀 服务问题

**端口被占用**：
```bash
./stop.sh  # 停止所有服务
./start.sh # 重新启动
```

**服务状态检查**：
```bash
./status.sh  # 详细的系统状态检查
```

**前端编译错误**：
```bash
# 清理并重新安装前端依赖
cd frontend && rm -rf node_modules && npm install
cd ../client && rm -rf node_modules && npm install
```

### 💡 环境检查

**完整环境检查脚本**：
```bash
# 检查所有必需软件
echo "Node.js: $(node --version 2>/dev/null || echo '❌ 未安装')"
echo "Python: $(python3 --version 2>/dev/null || echo '❌ 未安装')" 
echo "MySQL: $(mysql --version 2>/dev/null || echo '❌ 未安装')"
echo "Git: $(git --version 2>/dev/null || echo '❌ 未安装')"
```

## 📞 支持与反馈

遇到问题时：
1. 先运行 `./status.sh` 检查系统状态
2. 查看相关日志文件 `logs/` 目录
3. 提供详细的错误信息和系统状态

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)

---

💡 **提示**: 首次使用请按顺序运行 `./deploy.sh` → `./start.sh`，日常使用只需 `./start.sh` 启动即可。