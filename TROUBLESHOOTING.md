# 🔧 股票分析系统 - 故障排除指南

**版本**: v2.7.3
**最后更新**: 2025-11-11

## 📋 目录

1. [环境检查](#环境检查)
2. [启动问题](#启动问题)
3. [端口问题](#端口问题)
4. [数据库问题](#数据库问题)
5. [依赖问题](#依赖问题)
6. [API 问题](#api-问题)
7. [UI 问题](#ui-问题)
8. [性能问题](#性能问题)
9. [日志查看](#日志查看)
10. [高级诊断](#高级诊断)

---

## 环境检查

### 问题：无法启动任何服务

**第 1 步：运行环境检查**

```bash
./check-env.sh
```

**分析输出信息**:

- 如果显示 "✅ 通过"，环境没问题
- 如果显示 "⚠️ 警告"，某些功能可能不完整
- 如果显示 "❌ 失败"，需要安装缺失的依赖

### 第 2 步：安装缺失的依赖

根据检查结果安装：

```bash
# macOS
brew install node mysql python3

# Ubuntu/Debian
sudo apt-get install nodejs npm mysql-server python3

# Windows
# 访问官方网站下载安装程序
```

### 第 3 步：验证安装

```bash
node --version      # 应显示 v16+ 版本
python3 --version   # 应显示 Python 3.8+
mysql --version     # 应显示 MySQL 8.0+
npm --version       # 应显示 npm 8+
```

---

## 启动问题

### 问题 1️⃣：./start.sh 权限不足

**错误信息**:
```
bash: ./start.sh: Permission denied
```

**解决方案**:

```bash
# 添加执行权限
chmod +x start.sh stop.sh restart.sh status.sh check-env.sh quick-deploy.sh

# 重新启动
./start.sh
```

### 问题 2️⃣：start.sh 找不到

**错误信息**:
```
./start.sh: No such file or directory
```

**解决方案**:

```bash
# 确保在项目根目录
pwd  # 应该显示 .../stock-analysis-system

# 检查文件是否存在
ls -la start.sh

# 如果文件不存在，查看是否在其他目录
find . -name "start.sh"
```

### 问题 3️⃣：部分服务启动失败

**错误信息**:
```
❌ 后端 API (3007) - 启动失败
```

**诊断步骤**:

```bash
# 1. 查看后端日志
tail -f logs/backend.log

# 2. 手动启动后端查看错误
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --port 3007

# 3. 查看完整错误信息
```

**常见错误及解决方案**:

| 错误 | 原因 | 解决方案 |
|------|------|--------|
| `ModuleNotFoundError: No module named 'fastapi'` | 依赖未安装 | `pip install -r requirements.txt` |
| `pymysql.err.OperationalError` | 数据库连接失败 | 启动 MySQL: `brew services start mysql` |
| `OSError: [Errno 48] Address already in use` | 端口被占用 | 见 [端口问题](#端口问题) |

---

## 端口问题

### 问题 1️⃣：端口 3007 已被占用

**错误信息**:
```
OSError: [Errno 48] Address already in use: ('0.0.0.0', 3007)
```

**查看占用进程**:

```bash
# 查看所有占用端口的进程
lsof -i :3007

# 输出示例：
# COMMAND   PID  USER   FD  TYPE DEVICE SIZE/OFF NODE NAME
# python  12345 user    5u  IPv6      ...
```

**解决方案**:

```bash
# 方法 1：使用 stop.sh 停止服务
./stop.sh

# 方法 2：手动杀死进程
kill -9 12345  # 使用上面查到的 PID

# 方法 3：强制清理所有占用的端口
lsof -ti:3007,8006,8005 | xargs kill -9
```

### 问题 2️⃣：多个端口同时被占用

**查看所有占用的服务**:

```bash
# 查看后端、前端、客户端所有端口
lsof -i :3007,8006,8005

# 强制清理
./stop.sh

# 如果仍有问题，更激进的方法
lsof -ti:3007,8006,8005 | xargs kill -9
```

### 问题 3️⃣：想使用不同的端口

**修改端口的方式**:

```bash
# 编辑启动脚本
# 修改 start.sh 中的：
# BACKEND_PORT=3007
# FRONTEND_PORT=8006
# CLIENT_PORT=8005

# 然后启动
./start.sh
```

---

## 数据库问题

### 问题 1️⃣：MySQL 服务未运行

**错误信息**:
```
ConnectionRefusedError: [Errno 61] Connection refused
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on '127.0.0.1' (61)")
```

**解决方案**:

```bash
# macOS
brew services start mysql

# Ubuntu/Debian
sudo systemctl start mysql

# 验证服务运行
mysqladmin ping
```

### 问题 2️⃣：数据库不存在

**错误信息**:
```
DatabaseError: (pymysql.err.ProgrammingError) (1049, "Unknown database 'stock_analysis_dev'")
```

**解决方案**:

```bash
# 方法 1：重新启动（自动创建）
./stop.sh
./start.sh

# 方法 2：手动创建
mysql -u root << EOF
CREATE DATABASE IF NOT EXISTS stock_analysis_dev;
USE stock_analysis_dev;
EOF

# 验证数据库
mysql -u root -e "SHOW DATABASES LIKE 'stock_analysis_dev';"
```

### 问题 3️⃣：数据库表不存在

**错误信息**:
```
ProgrammingError: (pymysql.err.ProgrammingError) (1146, "Table 'stock_analysis_dev.daily_trading' doesn't exist")
```

**解决方案**:

```bash
# 方法 1：使用部署脚本初始化
cd scripts/deployment
bash deploy.sh

# 方法 2：手动初始化（如果部署脚本失败）
cd backend
source venv/bin/activate
python create_daily_trading_tables.py
python create_admin_table.py
```

### 问题 4️⃣：数据库连接密码错误

**错误信息**:
```
AccessDeniedError: (pymysql.err.OperationalError) (1045, "Access denied for user 'root'@'localhost'")
```

**解决方案**:

```bash
# 1. 检查当前密码
mysql -u root -p  # 按提示输入密码

# 2. 更新 .env 文件中的数据库密码
vi backend/.env
# 修改: DATABASE_PASSWORD=your_actual_password

# 3. 重启服务
./restart.sh
```

### 问题 5️⃣：数据库表结构不一致

**症状**: API 返回错误，无法查询数据

**解决方案**:

```bash
# 1. 查看表结构
mysql -u root stock_analysis_dev -e "DESCRIBE daily_trading;"

# 2. 如果表丢失或不完整，重新初始化
cd backend
source venv/bin/activate
python create_daily_trading_tables.py

# 3. 验证修复
mysql -u root stock_analysis_dev -e "SHOW TABLES;"
```

---

## 依赖问题

### 问题 1️⃣：Python 依赖缺失

**错误信息**:
```
ModuleNotFoundError: No module named 'fastapi'
ModuleNotFoundError: No module named 'sqlalchemy'
```

**解决方案**:

```bash
# 方法 1：重新安装所有依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 方法 2：清理并重新安装
rm -rf backend/venv
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 2️⃣：NPM 依赖缺失或损坏

**错误信息**:
```
Error: Cannot find module '@ant-design/icons'
error ERR! code E404
```

**解决方案**:

```bash
# 方法 1：清理并重新安装（推荐）
rm -rf frontend/node_modules client/node_modules
npm install --legacy-peer-deps

# 方法 2：仅清理一个应用
cd frontend
rm -rf node_modules package-lock.json
npm install

# 方法 3：使用快速部署脚本
./quick-deploy.sh
```

### 问题 3️⃣：特定包版本冲突

**错误信息**:
```
npm ERR! peer dep missing: react-dom@*
```

**解决方案**:

```bash
# 使用 --legacy-peer-deps 忽略警告
npm install --legacy-peer-deps

# 或更新到兼容版本
npm update
```

---

## API 问题

### 问题 1️⃣：API 返回 401 未授权

**错误信息**:
```json
{"detail": "Not authenticated"}
{"detail": "Invalid token"}
```

**解决方案**:

```bash
# 1. 检查是否正确登录
# 访问 http://localhost:8005 或 http://localhost:8006
# 输入正确的用户名和密码

# 2. 检查 token 是否过期
# Token 默认有效期为 30 分钟

# 3. 清除浏览器 cookie 并重新登录
# Chrome: 开发者工具 → Application → Clear Site Data

# 4. 查看 API 文档
# http://localhost:3007/docs
# 点击 "Authorize" 输入 token
```

### 问题 2️⃣：API 返回 403 禁止访问

**错误信息**:
```json
{"detail": "Permission denied"}
{"detail": "Not enough permissions"}
```

**解决方案**:

```bash
# 1. 检查用户权限
# - admin 账户 → 管理员权限
# - fullaccess_user → 普通用户权限

# 2. 对于受限的 API，使用相应权限的账户

# 3. 检查查询次数是否用尽
# 查看 http://localhost:8005 右上角 "账户信息"

# 4. 升级会员等级
# 访问 http://localhost:8005 点击 "充值"
```

### 问题 3️⃣：API 返回 500 服务器错误

**错误信息**:
```json
{"detail": "Internal server error"}
```

**诊断步骤**:

```bash
# 1. 查看后端日志获取详细错误信息
tail -f logs/backend.log

# 2. 检查错误类型
# - 数据库连接错误
# - 代码逻辑错误
# - 外部 API 调用失败

# 3. 常见解决方案
# - 重启服务: ./restart.sh
# - 检查数据库: mysql -u root stock_analysis_dev -e "SELECT 1;"
# - 查看完整错误日志
```

### 问题 4️⃣：文件上传失败

**错误信息**:
```
413 Request entity too large
```

**解决方案**:

```bash
# 1. 检查文件大小（建议 < 100MB）
ls -lh your_file.txt

# 2. 如果文件过大，分割后上传
split -l 100000 large_file.txt file_part_

# 3. 使用分块上传 API
# POST /api/v1/universal-import/import
```

---

## UI 问题

### 问题 1️⃣：页面无法加载或显示空白

**错误信息**: 浏览器显示空白页面

**解决方案**:

```bash
# 1. 检查浏览器控制台错误
# Chrome: F12 → Console 标签

# 2. 硬刷新清除缓存
# Chrome: Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)

# 3. 检查前端服务是否运行
./status.sh

# 4. 检查前端日志
tail -f logs/frontend.log
tail -f logs/client.log

# 5. 重启前端服务
./restart.sh
```

### 问题 2️⃣：样式错乱或组件显示不正确

**症状**: 页面样式混乱、按钮不可点击

**解决方案**:

```bash
# 1. 清除浏览器缓存
# Chrome: 开发者工具 → Application → Clear Site Data

# 2. 重新构建前端
cd frontend
npm run build

cd ../client
npm run build

# 3. 重启服务
./restart.sh
```

### 问题 3️⃣：登录页面无法登录

**错误信息**: 输入正确密码仍显示错误

**解决方案**:

```bash
# 1. 检查后端是否运行
./status.sh

# 2. 检查是否使用了正确的账户
# 管理端: admin / admin123
# 客户端: fullaccess_user / fullaccess123

# 3. 清除浏览器 cookie
# Chrome: 开发者工具 → Application → Cookies → 删除

# 4. 检查网络连接
# 打开浏览器控制台 → Network 标签 → 查看 login 请求

# 5. 查看后端错误日志
tail -f logs/backend.log
```

---

## 性能问题

### 问题 1️⃣：查询速度缓慢

**症状**: 查询股票或概念时响应慢

**解决方案**:

```bash
# 1. 检查数据库索引
mysql -u root stock_analysis_dev -e "SHOW INDEX FROM daily_trading;"

# 2. 检查是否启用了数据库优化
curl http://localhost:3007/api/v1/optimization/status

# 3. 清除缓存，让 Redis 重新生成
# 此步骤会临时降低性能，但能修复缓存问题

# 4. 重新启动服务以清除内存缓存
./restart.sh
```

### 问题 2️⃣：内存占用过高

**症状**: 系统变慢，无响应

**解决方案**:

```bash
# 1. 检查各进程的内存占用
top -o %MEM

# 2. 限制后端进程
# 在 start.sh 中添加内存限制
# ulimit -m 1048576  # 限制为 1GB

# 3. 增加 swap 空间
# Linux: sudo fallocate -l 4G /swapfile

# 4. 减少数据库连接数
# 编辑 backend/app/core/config.py
# DATABASE_POOL_SIZE=5  # 降低连接数
```

### 问题 3️⃣：CPU 占用过高

**症状**: 机器风扇转速加快

**解决方案**:

```bash
# 1. 查看哪个进程占用 CPU
top -o %CPU

# 2. 查看后端日志找出耗时操作
tail -f logs/backend.log | grep "slow"

# 3. 优化大数据查询
# 添加数据库索引
# 使用分页查询
# 启用查询缓存

# 4. 重启服务
./restart.sh
```

---

## 日志查看

### 实时查看日志

```bash
# 查看所有日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/backend.log    # 后端
tail -f logs/frontend.log   # 前端
tail -f logs/client.log     # 客户端
```

### 按关键字过滤日志

```bash
# 查看错误日志
grep -i error logs/*.log

# 查看警告日志
grep -i warning logs/*.log

# 查看特定时间的日志
tail -n 100 logs/backend.log | grep "2025-11-11"

# 查看 HTTP 状态码为 500 的请求
grep "500" logs/*.log
```

### 日志级别说明

| 级别 | 说明 | 色彩 | 常见消息 |
|------|------|------|--------|
| **DEBUG** | 调试信息 | 灰色 | 数据库查询、变量值 |
| **INFO** | 一般信息 | 绿色 | 服务启动、API 调用 |
| **WARNING** | 警告 | 黄色 | 性能问题、过期特性 |
| **ERROR** | 错误 | 红色 | 异常、失败 |
| **CRITICAL** | 严重错误 | 红色 | 系统故障 |

---

## 高级诊断

### 系统诊断报告

生成完整的诊断报告：

```bash
#!/bin/bash
# 保存为 diagnose.sh

echo "=== 系统诊断报告 ===" > diagnosis.txt
echo "日期: $(date)" >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== 环境信息 ===" >> diagnosis.txt
uname -a >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== Node.js 版本 ===" >> diagnosis.txt
node --version >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== Python 版本 ===" >> diagnosis.txt
python3 --version >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== MySQL 版本 ===" >> diagnosis.txt
mysql --version >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== 进程状态 ===" >> diagnosis.txt
./status.sh >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== 端口占用情况 ===" >> diagnosis.txt
lsof -i :3007,8006,8005 >> diagnosis.txt
echo "" >> diagnosis.txt

echo "=== 最近错误 ===" >> diagnosis.txt
tail -n 50 logs/backend.log | grep -i error >> diagnosis.txt
echo "" >> diagnosis.txt

echo "诊断报告已保存到 diagnosis.txt"
cat diagnosis.txt
```

### 数据库诊断

```bash
# 连接到数据库并运行诊断
mysql -u root << 'EOF'
USE stock_analysis_dev;

-- 检查表数量
SELECT COUNT(*) as table_count FROM information_schema.tables
WHERE table_schema='stock_analysis_dev';

-- 检查每个表的行数
SELECT table_name, table_rows
FROM information_schema.tables
WHERE table_schema='stock_analysis_dev'
ORDER BY table_rows DESC;

-- 检查索引
SELECT table_name, index_name, column_name
FROM information_schema.statistics
WHERE table_schema='stock_analysis_dev'
LIMIT 20;

-- 检查用户
SELECT user, host FROM mysql.user WHERE user IN ('root', 'stock_user');

EOF
```

### 网络诊断

```bash
# 测试到 localhost 的连接
curl -v http://localhost:3007/docs

# 测试 API 响应
curl -X GET http://localhost:3007/api/v1/health

# 查看网络连接状态
netstat -an | grep LISTEN
```

---

## 联系支持

如果问题无法解决：

1. 收集诊断信息：
   ```bash
   tar -czf diagnosis.tar.gz logs/ diagnosis.txt
   ```

2. 查看相关文档：
   - `QUICKSTART.md` - 快速开始指南
   - `README.md` - 项目文档
   - `DEVELOPMENT_PROGRESS.md` - 开发进度

3. 查看日志文件获取详细错误信息

---

**最后更新**: 2025-11-11
**版本**: v2.7.3
