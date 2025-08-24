# 股票分析系统本地开发指南

> 🚀 快速启动本地开发环境

## 📋 系统要求

### 必需环境
- **MySQL 8.0+** (用户名: `root`, 密码: `Pp123456`)
- **Python 3.8+**  
- **Node.js 16+**
- **npm 7+**

### 检查环境
```bash
# 检查 MySQL
mysql -u root -pPp123456 -e "SELECT VERSION();"

# 检查 Python
python3 --version

# 检查 Node.js 和 npm
node --version
npm --version
```

## ⚡ 一键启动

### 1. 首次使用（一键部署）
```bash
# 克隆项目后，在项目根目录运行
./scripts/setup-local.sh
```

这个脚本会自动：
- ✅ 创建数据库 `stock_analysis_dev`
- ✅ 初始化数据表和示例数据
- ✅ 创建 Python 虚拟环境
- ✅ 安装后端依赖
- ✅ 安装前端依赖
- ✅ 配置环境变量

### 2. 启动所有服务（一键启动）
```bash
# 启动前后端服务
./scripts/start-all.sh
```

🌐 **访问地址**：
- 前端应用: http://localhost:3000
- 后端API: http://localhost:8000  
- API文档: http://localhost:8000/docs

### 3. 停止所有服务
```bash
# 停止前后端服务
./scripts/stop-all.sh
```

## 🛠️ 分步启动（可选）

如果需要单独启动服务：

```bash
# 只启动后端
./scripts/start-backend.sh

# 只启动前端（新终端窗口）
./scripts/start-frontend.sh
```

## 📊 数据库信息

- **数据库名**: `stock_analysis_dev`
- **用户名**: `root`
- **密码**: `Pp123456`
- **端口**: `3306`

### 预置数据
系统会自动创建示例数据：
- 8只示例股票（平安银行、万科A、贵州茅台等）
- 6个概念分类（人工智能、5G概念、芯片概念等）
- 股票概念关联关系
- 历史交易数据

## 🔧 开发配置

### 环境变量文件
- **本地开发**: `.env` (自动从 `.env.local` 复制)
- **生产环境**: `.env.prod`

### 端口配置
- **后端端口**: 8000
- **前端端口**: 3000
- **MySQL端口**: 3306

## 📝 功能测试

启动成功后可以测试：

1. **用户注册登录** - http://localhost:3000/register
2. **股票查询** - 输入股票代码如 `000001`
3. **概念分析** - 查看热门概念排行
4. **支付系统** - 模拟支付套餐购买
5. **个人中心** - 查看用户信息和查询记录

## 🚨 常见问题

### MySQL 连接失败
```bash
# 确保 MySQL 服务运行
brew services start mysql  # macOS
# 或
sudo systemctl start mysql  # Linux

# 检查用户密码
mysql -u root -pPp123456 -e "SELECT 1;"
```

### Python 依赖安装失败
```bash
# 升级 pip
cd backend && source venv/bin/activate
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt
```

### 前端启动失败
```bash
cd frontend
# 清理依赖重新安装
rm -rf node_modules package-lock.json
npm install
```

### 端口被占用
```bash
# 检查端口占用
lsof -ti:8000  # 后端
lsof -ti:3000  # 前端

# 杀死占用进程
kill -9 $(lsof -ti:8000)
kill -9 $(lsof -ti:3000)
```

## 📁 项目结构

```
stock-analysis-system/
├── backend/           # FastAPI 后端
│   ├── app/          # 应用代码
│   ├── venv/         # Python 虚拟环境
│   └── logs/         # 日志文件
├── frontend/         # React 前端
│   ├── src/          # 源代码
│   └── node_modules/ # Node.js 依赖
├── database/         # 数据库脚本
├── scripts/          # 自动化脚本
└── docs/            # 项目文档
```

## 🎯 开发提示

- **代码热重载**：修改代码后自动重启
- **调试模式**：后端运行在debug模式
- **日志查看**：后端日志保存在 `backend/logs/` 
- **API测试**：访问 http://localhost:8000/docs

## 🎉 快速体验

1. 运行 `./scripts/setup-local.sh` 
2. 运行 `./scripts/start-all.sh`
3. 打开 http://localhost:3000
4. 注册账号并开始使用！

---

**祝开发愉快！** 🚀