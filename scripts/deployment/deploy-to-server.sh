#!/bin/bash

# 服务器部署脚本
# 用于将股票分析系统部署到远程服务器

set -e  # 遇到错误立即退出

# 配置信息
SERVER_IP="47.92.236.28"
SERVER_USER="root"
SERVER_PASSWORD="Pp123456"
PROJECT_NAME="stock-analysis-system"
REMOTE_DIR="/opt/$PROJECT_NAME"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }
log_info() { echo -e "${BLUE}[ℹ️]${NC} $1"; }

echo "🚀 股票分析系统服务器部署脚本"
echo "目标服务器: $SERVER_IP"
echo "=============================="

# 检查本地环境
check_local_env() {
    log_info "检查本地环境..."

    # 检查必要工具
    if ! command -v sshpass &> /dev/null; then
        log_warn "安装 sshpass..."
        brew install sshpass 2>/dev/null || {
            log_error "请手动安装 sshpass: brew install sshpass"
            exit 1
        }
    fi

    if ! command -v rsync &> /dev/null; then
        log_error "需要 rsync 工具"
        exit 1
    fi

    log_success "本地环境检查完成"
}

# 测试服务器连接
test_server_connection() {
    log_info "测试服务器连接..."

    if sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "echo '连接成功'" 2>/dev/null; then
        log_success "服务器连接正常"
    else
        log_error "无法连接到服务器，请检查IP地址和密码"
        exit 1
    fi
}

# 准备服务器环境
prepare_server() {
    log_info "准备服务器环境..."

    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# 更新系统
yum update -y

# 安装基础工具
yum install -y git curl wget

# 安装 Node.js 16+
curl -fsSL https://rpm.nodesource.com/setup_16.x | bash -
yum install -y nodejs

# 安装 Python 3.8+
yum install -y python3 python3-pip python3-venv

# 安装 MySQL 8.0
if ! command -v mysql &> /dev/null; then
    # 下载并安装 MySQL 8.0 仓库
    wget https://dev.mysql.com/get/mysql80-community-release-el7-3.noarch.rpm
    rpm -ivh mysql80-community-release-el7-3.noarch.rpm
    yum install -y mysql-server

    # 启动并设置开机自启
    systemctl start mysqld
    systemctl enable mysqld

    # 获取临时密码并重置
    TEMP_PASSWORD=$(grep 'temporary password' /var/log/mysqld.log | awk '{print $NF}')
    echo "MySQL临时密码: $TEMP_PASSWORD"

    # 重置密码为 Pp123456
    mysql -u root -p"$TEMP_PASSWORD" --connect-expired-password << 'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED BY 'Pp123456';
CREATE DATABASE IF NOT EXISTS stock_analysis_dev;
FLUSH PRIVILEGES;
SQL
    echo "MySQL密码已设置为: Pp123456"
fi

# 检查版本
echo "环境版本信息:"
echo "Node.js: $(node --version 2>/dev/null || echo '未安装')"
echo "Python: $(python3 --version 2>/dev/null || echo '未安装')"
echo "MySQL: $(mysql --version 2>/dev/null || echo '未安装')"

EOF

    log_success "服务器环境准备完成"
}

# 上传项目文件
upload_project() {
    log_info "上传项目文件..."

    # 创建远程目录
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "mkdir -p $REMOTE_DIR"

    # 上传文件（排除不必要的文件）
    rsync -avz --progress \
        --exclude='node_modules' \
        --exclude='venv' \
        --exclude='*.log' \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.DS_Store' \
        -e "sshpass -p $SERVER_PASSWORD ssh -o StrictHostKeyChecking=no" \
        ./ "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"

    log_success "项目文件上传完成"
}

# 服务器端部署
deploy_on_server() {
    log_info "在服务器上执行部署..."

    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF
cd $REMOTE_DIR

# 设置脚本执行权限
chmod +x scripts/deployment/*.sh

# 创建 .env 文件
cat > backend/.env << 'ENVFILE'
SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:Pp123456@localhost:3306/stock_analysis_dev
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=production
DEBUG=False
ENVFILE

# 执行部署
./scripts/deployment/deploy.sh

EOF

    log_success "服务器部署完成"
}

# 配置防火墙和端口
configure_firewall() {
    log_info "配置防火墙..."

    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
# 开放必要端口
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=3007/tcp  # API端口
    firewall-cmd --permanent --add-port=8005/tcp  # 客户端端口
    firewall-cmd --permanent --add-port=8006/tcp  # 管理端端口
    firewall-cmd --reload
elif command -v ufw &> /dev/null; then
    ufw allow 3007
    ufw allow 8005
    ufw allow 8006
fi

echo "防火墙配置完成"
EOF

    log_success "防火墙配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF
cd $REMOTE_DIR

# 启动所有服务
./scripts/deployment/start.sh

# 检查服务状态
sleep 5
./scripts/deployment/status.sh

EOF

    log_success "服务启动完成"
}

# 显示部署结果
show_results() {
    log_success "🎉 部署完成！"
    echo ""
    echo "📊 服务访问地址:"
    echo "  🔗 API服务:    http://$SERVER_IP:3007"
    echo "  📱 客户端:     http://$SERVER_IP:8005"
    echo "  🖥️ 管理端:     http://$SERVER_IP:8006"
    echo ""
    echo "👤 管理员账号: admin / admin123"
    echo ""
    echo "🔧 服务器管理:"
    echo "  SSH连接: ssh root@$SERVER_IP"
    echo "  项目目录: $REMOTE_DIR"
    echo ""
    echo "📋 常用命令:"
    echo "  启动服务: cd $REMOTE_DIR && ./scripts/deployment/start.sh"
    echo "  停止服务: cd $REMOTE_DIR && ./scripts/deployment/stop.sh"
    echo "  检查状态: cd $REMOTE_DIR && ./scripts/deployment/status.sh"
}

# 主部署流程
main() {
    echo "准备开始部署，请确认以下信息："
    echo "服务器IP: $SERVER_IP"
    echo "用户名: $SERVER_USER"
    echo "项目目录: $REMOTE_DIR"
    echo ""
    read -p "确认部署? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "用户取消部署"
        exit 0
    fi

    check_local_env
    test_server_connection
    prepare_server
    upload_project
    deploy_on_server
    configure_firewall
    start_services
    show_results
}

# 执行主流程
main

log_success "服务器部署脚本执行完成！"