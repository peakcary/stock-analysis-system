#!/bin/bash

# 快速导入脚本 - 一键导入 EEE.txt 和 TTV.txt

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  ${1}${NC}"
}

print_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

print_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  ${1}${NC}"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 默认参数
FILE_TYPE=${1:-""}
SKIP_CALC=${2:-""}
EEE_FILE="/Users/peakom/Downloads/EEE.txt"
TTV_FILE="/Users/peakom/Downloads/TTV.txt"

print_info "本地文件快速导入脚本"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    print_error "Python3 未找到，请先安装 Python3"
    exit 1
fi

# 检查数据库连接
print_info "检查数据库连接..."
if ! python3 -c "import psycopg2; psycopg2.connect('postgresql://postgres:Pp123456@localhost/stockdb')" 2>/dev/null; then
    print_error "无法连接到数据库"
    echo "请确保 PostgreSQL 正在运行"
    exit 1
fi
print_success "数据库连接正常"

# 检查 API 连接
print_info "检查后端服务..."
if ! curl -s http://localhost:3007/health > /dev/null 2>&1; then
    print_warning "后端服务未响应，将跳过重新计算步骤"
    SKIP_CALC="--skip-calc"
else
    print_success "后端服务正常"
fi

echo ""

# 处理导入类型
if [ -z "$FILE_TYPE" ]; then
    print_info "选择导入文件类型："
    echo "  1) EEE (热度数据)"
    echo "  2) TTV (交易数据)"
    echo "  3) 两个都导入"
    read -p "请选择 [1-3]: " choice

    case $choice in
        1) FILE_TYPE="eee" ;;
        2) FILE_TYPE="ttv" ;;
        3) FILE_TYPE="both" ;;
        *)
            print_error "无效选择"
            exit 1
            ;;
    esac
fi

# 导入函数
import_file() {
    local type=$1
    local file=$2

    if [ ! -f "$file" ]; then
        print_error "文件不存在: $file"
        return 1
    fi

    print_info "开始导入 $(basename $file)..."
    echo ""

    local cmd="python3 $SCRIPT_DIR/batch_import_local_files.py --type $type --file $file"

    if [ ! -z "$SKIP_CALC" ]; then
        cmd="$cmd $SKIP_CALC"
    fi

    if eval "$cmd"; then
        print_success "导入完成"
        return 0
    else
        print_error "导入失败"
        return 1
    fi
}

# 执行导入
case $FILE_TYPE in
    eee)
        import_file "eee" "$EEE_FILE" || exit 1
        ;;
    ttv)
        import_file "ttv" "$TTV_FILE" || exit 1
        ;;
    both)
        import_file "eee" "$EEE_FILE" || print_warning "EEE 导入失败，继续 TTV"
        echo ""
        import_file "ttv" "$TTV_FILE" || print_warning "TTV 导入失败"
        ;;
    *)
        print_error "不支持的文件类型: $FILE_TYPE"
        exit 1
        ;;
esac

echo ""
print_success "所有导入任务完成！"

if [ ! -z "$SKIP_CALC" ]; then
    print_info "数据已导入，但跳过了重新计算"
    echo "  你可以稍后在导入记录页面点击'重新计算'按钮"
fi

echo ""
print_info "后续步骤："
echo "  1. 访问管理页面查看导入记录"
echo "  2. 在导入记录列表中点击'重新计算'按钮"
echo "  3. 在概念分析页面查看汇总数据"
echo ""
