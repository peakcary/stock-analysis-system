# 股票分析系统 (Stock Analysis System)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Architecture](https://img.shields.io/badge/Architecture-Optimized-success.svg)](#)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](#)

一个功能完整的股票分析系统，包含用户管理、支付系统、数据分析等功能。**已完成架构优化，适合100人以下规模使用。**

## 🚀 项目特性

### 核心功能
- **🔐 用户系统**: 完整的注册/登录、JWT认证、会员等级管理
- **💳 支付系统**: 微信支付集成，4个套餐配置，自动会员升级
- **📊 数据分析**: 支持股票数据查询、概念分析、数据可视化
- **📱 响应式UI**: 基于 Ant Design 的现代化界面设计
- **🚀 一键部署**: 完整的部署脚本，快速搭建开发环境

### 🆕 最新更新 (2025-09-06)
- **🗑️ 删除功能**: 完善的单个/批量删除功能，美观确认对话框，数据完整性保证
- **🎨 界面优化**: 移除冗余统计，概念显示优化，导入区域美化
- **🔧 技术修复**: 登录系统修复，Modal对话框兼容性，API路由优化
- **📱 用户体验**: 响应式设计，加载状态，错误处理，操作反馈完善

### 历史更新 (2025-08-30)
- **🔒 安全增强**: 移除硬编码密码，环境变量管理，安全部署方案
- **⚡ 性能优化**: 数据库连接池优化，索引策略，Redis缓存方案  
- **🧹 代码质量**: API路由统一，**彻底解决enum映射问题**，共享模块建立
- **📋 双前端架构**: 管理端(8006)和用户端(8005)清晰分离
- **💳 支付系统**: **完全修复**数据库结构问题，支付订单创建正常，模拟支付可用

## 🏗️ 技术架构

- **后端**: Python + FastAPI + SQLAlchemy + MySQL + JWT
- **前端**: React 18 + TypeScript + Ant Design + Vite
- **数据库**: MySQL 8.0
- **认证**: JWT Token 认证系统
- **支付**: 微信支付 API 集成

## 📁 项目结构

```
stock-analysis-system/
├── backend/                    # Python 后端
│   ├── app/
│   │   ├── api/               # API路由 (统一在/api/v1)
│   │   ├── core/              # 核心配置和缓存
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic模式
│   │   └── services/          # 业务逻辑
│   ├── requirements.txt       # Python 依赖
│   └── Dockerfile            # 后端容器配置
├── client/                    # React 用户端 (端口8005)
│   ├── src/pages/            # 用户页面 (分析、会员、支付)
│   └── package.json          # 前端依赖
├── frontend/                  # React 管理端 (端口8006)  
│   ├── src/components/       # 管理功能 (用户、套餐、数据)
│   └── package.json          # 前端依赖
├── shared/                    # 共享模块
│   ├── auth.ts               # 统一认证工具
│   ├── types.ts              # 共享类型定义
│   └── package.json          # 共享依赖
├── database/                  # 数据库相关
│   ├── init.sql              # 数据库初始化
│   ├── optimize_indexes.sql  # 索引优化脚本
│   └── mysql_performance.cnf # 性能配置
├── docs/                      # 项目文档
├── .env.example              # 环境变量模板
├── deploy-secure.sh          # 安全部署脚本
├── ARCHITECTURE_OPTIMIZATION_FINAL.md  # 架构优化报告
└── README.md                 # 项目说明
```

## 📊 系统状态

### 整体评价: ⭐⭐⭐⭐☆ (4.2/5)
- **适用规模**: 100人以下访问量 ✅
- **架构状态**: 已优化，生产就绪
- **安全等级**: 基础安全完善
- **维护难度**: 低，自动化部署

### 应用访问
- **用户端**: http://localhost:8005 - 股票查询、会员购买
- **管理端**: http://localhost:8006 - 系统管理、数据导入  
- **API文档**: http://localhost:3007/docs - Swagger接口文档

## 🚀 快速开始

### 环境要求
- **Python**: 3.8+
- **Node.js**: 18+
- **MySQL**: 8.0+
- **系统**: Linux/macOS/Windows

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd stock-analysis-system

# 运行一键部署脚本
chmod +x deploy.sh
./deploy.sh

# 启动所有服务
./start_all.sh
```

### 环境要求

- Python 3.8+ 
- Node.js 16+
- MySQL 8.0
- Git

### 3. 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 数据库初始化

```bash
# 启动 MySQL 容器
docker run --name mysql-dev -e MYSQL_ROOT_PASSWORD=root123 -p 3306:3306 -d mysql:8.0

# 导入初始化脚本
docker exec -i mysql-dev mysql -uroot -proot123 < database/init.sql
```

## 🌐 访问地址

- **用户前端**: http://localhost:3001
- **管理前端**: http://localhost:3000  
- **API 文档**: http://localhost:8000/docs
- **API 根路径**: http://localhost:8000/api/v1

## 📊 支付套餐

| 套餐名称 | 价格 | 查询次数 | 有效期 | 会员等级 |
|---------|-----|---------|-------|---------|
| 10次查询包 | ¥100.00 | 10次 | 30天 | 免费版 |
| 专业版月卡 | ¥998.00 | 1000次 | 30天 | 专业版 |
| 专业版季卡 | ¥2888.00 | 3000次 | 90天 | 专业版 |
| 专业版年卡 | ¥8888.00 | 12000次 | 365天 | 专业版 |

## ✅ 已实现功能

### 用户系统
- 用户注册/登录 (JWT认证)
- 会员等级管理 (免费版/专业版)
- 查询次数限制和跟踪
- 用户状态管理

### 支付系统 ✅ 
- 微信支付完整集成 (支持模拟模式)
- 支付订单创建和管理 **已修复**
- 支付状态跟踪和轮询
- 支付成功自动升级会员
- 订单管理和通知处理
- **新增**: 管理员订单管理界面
- **新增**: 支付监控和告警系统
- **新增**: 用户会员权限管理服务

### 前端界面
- 响应式设计 (支持移动端)
- 会员中心页面 (直接展示套餐)
- 支付流程界面 (二维码支付)
- 用户状态显示 (会员等级、剩余次数)

## 🔧 开发指南

### 🛠️ 关键问题解决

#### Enum映射问题修复 (2025-08-30)
**问题**: SQLAlchemy Enum类型与数据库值不匹配，导致 `LookupError: Enum PaymentStatus cannot find value 'pending'`

**解决方案**:
1. **模型层**: 将所有 `Column(Enum(...))` 替换为 `Column(String(...))`
2. **常量类**: 使用 `PaymentStatus`、`PaymentMethod` 等常量类管理枚举值
3. **数据格式**: 统一使用小写字符串 (`pending`, `paid`, `wechat_native`)
4. **Schema层**: 更新Pydantic模型以匹配新的数据类型

**数据库修复**: 提供自动化脚本修复表结构，添加缺失的 `package_id` 字段

详细的开发文档请查看：
- [项目开发指南](docs/PROJECT_DEVELOPMENT_GUIDE.md)
- [当前开发状态](docs/CURRENT_STATUS.md)
- [微信支付配置指南](backend/WECHAT_PAYMENT_SETUP.md)

## 📝 API 文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的 API 文档。

## 🐳 Docker 部署

### 开发环境

```bash
# 启动开发环境
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 生产环境

```bash
# 使用生产配置启动
docker-compose --profile production up -d
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue: [GitHub Issues](https://github.com/your-username/stock-analysis-system/issues)
- 邮箱: your-email@example.com

---

**开发状态**: 🚧 开发中  
**最后更新**: 2025-08-25  
**版本**: v1.0-dev