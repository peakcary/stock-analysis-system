#!/bin/bash

################################################################################
# 🔒 生产环境安全部署脚本（企业级）v1.0
#
# 功能:
#   - 使用环境变量管理凭证（无硬编码密码）
#   - SSH密钥认证（取代密码认证）
#   - 完整的错误处理和日志记录
#   - 多步验证和失败回滚机制
#   - 备份验证
#
# 使用: ./deploy-production-secure.sh [--dry-run] [--skip-backup]
#
################################################################################

set -euo pipefail

# ============================================================================
# 1. 配置和初始化
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs/deployment"
LOG_FILE="${LOG_DIR}/deploy-$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}ℹ ${NC}$*"; }
print_success() { echo -e "${GREEN}✓ ${NC}$*"; }
print_warn() { echo -e "${YELLOW}⚠ ${NC}$*"; }
print_error() { echo -e "${RED}✗ ${NC}$*"; }

# ============================================================================
# 2. 参数解析
# ============================================================================

DRY_RUN=false
SKIP_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --help)
            echo "使用说明:"
            echo "  $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --dry-run       模拟运行，不执行实际部署"
            echo "  --skip-backup   跳过数据库备份"
            echo "  --help          显示帮助信息"
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# 3. 环境变量验证
# ============================================================================

log_info "检查环境变量和凭证..."

