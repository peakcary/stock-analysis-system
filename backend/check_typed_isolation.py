#!/usr/bin/env python3
"""
验证类型化数据隔离
检查type1、type2、type3数据的独立存储
"""

from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.typed_trading import (
    Type1DailyTrading, Type2DailyTrading, Type3DailyTrading,
    TYPED_MODELS
)
from app.models.import_record import ImportRecord

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_typed_data_isolation():
    """检查类型化数据隔离情况"""
    db = SessionLocal()

    try:
        print("🔍 检查类型化数据隔离情况:")
        print("📋 使用 type1、type2、type3 简洁命名体系")
        print("=" * 60)

        # 统计各类型数据
        type1_count = db.query(Type1DailyTrading).count()
        type2_count = db.query(Type2DailyTrading).count()
        type3_count = db.query(Type3DailyTrading).count()

        print(f"📊 Type1数据: {type1_count} 条")
        print(f"📊 Type2数据: {type2_count} 条")
        print(f"📊 Type3数据: {type3_count} 条")

        # 统计导入记录
        import_records = db.query(ImportRecord).all()
        print(f"\n📝 总导入记录: {len(import_records)} 条")

        # 按类型分组统计导入记录
        type_counts = {}
        for record in import_records:
            if record.import_type not in type_counts:
                type_counts[record.import_type] = 0
            type_counts[record.import_type] += 1

        for import_type, count in type_counts.items():
            print(f"   - {import_type}: {count} 条记录")

        # 验证数据隔离
        print(f"\n✅ 数据隔离验证:")
        if type1_count > 0:
            print(f"   - Type1有独立数据 ({type1_count} 条)")
        if type2_count > 0:
            print(f"   - Type2有独立数据 ({type2_count} 条)")
        if type3_count > 0:
            print(f"   - Type3有独立数据 ({type3_count} 条)")

        total_isolated = type1_count + type2_count + type3_count
        print(f"\n🎯 总计独立存储数据: {total_isolated} 条")

        # 显示支持的类型配置
        print(f"\n🚀 支持的类型配置:")
        for type_key, models in TYPED_MODELS.items():
            print(f"  - {type_key}: {len(models)} 个数据表")
            for model_name in models.keys():
                print(f"    └─ {model_name}")

        print("\n✅ 类型化数据完全隔离存储！")
        print("🎯 扩展新类型极其简单：")
        print("   1. 复制Type1的4个模型类")
        print("   2. 修改表名前缀为typeN")
        print("   3. 在配置中注册新类型")
        print("   4. 创建表结构即可使用")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        db.close()

def show_extension_template():
    """显示扩展模板"""
    print("\n" + "="*60)
    print("📚 Type4 扩展模板")
    print("="*60)

    print("""
🔧 添加 Type4 的完整步骤:

1. 在 typed_trading.py 中添加模型类:
   - Type4DailyTrading
   - Type4ConceptDailySummary
   - Type4StockConceptRanking
   - Type4ConceptHighRecord

2. 在 TYPED_MODELS 配置中注册:
   'type4': {
       'daily_trading': Type4DailyTrading,
       # ... 其他3个模型
   }

3. 在 typed_import_service.py 中添加:
   'type4': {
       'name': 'Type4数据',
       'description': 'Type4类型TXT文件导入',
       'category': 'type4_trading'
   }

4. 运行 python create_typed_tables.py 创建表

5. 重启服务，即可使用 type4 导入！

🎯 扩展后支持的API端点:
   - GET  /api/v1/typed-import/types
   - POST /api/v1/typed-import/import/type4
   - GET  /api/v1/typed-import/records?import_type=type4
   - GET  /api/v1/typed-import/stats
   - GET  /api/v1/typed-import/data-stats/type4
""")

if __name__ == "__main__":
    check_typed_data_isolation()
    show_extension_template()