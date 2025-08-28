#!/bin/bash

# 云服务器部署脚本
# Cloud Server Deployment Script

set -e  # 遇到错误立即停止

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="stock-analysis-system"
DOCKER_COMPOSE_VERSION="v2.24.0"
DOMAIN=${DOMAIN:-"your-domain.com"}
EMAIL=${EMAIL:-"your-email@example.com"}

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "不建议使用root用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查系统要求
check_system() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "操作系统: Linux"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [[ $MEMORY -lt 2 ]]; then
        log_warning "内存不足 ${MEMORY}GB，建议至少2GB"
    else
        log_success "内存充足: ${MEMORY}GB"
    fi
    
    # 检查磁盘空间
    DISK=$(df -h / | awk 'NR==2{print $4}' | sed 's/G//')
    if [[ ${DISK%.*} -lt 10 ]]; then
        log_warning "磁盘空间不足 ${DISK}GB，建议至少10GB"
    else
        log_success "磁盘空间充足: ${DISK}GB"
    fi
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get upgrade -y
        sudo apt-get install -y curl wget git ufw
    elif command -v yum &> /dev/null; then
        sudo yum update -y
        sudo yum install -y curl wget git firewalld
    else
        log_error "不支持的包管理器"
        exit 1
    fi
    
    log_success "系统更新完成"
}

# 安装Docker
install_docker() {
    if command -v docker &> /dev/null; then
        log_success "Docker 已安装: $(docker --version)"
        return
    fi
    
    log_info "安装 Docker..."
    
    # 官方安装脚本
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    # 启动并启用Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    log_success "Docker 安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose 已安装: $(docker-compose --version)"
        return
    fi
    
    log_info "安装 Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 添加执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    # 创建符号链接
    sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose 安装完成: $(docker-compose --version)"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        sudo ufw --force reset
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        
        # 允许SSH
        sudo ufw allow ssh
        sudo ufw allow 22/tcp
        
        # 允许HTTP/HTTPS
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        
        # 允许应用端口 (仅在需要直接访问时开放)
        # sudo ufw allow 8000/tcp  # Backend API
        # sudo ufw allow 3000/tcp  # Frontend
        # sudo ufw allow 8006/tcp  # Client
        
        sudo ufw --force enable
        log_success "UFW 防火墙配置完成"
        
    elif command -v firewall-cmd &> /dev/null; then
        sudo systemctl start firewalld
        sudo systemctl enable firewalld
        
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        
        sudo firewall-cmd --reload
        log_success "Firewalld 防火墙配置完成"
    fi
}

# 安装SSL证书 (Let's Encrypt)
install_ssl() {
    if [[ "$DOMAIN" == "your-domain.com" ]]; then
        log_warning "跳过SSL证书安装，请先配置域名"
        return
    fi
    
    log_info "安装 Certbot..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y snapd
        sudo snap install core; sudo snap refresh core
        sudo snap install --classic certbot
        sudo ln -sf /snap/bin/certbot /usr/bin/certbot
    elif command -v yum &> /dev/null; then
        sudo yum install -y epel-release
        sudo yum install -y certbot
    fi
    
    log_info "获取SSL证书..."
    sudo certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email
    
    # 设置自动续期
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
    
    log_success "SSL证书安装完成"
}

# 创建项目目录
create_project_dir() {
    log_info "创建项目目录..."
    
    PROJECT_DIR="/opt/$PROJECT_NAME"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_warning "项目目录已存在，备份旧版本..."
        sudo mv "$PROJECT_DIR" "${PROJECT_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    
    log_success "项目目录创建完成: $PROJECT_DIR"
}

# 克隆或更新项目代码
deploy_project() {
    log_info "部署项目代码..."
    
    cd "/opt/$PROJECT_NAME"
    
    # 如果是Git仓库，拉取最新代码
    if [[ -d ".git" ]]; then
        git pull origin main
    else
        log_info "请手动上传项目文件到 /opt/$PROJECT_NAME"
        read -p "项目文件已上传完成? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "请上传项目文件后重新运行"
            exit 1
        fi
    fi
    
    # 检查必要文件
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "未找到 docker-compose.yml 文件"
        exit 1
    fi
    
    log_success "项目代码部署完成"
}

