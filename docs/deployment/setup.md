# 股票概念分析系统 - 一键部署指南

## 🚀 新环境部署清单

### 1. 基础环境要求

#### 必需软件
- **Node.js**: v18+ (推荐 v20+)
- **Python**: 3.11+
- **MySQL**: 8.0+
- **Git**: 最新版本

#### 系统要求
- **操作系统**: macOS 10.15+, Windows 10+, Linux Ubuntu 20.04+
- **内存**: 8GB+ (推荐 16GB)
- **硬盘**: 5GB+ 可用空间

### 2. 环境安装步骤

#### 2.1 安装 Node.js
```bash
# macOS (使用 Homebrew)
brew install node@20

# Windows (下载安装包)
# 访问 https://nodejs.org 下载 LTS 版本

# Linux
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 2.2 安装 Python
```bash
# macOS
brew install python@3.11

# Windows (下载安装包)
# 访问 https://www.python.org/downloads/

# Linux
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

#### 2.3 安装 MySQL
```bash
# macOS
brew install mysql@8.0
brew services start mysql@8.0

# Windows
# 下载 MySQL Community Server 8.0 安装包

# Linux
sudo apt update
sudo apt install mysql-server-8.0
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### 2.4 配置 MySQL
```sql
-- 创建数据库和用户
CREATE DATABASE stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'stock_user'@'localhost' IDENTIFIED BY 'stock_password_2024!';
GRANT ALL PRIVILEGES ON stock_analysis_dev.* TO 'stock_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 项目部署

#### 3.1 克隆项目
```bash
git clone <repository-url>
cd stock-analysis-system
```

#### 3.2 后端配置
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 3.3 前端配置
```bash
# 客户端
cd client
npm install

# 后端管理
cd ../frontend  
npm install
```

#### 3.4 环境变量配置
```bash
# 复制配置文件
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env
```

### 4. 配置文件模板

#### backend/.env
```bash
# 应用基本配置
APP_NAME=股票概念分析系统
APP_VERSION=1.0.0
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=3007

# 数据库配置
DATABASE_URL=mysql+pymysql://stock_user:stock_password_2024!@127.0.0.1:3306/stock_analysis_dev
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_USER=stock_user
DATABASE_PASSWORD=stock_password_2024!
DATABASE_NAME=stock_analysis_dev

# JWT 配置
SECRET_KEY=your-super-secret-key-change-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
ALLOWED_ORIGINS=["http://localhost:8005","http://127.0.0.1:8005","http://localhost:8006","http://127.0.0.1:8006"]

# 分页配置
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100

# 文件上传配置
MAX_FILE_SIZE=104857600
UPLOAD_DIR=uploads

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 支付配置
PAYMENT_ORDER_TIMEOUT_HOURS=2
PAYMENT_ENABLED=true
```

### 5. 一键部署脚本

#### 5.1 创建 deploy.sh
```bash
#!/bin/bash

echo "🚀 开始部署股票概念分析系统..."

# 检查环境
echo "📋 检查环境依赖..."
command -v node >/dev/null 2>&1 || { echo "❌ Node.js 未安装"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 未安装"; exit 1; }
command -v mysql >/dev/null 2>&1 || { echo "❌ MySQL 未安装"; exit 1; }

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 初始化数据库
echo "🗄️ 初始化数据库..."
python -c "
from app.core.database import Base, engine
from app.models import *
Base.metadata.create_all(bind=engine)
print('✅ 数据库表创建完成')
"

# 安装前端依赖
echo "📦 安装客户端依赖..."
cd ../client
npm install

echo "📦 安装管理端依赖..."
cd ../frontend
npm install

cd ..
echo "✅ 部署完成！"
echo "📋 使用 ./start.sh 启动系统"
```

### 6. 系统要求检查脚本

#### check-env.sh
```bash
#!/bin/bash

echo "🔍 检查系统环境..."

# 检查 Node.js
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
else
    echo "❌ Node.js 未安装"
    exit 1
fi

# 检查 Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python 未安装"
    exit 1
fi

# 检查 MySQL
if command -v mysql >/dev/null 2>&1; then
    MYSQL_VERSION=$(mysql --version)
    echo "✅ MySQL: $MYSQL_VERSION"
else
    echo "❌ MySQL 未安装"
    exit 1
fi

# 检查端口占用
check_port() {
    if lsof -ti:$1 >/dev/null 2>&1; then
        echo "⚠️ 端口 $1 被占用"
        return 1
    else
        echo "✅ 端口 $1 可用"
        return 0
    fi
}

check_port 3007
check_port 8005
check_port 8006

echo "🎉 环境检查完成！"
```

### 7. 故障排查

#### 常见问题
1. **数据库连接失败**
   - 检查 MySQL 服务是否启动
   - 验证数据库用户名密码
   - 确认使用 127.0.0.1 而不是 localhost

2. **端口占用**
   ```bash
   # 查找占用端口的进程
   lsof -ti:3007
   
   # 杀掉进程
   kill -9 $(lsof -ti:3007)
   ```

3. **Python 依赖问题**
   ```bash
   # 清理缓存重新安装
   pip cache purge
   pip install -r requirements.txt --no-cache-dir
   ```

4. **Node.js 依赖问题**
   ```bash
   # 清理缓存重新安装
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```