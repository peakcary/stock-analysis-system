#!/bin/bash

# Docker 开发环境启动脚本
# Docker Development Environment Startup Script

set -e

echo "🚀 启动股票概念分析系统 Docker 开发环境..."
echo "🚀 Starting Stock Analysis System Docker Development Environment..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装，请先安装 Docker${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装，请先安装 Docker Compose${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
}

# 清理旧的容器和镜像
cleanup() {
    echo -e "${YELLOW}🧹 清理旧的容器和镜像...${NC}"
    docker-compose down -v --remove-orphans 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# 构建和启动服务
start_services() {
    echo -e "${BLUE}🏗️  构建 Docker 镜像...${NC}"
    docker-compose build --no-cache
    
    echo -e "${BLUE}🚀 启动服务...${NC}"
    docker-compose up -d
    
    echo -e "${BLUE}⏳ 等待服务启动...${NC}"
    sleep 10
    
    # 检查服务状态
    check_services
}

# 检查服务状态
check_services() {
    echo -e "${BLUE}🔍 检查服务状态...${NC}"
    
    # 检查 MySQL
    if docker-compose exec -T mysql mysqladmin ping -h localhost --silent; then
        echo -e "${GREEN}✅ MySQL 服务正常${NC}"
    else
        echo -e "${RED}❌ MySQL 服务异常${NC}"
        exit 1
    fi
    
    # 检查 Redis
    if docker-compose exec -T redis redis-cli ping --silent; then
        echo -e "${GREEN}✅ Redis 服务正常${NC}"
    else
        echo -e "${RED}❌ Redis 服务异常${NC}"
        exit 1
    fi
    
    # 检查后端服务
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务正常${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务还在启动中...${NC}"
        echo -e "${YELLOW}   等待30秒后再次检查...${NC}"
        sleep 30
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端服务正常${NC}"
        else
            echo -e "${RED}❌ 后端服务启动失败${NC}"
            exit 1
        fi
    fi
}

# 显示服务信息
show_info() {
    echo ""
    echo -e "${GREEN}🎉 股票概念分析系统 Docker 开发环境启动成功！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务访问地址：${NC}"
    echo -e "  🌐 前端管理端: ${GREEN}http://localhost:3000${NC}"
    echo -e "  🌐 前端用户端: ${GREEN}http://localhost:8006${NC}"
    echo -e "  🔧 后端API:    ${GREEN}http://localhost:8000${NC}"
    echo -e "  📖 API文档:    ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${BLUE}🗄️  数据库连接信息：${NC}"
    echo -e "  📊 MySQL:      ${GREEN}localhost:3306${NC}"
    echo -e "  🎯 数据库名:   ${GREEN}stock_analysis_dev${NC}"
    echo -e "  👤 用户名:     ${GREEN}dev_user${NC}"
    echo -e "  🔐 密码:       ${GREEN}dev_password${NC}"
    echo ""
    echo -e "${BLUE}🔧 Redis 连接信息：${NC}"
    echo -e "  📍 地址:       ${GREEN}localhost:6379${NC}"
    echo ""
    echo -e "${YELLOW}🛠️  常用命令：${NC}"
    echo -e "  📊 查看日志:    ${BLUE}docker-compose logs -f [service]${NC}"
    echo -e "  🔄 重启服务:    ${BLUE}docker-compose restart [service]${NC}"
    echo -e "  🛑 停止服务:    ${BLUE}docker-compose down${NC}"
    echo -e "  🔧 进入容器:    ${BLUE}docker-compose exec [service] bash${NC}"
    echo ""
    echo -e "${GREEN}💡 提示：首次启动需要下载镜像，请耐心等待...${NC}"
    echo ""
}

# 主函数
main() {
    case "$1" in
        "start")
            check_docker
            start_services
            show_info
            ;;
        "stop")
            echo -e "${YELLOW}🛑 停止服务...${NC}"
            docker-compose down
            echo -e "${GREEN}✅ 服务已停止${NC}"
            ;;
        "restart")
            echo -e "${YELLOW}🔄 重启服务...${NC}"
            docker-compose restart
            echo -e "${GREEN}✅ 服务已重启${NC}"
            ;;
        "clean")
            cleanup
            echo -e "${GREEN}✅ 清理完成${NC}"
            ;;
        "logs")
            if [ -n "$2" ]; then
                docker-compose logs -f "$2"
            else
                docker-compose logs -f
            fi
            ;;
        "status")
            docker-compose ps
            ;;
        "shell")
            if [ -n "$2" ]; then
                docker-compose exec "$2" bash
            else
                echo -e "${YELLOW}请指定服务名称: backend, mysql, redis${NC}"
            fi
            ;;
        *)
            echo "使用方法: $0 {start|stop|restart|clean|logs|status|shell}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动所有服务"
            echo "  stop    - 停止所有服务"
            echo "  restart - 重启所有服务"
            echo "  clean   - 清理容器和镜像"
            echo "  logs    - 查看日志 (logs [service])"
            echo "  status  - 查看服务状态"
            echo "  shell   - 进入容器 (shell [service])"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"