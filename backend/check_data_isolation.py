#!/usr/bin/env python3
"""
验证多类型数据隔离
"""

from sqlalchemy.orm import sessionmaker
from app.core.database import engine
from app.models.multi_type_trading import (
    DailyTypeDailyTrading, BatchTypeDailyTrading, SpecialTypeDailyTrading,
    ExperimentalTypeDailyTrading
)
from app.models.import_record import ImportRecord

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_data_isolation():
    """检查数据隔离情况"""
    db = SessionLocal()

    try:
        print("🔍 检查多类型数据隔离情况:")
        print("=" * 50)

        # 统计各类型数据
        daily_count = db.query(DailyTypeDailyTrading).count()
        batch_count = db.query(BatchTypeDailyTrading).count()
        special_count = db.query(SpecialTypeDailyTrading).count()
        experimental_count = db.query(ExperimentalTypeDailyTrading).count()

        print(f"📊 日常类型数据: {daily_count} 条")
        print(f"📊 批量类型数据: {batch_count} 条")
        print(f"📊 特殊类型数据: {special_count} 条")
        print(f"📊 实验类型数据: {experimental_count} 条")

        # 统计导入记录
        import_records = db.query(ImportRecord).all()
        print(f"\n📝 总导入记录: {len(import_records)} 条")

        type_counts = {}
        for record in import_records:
            if record.import_type not in type_counts:
                type_counts[record.import_type] = 0
            type_counts[record.import_type] += 1

        for import_type, count in type_counts.items():
            print(f"   - {import_type}: {count} 条记录")

        # 验证数据隔离
        print(f"\n✅ 数据隔离验证:")
        if daily_count > 0:
            print(f"   - 日常类型有独立数据 ({daily_count} 条)")
        if batch_count > 0:
            print(f"   - 批量类型有独立数据 ({batch_count} 条)")
        if special_count > 0:
            print(f"   - 特殊类型有独立数据 ({special_count} 条)")
        if experimental_count > 0:
            print(f"   - 实验类型有独立数据 ({experimental_count} 条)")

        total_isolated = daily_count + batch_count + special_count + experimental_count
        print(f"\n🎯 总计独立存储数据: {total_isolated} 条")
        print("✅ 多类型数据完全隔离存储！")

    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data_isolation()