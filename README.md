# 股票概念分析系统

一个基于 FastAPI + React + MySQL 的股票概念数据分析和查询系统。

## 🚀 项目特性

- **数据导入**: 支持 CSV 和 TXT 格式的股票数据导入
- **排名计算**: 自动计算概念内股票每日排名和概念总和
- **多维查询**: 支持股票查询、概念分析、转债分析
- **图表展示**: 基于 ECharts 的数据可视化
- **会员系统**: 完整的用户注册、登录和会员权限管理
- **支付集成**: 支持支付宝和微信支付
- **容器化部署**: 基于 Docker 的一键部署

## 🏗️ 技术架构

- **后端**: Python + FastAPI + SQLAlchemy + MySQL
- **前端**: React + TypeScript + Ant Design + ECharts
- **数据库**: MySQL 8.0
- **部署**: Docker + Docker Compose

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

### 1. 环境要求

- Docker & Docker Compose
- Node.js 18+ (本地开发)
- Python 3.11+ (本地开发)

### 2. 使用 Docker 启动 (推荐)

```bash
# 克隆项目
cd stock-analysis-system

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

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

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:3306

## 📊 主要功能

### 1. 股票查询界面
- 输入股票代码查询股票信息
- 显示股票所属的所有概念（按热度排序）
- 点击概念查看该概念下的所有股票
- 显示股票在概念中的排名走势图

### 2. 概念分析界面
- 查询指定天数内创新高的概念
- 显示概念的热度总和和排名变化
- 查询前N个概念的所有股票

### 3. 转债分析界面
- 专门针对转债（1开头代码）的分析
- 转债概念排行和图表展示

### 4. 会员系统
- 免费用户: 10次查询限制
- 付费套餐: 100元/10次，998元/月，2888元/季度，8888元/年

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
**最后更新**: 2025-08-21