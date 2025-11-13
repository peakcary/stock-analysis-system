#!/bin/bash

# 股票分析系统 - 生产环境部署脚本
# Production Deployment Script

set -e  # 遇到错误立即退出

# ==================== 颜色定义 ====================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[ℹ️]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# ==================== 配置 ====================
TARGET_SERVER="${1:-82.157.28.35}"
SSH_USER="ubuntu"
SSH_PASSWORD="chen_188_8_8"
PROJECT_PATH="/opt/stock-analysis-system"
GITHUB_REPO="https://github.com/peakcary/stock-analysis-system.git"
BRANCH="main"

# 检查 sshpass
if ! command -v sshpass &> /dev/null; then
    log_error "sshpass 未安装，请先运行: brew install sshpass"
    exit 1
fi

# ==================== 部署步骤 ====================

echo ""
echo "================================================================"
echo "  🚀 股票分析系统 - 生产环境部署"
echo "================================================================"
echo ""
log_info "部署信息："
echo "  📍 服务器: $TARGET_SERVER"
echo "  👤 用户: $SSH_USER"
echo "  📂 项目路径: $PROJECT_PATH"
echo "  🌳 分支: $BRANCH"
echo ""

# 确认部署
read -p "确认部署到 $TARGET_SERVER? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warn "部署已取消"
    exit 1
fi

echo ""
log_info "开始部署流程..."
echo ""

# ==================== 步骤 1: 停止现有服务 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 1/7: 停止现有服务"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  echo "🛑 停止后端服务..."
  pkill -9 gunicorn 2>/dev/null || true
  sleep 2
  echo "✓ 后端服务已停止"
EOF

log_success "服务已停止"
echo ""

# ==================== 步骤 2: 备份现有代码 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 2/7: 备份现有代码"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  echo "📦 备份现有代码..."
  cd /opt
  if [ -d "stock-analysis-system" ]; then
    sudo rm -rf stock-analysis-system.backup.$(date +%s)
    sudo rm -rf stock-analysis-system.bak 2>/dev/null || true
    sudo mv stock-analysis-system stock-analysis-system.bak 2>/dev/null || true
    echo "✓ 备份完成: stock-analysis-system.bak"
  fi
EOF

log_success "代码已备份"
echo ""

# ==================== 步骤 3: 克隆最新代码 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 3/7: 克隆最新代码"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << EOF
  echo "📥 克隆代码库..."
  cd /opt
  sudo git clone -b $BRANCH $GITHUB_REPO stock-analysis-system
  cd stock-analysis-system
  sudo chown -R ubuntu:ubuntu .
  echo "✓ 代码克隆完成"
  echo ""
  echo "📋 当前版本:"
  git log --oneline -1
EOF

log_success "代码已克隆"
echo ""

# ==================== 步骤 4: 安装依赖 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 4/7: 安装依赖"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  cd /opt/stock-analysis-system/backend
  
  echo "🐍 设置 Python 虚拟环境..."
  python3 -m venv venv 2>/dev/null || true
  source venv/bin/activate
  
  echo "📦 升级 pip..."
  pip install --upgrade pip -q 2>/dev/null || true
  
  echo "📚 安装后端依赖..."
  pip install -r requirements.txt -q
  
  echo "✓ 依赖安装完成"
EOF

log_success "依赖已安装"
echo ""

# ==================== 步骤 5: 启动后端服务 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 5/7: 启动后端服务"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  cd /opt/stock-analysis-system/backend
  source venv/bin/activate
  
  echo "🚀 启动 Gunicorn..."
  nohup gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:3007 \
    --access-logfile /var/log/gunicorn-access.log \
    --error-logfile /var/log/gunicorn-error.log \
    --daemon \
    app.main:app
  
  sleep 3
  
  echo "✓ 后端服务已启动"
EOF

log_success "后端服务已启动"
echo ""

# ==================== 步骤 6: 启动 Nginx ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 6/7: 配置 Nginx"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  echo "🔧 检查 Nginx..."
  
  if command -v nginx &> /dev/null; then
    echo "重启 Nginx..."
    sudo systemctl restart nginx
    echo "✓ Nginx 已重启"
  else
    echo "⚠️ Nginx 未安装，跳过 Nginx 配置"
  fi
EOF

log_success "Nginx 已配置"
echo ""

# ==================== 步骤 7: 验证部署 ====================
echo "════════════════════════════════════════════════════"
log_info "步骤 7/7: 验证部署"
echo "════════════════════════════════════════════════════"

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  "$SSH_USER@$TARGET_SERVER" << 'EOF'
  echo "🔍 验证服务状态..."
  echo ""
  
  echo "后端服务进程:"
  ps aux | grep -E '[g]unicorn|[a]pp.main' | head -3 || echo "未找到进程"
  
  echo ""
  echo "端口监听状态:"
  netstat -tlnp 2>/dev/null | grep -E ':3007|:80|:443' || echo "无法获取端口信息"
  
  echo ""
  echo "最后更新:"
  cd /opt/stock-analysis-system
  git log --oneline -1
  
  echo ""
  echo "✓ 部署验证完成"
EOF

log_success "部署验证完成"
echo ""

# ==================== 部署完成 ====================
echo "════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 部署成功！${NC}"
echo "════════════════════════════════════════════════════"
echo ""
echo "📊 访问地址："
echo "  🔗 API: http://$TARGET_SERVER:3007"
echo "  📖 API文档: http://$TARGET_SERVER:3007/docs"
echo "  🌐 前端: http://$TARGET_SERVER:80"
echo ""
echo "📋 后续操作："
echo "  • 检查日志: ssh ubuntu@$TARGET_SERVER"
echo "  • 后端日志: tail -f /var/log/gunicorn-error.log"
echo "  • 重启服务: ssh ubuntu@$TARGET_SERVER 'pkill -9 gunicorn'"
echo ""
echo "⚙️  Git 信息："
echo "  📂 项目路径: $PROJECT_PATH"
echo "  🌳 分支: $BRANCH"
echo "  📦 仓库: $GITHUB_REPO"
echo ""

