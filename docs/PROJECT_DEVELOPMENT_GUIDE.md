# 股票概念分析系统开发指南

## 项目概览

**项目名称**: 股票概念分析系统 (Stock Concept Analysis System)  
**技术栈**: Python (FastAPI) + React + MySQL  
**开发模式**: 前后端分离  
**部署方式**: Docker容器化  

---

## 📋 项目状态追踪

### 当前开发状态
- **项目阶段**: 🏗️ 正在创建项目结构
- **当前日期**: 2025-08-21
- **当前任务**: 阶段一 - 环境搭建
- **完成度**: 5% (项目结构创建中)

### 开发进度记录
```
2025-08-21 开始: 
✅ 完成系统架构设计
✅ 完成技术栈选型 (FastAPI + React + MySQL)
✅ 完成服务器需求分析
🏗️ 正在创建项目结构

当前正在进行:
🔄 创建项目目录结构
🔄 设置后端Python环境
🔄 创建React前端项目
🔄 配置Docker环境

下次继续开发时请查看: docs/CURRENT_STATUS.md
```

---

## 🏗️ 系统架构

### 技术架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React前端     │────│   FastAPI后端   │────│   MySQL数据库    │
│  (端口: 3000)   │    │  (端口: 8000)   │    │  (端口: 3306)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 目录结构
```
stock-analysis-system/
├── backend/                 # Python后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI应用入口
│   │   ├── config/         # 配置文件
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── crud/           # 数据库操作
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心功能
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile
├── frontend/               # React前端
│   ├── public/
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── store/          # Redux状态管理
│   │   ├── services/       # API服务
│   │   ├── utils/          # 工具函数
│   │   └── types/          # TypeScript类型
│   ├── package.json
│   └── Dockerfile
├── database/               # 数据库相关
│   ├── init.sql           # 初始化脚本
│   └── migrations/        # 迁移脚本
├── docs/                  # 项目文档
│   ├── PROJECT_DEVELOPMENT_GUIDE.md  # 开发指南
│   ├── CURRENT_STATUS.md             # 当前状态
│   ├── API_DOCUMENTATION.md          # API文档
│   └── DEPLOYMENT_GUIDE.md           # 部署指南
├── docker-compose.yml     # Docker编排
└── README.md             # 项目说明
```

---

## 📋 数据导入功能说明

### 数据导入逻辑设计

#### CSV文件导入 - 股票基础信息
- **文件类型**: CSV格式文件
- **导入内容**: 股票代码、名称、行业、概念等基础信息  
- **导入模式**: 增量更新模式
- **处理逻辑**:
  - 概念关联：增量添加新关系，不删除旧关系
  - 股票信息：完全覆盖，使用最新CSV数据  
  - 新建数据：自动创建新股票和新概念
  - 文件限制：最大100MB

#### TXT文件导入 - 每日热度数据  
- **文件类型**: TXT格式文件（制表符分隔）
- **导入内容**: 股票代码、日期、热度值等每日数据
- **导入模式**: 完全覆盖模式
- **处理逻辑**:
  - 日期检测：智能从文件内容中提取日期
  - 数据覆盖：基于日期完全删除旧数据后导入新数据
  - 数据纠正：支持重新导入同一日期数据进行纠正
  - 文件限制：最大50MB

#### 导入结果统计
- **导入记录统计**: 显示成功导入的记录数量
- **跳过记录统计**: 显示跳过处理的记录数量  
- **错误记录统计**: 显示导入失败的记录及错误信息
- **导入文件信息**: 显示导入的文件名和导入时间
- **覆盖模式标识**: 标识是新增导入还是覆盖导入

---

## 💾 数据库设计

### 核心表结构

#### 1. 股票基本信息表 (stocks)
```sql
CREATE TABLE stocks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) UNIQUE NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    industry VARCHAR(100) COMMENT '行业',
    is_convertible_bond BOOLEAN DEFAULT FALSE COMMENT '是否为转债',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_stock_code (stock_code),
    INDEX idx_convertible_bond (is_convertible_bond)
);
```

#### 2. 概念表 (concepts)
```sql
CREATE TABLE concepts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_name VARCHAR(100) UNIQUE NOT NULL COMMENT '概念名称',
    description TEXT COMMENT '概念描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_concept_name (concept_name)
);
```

#### 3. 股票概念关联表 (stock_concepts)
```sql
CREATE TABLE stock_concepts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_id INT NOT NULL,
    concept_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_stock_concept (stock_id, concept_id),
    INDEX idx_stock_id (stock_id),
    INDEX idx_concept_id (concept_id)
);
```

#### 4. 每日股票数据表 (daily_stock_data)
```sql
CREATE TABLE daily_stock_data (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stock_id INT NOT NULL,
    trade_date DATE NOT NULL COMMENT '交易日期',
    pages_count INT DEFAULT 0 COMMENT '页数',
    total_reads INT DEFAULT 0 COMMENT '总阅读数',
    price DECIMAL(10, 2) DEFAULT 0 COMMENT '价格',
    turnover_rate DECIMAL(5, 2) DEFAULT 0 COMMENT '换手率',
    net_inflow DECIMAL(15, 2) DEFAULT 0 COMMENT '净流入',
    heat_value DECIMAL(15, 2) DEFAULT 0 COMMENT '热度值',
    FOREIGN KEY (stock_id) REFERENCES stocks(id),
    UNIQUE KEY unique_stock_date (stock_id, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_stock_date (stock_id, trade_date)
);
```

