#!/bin/bash
# 环境备份脚本 - 将当前环境打包，便于在其他电脑恢复
# Environment Backup Script

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_${BACKUP_DATE}"

echo "📦 开始备份股票分析系统环境..."
echo "备份目录: ${BACKUP_DIR}"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "🗂️ 备份项目文件..."

# 备份项目代码 (排除不需要的文件)
rsync -av --progress \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='uploads' \
    --exclude='dist' \
    --exclude='build' \
    ./ "${BACKUP_DIR}/project/"

echo "🗄️ 备份数据库..."

# 备份数据库
mysqldump -u root -proot123 --single-transaction --routines --triggers stock_analysis > "${BACKUP_DIR}/database_backup.sql"

echo "⚙️ 备份配置信息..."

# 备份系统信息
cat > "${BACKUP_DIR}/system_info.txt" << EOF
# 系统环境信息
备份时间: $(date)
操作系统: $(uname -a)
Python版本: $(python3 --version 2>/dev/null || echo "未安装")
Node.js版本: $(node --version 2>/dev/null || echo "未安装")
MySQL版本: $(mysql --version 2>/dev/null || echo "未安装")

# 项目依赖版本
后端依赖: 见 requirements.txt
前端依赖: 见 package.json
EOF

# 创建恢复脚本
cat > "${BACKUP_DIR}/restore_environment.sh" << 'EOF'
#!/bin/bash
# 环境恢复脚本

set -e

echo "🔄 开始恢复股票分析系统环境..."

# 检查必要软件
check_requirements() {
    echo "🔍 检查环境要求..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 未安装"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js 未安装" 
        exit 1
    fi
    
    if ! command -v mysql &> /dev/null; then
        echo "❌ MySQL 未安装"
        exit 1
    fi
    
    echo "✅ 基础环境检查通过"
}

# 恢复项目文件
restore_project() {
    echo "📁 恢复项目文件..."
    
    # 复制项目文件到目标目录
    TARGET_DIR="../stock-analysis-system-restored"
    mkdir -p "$TARGET_DIR"
    cp -r project/* "$TARGET_DIR/"
    
    echo "✅ 项目文件恢复到: $TARGET_DIR"
}

# 恢复数据库
restore_database() {
    echo "🗄️ 恢复数据库..."
    
    # 检查 MySQL 连接
    if ! mysql -u root -proot123 -e "SELECT 1;" &>/dev/null; then
        echo "❌ MySQL 连接失败，请确保："
        echo "1. MySQL 服务已启动"
        echo "2. root 密码为 root123"
        exit 1
    fi
    
    # 恢复数据库
    mysql -u root -proot123 < database_backup.sql
    echo "✅ 数据库恢复完成"
}

# 设置环境
setup_environment() {
    echo "⚙️ 设置开发环境..."
    
    cd "$TARGET_DIR"
    
    # 后端环境
    echo "🐍 设置后端环境..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    
    # 前端环境
    echo "📦 设置前端环境..."
    cd frontend
    npm install
    cd ..
    
    # 设置脚本权限
    chmod +x *.sh
    
    echo "✅ 环境设置完成"
}

# 主恢复流程
main() {
    check_requirements
    restore_project
    restore_database
    setup_environment
    
    echo ""
    echo "🎉 环境恢复完成！"
    echo ""
    echo "📋 下一步操作："
    echo "1. cd ../stock-analysis-system-restored"
    echo "2. ./start_backend.sh  # 启动后端"
    echo "3. ./start_frontend.sh # 启动前端"
    echo ""
    echo "🌐 访问地址："
    echo "- 前端: http://localhost:3000"
    echo "- 后端: http://localhost:8000"
}

# 显示帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "环境恢复脚本使用说明："
    echo ""
    echo "前提条件："
    echo "1. Python 3.11+"
    echo "2. Node.js 20+"
    echo "3. MySQL 8.0 (root密码: root123)"
    echo ""
    echo "使用方法："
    echo "./restore_environment.sh"
    exit 0
fi

main
EOF

chmod +x "${BACKUP_DIR}/restore_environment.sh"

echo "📋 创建使用说明..."

# 创建使用说明
cat > "${BACKUP_DIR}/README_RESTORE.md" << 'EOF'
# 环境恢复使用说明

## 🎯 在新电脑上恢复开发环境

### 1. 前提条件
在新电脑上先安装以下软件：

#### macOS:
```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装必要软件
brew install python@3.11 node@20 mysql@8.0 git

# 启动 MySQL
brew services start mysql@8.0

# 设置 MySQL root 密码
mysql -u root
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';
FLUSH PRIVILEGES;
EXIT;
```

#### Linux (Ubuntu/Debian):
```bash
# 更新包管理器
sudo apt update

# 安装必要软件
sudo apt install -y python3.11 python3.11-venv python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs mysql-server-8.0

# 启动 MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# 设置 MySQL root 密码
sudo mysql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123';
FLUSH PRIVILEGES;
EXIT;
```

### 2. 恢复环境
```bash
# 解压备份文件
# 进入备份目录
cd backup_YYYYMMDD_HHMMSS

# 运行恢复脚本
./restore_environment.sh

# 进入恢复的项目目录
cd ../stock-analysis-system-restored

# 启动服务
./start_backend.sh   # 新终端窗口
./start_frontend.sh  # 新终端窗口
```

### 3. 验证恢复
- 访问 http://localhost:3000 (前端)
- 访问 http://localhost:8000 (后端)
- 访问 http://localhost:8000/docs (API文档)

### 4. 开发继续
恢复完成后，查看项目中的 `docs/CURRENT_STATUS.md` 了解开发进度，继续开发工作。
EOF

echo "📊 备份统计信息..."
du -sh "${BACKUP_DIR}"

echo ""
echo "🎉 环境备份完成！"
echo ""
echo "📁 备份位置: ${BACKUP_DIR}"
echo "📋 备份内容:"
echo "   - 完整项目代码"
echo "   - 数据库数据"
echo "   - 系统配置信息"
echo "   - 自动恢复脚本"
echo ""
echo "💾 将整个 ${BACKUP_DIR} 目录复制到新电脑"
echo "📖 在新电脑上查看: ${BACKUP_DIR}/README_RESTORE.md"
echo ""
echo "🔄 在新电脑上恢复:"
echo "   cd ${BACKUP_DIR}"
echo "   ./restore_environment.sh"