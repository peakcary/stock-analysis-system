#!/bin/bash
# 股票分析系统环境检查和修复脚本
# Stock Analysis System Environment Check and Repair Script
# 版本：自动检测和修复常见环境问题

set -e

echo "🔍 开始检查股票分析系统环境..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 检查和修复函数
check_and_fix_nodejs() {
    log_info "检查 Node.js 版本..."
    local required_version="20.19.0"
    
    if command -v node &> /dev/null; then
        local current_version=$(node --version | sed 's/v//')
        if [[ "$current_version" < "$required_version" ]]; then
            log_warn "Node.js 版本过低 ($current_version < $required_version)"
            
            if command -v nvm &> /dev/null || [ -s "$HOME/.nvm/nvm.sh" ]; then
                log_info "使用 NVM 升级 Node.js..."
                export NVM_DIR="$HOME/.nvm"
                [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
                nvm install $required_version
                nvm use $required_version
                nvm alias default $required_version
                log_success "Node.js 已升级至 $required_version"
            else
                log_error "需要安装 NVM 或手动升级 Node.js 到 $required_version+"
                return 1
            fi
        else
            log_success "Node.js 版本正常：$current_version"
        fi
    else
        log_error "Node.js 未安装"
        return 1
    fi
}

check_and_fix_python() {
    log_info "检查 Python 环境..."
    
    if command -v python3 &> /dev/null; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python 版本：$version"
        
        # 检查虚拟环境
        if [ ! -d "backend/venv" ]; then
            log_warn "后端虚拟环境不存在，正在创建..."
            cd backend
            python3 -m venv venv
            cd ..
            log_success "虚拟环境已创建"
        fi
        
        # 检查依赖
        log_info "检查 Python 依赖..."
        cd backend
        source venv/bin/activate
        
        # 检查关键依赖
        if ! pip show email-validator &> /dev/null; then
            log_warn "缺少 email-validator，正在安装..."
            pip install email-validator
            log_success "email-validator 已安装"
        fi
        
        if ! pip show fastapi &> /dev/null; then
            log_warn "缺少核心依赖，正在安装..."
            pip install -r requirements.txt
            log_success "依赖已安装"
        fi
        
        cd ..
    else
        log_error "Python3 未安装"
        return 1
    fi
}

check_and_fix_mysql() {
    log_info "检查 MySQL 服务..."
    
    if brew services list | grep mysql@8.0 | grep started &> /dev/null; then
        log_success "MySQL 8.0 服务正在运行"
        
        # 测试数据库连接
        if mysql -u root -pPp123456 -e "SELECT 1" &> /dev/null; then
            log_success "MySQL 连接正常"
            
            # 检查数据库是否存在
            if mysql -u root -pPp123456 -e "USE stock_analysis_dev;" &> /dev/null; then
                log_success "数据库 stock_analysis_dev 存在"
            else
                log_warn "数据库不存在，正在创建..."
                mysql -u root -pPp123456 -e "CREATE DATABASE stock_analysis_dev;" &> /dev/null
                log_success "数据库已创建"
            fi
        else
            log_warn "MySQL 连接失败，尝试修复密码..."
            if mysql -u root -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Pp123456';" &> /dev/null; then
                log_success "MySQL 密码已设置"
            else
                log_error "无法设置 MySQL 密码，请手动运行: mysql_secure_installation"
                return 1
            fi
        fi
    else
        log_warn "MySQL 服务未运行，正在启动..."
        if brew services start mysql@8.0; then
            sleep 5
            log_success "MySQL 服务已启动"
        else
            log_error "无法启动 MySQL 服务"
            return 1
        fi
    fi
}

check_and_fix_network_config() {
    log_info "检查网络配置..."
    local fixed_count=0
    
    # 检查后端配置
    if [ -f "backend/app/core/config.py" ]; then
        if grep -q "localhost:3306" backend/app/core/config.py; then
            log_warn "发现 IPv6 兼容性问题，正在修复..."
            sed -i '' 's/localhost:3306/127.0.0.1:3306/g' backend/app/core/config.py
            sed -i '' 's/"localhost"/"127.0.0.1"/g' backend/app/core/config.py
            ((fixed_count++))
        fi
        
        if grep -q "PORT: int = 8000" backend/app/core/config.py; then
            log_warn "修复后端端口配置..."
            sed -i '' 's/PORT: int = 8000/PORT: int = 3007/g' backend/app/core/config.py
            ((fixed_count++))
        fi
    fi
    
    # 检查客户端配置
    if [ -f "client/vite.config.ts" ]; then
        if grep -q "localhost:3007" client/vite.config.ts; then
            log_warn "修复客户端代理配置..."
            sed -i '' 's/localhost:3007/127.0.0.1:3007/g' client/vite.config.ts
            ((fixed_count++))
        fi
    fi
    
    # 检查管理前端配置
    if [ -f "frontend/vite.config.ts" ]; then
        if grep -q "localhost:" frontend/vite.config.ts; then
            log_warn "修复管理前端配置..."
            sed -i '' 's/localhost:/127.0.0.1:/g' frontend/vite.config.ts
            ((fixed_count++))
        fi
    fi
    
    if [ $fixed_count -gt 0 ]; then
        log_success "已修复 $fixed_count 个网络配置问题"
    else
        log_success "网络配置正常"
    fi
}

check_project_dependencies() {
    log_info "检查项目依赖..."
    
    # 检查客户端依赖
    if [ -d "client" ]; then
        cd client
        if [ ! -d "node_modules" ]; then
            log_warn "客户端依赖缺失，正在安装..."
            npm install
            log_success "客户端依赖已安装"
        else
            log_success "客户端依赖正常"
        fi
        cd ..
    fi
    
    # 检查管理前端依赖
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            log_warn "管理前端依赖缺失，正在安装..."
            npm install
            log_success "管理前端依赖已安装"
        else
            log_success "管理前端依赖正常"
        fi
        cd ..
    fi
}

check_ports_available() {
    log_info "检查端口占用..."
    local ports=(3007 8005 8006)
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            log_warn "端口 $port 被占用"
            local process=$(lsof -Pi :$port -sTCP:LISTEN -t | head -1)
            if [ ! -z "$process" ]; then
                local process_name=$(ps -p $process -o comm= 2>/dev/null || echo "Unknown")
                echo "    占用进程: $process_name (PID: $process)"
            fi
        else
            log_success "端口 $port 可用"
        fi
    done
}

check_startup_scripts() {
    log_info "检查启动脚本..."
    local scripts=("start_backend.sh" "start_client.sh" "start_frontend.sh")
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                log_success "$script 存在且可执行"
            else
                log_warn "$script 不可执行，正在修复..."
                chmod +x "$script"
                log_success "$script 权限已修复"
            fi
        else
            log_error "$script 不存在"
        fi
    done
}

# 主检查流程
main() {
    echo "========================================="
    echo "🔧 股票分析系统环境检查和修复"
    echo "========================================="
    
    local error_count=0
    
    # 执行各项检查
    check_and_fix_nodejs || ((error_count++))
    echo ""
    
    check_and_fix_python || ((error_count++))
    echo ""
    
    check_and_fix_mysql || ((error_count++))
    echo ""
    
    check_and_fix_network_config
    echo ""
    
    check_project_dependencies
    echo ""
    
    check_ports_available
    echo ""
    
    check_startup_scripts
    echo ""
    
    # 总结
    echo "========================================="
    if [ $error_count -eq 0 ]; then
        log_success "🎉 环境检查完成，所有组件正常！"
        echo ""
        echo "✅ 可以运行以下命令启动系统："
        echo "   ./start_all.sh"
        echo ""
        echo "🌐 系统访问地址："
        echo "   📱 用户前端: http://localhost:8006"
        echo "   🔧 管理前端: http://localhost:8005"
        echo "   🔗 后端API: http://localhost:3007/docs"
    else
        log_error "❌ 发现 $error_count 个问题需要手动处理"
        echo ""
        echo "🔧 建议操作："
        echo "1. 检查上述错误信息"
        echo "2. 手动修复相关问题"
        echo "3. 重新运行此脚本验证"
    fi
    echo "========================================="
}

# 检查是否需要帮助
if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo ""
    echo "此脚本将检查并修复以下组件:"
    echo "- Node.js 版本和 NVM 配置"
    echo "- Python 虚拟环境和依赖"
    echo "- MySQL 服务和数据库"
    echo "- 网络配置和 IPv4/IPv6 兼容性"
    echo "- 项目依赖和启动脚本权限"
    echo "- 端口占用情况"
    exit 0
fi

# 运行主检查流程
main