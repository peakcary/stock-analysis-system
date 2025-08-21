# 跨电脑环境迁移指南

## 🎯 使用场景
- 在多台电脑上开发同一个项目
- 团队成员环境同步
- 开发环境备份和恢复
- 从开发环境迁移到生产环境

## 🔄 完整的环境迁移流程

### 1. 在当前电脑备份环境
```bash
# 在项目根目录执行
./backup_environment.sh

# 将生成的备份目录复制到新电脑
# backup_YYYYMMDD_HHMMSS/
```

### 2. 在新电脑恢复环境
```bash
# 解压备份文件后
cd backup_YYYYMMDD_HHMMSS
./restore_environment.sh

# 恢复完成后
cd ../stock-analysis-system-restored
./start_dev.sh  # 一键启动开发环境
```

## 📋 快速开发流程 (无Docker)

### 首次设置新电脑
```bash
# 1. 安装基础环境
./setup_environment.sh

# 2. 初始化数据库  
./setup_database.sh

# 3. 一键启动开发
./start_dev.sh
```

### 日常开发流程
```bash
# 启动开发环境
./start_dev.sh

# 开发完成后停止
./stop_dev.sh

# 需要时备份环境
./backup_environment.sh
```

## 🛠️ 可用的脚本命令

| 脚本 | 功能 | 使用时机 |
|------|------|----------|
| `setup_environment.sh` | 安装所有基础软件和环境 | 新电脑首次设置 |
| `setup_database.sh` | 初始化数据库和配置 | 首次设置或重置数据库 |
| `start_dev.sh` | 一键启动开发环境 | 日常开发启动 |
| `start_backend.sh` | 仅启动后端服务 | 单独调试后端 |
| `start_frontend.sh` | 仅启动前端服务 | 单独调试前端 |
| `stop_dev.sh` | 停止所有开发服务 | 开发结束 |
| `backup_environment.sh` | 备份完整环境 | 换电脑前/重要节点 |

## 🔧 手动环境配置 (备选方案)

### 软件要求
- **Python 3.11+**: 后端开发语言
- **Node.js 20+**: 前端开发环境  
- **MySQL 8.0**: 数据库
- **Git**: 版本控制

### macOS 安装
```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装软件
brew install python@3.11 node@20 mysql@8.0 git

# 启动 MySQL 并设置密码
brew services start mysql@8.0
mysql -u root
> ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';
> FLUSH PRIVILEGES;
> EXIT;
```

### Linux (Ubuntu/Debian) 安装
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 安装 Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 MySQL
sudo apt install -y mysql-server-8.0
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置 MySQL 密码
sudo mysql
> ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';
> FLUSH PRIVILEGES;
> EXIT;

# 安装 Git
sudo apt install -y git
```

### Windows 安装
```powershell
# 使用 Chocolatey 包管理器
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# 安装软件
choco install python311 nodejs mysql git -y

# 手动设置 MySQL 密码为 root123
```

## 🚨 常见问题解决

### 问题1: MySQL 连接失败
```bash
# 检查 MySQL 状态
# macOS
brew services list | grep mysql

# Linux  
sudo systemctl status mysql

# 重置 MySQL 密码
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';
FLUSH PRIVILEGES;
```

### 问题2: 端口被占用
```bash
# 查看端口占用
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 关闭占用进程
pkill -f "uvicorn"
pkill -f "vite"
```

### 问题3: Python 虚拟环境问题
```bash
# 重新创建虚拟环境
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题4: 前端依赖安装失败
```bash
# 清理并重新安装
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📦 环境迁移清单

### 迁移前检查
- [ ] 代码已提交到 Git 仓库
- [ ] 数据库数据已备份
- [ ] 运行 `./backup_environment.sh`
- [ ] 备份目录已复制到新电脑

### 新电脑设置清单
- [ ] 安装基础软件 (Python, Node.js, MySQL, Git)
- [ ] 设置 MySQL root 密码为 root123
- [ ] 运行恢复脚本
- [ ] 验证环境正常启动
- [ ] 查看 `docs/CURRENT_STATUS.md` 继续开发

## 🎯 最佳实践

1. **每次重要开发节点都备份环境**
2. **使用 Git 管理代码版本**
3. **定期更新 `docs/CURRENT_STATUS.md`**
4. **保持数据库数据的备份习惯**
5. **在新电脑上验证环境后再开始开发**

这样无论在哪台电脑上，都能快速恢复到完全相同的开发环境！