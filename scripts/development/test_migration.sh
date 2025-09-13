#!/bin/bash
# 测试迁移脚本修复

echo "🧪 测试股票代码字段升级脚本..."

cd backend
source venv/bin/activate

echo "🔍 测试Python模块导入..."
python -c "
try:
    print('正在测试模块导入...')
    from app.core.database import engine, get_db
    from app.models.daily_trading import DailyTrading
    print('✅ 模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️ 其他错误: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Python模块路径修复成功"
    echo "🚀 现在可以运行: ./deploy.sh --upgrade-stock-codes"
else
    echo "❌ 模块导入仍然失败"
    echo "🔧 请检查虚拟环境和依赖安装"
fi

cd ..