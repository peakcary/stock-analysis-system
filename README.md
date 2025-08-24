# 股票分析系统 (Stock Analysis System)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

一个功能完整的股票分析系统，包含用户管理、支付系统、数据分析等功能。

## 🚀 项目特性

- **用户系统**: 完整的注册/登录、JWT认证、会员等级管理
- **支付系统**: 微信支付集成，4个套餐配置，自动会员升级
- **数据分析**: 支持股票数据查询、概念分析、数据可视化
- **响应式UI**: 基于 Ant Design 的现代化界面设计
- **一键部署**: 完整的部署脚本，快速搭建开发环境

## 🏗️ 技术架构

- **后端**: Python + FastAPI + SQLAlchemy + MySQL + JWT
- **前端**: React 18 + TypeScript + Ant Design + Vite
- **数据库**: MySQL 8.0
- **认证**: JWT Token 认证系统
- **支付**: 微信支付 API 集成

## 📁 项目结构

```
stock-analysis-system/
├── backend/                 # Python 后端
│   ├── app/                # 应用核心代码
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile         # 后端容器配置
├── frontend/               # React 前端
│   ├── src/               # 前端源代码
│   ├── package.json       # 前端依赖
│   └── Dockerfile         # 前端容器配置
├── database/               # 数据库相关
│   └── init.sql           # 数据库初始化脚本
├── docs/                   # 项目文档
├── docker-compose.yml      # Docker 编排配置
└── README.md              # 项目说明
```

## 🚀 快速开始

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

### 支付系统
- 微信支付完整集成
- 4个套餐配置管理
- 支付状态跟踪和轮询
- 支付成功自动升级会员
- 订单管理和通知处理

### 前端界面
- 响应式设计 (支持移动端)
- 会员中心页面 (直接展示套餐)
- 支付流程界面 (二维码支付)
- 用户状态显示 (会员等级、剩余次数)

## 🔧 开发指南

详细的开发文档请查看：
- [项目开发指南](docs/PROJECT_DEVELOPMENT_GUIDE.md)
- [当前开发状态](docs/CURRENT_STATUS.md)

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