#!/bin/bash

# 🚀 生产环境构建优化脚本
# ========================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 生产环境构建优化${NC}"
echo "========================"

# 检查必要工具
check_tools() {
    echo -e "${BLUE}🔍 检查构建工具...${NC}"
    
    local tools=("node" "npm" "gzip")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            echo -e "${RED}❌ ${tool} 未安装${NC}"
            return 1
        else
            echo -e "${GREEN}✅ ${tool} 已安装${NC}"
        fi
    done
    
    return 0
}

# 优化构建函数
optimize_build() {
    local name=$1
    local path=$2
    
    echo -e "${YELLOW}⚡ 优化构建 ${name}...${NC}"
    
    cd "$path"
    
    # 清理依赖缓存
    echo "🧹 清理缓存..."
    npm cache clean --force 2>/dev/null || true
    
    # 重新安装依赖（生产环境）
    echo "📦 安装生产依赖..."
    rm -rf node_modules package-lock.json
    npm install --production=false --frozen-lockfile
    
    # 执行构建
    echo "🔨 执行优化构建..."
    BUILD_START=$(date +%s)
    
    # 设置生产环境变量
    export NODE_ENV=production
    export VITE_BUILD_MODE=production
    
    # 使用Vite进行生产构建
    npx vite build --mode production
    
    BUILD_END=$(date +%s)
    BUILD_DURATION=$((BUILD_END - BUILD_START))
    
    echo -e "${GREEN}✅ ${name} 构建完成 (${BUILD_DURATION}秒)${NC}"
    
    # 构建分析
    if [ -d "dist" ]; then
        echo "📊 构建分析:"
        
        # 文件大小统计
        echo "   📁 总大小: $(du -sh dist | cut -f1)"
        echo "   📄 文件数量: $(find dist -type f | wc -l)"
        
        # 压缩效果测试
        echo "   🗜️  压缩效果:"
        local total_size=0
        local compressed_size=0
        
        for file in $(find dist -name "*.js" -o -name "*.css" -o -name "*.html"); do
            if [ -f "$file" ]; then
                local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
                local gzip_size=$(gzip -c "$file" | wc -c)
                total_size=$((total_size + size))
                compressed_size=$((compressed_size + gzip_size))
            fi
        done
        
        if [ $total_size -gt 0 ]; then
            local ratio=$((100 - (compressed_size * 100 / total_size)))
            echo "      原始: $(numfmt --to=iec-i --suffix=B $total_size)"
            echo "      压缩: $(numfmt --to=iec-i --suffix=B $compressed_size)"
            echo "      压缩率: ${ratio}%"
        fi
        
        # 大文件检查
        echo "   🔍 大文件检查 (>500KB):"
        find dist -type f -size +500k -exec ls -lh {} \; | awk '{print "      " $5 " " $9}' | head -5
        
        # 优化建议
        echo "   💡 优化建议:"
        local large_js=$(find dist -name "*.js" -size +1M | wc -l)
        if [ $large_js -gt 0 ]; then
            echo "      • 发现 ${large_js} 个大于1MB的JS文件，建议进一步代码分割"
        fi
        
        local total_js_size=$(find dist -name "*.js" -exec stat -f%z {} \; 2>/dev/null | awk '{sum+=$1} END {print sum}' || echo 0)
        if [ $total_js_size -gt 2097152 ]; then # 2MB
            echo "      • JS总大小较大，建议启用懒加载"
        fi
        
        echo "      • 确保服务器启用gzip/brotli压缩"
        echo "      • 配置CDN缓存策略"
        echo "      • 启用HTTP/2推送"
    fi
    
    return 0
}

# 生成部署包
create_deployment_package() {
    echo -e "${PURPLE}📦 创建部署包...${NC}"
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local package_name="stock-analysis-frontend-${timestamp}.tar.gz"
    
    # 创建临时目录
    local temp_dir="./deployment_temp"
    rm -rf "$temp_dir"
    mkdir -p "$temp_dir"
    
    # 复制构建产物
    if [ -d "./frontend/dist" ]; then
        cp -r "./frontend/dist" "$temp_dir/admin"
        echo "   ✅ 管理端构建产物已复制"
    fi
    
    if [ -d "./client/dist" ]; then
        cp -r "./client/dist" "$temp_dir/client"
        echo "   ✅ 客户端构建产物已复制"
    fi
    
    # 创建部署说明
    cat > "$temp_dir/README.md" << 'EOF'
# 股票分析系统前端部署包

## 目录结构
- `admin/` - 管理端构建产物 (端口 8006)
- `client/` - 客户端构建产物 (端口 8005)

## 部署说明

### Nginx配置示例
```nginx
# 管理端
server {
    listen 8006;
    server_name _;
    root /path/to/admin;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# 客户端
server {
    listen 8005;
    server_name _;
    root /path/to/client;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://127.0.0.1:3007;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 性能优化建议
1. 启用gzip压缩
2. 设置适当的缓存头
3. 配置CDN
4. 启用HTTP/2
EOF
    
    # 打包
    tar -czf "$package_name" -C "$temp_dir" .
    rm -rf "$temp_dir"
    
    echo -e "${GREEN}✅ 部署包创建完成: ${package_name}${NC}"
    echo "   📁 大小: $(du -sh "$package_name" | cut -f1)"
    
    return 0
}

# 主流程
main() {
    local script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    cd "$script_dir"
    
    # 检查工具
    if ! check_tools; then
        echo -e "${RED}❌ 工具检查失败${NC}"
        exit 1
    fi
    
    echo
    
    # 优化构建管理端
    if [ -d "./frontend" ]; then
        optimize_build "管理端" "./frontend"
        echo
    fi
    
    # 优化构建客户端
    if [ -d "./client" ]; then
        optimize_build "客户端" "./client"
        echo
    fi
    
    # 创建部署包
    create_deployment_package
    
    echo
    echo "================================"
    echo -e "${GREEN}🎉 生产环境构建完成！${NC}"
    echo
    echo -e "${CYAN}📋 后续步骤:${NC}"
    echo "   1. 上传部署包到服务器"
    echo "   2. 解压到Web服务器目录"
    echo "   3. 配置Nginx/Apache"
    echo "   4. 启用SSL证书"
    echo "   5. 配置CDN加速"
    echo
}

# 执行主流程
main "$@"