#!/usr/bin/env python3
"""
创建多类型独立数据表
"""

from app.core.database import engine
from app.models.multi_type_trading import (
    DailyTypeDailyTrading, DailyTypeConceptDailySummary,
    DailyTypeStockConceptRanking, DailyTypeConceptHighRecord,
    BatchTypeDailyTrading, BatchTypeConceptDailySummary,
    BatchTypeStockConceptRanking, BatchTypeConceptHighRecord,
    SpecialTypeDailyTrading, SpecialTypeConceptDailySummary,
    SpecialTypeStockConceptRanking, SpecialTypeConceptHighRecord
)
from app.models.import_record import ImportRecord
from app.core.database import Base

def create_all_tables():
    """创建所有多类型数据表"""
    print("🚀 开始创建多类型独立数据表...")

    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 所有表创建成功!")

        # 验证表是否存在
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        multi_type_tables = [
            'daily_type_daily_trading',
            'daily_type_concept_daily_summary',
            'daily_type_stock_concept_ranking',
            'daily_type_concept_high_record',
            'batch_type_daily_trading',
            'batch_type_concept_daily_summary',
            'batch_type_stock_concept_ranking',
            'batch_type_concept_high_record',
            'special_type_daily_trading',
            'special_type_concept_daily_summary',
            'special_type_stock_concept_ranking',
            'special_type_concept_high_record',
            'import_records'
        ]

        print(f"\n📊 数据库中现有表数量: {len(tables)}")
        print("\n🔍 多类型表创建状态:")

        for table_name in multi_type_tables:
            if table_name in tables:
                print(f"✅ {table_name}")
            else:
                print(f"❌ {table_name}")

    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        raise

if __name__ == "__main__":
    create_all_tables()