#### 5. 每日概念排名表 (daily_concept_rankings)
```sql
CREATE TABLE daily_concept_rankings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_id INT NOT NULL,
    stock_id INT NOT NULL,
    trade_date DATE NOT NULL,
    rank_in_concept INT NOT NULL,
    heat_value DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    FOREIGN KEY (stock_id) REFERENCES stocks(id) ON DELETE CASCADE,
    UNIQUE KEY unique_concept_stock_date (concept_id, stock_id, trade_date),
    INDEX idx_concept_date (concept_id, trade_date),
    INDEX idx_trade_date_rank (trade_date, rank_in_concept)
);
```

#### 6. 每日概念总和表 (daily_concept_sums)
```sql
CREATE TABLE daily_concept_sums (
    id INT PRIMARY KEY AUTO_INCREMENT,
    concept_id INT NOT NULL,
    trade_date DATE NOT NULL,
    total_heat_value DECIMAL(15, 2) NOT NULL,
    stock_count INT NOT NULL,
    average_heat_value DECIMAL(15, 2) NOT NULL,
    is_new_high BOOLEAN DEFAULT FALSE,
    days_for_high_check INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE,
    UNIQUE KEY unique_concept_date (concept_id, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_new_high (trade_date, is_new_high),
    INDEX idx_concept_date (concept_id, trade_date)
);
```

#### 7. 用户表 (users)
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    membership_type ENUM('free', 'paid_10', 'monthly', 'quarterly', 'yearly') DEFAULT 'free',
    queries_remaining INT DEFAULT 10,
    membership_expires_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## 🔧 后端设计

### FastAPI应用结构

#### 1. 主应用配置 (main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="股票概念分析系统",
    description="Stock Concept Analysis System API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
```

#### 2. 核心API端点设计
```python
# 股票查询相关
GET  /api/v1/stocks/{stock_code}           # 查询单只股票信息
GET  /api/v1/stocks/{stock_code}/concepts  # 查询股票所属概念
GET  /api/v1/stocks/{stock_code}/chart     # 查询股票图表数据

# 概念查询相关  
GET  /api/v1/concepts                      # 查询所有概念
GET  /api/v1/concepts/{concept_name}/stocks # 查询概念下的股票
GET  /api/v1/concepts/top/{n}              # 查询前N个概念
GET  /api/v1/concepts/new-highs            # 查询创新高的概念

# 转债相关
GET  /api/v1/bonds                         # 查询转债列表
GET  /api/v1/bonds/{bond_code}             # 查询转债详情
GET  /api/v1/bonds/concepts                # 查询转债概念

# 用户系统
POST /api/v1/auth/register                 # 用户注册
POST /api/v1/auth/login                    # 用户登录
GET  /api/v1/users/profile                 # 用户资料
POST /api/v1/payments/create               # 创建支付订单

# 数据管理
POST /api/v1/data/import                   # 导入数据
GET  /api/v1/data/calculate                # 触发计算任务
```

---

## 🎨 前端设计

### React应用结构

#### 1. 主要页面组件
- **StockQuery.tsx** - 股票查询页面
- **ConceptAnalysis.tsx** - 概念分析页面  
- **BondAnalysis.tsx** - 转债分析页面

#### 2. 核心功能
- ECharts图表集成
- Ant Design UI组件
- Redux状态管理
- TypeScript类型安全

---

## 📝 开发任务清单

### 阶段一：环境搭建 (1-2天) - 当前阶段
- [🔄] 创建项目目录结构  
- [ ] 配置Python虚拟环境
- [ ] 安装后端依赖 (FastAPI, SQLAlchemy等)
- [ ] 创建React项目
- [ ] 安装前端依赖 (Ant Design, ECharts等)
- [ ] 配置Docker开发环境
- [ ] 数据库初始化

### 阶段二：后端核心功能 (3-5天)
- [ ] 数据模型定义
- [ ] 数据库迁移脚本
- [ ] 数据导入功能
- [ ] 基础CRUD操作
- [ ] 排名计算引擎
- [ ] 核心查询API

### 阶段三：前端界面开发 (4-6天)  
- [ ] 基础路由配置
- [ ] 股票查询界面
- [ ] 概念分析界面
- [ ] 转债分析界面
- [ ] 图表组件集成
- [ ] 状态管理集成

### 阶段四：用户系统 (2-3天)
- [ ] 用户注册登录
- [ ] JWT认证中间件
- [ ] 会员权限控制
- [ ] 查询次数限制

### 阶段五：支付集成 (2-3天)
- [ ] 支付宝SDK集成
- [ ] 微信支付集成
- [ ] 订单管理系统
- [ ] 支付回调处理

### 阶段六：优化部署 (2-3天)
- [ ] 性能优化
- [ ] Docker生产配置
- [ ] 监控日志配置
- [ ] 项目部署

---

## 📞 下次开发对接说明

**重要**: 下次继续开发时，请按以下步骤：

1. **查看当前状态**: 阅读 `docs/CURRENT_STATUS.md`
2. **了解进度**: 查看开发任务清单中的完成情况
3. **继续开发**: 从未完成的任务开始
4. **更新文档**: 完成阶段后更新 `docs/CURRENT_STATUS.md`

### 对接模板：
```
当前项目状态：[从 docs/CURRENT_STATUS.md 获取]
已完成阶段：阶段X
当前任务：具体任务描述
遇到问题：[如果有问题请描述]
需要实现：下一步功能
```

---

**📋 开发文档版本**: v1.0  
**📅 最后更新**: 2025-08-21  
**👨‍💻 当前阶段**: 阶段一 - 环境搭建
**📍 下次重点**: 继续完成项目结构创建