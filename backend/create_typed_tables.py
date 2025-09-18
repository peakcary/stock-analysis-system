#!/usr/bin/env python3
"""
创建类型化独立数据表
使用type1、type2、type3简洁命名，方便扩展
"""

from app.core.database import engine
from app.models.typed_trading import (
    Type1DailyTrading, Type1ConceptDailySummary,
    Type1StockConceptRanking, Type1ConceptHighRecord,
    Type2DailyTrading, Type2ConceptDailySummary,
    Type2StockConceptRanking, Type2ConceptHighRecord,
    Type3DailyTrading, Type3ConceptDailySummary,
    Type3StockConceptRanking, Type3ConceptHighRecord,
    TYPED_MODELS
)
from app.models.import_record import ImportRecord
from app.core.database import Base

def create_all_typed_tables():
    """创建所有类型化数据表"""
    print("🚀 开始创建类型化独立数据表...")
    print("📋 使用 type1、type2、type3 简洁命名体系")

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 所有表创建成功!")

        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        typed_tables = [
            # Type1 tables
            'type1_daily_trading',
            'type1_concept_daily_summary',
            'type1_stock_concept_ranking',
            'type1_concept_high_record',
            # Type2 tables
            'type2_daily_trading',
            'type2_concept_daily_summary',
            'type2_stock_concept_ranking',
            'type2_concept_high_record',
            # Type3 tables
            'type3_daily_trading',
            'type3_concept_daily_summary',
            'type3_stock_concept_ranking',
            'type3_concept_high_record',
            # Import records
            'import_records'
        ]

        print(f"\n📊 数据库中现有表数量: {len(tables)}")
        print("\n🔍 类型化表创建状态:")

        created_count = 0
        for table_name in typed_tables:
            if table_name in tables:
                print(f"✅ {table_name}")
                created_count += 1
            else:
                print(f"❌ {table_name}")

        print(f"\n📈 成功创建 {created_count}/{len(typed_tables)} 个类型化表")

        # 显示类型配置
        print(f"\n🎯 支持的导入类型:")
        for type_key, models in TYPED_MODELS.items():
            print(f"  - {type_key}: {len(models)} 个数据表")
            for model_name, model_class in models.items():
                print(f"    └─ {model_class.__tablename__}")

        print(f"\n🚀 类型化数据系统配置完成！")
        print("📝 扩展新类型只需要:")
        print("   1. 添加 TypeN 相关的4个模型类")
        print("   2. 在 TYPED_MODELS 中注册配置")
        print("   3. 在服务层添加类型定义")
        print("   4. 运行此脚本创建表结构")

    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        raise

def show_extension_example():
    """显示扩展示例"""
    print("\n" + "="*60)
    print("📚 扩展示例: 添加 Type4")
    print("="*60)

    print("""
1. 在 typed_trading.py 中添加 Type4 模型类:

class Type4DailyTrading(Base):
    __tablename__ = "type4_daily_trading"
    # ... 字段定义（复制Type1并修改表名）

class Type4ConceptDailySummary(Base):
    __tablename__ = "type4_concept_daily_summary"
    # ... 字段定义（复制Type1并修改表名）

# ... 其他两个模型类

2. 在 TYPED_MODELS 中注册:

TYPED_MODELS = {
    'type1': { ... },
    'type2': { ... },
    'type3': { ... },
    'type4': {
        'daily_trading': Type4DailyTrading,
        'concept_daily_summary': Type4ConceptDailySummary,
        'stock_concept_ranking': Type4StockConceptRanking,
        'concept_high_record': Type4ConceptHighRecord,
    }
}

3. 在 typed_import_service.py 中添加类型定义:

IMPORT_TYPES = {
    # ... 现有类型
    'type4': {
        'name': 'Type4数据',
        'description': 'Type4类型TXT文件导入',
        'category': 'type4_trading'
    }
}

4. 运行此脚本创建表结构
5. 重启服务，即可使用 type4 导入功能
""")

if __name__ == "__main__":
    create_all_typed_tables()
    show_extension_example()