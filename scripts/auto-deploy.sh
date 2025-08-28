#!/bin/bash

# 自动化部署脚本 - 用于CI/CD或更新部署
# Auto Deployment Script for CI/CD or Updates

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
PROJECT_DIR="/opt/stock-analysis-system"
BACKUP_DIR="/opt/backups"
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
GIT_BRANCH="main"
SLACK_WEBHOOK_URL=""  # 可选：Slack通知URL

# 日志函数
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] [INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR]${NC} $1"
}

# Slack通知函数
send_slack_notification() {
    local message="$1"
    local color="${2:-good}"
    
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" || log_warning "Slack通知发送失败"
    fi
}

# 检查权限
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户运行，建议使用普通用户"
    fi
    
    if [[ ! -w "$PROJECT_DIR" ]]; then
        log_error "没有项目目录写权限: $PROJECT_DIR"
        exit 1
    fi
}

# 创建备份
create_backup() {
    log_info "创建备份..."
    
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$BACKUP_DIR/backup_$backup_timestamp"
    
    mkdir -p "$backup_path"
    
    cd "$PROJECT_DIR"
    
    # 备份数据库
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q mysql; then
        log_info "备份数据库..."
        docker-compose -f "$COMPOSE_FILE" exec -T mysql mysqldump \
            -u root -p$MYSQL_ROOT_PASSWORD stock_analysis \
            > "$backup_path/database.sql" 2>/dev/null || log_warning "数据库备份失败"
    fi
    
    # 备份上传文件
    if [[ -d "backend/uploads" ]]; then
        log_info "备份上传文件..."
        tar -czf "$backup_path/uploads.tar.gz" backend/uploads/
    fi
    
    # 备份配置文件
    cp "$ENV_FILE" "$backup_path/" 2>/dev/null || true
    
    # 清理旧备份 (保留最近7天)
    find "$BACKUP_DIR" -maxdepth 1 -name "backup_*" -mtime +7 -exec rm -rf {} \;
    
    log_success "备份完成: $backup_path"
    echo "$backup_path" > /tmp/latest_backup_path
}

# 更新代码
update_code() {
    log_info "更新应用代码..."
    
    cd "$PROJECT_DIR"
    
    # 保存当前commit hash
    local current_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    log_info "当前版本: $current_commit"
    
    # 拉取最新代码
    if [[ -d ".git" ]]; then
        git fetch origin
        git reset --hard origin/$GIT_BRANCH
        local new_commit=$(git rev-parse HEAD)
        log_info "更新到版本: $new_commit"
        
        if [[ "$current_commit" == "$new_commit" ]]; then
            log_info "代码已是最新版本，跳过更新"
            return 1
        fi
    else
        log_warning "不是Git仓库，跳过代码更新"
        return 1
    fi
    
    log_success "代码更新完成"
    return 0
}

# 健康检查
health_check() {
    local service="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1
    
    log_info "等待 $service 服务启动..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "$service 服务健康检查通过"
            return 0
        fi
        
        log_info "尝试 $attempt/$max_attempts - 等待 $service 服务启动..."
        sleep 5
        ((attempt++))
    done
    
    log_error "$service 服务健康检查失败"
    return 1
}

# 服务健康检查
check_all_services() {
    log_info "检查所有服务健康状态..."
    
    local services_ok=true
    
    # 检查后端API
    if ! health_check "Backend API" "http://localhost:8000/health"; then
        services_ok=false
    fi
    
    # 检查前端
    if ! health_check "Frontend" "http://localhost:3000"; then
        services_ok=false
    fi
    
    # 检查客户端
    if ! health_check "Client" "http://localhost:8006"; then
        services_ok=false
    fi
    
    # 检查Nginx (如果配置了域名)
    if [[ -n "$DOMAIN" ]]; then
        if ! health_check "Nginx" "https://$DOMAIN/nginx-health"; then
            services_ok=false
        fi
    fi
    
    if [[ "$services_ok" == true ]]; then
        log_success "所有服务健康检查通过"
        return 0
    else
        log_error "部分服务健康检查失败"
        return 1
    fi
}

# 部署应用
deploy_application() {
    log_info "部署应用..."
    
    cd "$PROJECT_DIR"
    
    # 检查必要文件
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "未找到Docker Compose文件: $COMPOSE_FILE"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "未找到环境配置文件: $ENV_FILE"
        exit 1
    fi
    
    # 拉取最新镜像
    log_info "拉取Docker镜像..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" pull || log_warning "部分镜像拉取失败"
    
    # 停止服务
    log_info "停止旧服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down
    
    # 构建并启动服务
    log_info "构建并启动服务..."
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build
    
    # 等待服务启动
    sleep 30
    
    # 检查服务状态
    docker-compose -f "$COMPOSE_FILE" ps
    
    log_success "应用部署完成"
}

