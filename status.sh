#!/bin/bash

# 股票概念分析系统 - 服务状态检查脚本
# Stock Analysis System - Service Status Check Script

echo "📊 股票概念分析系统 - 服务状态"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查服务状态函数
check_service() {
    local service_name=$1
    local port=$2
    local url=$3
    local pid_file=$4
    
    echo ""
    echo "🔍 检查 $service_name (端口 $port)"
    echo "----------------------------------------"
    
    # 检查端口是否被监听
    if lsof -ti:$port &>/dev/null; then
        local pid=$(lsof -ti:$port)
        log_success "端口 $port 正在被监听 (PID: $pid)"
        
        # 获取进程详细信息
        local process_info=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
        if [ ! -z "$process_info" ]; then
            echo "  进程信息: $process_info"
        fi
        
        # 检查 HTTP 服务响应
        if [ ! -z "$url" ]; then
            if curl -s "$url" &>/dev/null; then
                log_success "HTTP 服务响应正常: $url"
            else
                log_warn "HTTP 服务无响应: $url"
            fi
        fi
        
        # 检查 PID 文件
        if [ -f "$pid_file" ]; then
            local file_pid=$(cat "$pid_file")
            if [ "$pid" = "$file_pid" ]; then
                log_success "PID 文件匹配: $pid_file"
            else
                log_warn "PID 文件不匹配: 实际 $pid, 文件 $file_pid"
            fi
        else
            log_warn "PID 文件不存在: $pid_file"
        fi
        
    else
        log_error "端口 $port 未被监听"
        
        # 检查 PID 文件中的进程是否存在
        if [ -f "$pid_file" ]; then
            local file_pid=$(cat "$pid_file")
            if kill -0 "$file_pid" 2>/dev/null; then
                log_warn "PID 文件中的进程 $file_pid 仍在运行，但未监听端口"
            else
                log_error "PID 文件中的进程 $file_pid 已停止"
            fi
        fi
    fi
}

# 检查系统资源
echo "💻 系统资源使用情况"
echo "----------------------------------------"

# CPU 使用率
cpu_usage=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
echo "CPU 使用率: ${cpu_usage}%"

# 内存使用情况
if command -v free &> /dev/null; then
    # Linux
    mem_info=$(free -h | awk '/^Mem:/ {print $3 "/" $2}')
    echo "内存使用: $mem_info"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    mem_pressure=$(memory_pressure 2>/dev/null | grep "System" | head -1)
    echo "内存状态: $mem_pressure"
fi

# 磁盘使用情况
disk_usage=$(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')
echo "磁盘使用: $disk_usage"

echo ""

# 检查数据库连接
echo "🗄️ 数据库状态检查"
echo "----------------------------------------"

if command -v mysql &> /dev/null; then
    if mysql -h127.0.0.1 -uroot -pPp123456 -e "SELECT 1;" &>/dev/null; then
        log_success "MySQL 连接正常"
        
        # 获取数据库信息
        db_version=$(mysql -h127.0.0.1 -uroot -pPp123456 -e "SELECT VERSION();" -s -N 2>/dev/null)
        echo "  数据库版本: $db_version"
        
        # 检查表数量
        table_count=$(mysql -h127.0.0.1 -uroot -pPp123456 stock_analysis_dev -e "SHOW TABLES;" -s 2>/dev/null | wc -l)
        echo "  数据表数量: $table_count"
        
        # 检查数据库大小
        db_size=$(mysql -h127.0.0.1 -uroot -pPp123456 -e "
            SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'DB Size(MB)'
            FROM information_schema.tables 
            WHERE table_schema = 'stock_analysis_dev';
        " -s -N 2>/dev/null)
        echo "  数据库大小: ${db_size} MB"
        
    else
        log_error "MySQL 连接失败"
    fi
else
    log_warn "MySQL 命令未找到"
fi

# 检查各个服务
check_service "接口服务 (FastAPI)" "3007" "http://localhost:3007/docs" "logs/backend.pid"
check_service "后端管理 (Frontend)" "8005" "http://localhost:8005" "logs/frontend.pid"
check_service "客户端 (Client)" "8006" "http://localhost:8006" "logs/client.pid"

# 检查日志文件
echo ""
echo "📝 日志文件状态"
echo "----------------------------------------"

check_log_file() {
    local log_file=$1
    local service_name=$2
    
    if [ -f "$log_file" ]; then
        local file_size=$(du -h "$log_file" | cut -f1)
        local last_modified=$(stat -c %y "$log_file" 2>/dev/null || stat -f "%Sm" "$log_file" 2>/dev/null)
        log_success "$service_name: $log_file ($file_size)"
        echo "  最后修改: $last_modified"
        
        # 显示最后几行日志
        echo "  最新日志:"
        tail -n 3 "$log_file" | sed 's/^/    /'
    else
        log_warn "$service_name: $log_file (不存在)"
    fi
    echo ""
}

check_log_file "logs/backend.log" "接口服务日志"
check_log_file "logs/frontend.log" "后端管理日志"
check_log_file "logs/client.log" "客户端日志"

# 网络连接检查
echo "🌐 网络连接检查"
echo "----------------------------------------"

# 检查关键端口的网络连接
netstat_info=$(netstat -an 2>/dev/null | grep -E ':(3007|8005|8006)' | grep LISTEN)
if [ ! -z "$netstat_info" ]; then
    echo "监听端口:"
    echo "$netstat_info" | sed 's/^/  /'
else
    log_warn "未找到监听的端口"
fi

echo ""

# 总结
echo "📋 服务状态总结"
echo "=================================="

services_running=0
total_services=3

if lsof -ti:3007 &>/dev/null; then
    log_success "✅ 接口服务 (3007) - 运行中"
    ((services_running++))
else
    log_error "❌ 接口服务 (3007) - 未运行"
fi

if lsof -ti:8005 &>/dev/null; then
    log_success "✅ 后端管理 (8005) - 运行中"
    ((services_running++))
else
    log_error "❌ 后端管理 (8005) - 未运行"
fi

if lsof -ti:8006 &>/dev/null; then
    log_success "✅ 客户端 (8006) - 运行中"
    ((services_running++))
else
    log_error "❌ 客户端 (8006) - 未运行"
fi

echo ""
echo "运行状态: $services_running/$total_services 个服务正在运行"

if [ $services_running -eq $total_services ]; then
    log_success "🎉 所有服务运行正常！"
    echo ""
    echo "📊 访问地址："
    echo "  🔗 接口服务:   http://localhost:3007"
    echo "  📱 客户端:     http://localhost:8006"
    echo "  🖥️  后端管理:   http://localhost:8005"
elif [ $services_running -eq 0 ]; then
    log_error "🚨 所有服务都未运行，请使用 ./start.sh 启动系统"
else
    log_warn "⚠️  部分服务未运行，可能需要重启系统"
    echo ""
    echo "🔧 操作建议："
    echo "  重启所有服务: ./stop.sh && ./start.sh"
    echo "  查看日志:     tail -f logs/*.log"
fi

echo ""