# 配置生产环境变量
configure_env() {
    log_info "配置生产环境变量..."
    
    cd "/opt/$PROJECT_NAME"
    
    if [[ ! -f ".env.prod" ]]; then
        log_info "创建生产环境配置文件..."
        cp .env .env.prod
        
        # 生成安全密钥
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        MYSQL_ROOT_PASS=$(openssl rand -base64 32)
        MYSQL_PASS=$(openssl rand -base64 32)
        
        # 更新配置
        sed -i "s/DEBUG=True/DEBUG=False/" .env.prod
        sed -i "s/ENVIRONMENT=development/ENVIRONMENT=production/" .env.prod
        sed -i "s/your_local_secret_key_here_at_least_32_characters_long/$SECRET_KEY/" .env.prod
        sed -i "s/root123/$MYSQL_ROOT_PASS/" .env.prod
        sed -i "s/stockpass/$MYSQL_PASS/" .env.prod
        
        # 更新域名配置
        if [[ "$DOMAIN" != "your-domain.com" ]]; then
            sed -i "s/localhost/$DOMAIN/g" .env.prod
            sed -i "s/http:/https:/g" .env.prod
        fi
        
        log_warning "请检查并更新 .env.prod 文件中的配置"
        log_warning "特别注意数据库密码和API密钥的配置"
    fi
    
    log_success "环境变量配置完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "/opt/$PROJECT_NAME"
    
    # 使用生产环境配置
    export COMPOSE_FILE=docker-compose.prod.yml
    
    # 如果没有生产配置文件，使用默认配置
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        COMPOSE_FILE=docker-compose.yml
    fi
    
    # 停止旧服务
    docker-compose -f $COMPOSE_FILE down
    
    # 构建并启动服务
    docker-compose -f $COMPOSE_FILE --env-file .env.prod up -d --build
    
    # 等待服务启动
    sleep 30
    
    # 检查服务状态
    docker-compose -f $COMPOSE_FILE ps
    
    log_success "服务启动完成"
}

# 检查服务健康状态
check_health() {
    log_info "检查服务健康状态..."
    
    # 检查后端API
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "后端服务运行正常"
    else
        log_warning "后端服务可能未正常启动"
    fi
    
    # 检查前端服务
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "管理端服务运行正常"
    else
        log_warning "管理端服务可能未正常启动"
    fi
    
    # 检查客户端服务
    if curl -f http://localhost:8006 > /dev/null 2>&1; then
        log_success "用户端服务运行正常"
    else
        log_warning "用户端服务可能未正常启动"
    fi
    
    # 显示Docker状态
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 显示部署信息
show_info() {
    log_success "部署完成!"
    echo
    echo "=== 访问信息 ==="
    if [[ "$DOMAIN" != "your-domain.com" ]]; then
        echo "管理端: https://$DOMAIN"
        echo "用户端: https://$DOMAIN:8006"
        echo "API文档: https://$DOMAIN/docs"
    else
        echo "管理端: http://$(curl -s ifconfig.me):3000"
        echo "用户端: http://$(curl -s ifconfig.me):8006"
        echo "API文档: http://$(curl -s ifconfig.me):8000/docs"
    fi
    echo
    echo "=== 常用命令 ==="
    echo "查看服务状态: cd /opt/$PROJECT_NAME && docker-compose ps"
    echo "查看日志: cd /opt/$PROJECT_NAME && docker-compose logs -f"
    echo "重启服务: cd /opt/$PROJECT_NAME && docker-compose restart"
    echo "停止服务: cd /opt/$PROJECT_NAME && docker-compose down"
    echo
    echo "=== 重要文件位置 ==="
    echo "项目目录: /opt/$PROJECT_NAME"
    echo "环境配置: /opt/$PROJECT_NAME/.env.prod"
    echo "SSL证书: /etc/letsencrypt/live/$DOMAIN/ (如果已配置)"
}

# 主函数
main() {
    echo "=== 股票分析系统云服务器部署 ==="
    echo
    
    check_root
    check_system
    update_system
    install_docker
    install_docker_compose
    configure_firewall
    
    # SSL安装是可选的
    read -p "是否安装SSL证书? (需要已解析的域名) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入域名: " DOMAIN
        read -p "请输入邮箱: " EMAIL
        install_ssl
    fi
    
    create_project_dir
    deploy_project
    configure_env
    start_services
    check_health
    show_info
    
    log_success "部署脚本执行完成!"
}

# 检查参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            EMAIL="$2"
            shift 2
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --domain DOMAIN    设置域名"
            echo "  --email EMAIL      设置邮箱"
            echo "  --help            显示帮助"
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# 执行主函数
main