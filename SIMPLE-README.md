# 📊 股票分析系统

一个功能完整的股票分析系统，包含用户管理、支付系统、数据分析等功能。

## 🚀 快速开始

### 四个核心脚本，简单易用：

```bash
# 1️⃣ 一键部署 - 环境检测、安装配置、数据库初始化
./deploy.sh

# 2️⃣ 一键启动 - 启动前后端服务  
./start.sh

# 3️⃣ 一键停止 - 停止所有服务
./stop.sh

# 4️⃣ 数据库初始化 - 独立的数据库管理脚本
./init-database.sh
```

### 🔥 首次使用流程：

1. **环境准备**：确保已安装 Node.js、Python3、MySQL
2. **一键部署**：`./deploy.sh` （自动检测环境、安装依赖、配置数据库）
3. **启动系统**：`./start.sh` （启动所有服务）
4. **开始使用**：访问 http://localhost:8005

### 🔄 日常开发流程：

```bash
./start.sh   # 启动开发环境
./stop.sh    # 停止所有服务
```

## 📋 系统要求

- **Node.js** v18+ 
- **Python3** v3.11+
- **MySQL** v8.0+
- **操作系统**: macOS / Linux / Windows

## 🎯 固定端口配置

- **API服务**: 3007 (FastAPI后端)
- **客户端**: 8005 (React用户端)
- **管理端**: 8006 (React管理端)

## 📊 访问地址

启动成功后，可访问以下地址：

| 服务 | 地址 | 标题 | 说明 |
|-----|------|-----|-----|
| 🔗 **API文档** | http://localhost:3007/docs | Stock Analysis API | Swagger接口文档 |
| 📱 **用户端** | http://localhost:8005 | 股票分析系统 | 股票查询、会员购买 |
| 🖥️ **管理端** | http://localhost:8006 | 股票分析系统 - 管理端 | 系统管理、数据导入 |

## 👤 默认账户

| 类型 | 用户名 | 密码 | 说明 |
|-----|-------|------|-----|
| 管理员 | admin | admin123 | 系统管理员账户 |

## 🔧 deploy.sh - 一键部署

**功能说明**:
- ✅ 环境依赖检测（Node.js、Python3、MySQL）
- ✅ 自动启动MySQL服务
- ✅ 数据库服务检测和表创建
- ✅ Python虚拟环境创建和依赖安装
- ✅ Node.js依赖安装
- ✅ 数据库表自动创建
- ✅ 前后端配置文件生成
- ✅ 端口代理配置

**首次使用**必须运行此脚本！

## ▶️ start.sh - 一键启动

**功能说明**:
- ✅ 检查端口占用并自动清理
- ✅ 启动后端API服务
- ✅ 启动客户端前端
- ✅ 启动管理端前端
- ✅ 服务状态检查
- ✅ 显示访问地址和日志位置

## 🛑 stop.sh - 一键停止

**功能说明**:
- ✅ 优雅停止所有服务进程
- ✅ 清理端口占用
- ✅ 删除PID文件
- ✅ 支持强制终止

## 🗄️ init-database.sh - 数据库初始化

**功能说明**:
- ✅ MySQL服务检测和启动
- ✅ 数据库连接测试
- ✅ 自动创建数据库（stock_analysis_dev）
- ✅ 执行初始化SQL脚本
- ✅ 使用SQLAlchemy创建数据表
- ✅ 执行所有database/*.sql脚本
- ✅ 创建默认管理员用户（admin/admin123）
- ✅ 数据库状态检查和报告

**使用场景**:
- 🔧 单独重置数据库
- 🆕 新环境数据库初始化
- 🔄 数据库结构更新
- 🐛 数据库问题排查

## 📝 日志查看

```bash
# 查看所有日志
tail -f logs/*.log

# 分别查看
tail -f logs/backend.log   # API服务日志
tail -f logs/client.log    # 客户端日志  
tail -f logs/frontend.log  # 管理端日志
```

## 🛠️ 故障排除

### 常见问题解决

#### 1. 环境问题
```bash
# macOS 安装依赖
brew install node python mysql@8.0

# 检查版本
node --version    # 应该 >= 18
python3 --version # 应该 >= 3.11
mysql --version   # 应该 >= 8.0
```

#### 2. 端口占用
```bash
./stop.sh         # 停止所有服务
./start.sh        # 重新启动
```

#### 3. 数据库问题
```bash
./init-database.sh  # 重新初始化数据库
```

#### 4. 登录问题
- 确保使用默认账户：`admin` / `admin123`
- 检查数据库是否正常初始化
- 查看API服务日志：`tail -f logs/backend.log`

#### 5. 前端无法访问
- 检查端口是否正确：8005(用户端)、8006(管理端)
- 确认API服务运行正常：http://localhost:3007/docs

### 重新部署
如需完全重新配置：
```bash
./stop.sh         # 停止服务
./deploy.sh       # 重新部署
./start.sh        # 启动服务
```

## 📝 使用场景

### 开发人员
```bash
# 首次设置
./deploy.sh

# 日常开发
./start.sh    # 开始工作
./stop.sh     # 结束工作

# 数据库管理
./init-database.sh  # 重置数据库
```

### 换电脑/新环境
```bash
# 1. 克隆代码
git clone <repository-url>
cd stock-analysis-system

# 2. 一键部署
./deploy.sh

# 3. 开始使用
./start.sh
```

### 生产部署
```bash
# 1. 环境检测
./deploy.sh

# 2. 数据库初始化（生产数据）
./init-database.sh

# 3. 启动服务
./start.sh
```

---

💡 **核心理念**: 用最简单的方式解决最复杂的环境配置问题