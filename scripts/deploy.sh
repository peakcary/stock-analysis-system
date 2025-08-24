#!/bin/bash

# 股票分析系统生产环境部署脚本
set -e

echo "🚀 开始部署股票分析系统..."

# 检查必要文件
if [ ! -f ".env.prod" ]; then
    echo "❌ 错误: 未找到 .env.prod 文件"
    echo "请复制 .env.prod.example 为 .env.prod 并配置相应参数"
    exit 1
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p nginx/ssl
mkdir -p database/backups

# 拉取最新镜像
echo "📥 拉取最新镜像..."
docker-compose -f docker-compose.prod.yml pull

# 构建应用镜像
echo "🏗️ 构建应用镜像..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 停止现有服务
echo "⏹️ 停止现有服务..."
docker-compose -f docker-compose.prod.yml down

# 启动服务
echo "▶️ 启动生产服务..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 30

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker-compose.prod.yml ps

# 健康检查
echo "❤️ 执行健康检查..."
timeout 60s bash -c 'until curl -f http://localhost/health; do echo "等待前端服务..."; sleep 5; done'
timeout 60s bash -c 'until curl -f http://localhost:8000/health; do echo "等待后端服务..."; sleep 5; done'

echo "✅ 部署完成!"
echo "🌐 前端访问地址: http://localhost"
echo "📚 API 文档: http://localhost:8000/docs"
echo "📊 查看日志: docker-compose -f docker-compose.prod.yml logs -f"