#!/usr/bin/env python3
"""
创建日交易相关数据表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, get_db
from app.models.daily_trading import (
    DailyTrading, ConceptDailySummary, 
    StockConceptRanking, ConceptHighRecord
)
from app.models import Base
from sqlalchemy.orm import Session

def create_tables():
    """创建所有表"""
    try:
        print("📊 开始创建日交易数据表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ 数据库表创建完成")
        
        # 验证表是否创建成功
        db = next(get_db())
        try:
            # 验证各表是否可以正常查询
            daily_trading_count = db.query(DailyTrading).count()
            concept_summary_count = db.query(ConceptDailySummary).count()
            ranking_count = db.query(StockConceptRanking).count()
            high_record_count = db.query(ConceptHighRecord).count()
            
            print(f"📋 表验证结果:")
            print(f"  - daily_trading: {daily_trading_count} 条记录")
            print(f"  - concept_daily_summary: {concept_summary_count} 条记录")
            print(f"  - stock_concept_ranking: {ranking_count} 条记录")
            print(f"  - concept_high_record: {high_record_count} 条记录")
            
        finally:
            db.close()
            
        print("🎉 日交易数据表初始化完成！")
        
    except Exception as e:
        print(f"❌ 创建表时出错: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_tables()
    if success:
        print("\n📚 使用说明:")
        print("1. 使用 /api/v1/txt-import/import 端点上传TXT文件")
        print("2. 使用 /api/v1/txt-import/stats/{date} 查看导入统计")
        print("3. 使用 /api/v1/txt-import/recent-imports 查看最近导入记录")
        print("\n💡 TXT文件格式: 股票代码\\t日期\\t交易量")
        sys.exit(0)
    else:
        sys.exit(1)