# 回滚功能
rollback() {
    log_warning "执行回滚操作..."
    
    local backup_path
    if [[ -f "/tmp/latest_backup_path" ]]; then
        backup_path=$(cat /tmp/latest_backup_path)
    else
        log_error "未找到备份路径，无法回滚"
        exit 1
    fi
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "备份目录不存在: $backup_path"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # 回滚数据库
    if [[ -f "$backup_path/database.sql" ]]; then
        log_info "回滚数据库..."
        docker-compose -f "$COMPOSE_FILE" exec -T mysql mysql \
            -u root -p$MYSQL_ROOT_PASSWORD stock_analysis \
            < "$backup_path/database.sql" 2>/dev/null || log_warning "数据库回滚失败"
    fi
    
    # 回滚上传文件
    if [[ -f "$backup_path/uploads.tar.gz" ]]; then
        log_info "回滚上传文件..."
        rm -rf backend/uploads/*
        tar -xzf "$backup_path/uploads.tar.gz" -C ./
    fi
    
    # 重启服务
    docker-compose -f "$COMPOSE_FILE" restart
    
    log_success "回滚完成"
    send_slack_notification "部署回滚完成: $(hostname)" "warning"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    
    # 清理未使用的镜像
    docker image prune -af --filter "until=24h"
    
    # 清理未使用的容器
    docker container prune -f
    
    # 清理未使用的网络
    docker network prune -f
    
    # 清理未使用的卷 (谨慎使用)
    # docker volume prune -f
    
    log_success "资源清理完成"
}

# 主部署流程
main_deploy() {
    log_info "开始自动部署流程..."
    send_slack_notification "开始部署: $(hostname)" "good"
    
    local deploy_start_time=$(date +%s)
    
    # 检查权限
    check_permissions
    
    # 创建备份
    create_backup
    
    # 更新代码
    if update_code; then
        # 部署应用
        deploy_application
        
        # 健康检查
        if check_all_services; then
            # 清理资源
            cleanup
            
            local deploy_end_time=$(date +%s)
            local deploy_duration=$((deploy_end_time - deploy_start_time))
            
            log_success "部署完成! 耗时: ${deploy_duration}秒"
            send_slack_notification "部署成功: $(hostname) - 耗时: ${deploy_duration}秒" "good"
        else
            log_error "健康检查失败，考虑回滚"
            send_slack_notification "部署后健康检查失败: $(hostname)" "danger"
            
            if [[ "$AUTO_ROLLBACK" == "true" ]]; then
                rollback
            fi
            exit 1
        fi
    else
        log_info "无需更新，部署流程结束"
    fi
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo
    echo "选项:"
    echo "  deploy          执行部署 (默认)"
    echo "  rollback        执行回滚"
    echo "  health-check    仅执行健康检查"
    echo "  backup          仅创建备份"
    echo "  cleanup         仅清理资源"
    echo "  --auto-rollback 部署失败时自动回滚"
    echo "  --help          显示此帮助"
    echo
    echo "环境变量:"
    echo "  PROJECT_DIR     项目目录 (默认: /opt/stock-analysis-system)"
    echo "  GIT_BRANCH      Git分支 (默认: main)"
    echo "  SLACK_WEBHOOK_URL  Slack通知URL"
    echo "  AUTO_ROLLBACK   自动回滚 (true/false)"
}

# 参数处理
AUTO_ROLLBACK="${AUTO_ROLLBACK:-false}"
ACTION="deploy"

while [[ $# -gt 0 ]]; do
    case $1 in
        deploy)
            ACTION="deploy"
            shift
            ;;
        rollback)
            ACTION="rollback"
            shift
            ;;
        health-check)
            ACTION="health-check"
            shift
            ;;
        backup)
            ACTION="backup"
            shift
            ;;
        cleanup)
            ACTION="cleanup"
            shift
            ;;
        --auto-rollback)
            AUTO_ROLLBACK="true"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 执行相应操作
case $ACTION in
    deploy)
        main_deploy
        ;;
    rollback)
        rollback
        ;;
    health-check)
        check_all_services
        ;;
    backup)
        create_backup
        ;;
    cleanup)
        cleanup
        ;;
    *)
        log_error "未知操作: $ACTION"
        show_help
        exit 1
        ;;
esac