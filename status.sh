#!/bin/bash

# 股票分析系统 - 状态检查脚本
echo "📊 股票分析系统状态检查"
echo "======================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# 获取端口配置
if [ -f "ports.env" ]; then
    source ports.env
else
    BACKEND_PORT=3007
    CLIENT_PORT=8005
    FRONTEND_PORT=8006
fi

echo "🔍 检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📊 端口配置: API($BACKEND_PORT) | 客户端($CLIENT_PORT) | 管理端($FRONTEND_PORT)"
echo ""

RUNNING_SERVICES=0
TOTAL_SERVICES=3

# 检查单个服务状态
check_service_status() {
    local port=$1
    local name=$2
    local url=$3
    local pid_file=$4
    
    printf "%-12s " "$name:"
    
    # 检查端口占用
    if lsof -ti:$port &>/dev/null; then
        # 获取进程信息
        local pids=$(lsof -ti:$port)
        local main_pid=$(echo $pids | awk '{print $1}')
        
        # 检查PID文件
        local pid_status=""
        if [ -f "$pid_file" ]; then
            local file_pid=$(cat "$pid_file")
            if echo "$pids" | grep -q "$file_pid"; then
                pid_status=" (PID: $file_pid)"
            else
                pid_status=" (PID文件过期)"
            fi
        else
            pid_status=" (PID: $main_pid, 无文件)"
        fi
        
        # 检查HTTP响应
        if curl -s --max-time 3 "$url" &>/dev/null; then
            log_success "运行正常$pid_status"
            ((RUNNING_SERVICES++))
            return 0
        else
            log_warn "端口占用但HTTP无响应$pid_status" 
            return 1
        fi
    else
        log_error "未运行"
        return 1
    fi
}

# 检查各服务状态
log_info "服务运行状态:"
check_service_status $BACKEND_PORT "API服务" "http://localhost:$BACKEND_PORT/" "logs/backend.pid"
check_service_status $CLIENT_PORT "客户端" "http://localhost:$CLIENT_PORT/" "logs/client.pid"
check_service_status $FRONTEND_PORT "管理端" "http://localhost:$FRONTEND_PORT/" "logs/frontend.pid"

echo ""

# 系统资源检查
log_info "系统资源使用:"

# CPU和内存使用
if command -v ps &> /dev/null; then
    echo "进程资源使用:"
    for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
        if lsof -ti:$port &>/dev/null; then
            pids=$(lsof -ti:$port)
            for pid in $pids; do
                process_info=$(ps -p $pid -o pid,pcpu,pmem,comm 2>/dev/null | tail -n 1)
                if [ -n "$process_info" ]; then
                    echo "  端口 $port: $process_info"
                fi
            done
        fi
    done
fi

echo ""

# 数据库连接检查
log_info "数据库连接检查:"
if command -v mysqladmin &> /dev/null; then
    if mysqladmin ping -h127.0.0.1 --silent 2>/dev/null; then
        log_success "MySQL数据库连接正常"
    else
        log_error "MySQL数据库连接失败"
    fi
else
    log_warn "MySQL客户端未安装，跳过数据库检查"
fi

echo ""

# 日志文件检查
log_info "日志文件状态:"
if [ -d "logs" ]; then
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            file_size=$(du -h "$log_file" | cut -f1)
            file_name=$(basename "$log_file")
            last_modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$log_file" 2>/dev/null || stat -c "%y" "$log_file" 2>/dev/null | cut -d'.' -f1)
            printf "  %-15s %8s  %s\n" "$file_name" "$file_size" "$last_modified"
        fi
    done
    
    # 检查最近的错误
    echo ""
    log_info "最近错误日志 (最近10行):"
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            errors=$(grep -i -E "error|exception|failed|traceback" "$log_file" | tail -3)
            if [ -n "$errors" ]; then
                echo "  $(basename "$log_file"):"
                echo "$errors" | sed 's/^/    /'
            fi
        fi
    done
else
    log_warn "日志目录不存在"
fi

echo ""

# 网络检查
log_info "网络可达性检查:"
for port in $BACKEND_PORT $CLIENT_PORT $FRONTEND_PORT; do
    if curl -s --max-time 2 "http://localhost:$port/" &>/dev/null; then
        printf "  %-20s " "http://localhost:$port"
        log_success "可访问"
    else
        printf "  %-20s " "http://localhost:$port"
        log_error "不可访问"
    fi
done

echo ""

# 总体状态评估
SERVICE_HEALTH=$(( RUNNING_SERVICES * 100 / TOTAL_SERVICES ))

echo "📋 系统状态总结:"
echo "  运行服务: $RUNNING_SERVICES/$TOTAL_SERVICES"
echo "  健康度: $SERVICE_HEALTH%"

if [ $RUNNING_SERVICES -eq $TOTAL_SERVICES ]; then
    STATUS="🟢 系统正常"
    log_success "所有服务运行正常"
elif [ $RUNNING_SERVICES -gt 0 ]; then
    STATUS="🟡 部分服务"
    log_warn "部分服务运行正常，请检查未运行的服务"
else
    STATUS="🔴 系统停止"
    log_error "所有服务都未运行"
fi

echo "  状态: $STATUS"

echo ""
echo "🔧 管理命令:"
echo "  启动系统: ./start.sh"
echo "  停止系统: ./stop.sh" 
echo "  查看日志: tail -f logs/[service].log"
echo "  重新部署: ./deploy.sh"

echo ""
echo "📱 访问地址:"
if [ $RUNNING_SERVICES -gt 0 ]; then
    echo "  🔗 API文档:  http://localhost:$BACKEND_PORT/docs"
    echo "  📱 客户端:   http://localhost:$CLIENT_PORT"
    echo "  🖥️ 管理端:   http://localhost:$FRONTEND_PORT"
    echo ""
    echo "👤 管理员登录: admin / admin123"
else
    echo "  (系统未运行，请先启动服务)"
fi

echo ""
echo "💻 环境信息:"
echo "  操作系统: $(uname -s) $(uname -r)"
echo "  Python: $(python3 --version 2>/dev/null || echo '❌ 未安装')"
echo "  Node.js: $(node --version 2>/dev/null || echo '❌ 未安装')"
echo "  MySQL: $(mysql --version 2>/dev/null | cut -d' ' -f6 2>/dev/null || echo '❌ 未安装')"

echo ""
echo "💡 性能建议:"
if [ $SERVICE_HEALTH -lt 50 ]; then
    echo "  🔧 系统状态不佳，建议检查:"
    echo "     - 运行 ./stop.sh 然后 ./start.sh 重启服务"
    echo "     - 检查端口是否被其他程序占用"
    echo "     - 查看日志文件确认错误原因"
elif [ $SERVICE_HEALTH -lt 100 ]; then
    echo "  ⚠️  部分服务异常，建议:"
    echo "     - 查看具体服务日志: tail -f logs/[service].log"
    echo "     - 重启异常服务或整个系统"
else
    echo "  ✅ 系统运行良好！"
    echo "     - 可以通过管理端进行数据导入和分析"
    echo "     - 定期备份数据库数据"
fi