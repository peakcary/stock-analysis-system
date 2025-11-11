# 🚀 股票分析系统 - 快速开始指南

**版本**: v2.7.3
**最后更新**: 2025-11-11

## 📋 目录

1. [环境要求](#环境要求)
2. [一键启动](#一键启动)
3. [详细步骤](#详细步骤)
4. [登录信息](#登录信息)
5. [常见操作](#常见操作)
6. [故障排除](#故障排除)

---

## 环境要求

### 必需组件

- **Node.js** 16+ ([安装指南](https://nodejs.org/))
- **Python** 3.8+ ([安装指南](https://www.python.org/downloads/))
- **MySQL** 8.0+ ([安装指南](https://dev.mysql.com/downloads/mysql/))

### macOS 快速安装

```bash
# 使用 Homebrew 安装
brew install node python mysql

# 启动 MySQL 服务
brew services start mysql
```

### Windows 快速安装

- **Node.js**: 下载 [官方安装程序](https://nodejs.org/)
- **Python**: 下载 [官方安装程序](https://www.python.org/downloads/) （勾选 "Add Python to PATH"）
- **MySQL**: 下载 [官方安装程序](https://dev.mysql.com/downloads/mysql/)

### Linux (Ubuntu/Debian)

```bash
# 安装依赖
sudo apt-get update
sudo apt-get install -y node npm python3 python3-venv mysql-server

# 启动 MySQL
sudo systemctl start mysql
```

---

## 一键启动 ⚡

### 最简单的方式（推荐）

```bash
# 进入项目目录
cd /path/to/stock-analysis-system

# 一键启动（包含环境检查和依赖安装）
./start.sh
```

就是这样！系统会自动：
- ✅ 检查环境
- ✅ 安装依赖
- ✅ 启动所有服务
- ✅ 显示访问地址

### 访问地址

启动完成后，访问以下地址：

| 服务 | 地址 | 账户 | 密码 |
|------|------|------|------|
| **后端 API** | http://localhost:3007 | - | - |
| **API 文档** | http://localhost:3007/docs | - | - |
| **管理端** | http://localhost:8006 | admin | admin123 |
| **客户端** | http://localhost:8005 | fullaccess_user | fullaccess123 |

---

## 详细步骤

### 第 1 步：检查环境

```bash
# 检查系统环境是否满足要求
./check-env.sh
```

输出示例：
```
🔍 系统依赖检查
────────────────────
✅ Node.js: v16.13.0
✅ Python: Python 3.8.10
✅ MySQL: mysql  Ver 8.0.23 for osx10.15 on x86_64

✅ 通过: 15
⚠️ 警告: 2
❌ 失败: 0
```

### 第 2 步：快速安装依赖（可选）

如果已有依赖，此步骤可跳过。

```bash
# 快速安装所有依赖
./quick-deploy.sh
```

### 第 3 步：启动服务

```bash
# 启动所有服务
./start.sh
```

等待输出：
```
🎉 所有服务启动成功！

📊 访问地址:
  🔗 后端 API: http://localhost:3007
  📖 API文档:  http://localhost:3007/docs
  🖥️  管理端:  http://localhost:8006 (admin/admin123)
  📱 客户端:   http://localhost:8005 (fullaccess_user/fullaccess123)
```

### 第 4 步：打开浏览器

访问 http://localhost:8006 (管理端) 或 http://localhost:8005 (客户端)

---

## 登录信息

### 管理员账户（管理端）

```
地址: http://localhost:8006
用户名: admin
密码: admin123
```

**权限**:
- 系统管理
- 用户管理
- 数据导入
- 支付监控

### 普通用户账户（客户端）

```
地址: http://localhost:8005
用户名: fullaccess_user
密码: fullaccess123
```

**权限**:
- Premium 会员
- 100,000+ 查询次数
- 所有功能访问

---

## 常见操作

### 启动/停止/重启

```bash
# 启动服务
./start.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh

# 检查状态
./status.sh
```

### 查看日志

```bash
# 查看后端日志（实时）
tail -f logs/backend.log

# 查看前端日志（实时）
tail -f logs/frontend.log

# 查看客户端日志（实时）
tail -f logs/client.log

# 查看所有日志
tail -f logs/*.log
```

### 数据库管理

```bash
# 连接到数据库
mysql -u root

# 选择数据库
USE stock_analysis_dev;

# 查看表
SHOW TABLES;

# 查看用户
SELECT * FROM users;
```

### 查看 API 文档

访问 http://localhost:3007/docs

这是 FastAPI 自动生成的交互式 API 文档，可以在线测试所有 API 端点。

---

## 故障排除

### ❌ "端口已被占用"

```bash
# 查看占用的进程
lsof -i :3007,8006,8005

# 手动清理
./stop.sh

# 或强制杀死进程
kill -9 <PID>
```

### ❌ "MySQL 连接失败"

```bash
# 启动 MySQL 服务
brew services start mysql  # macOS
sudo systemctl start mysql # Linux

# 验证 MySQL 运行
mysqladmin ping
```

### ❌ "依赖安装失败"

```bash
# 清理并重新安装
rm -rf backend/venv frontend/node_modules client/node_modules
./start.sh
```

### ❌ "环境检查失败"

查看详细故障排除指南：

```bash
cat TROUBLESHOOTING.md
```

或手动检查：

```bash
# 检查 Node.js
node --version

# 检查 Python
python3 --version

# 检查 MySQL
mysql --version
```

### ❌ 部分服务启动失败

```bash
# 1. 查看详细日志
tail -f logs/[backend|frontend|client].log

# 2. 尝试单独启动
cd backend && source venv/bin/activate && \
  python -m uvicorn app.main:app --port 3007 --reload

# 3. 查看完整故障排除指南
cat TROUBLESHOOTING.md
```

---

## 下一步

### 导入数据

1. 访问 http://localhost:8006 (管理端)
2. 登录: admin / admin123
3. 进入 "数据导入" 页面
4. 上传 TXT/TTV/EEE 文件

### 查询股票

1. 访问 http://localhost:8005 (客户端)
2. 登录: fullaccess_user / fullaccess123
3. 使用 "个股查询" 功能

### 支付测试

1. 客户端右上角 "充值"
2. 选择套餐
3. 支付功能处于模拟模式（开发环境）

---

## 常见问题

### Q: 如何修改端口？
A: 编辑各启动脚本中的 `BACKEND_PORT=3007` 等配置，或编辑 package.json 中的 `--port` 参数。

### Q: 如何使用真实微信支付？
A: 修改 `.env` 文件中的支付配置，并将 `PAYMENT_MOCK_MODE=false`。

### Q: 如何重置数据库？
A:
```bash
# 停止服务
./stop.sh

# 删除数据库
mysql -u root -e "DROP DATABASE stock_analysis_dev;"

# 重新启动（会自动创建数据库）
./start.sh
```

### Q: 如何添加新用户？
A:
1. 登录管理端 (http://localhost:8006)
2. 进入 "用户管理" 页面
3. 点击 "新增用户"

### Q: 支持哪些文件格式？
A: TXT、TTV、EEE、CSV（可扩展）

---

## 获取帮助

- 📖 查看完整文档: `README.md`
- 🔧 故障排除: `TROUBLESHOOTING.md`
- 📊 开发进度: `DEVELOPMENT_PROGRESS.md`
- 💬 查看日志: `tail -f logs/*.log`

---

## 脚本说明

| 脚本 | 说明 | 用途 |
|------|------|------|
| `check-env.sh` | 环境检查 | 验证系统环境是否满足要求 |
| `quick-deploy.sh` | 快速部署 | 快速安装依赖 |
| `start.sh` | 启动服务 | 一键启动所有服务 |
| `stop.sh` | 停止服务 | 优雅地停止所有服务 |
| `restart.sh` | 重启服务 | 重启所有服务 |
| `status.sh` | 检查状态 | 查看服务运行状态 |
| `scripts/deployment/deploy.sh` | 部署脚本 | 完整的部署和初始化 |

---

**祝你使用愉快！** 🎉

如有问题，请参考 `TROUBLESHOOTING.md` 或查看日志文件。
