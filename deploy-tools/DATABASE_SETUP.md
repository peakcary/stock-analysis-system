# MySQL 数据库配置指南

## 当前问题

MySQL root 用户的密码认证存在问题。这需要一次性的手动配置。

## 解决方案

### 方案 A: 重新安装 MySQL (推荐，一次性)

```bash
# 1. SSH连接到服务器
sshpass -p "chen_188_8_8" ssh -o StrictHostKeyChecking=no ubuntu@82.157.28.35

# 2. 在服务器上执行：
sudo apt-get remove -y mysql-server
sudo apt-get install -y mysql-server

# 3. 安装过程中会提示设置root密码，输入: Pp123456
# 或者完成后用以下命令重置：
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH caching_sha2_password BY 'Pp123456';"
```

### 方案 B: 使用 Docker MySQL (最简单)

如果你不想处理系统 MySQL，可以用 Docker：

```bash
# 在服务器上：
docker run --name mysql-stock \
  -e MYSQL_ROOT_PASSWORD=Pp123456 \
  -e MYSQL_DATABASE=stock_analysis_prod \
  -p 127.0.0.1:3306:3306 \
  -v /data/mysql:/var/lib/mysql \
  -d mysql:8.0

# 等待容器启动：
sleep 10
docker logs mysql-stock | grep "ready for connections"
```

### 方案 C: 使用临时SQLite (快速测试)

如果你只想快速测试API，可以临时用SQLite：

```bash
# 编辑服务器上的 .env 文件
DATABASE_URL=sqlite:///./stock_analysis.db

# 重启服务
sudo systemctl restart stock-api
```

## 完成后验证

```bash
# 检查数据库连接
curl https://qwquant.com/api/v1/health

# 查看API日志
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo journalctl -u stock-api -n 20 --no-pager"
```

## 自动数据库初始化

完成MySQL配置后，运行初始化脚本：

```bash
cd /opt/stock-analysis-system/backend

# 用Python初始化表结构
python3 init_database.py
```

或从本地运行：

```bash
cd /Users/peakom/work/stock-analysis-system/backend

# 设置环境变量
export DATABASE_URL="mysql+pymysql://root:Pp123456@82.157.28.35:3306/stock_analysis_prod"

# 运行初始化
python3 init_database.py
```

## 快速检查清单

- [ ] MySQL 已安装并运行
- [ ] root 用户可以用 Pp123456 密码连接
- [ ] 数据库 `stock_analysis_prod` 已创建
- [ ] 后端 `.env.production` 已更新数据库URL
- [ ] 运行了 `init_database.py` 初始化表结构
- [ ] 服务已重启：`sudo systemctl restart stock-api`
- [ ] 健康检查通过：`curl https://qwquant.com/api/v1/health`

## 推荐配置

我推荐方案 B (Docker MySQL) 或方案 A (重新安装)。

如有问题，可以：
1. 检查 MySQL 状态：`sudo systemctl status mysql`
2. 查看 MySQL 日志：`sudo tail -50 /var/log/mysql/error.log`
3. 测试 MySQL 连接：`mysql -u root -p`
