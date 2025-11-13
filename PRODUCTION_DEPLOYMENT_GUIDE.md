# 生产环境部署指南

## 📋 目录

1. [快速部署](#快速部署)
2. [详细步骤](#详细步骤)
3. [验证部署](#验证部署)
4. [常见问题](#常见问题)

---

## 🚀 快速部署

### 前置要求

```bash
# 1. 安装 sshpass (macOS)
brew install sshpass

# 2. 从项目根目录运行部署脚本
./scripts/deploy/deploy-production.sh 82.157.28.35
```

### 服务器信息

| 项目 | 值 |
|------|-----|
| **服务器 IP** | 82.157.28.35 |
| **SSH 用户** | ubuntu |
| **SSH 密码** | chen_188_8_8 |
| **项目路径** | /opt/stock-analysis-system |
| **部署分支** | main |

---

## 📖 详细步骤

### 使用自动化脚本（推荐）

```bash
# 执行部署脚本
chmod +x scripts/deploy/deploy-production.sh
./scripts/deploy/deploy-production.sh 82.157.28.35
```

脚本会自动执行：
1. ✅ 停止现有服务
2. ✅ 备份现有代码
3. ✅ 克隆最新代码
4. ✅ 安装依赖
5. ✅ 启动后端服务
6. ✅ 重启 Nginx
7. ✅ 验证部署

### 手动部署步骤

```bash
# 步骤1：连接服务器
ssh ubuntu@82.157.28.35

# 步骤2：停止现有服务
pkill -9 gunicorn

# 步骤3：备份现有代码
cd /opt
sudo mv stock-analysis-system stock-analysis-system.bak

# 步骤4：克隆最新代码
sudo git clone -b main https://github.com/peakcary/stock-analysis-system.git stock-analysis-system
cd stock-analysis-system
sudo chown -R ubuntu:ubuntu .

# 步骤5：安装依赖
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 步骤6：启动后端服务
nohup gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:3007 \
  --access-logfile /var/log/gunicorn-access.log \
  --error-logfile /var/log/gunicorn-error.log \
  --daemon \
  app.main:app

# 步骤7：重启 Nginx
sudo systemctl restart nginx
```

---

## ✅ 验证部署

### 检查后端服务

```bash
# 检查进程
ps aux | grep gunicorn

# 测试 API
curl -I http://82.157.28.35:3007/docs

# 查看错误日志
tail -50 /var/log/gunicorn-error.log
```

### 访问应用

| 服务 | URL |
|------|-----|
| **后端 API** | http://82.157.28.35:3007 |
| **API 文档** | http://82.157.28.35:3007/docs |
| **前端应用** | http://82.157.28.35 |

### 默认登录凭证

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 用户 | fullaccess_user | fullaccess123 |

---

## 🔍 常见问题

### Q1: 部署失败？

检查日志：
```bash
ssh ubuntu@82.157.28.35
tail -100 /var/log/gunicorn-error.log
```

### Q2: 端口被占用？

```bash
# 查找占用进程
sudo lsof -i :3007

# 杀死进程
sudo kill -9 [PID]
```

### Q3: 数据库连接失败？

检查环境变量：
```bash
cd /opt/stock-analysis-system/backend
cat .env | grep DATABASE
```

### Q4: 快速回滚？

```bash
cd /opt
pkill -9 gunicorn
sudo rm -rf stock-analysis-system
sudo mv stock-analysis-system.bak stock-analysis-system
```

---

## 📝 部署清单

部署前：
- [ ] 代码已 commit 到 main 分支
- [ ] 所有测试已通过
- [ ] 通知了团队

部署后：
- [ ] API 可访问 (http://82.157.28.35:3007)
- [ ] 前端应用可加载
- [ ] 登录功能正常
- [ ] 无错误日志

---

**版本**: 1.0
**最后更新**: 2025-01-13
