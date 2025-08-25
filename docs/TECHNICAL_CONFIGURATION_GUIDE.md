# 技术配置指南与环境说明
Technical Configuration Guide and Environment Setup

## 📋 目录
- [系统要求](#系统要求)
- [环境配置](#环境配置)
- [数据库配置](#数据库配置)
- [网络与端口配置](#网络与端口配置)
- [自动化脚本](#自动化脚本)
- [配置文件说明](#配置文件说明)
- [故障排除](#故障排除)
- [性能调优](#性能调优)

---

## 🖥 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上 (推荐8GB)
- **存储**: 20GB可用空间
- **网络**: 稳定的互联网连接

### 操作系统支持
- ✅ **macOS**: 10.15+ (Catalina 或更新)
- ✅ **Linux**: Ubuntu 18.04+, CentOS 7+, Debian 10+
- ❌ **Windows**: 暂不支持 (可使用 WSL2)

---

## ⚙️ 环境配置

### 核心依赖版本

#### 后端 Python 环境 (4,137 文件)
```bash
Python: 3.11+
FastAPI: 0.100+
SQLAlchemy: 2.0+
PyMySQL: 1.1+
Pydantic: 2.0+
Uvicorn: 0.20+
email-validator: 2.0+  # 必需依赖
```

#### 前端 Node.js 环境 (30,074 文件)
```bash
Node.js: 20.19+ (必需，支持Vite 7.x)
npm: 10.0+
Vite: 7.1.2
React: 18.2.0 (client) / 19.1.1 (frontend)
TypeScript: 5.8.3
Ant Design: 5.27.1
```

#### 数据库环境
```bash
MySQL: 8.0 (推荐版本)
认证插件: mysql_native_password
字符集: utf8mb4
排序规则: utf8mb4_unicode_ci
```

### 自动环境安装
```bash
# 一键安装所有依赖
./setup_environment.sh

# 检查环境状态
./check_environment.sh
```

---

## 🗄️ 数据库配置

### MySQL 8.0 安装与配置

#### macOS 安装
```bash
# 使用 Homebrew 安装 MySQL 8.0
brew install mysql@8.0

# 启动 MySQL 服务
brew services start mysql@8.0

# 添加到 PATH
echo 'export PATH="/opt/homebrew/opt/mysql@8.0/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Linux 安装 (Ubuntu/Debian)
```bash
# 更新包管理器
sudo apt update

# 安装 MySQL 8.0
sudo apt install mysql-server-8.0

# 启动服务
sudo systemctl start mysql
sudo systemctl enable mysql
```

### 数据库用户配置
```sql
-- 设置 root 密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Pp123456';

-- 创建管理员用户 (兼容性更好)
CREATE USER 'admin'@'%' IDENTIFIED WITH mysql_native_password BY 'Pp123456';
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

-- 创建项目数据库
CREATE DATABASE stock_analysis_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 数据库连接配置
```python
# backend/app/core/config.py
DATABASE_URL = "mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev"
DATABASE_HOST = "127.0.0.1"  # 使用IPv4地址
DATABASE_PORT = 3306
DATABASE_USER = "root"
DATABASE_PASSWORD = "Pp123456"
DATABASE_NAME = "stock_analysis_dev"
```

### 重要注意事项
- ⚠️ **必须使用 127.0.0.1 而不是 localhost** (IPv4/IPv6 兼容性)
- ⚠️ **必须使用 mysql_native_password 认证** (客户端兼容性)
- ⚠️ **推荐使用 MySQL 8.0** (避免 9.x 的兼容性问题)

---

## 🌐 网络与端口配置

### 端口分配标准
```bash
3007  # 后端 API 服务 (FastAPI + Uvicorn)
8005  # 前端管理端 (React Admin Dashboard)
8006  # 前端客户端 (React User Interface)
3306  # MySQL 数据库服务
```

### 后端服务配置
```python
# backend/app/core/config.py
HOST = "0.0.0.0"
PORT = 3007

# CORS 配置
ALLOWED_ORIGINS = [
    "http://localhost:8005",      # 管理端
    "http://127.0.0.1:8005",
    "http://localhost:8006",      # 客户端
    "http://127.0.0.1:8006"
]
```

### 前端代理配置

#### 客户端配置 (8006)
```typescript
// client/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8006,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',  # 使用IPv4地址
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

#### 管理端配置 (8005)
```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8005,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

### IPv4/IPv6 兼容性说明
- **问题**: `localhost` 在某些系统上解析为 `::1` (IPv6)，导致连接失败
- **解决**: 统一使用 `127.0.0.1` (IPv4) 确保兼容性
- **影响**: 前端代理、后端数据库连接、服务间通信

---

## 🤖 自动化脚本

#### 核心脚本文件 (6个)
### 1. 环境安装脚本 (`setup_environment.sh`)

#### 功能特性
- ✅ 自动检测操作系统 (macOS/Linux)
- ✅ 安装必要的包管理器 (Homebrew/apt)
- ✅ 安装和配置 Python 3.11+
- ✅ 安装和配置 Node.js 20.19+ (通过NVM)
- ✅ 安装和配置 MySQL 8.0
- ✅ 自动修复 IPv4/IPv6 兼容性
- ✅ 安装项目依赖
- ✅ 创建启动脚本

#### 使用方法
```bash
chmod +x setup_environment.sh
./setup_environment.sh
```

#### 安装过程
1. 检测系统环境
2. 安装包管理器
3. 安装 Python 和依赖
4. 安装 Node.js (自动版本管理)
5. 安装和配置 MySQL
6. 修复配置文件
7. 安装项目依赖
8. 创建数据库和表
9. 生成启动脚本

### 2. 服务启动脚本 (`start_all.sh`)

#### 功能特性
- ✅ 端口占用检查
- ✅ MySQL 服务状态验证
- ✅ 后台服务启动
- ✅ 日志文件分离
- ✅ 启动状态监控
- ✅ 访问地址显示

#### 使用方法
```bash
chmod +x start_all.sh
./start_all.sh
```

#### 启动流程
1. 创建日志目录
2. 检查 MySQL 服务状态
3. 启动后端服务 (端口3007)
4. 启动用户前端 (端口8006)
5. 启动管理前端 (端口8005)
6. 显示访问地址和日志命令

### 3. 环境检查脚本 (`check_environment.sh`)

#### 功能特性
- ✅ Node.js 版本检查和升级
- ✅ Python 虚拟环境验证
- ✅ MySQL 服务和连接测试
- ✅ 配置文件自动修复
- ✅ 项目依赖完整性检查
- ✅ 端口占用状态检查

#### 使用方法
```bash
chmod +x check_environment.sh
./check_environment.sh
```

#### 检查项目
1. Node.js 版本兼容性
2. Python 环境和依赖
3. MySQL 服务状态
4. 网络配置正确性
5. 项目依赖完整性
6. 启动脚本权限
7. 端口可用性

### 4. 服务停止脚本 (`stop_all.sh`)
- ✅ 停止所有后台服务
- ✅ 清理进程和端口占用
- ✅ 安全关闭数据库连接

### 5. 备份脚本 (`backup_environment.sh`)
- ✅ 数据库备份
- ✅ 配置文件备份
- ✅ 日志文件归档

### 6. 快速启动脚本 (`quick_start.sh`)
- ✅ 简化的启动流程
- ✅ 状态检查和报告

---

## 📁 配置文件说明

### 后端配置文件

#### `backend/app/core/config.py`
```python
class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "股票概念分析系统"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 3007  # 固定端口
    
    # 数据库配置 (IPv4地址)
    DATABASE_URL: str = "mysql+pymysql://root:Pp123456@127.0.0.1:3306/stock_analysis_dev"
    DATABASE_HOST: str = "127.0.0.1"
    DATABASE_PORT: int = 3306
    
    # CORS配置 (正确的前端端口)
    ALLOWED_ORIGINS: list = [
        "http://localhost:8005",
        "http://127.0.0.1:8005",
        "http://localhost:8006",
        "http://127.0.0.1:8006"
    ]
    
    # JWT配置
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

### 前端配置文件

#### 客户端 `client/vite.config.ts`
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8006,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',  // IPv4地址
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

#### 管理端 `frontend/vite.config.ts`
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8005,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:3007',  // IPv4地址
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

### 包配置文件

#### 客户端 `client/package.json`
```json
{
  "scripts": {
    "dev": "vite --port 8006",
    "start": "vite --port 8006",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

#### 管理端 `frontend/package.json`
```json
{
  "scripts": {
    "dev": "vite --port 8005",
    "build": "tsc && vite build",
    "preview": "vite preview"
  }
}
```

---

## 🐳 Docker 配置

### 开发环境 (`docker-compose.yml`)
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "3007:3007"
    environment:
      - DATABASE_URL=mysql+pymysql://root:password@mysql:3306/stock_analysis_dev
    depends_on:
      - mysql
      
  frontend-client:
    build: ./client
    ports:
      - "8006:8006"
    environment:
      - VITE_API_URL=http://localhost:3007
      
  frontend-admin:
    build: ./frontend
    ports:
      - "8005:8005"
    environment:
      - VITE_API_URL=http://localhost:3007
      
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=stock_analysis_dev
    command: --default-authentication-plugin=mysql_native_password
```

### 生产环境 (`docker-compose.prod.yml`)
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend-client
      - frontend-admin
      
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=mysql+pymysql://root:${DB_PASSWORD}@mysql:3306/stock_analysis_prod
      
  frontend-client:
    build: 
      context: ./client
      dockerfile: Dockerfile.prod
      
  frontend-admin:
    build: 
      context: ./frontend  
      dockerfile: Dockerfile.prod
      
  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=stock_analysis_prod
    command: --default-authentication-plugin=mysql_native_password
    
volumes:
  mysql_data:
```

---

## 🚨 故障排除

### 常见问题与解决方案

#### 1. Node.js 版本兼容性问题
```bash
# 问题: Vite 7.x 需要 Node.js 20.19+
# 错误信息: "Node.js version mismatch" 或启动失败

# 解决方案:
# 检查当前版本
node --version

# 使用 NVM 安装正确版本
nvm install 20.19.0
nvm use 20.19.0
nvm alias default 20.19.0

# 自动修复
./check_environment.sh
```

#### 2. MySQL 连接失败
```bash
# 问题: 数据库连接失败
# 错误信息: "Can't connect to MySQL server"

# 解决方案:
# 检查 MySQL 服务状态
brew services list | grep mysql

# 启动 MySQL 服务
brew services start mysql@8.0

# 测试连接
mysql -u root -pPp123456 -e "SELECT 1"

# 重置密码 (如需要)
mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Pp123456';"
```

#### 3. 端口被占用
```bash
# 问题: 端口冲突
# 错误信息: "Port already in use" 或 "EADDRINUSE"

# 解决方案:
# 查看端口占用
lsof -Pi :3007 -sTCP:LISTEN
lsof -Pi :8005 -sTCP:LISTEN  
lsof -Pi :8006 -sTCP:LISTEN

# 终止占用进程
kill -9 <PID>

# 或使用停止脚本
./stop_all.sh
```

#### 4. IPv6/IPv4 连接问题
```bash
# 问题: localhost 解析问题
# 错误信息: "ECONNREFUSED ::1:3007"

# 解决方案:
# 检查配置文件是否使用 IPv4 地址
grep -r "localhost:" client/vite.config.ts
grep -r "localhost:" frontend/vite.config.ts
grep -r "localhost:" backend/app/core/config.py

# 自动修复
./check_environment.sh

# 手动修复
sed -i '' 's/localhost:/127.0.0.1:/g' client/vite.config.ts
```

#### 5. 依赖缺失问题
```bash
# 问题: Python 或 Node.js 依赖缺失
# 错误信息: "ModuleNotFoundError" 或 "Module not found"

# Python 依赖解决:
cd backend
source venv/bin/activate
pip install -r requirements.txt
pip install email-validator  # 常见缺失依赖

# Node.js 依赖解决:
cd client && npm install
cd frontend && npm install

# 自动修复
./check_environment.sh
```

### 日志文件分析

#### 后端日志 (`logs/backend.log`)
```bash
# 查看后端启动日志
tail -f logs/backend.log

# 搜索错误信息
grep -i error logs/backend.log
grep -i "traceback" logs/backend.log

# 常见错误模式:
# - "ModuleNotFoundError": 依赖缺失
# - "OperationalError": 数据库连接问题  
# - "Port already in use": 端口冲突
```

#### 前端日志 (`logs/client.log`, `logs/frontend.log`)
```bash
# 查看前端启动日志
tail -f logs/client.log
tail -f logs/frontend.log

# 搜索代理错误
grep -i "proxy error" logs/client.log

# 常见错误模式:
# - "ECONNREFUSED": 后端连接失败
# - "Module parse failed": 编译错误
# - "Network request failed": API 请求失败
```

---

## ⚡ 性能调优

### 数据库优化

#### 索引配置
```sql
-- 股票表索引
CREATE INDEX idx_stock_code ON stocks(stock_code);
CREATE INDEX idx_stock_name ON stocks(stock_name);

-- 概念表索引  
CREATE INDEX idx_concept_name ON concepts(concept_name);

-- 关联表索引
CREATE INDEX idx_stock_concept_stock ON stock_concepts(stock_id);
CREATE INDEX idx_stock_concept_concept ON stock_concepts(concept_id);

-- 用户查询日志索引
CREATE INDEX idx_query_logs_user_time ON query_logs(user_id, created_at);
CREATE INDEX idx_query_logs_time ON query_logs(created_at);
```

#### 连接池配置
```python
# backend/app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 最大溢出连接
    pool_recycle=3600,     # 连接回收时间
    pool_pre_ping=True,    # 连接预检查
    echo=False             # 生产环境关闭SQL日志
)
```

### 应用程序优化

#### 查询缓存
```python
# 内存缓存热点数据
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_hot_concepts():
    # 缓存热门概念数据
    return query_hot_concepts()

# 定期清理缓存
import schedule
schedule.every(10).minutes.do(lambda: get_hot_concepts.cache_clear())
```

#### 分页优化
```python
# 使用游标分页替代偏移分页
def get_stocks_cursor(cursor_id=None, limit=20):
    query = select(Stock)
    if cursor_id:
        query = query.where(Stock.id > cursor_id)
    return query.order_by(Stock.id).limit(limit)
```

### 前端优化

#### 代码分割
```typescript
// 路由级别代码分割
import { lazy, Suspense } from 'react';

const StockAnalysis = lazy(() => import('./pages/StockAnalysis'));
const ConceptAnalysis = lazy(() => import('./pages/ConceptAnalysis'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/stocks" element={<StockAnalysis />} />
        <Route path="/concepts" element={<ConceptAnalysis />} />
      </Routes>
    </Suspense>
  );
}
```

#### 虚拟滚动
```typescript
// 大列表虚拟滚动
import { FixedSizeList as List } from 'react-window';

function StockList({ stocks }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      <StockItem stock={stocks[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={stocks.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </List>
  );
}
```

### 网络优化

#### Nginx 配置
```nginx
# nginx/nginx.conf
http {
    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API 请求优化
    location /api/ {
        proxy_pass http://backend:3007;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 5s;
        proxy_read_timeout 30s;
    }
}
```

---

## 🔒 安全配置

### 环境变量管理
```bash
# .env.prod (生产环境)
SECRET_KEY=your-super-strong-secret-key-change-in-production
DATABASE_PASSWORD=strong-database-password
JWT_SECRET_KEY=jwt-signing-key
WECHAT_API_KEY=wechat-payment-api-key

# 权限设置
chmod 600 .env.prod
```

### SSL/TLS 配置
```nginx
# HTTPS 配置
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

### API 安全
```python
# 限流配置
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/stocks/search")
@limiter.limit("30/minute")  # 每分钟30次请求
async def search_stocks(request: Request):
    pass
```

---

## 📊 监控与日志

### 日志配置
```python
# backend/app/core/logging.py
import logging
from datetime import datetime

# 结构化日志格式
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s"}'
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
```

### 健康检查
```python
# 系统健康检查接口
@app.get("/health")
async def health_check():
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
```

---

## 🎯 总结

这个技术配置指南涵盖了股票分析系统的完整技术栈配置，包括：

### ✅ 核心配置
- **环境要求**: Python 3.11+, Node.js 20.19+, MySQL 8.0
- **端口配置**: 后端3007, 管理端8005, 客户端8006  
- **网络配置**: IPv4 兼容性 (127.0.0.1)
- **认证配置**: mysql_native_password

### ✅ 自动化工具
- **环境安装**: `setup_environment.sh` 一键安装
- **服务启动**: `start_all.sh` 一键启动
- **状态检查**: `check_environment.sh` 环境诊断

### ✅ 生产就绪
- **Docker 支持**: 完整容器化配置
- **性能优化**: 数据库索引、前端优化、网络优化
- **安全配置**: SSL、限流、安全头
- **监控日志**: 结构化日志、健康检查

通过这个配置指南，开发者可以在任何兼容的机器上快速搭建和运行股票分析系统！

---

**📅 最后更新**: 2025-08-25  
**📝 文档版本**: v1.1  
**🔄 适用版本**: 系统 v2.1 (文档完善版)
**📊 项目规模**: Python 4,137文件 + TypeScript 30,074文件