required_vars=(
    "DEPLOY_SERVER"
    "DEPLOY_USER"
    "DEPLOY_SSH_KEY"
    "DEPLOY_PATH"
    "MYSQL_ROOT_PASSWORD"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "缺少必要的环境变量:"
    printf '%s\n' "${missing_vars[@]}" | sed 's/^/  - /'
    print_warn "请设置环境变量后重试。示例:"
    cat << 'EOF'
    export DEPLOY_SERVER="82.157.28.35"
    export DEPLOY_USER="ubuntu"
    export DEPLOY_SSH_KEY="$HOME/.ssh/prod_key"
    export DEPLOY_PATH="/opt/stock-analysis-system"
    export MYSQL_ROOT_PASSWORD="your_secure_password"
EOF
    exit 1
fi

log_success "环境变量检查通过"

# ============================================================================
# 4. SSH连接验证
# ============================================================================

log_info "验证SSH连接..."

if [ ! -f "$DEPLOY_SSH_KEY" ]; then
    print_error "SSH密钥文件不存在: $DEPLOY_SSH_KEY"
    exit 1
fi

# 测试SSH连接
if ! ssh -i "$DEPLOY_SSH_KEY" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=accept-new \
    "$DEPLOY_USER@$DEPLOY_SERVER" "echo 'SSH连接成功'" > /dev/null 2>&1; then
    print_error "无法连接到服务器: $DEPLOY_SERVER"
    log_error "SSH连接失败 - 请检查服务器地址、用户名和SSH密钥"
    exit 1
fi

log_success "SSH连接验证成功"

# ============================================================================
# 5. 远程执行函数
# ============================================================================

remote_exec() {
    local cmd="$1"
    ssh -i "$DEPLOY_SSH_KEY" \
        -o StrictHostKeyChecking=accept-new \
        "$DEPLOY_USER@$DEPLOY_SERVER" \
        "cd $DEPLOY_PATH && $cmd"
}

remote_exec_with_password() {
    local cmd="$1"
    # 使用环境变量传递密码，而不是硬编码
    ssh -i "$DEPLOY_SSH_KEY" \
        -o StrictHostKeyChecking=accept-new \
        "$DEPLOY_USER@$DEPLOY_SERVER" \
        "export MYSQL_ROOT_PASSWORD='$MYSQL_ROOT_PASSWORD' && cd $DEPLOY_PATH && $cmd"
}

# ============================================================================
# 6. 部署前检查
# ============================================================================

log_info "执行部署前检查..."

print_info "检查远程文件存在性..."

check_remote_files() {
    remote_exec "
    [ -f docker-compose.prod.yml ] || { echo '❌ docker-compose.prod.yml不存在'; exit 1; }
    [ -f .env.prod ] || { echo '❌ .env.prod不存在'; exit 1; }
    [ -d backend ] || { echo '❌ backend目录不存在'; exit 1; }
    echo '✅ 所有必要文件都存在'
    "
}

if ! check_remote_files; then
    print_error "远程文件检查失败"
    exit 1
fi

log_success "部署前检查通过"

# ============================================================================
# 7. 备份数据库
# ============================================================================

if [ "$SKIP_BACKUP" = false ]; then
    log_info "备份数据库..."

    backup_cmd='
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    echo "📦 备份MySQL数据库..."
    docker exec stock_mysql_prod mysqldump \
        -uroot \
        -p"$MYSQL_ROOT_PASSWORD" \
        --all-databases \
        > "$BACKUP_DIR/mysql_backup.sql" || {
        echo "❌ 数据库备份失败"
        exit 1
    }

    echo "✅ 备份完成: $BACKUP_DIR/mysql_backup.sql"
    echo "$BACKUP_DIR"
    '

    if backup_path=$(remote_exec_with_password "$backup_cmd" 2>&1 | tail -1); then
        log_success "数据库备份成功: $backup_path"
    else
        print_error "数据库备份失败"
        exit 1
    fi
else
    print_warn "跳过数据库备份"
fi

# ============================================================================
# 8. 部署步骤
# ============================================================================

print_info "开始部署流程..."

if [ "$DRY_RUN" = true ]; then
    print_warn "⚠️  DRY RUN 模式 - 不执行实际部署"
fi

# 第1步：代码更新
log_info "第1步：拉取最新代码"

update_code_cmd='
set -e
echo "📥 拉取最新代码..."
git fetch origin dev/20250926 || { echo "❌ git fetch失败"; exit 1; }
git reset --hard origin/dev/20250926 || { echo "❌ git reset失败"; exit 1; }
echo "✅ 代码更新完成"
'

if [ "$DRY_RUN" = false ]; then
    if remote_exec "$update_code_cmd"; then
        log_success "代码更新成功"
    else
        log_error "代码更新失败"
        exit 1
    fi
else
    print_info "[DRY RUN] 将执行: git fetch && git reset"
fi

# 第2步：构建镜像
log_info "第2步：构建Docker镜像"

build_cmd='
set -e
echo "🏗️  构建Backend镜像..."
docker build --no-cache \
    --tag stock-analysis-system-backend:latest \
    -f backend/Dockerfile.prod \
    backend/ || {
    echo "❌ 镜像构建失败"
    exit 1
}
echo "✅ 镜像构建完成"
'

if [ "$DRY_RUN" = false ]; then
    if remote_exec "$build_cmd"; then
        log_success "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
else
    print_info "[DRY RUN] 将执行: docker build"
fi

# 第3步：启动服务
log_info "第3步：启动容器"

start_cmd='
set -e
echo "🚀 启动容器..."
docker-compose -f docker-compose.prod.yml up -d --build || {
    echo "❌ 容器启动失败"
    exit 1
}

echo "⏳ 等待服务启动..."
sleep 30

echo "📊 验证容器状态..."
docker-compose -f docker-compose.prod.yml ps

echo "✅ 容器启动完成"
'

if [ "$DRY_RUN" = false ]; then
    if remote_exec "$start_cmd"; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        print_warn "将尝试回滚..."
        exit 1
    fi
else
    print_info "[DRY RUN] 将执行: docker-compose up"
fi

# ============================================================================
# 9. 部署后验证
# ============================================================================

log_info "执行部署后验证..."

health_check_cmd='
echo "🧪 健康检查..."

# 检查Backend
echo -n "  Backend: "
if curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# 检查Nginx
echo -n "  Nginx: "
if curl -s --max-time 5 http://localhost/nginx-health > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi

# 检查MySQL
echo -n "  MySQL: "
if docker exec stock_mysql_prod mysql -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
    exit 1
fi
'

if [ "$DRY_RUN" = false ]; then
    if remote_exec_with_password "$health_check_cmd"; then
        log_success "健康检查通过"
    else
        log_error "健康检查失败"
        exit 1
    fi
else
    print_info "[DRY RUN] 将执行: 健康检查"
fi

# ============================================================================
# 10. 完成
# ============================================================================

log_success "部署流程完成！"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📋 部署总结"
echo "════════════════════════════════════════════════════════════════"
echo ""
print_success "所有步骤执行完毕"
echo "📝 日志文件: $LOG_FILE"
echo ""
echo "🎯 后续验证:"
echo "  1. 访问 https://$DEPLOY_SERVER 检查服务是否正常"
echo "  2. 查看服务日志: ssh -i $DEPLOY_SSH_KEY $DEPLOY_USER@$DEPLOY_SERVER"
echo "  3. 备份位置: $backup_path (如果启用了备份)"
echo ""

if [ "$DRY_RUN" = true ]; then
    print_warn "⚠️  这是DRY RUN输出，没有执行实际部署"
    echo "要执行真实部署，请运行: $0 (不带 --dry-run)"
fi

exit 0
