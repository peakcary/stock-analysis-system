#!/usr/bin/env python3
"""
测试优化后的CSV导入逻辑
"""
import asyncio
import sys
import os
from io import StringIO
from datetime import date

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.data_import import DataImportService


async def test_csv_import():
    """测试CSV导入功能"""
    print("🧪 开始测试CSV导入功能...")
    
    # 创建测试CSV数据
    test_csv_data = """股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
000001,平安银行,10,50000,12.5,银行,银行股,0.8,1000000
000001,平安银行,10,50000,12.5,银行,金融服务,0.8,1000000
000002,万科A,15,30000,8.2,房地产,房地产,1.2,-500000
000002,万科A,15,30000,8.2,房地产,深圳本地,1.2,-500000
123001,东财转债,5,12000,105.5,证券,转债标的,2.1,200000
123001,东财转债,5,12000,105.5,证券,可转债,2.1,200000"""
    
    # 转换为bytes
    csv_bytes = test_csv_data.encode('utf-8')
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 创建导入服务
        service = DataImportService(db)
        
        print("📁 测试数据准备完成")
        print(f"   - CSV行数: {len(test_csv_data.split(chr(10))) - 1}")
        print(f"   - 包含股票: 000001(平安银行), 000002(万科A), 123001(东财转债)")
        print(f"   - 包含概念: 银行股, 金融服务, 房地产, 深圳本地, 转债标的, 可转债")
        
        # 执行导入
        print("\n🔄 开始执行CSV导入...")
        result = await service.import_csv_data(
            content=csv_bytes,
            filename="test_data_2025_09_06.csv",
            allow_overwrite=True,
            trade_date=date(2025, 9, 6)
        )
        
        print("\n📊 导入结果:")
        print(f"   ✅ 导入成功: {result['imported_records']} 条记录")
        print(f"   ⚠️  跳过记录: {result['skipped_records']} 条记录")
        if result.get('stats'):
            stats = result['stats']
            print(f"   🏢 股票处理: {stats['new_stocks']} 新增, {stats['updated_stocks']} 更新")
            print(f"   🏷️  概念处理: {stats['new_concepts']} 新增概念")
            print(f"   🔗 关联处理: {stats['new_relations']} 新增关联")
            print(f"   📈 数据处理: {stats['new_daily_data']} 新增, {stats['updated_daily_data']} 更新")
        
        if result.get('errors'):
            print(f"   ❌ 错误: {len(result['errors'])} 个")
            for error in result['errors'][:3]:  # 只显示前3个错误
                print(f"      - {error}")
        
        print(f"   📅 导入日期: {result['import_date']}")
        print(f"   🔄 覆盖模式: {result.get('overwrite', False)}")
        
        print("\n✅ 测试完成!")
        
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        raise
    finally:
        db.close()


async def test_repeat_import():
    """测试重复导入逻辑"""
    print("\n🔄 测试重复导入逻辑...")
    
    # 修改后的数据（更新股票名称和添加新概念）
    updated_csv_data = """股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
000001,平安银行股份,11,55000,13.2,金融,银行股,0.9,1200000
000001,平安银行股份,11,55000,13.2,金融,大盘蓝筹,0.9,1200000
000001,平安银行股份,11,55000,13.2,金融,沪深300,0.9,1200000
000002,万科A集团,16,35000,8.5,地产,房地产,1.3,-300000
000002,万科A集团,16,35000,8.5,地产,央企改革,1.3,-300000
123002,新转债,3,8000,102.3,制造业,转债标的,1.8,150000"""
    
    csv_bytes = updated_csv_data.encode('utf-8')
    db = next(get_db())
    
    try:
        service = DataImportService(db)
        
        print("📁 更新数据准备:")
        print("   - 000001: 名称 '平安银行' -> '平安银行股份', 行业 '银行' -> '金融'")
        print("   - 000001: 新增概念 '大盘蓝筹', '沪深300'") 
        print("   - 000002: 名称 '万科A' -> '万科A集团', 行业 '房地产' -> '地产'")
        print("   - 000002: 新增概念 '央企改革'")
        print("   - 123002: 新股票 '新转债'")
        
        # 执行第二次导入
        result = await service.import_csv_data(
            content=csv_bytes,
            filename="updated_data_2025_09_06.csv",
            allow_overwrite=True,
            trade_date=date(2025, 9, 6)
        )
        
        print("\n📊 重复导入结果:")
        print(f"   ✅ 导入成功: {result['imported_records']} 条记录")
        if result.get('stats'):
            stats = result['stats']
            print(f"   🏢 股票处理: {stats['new_stocks']} 新增, {stats['updated_stocks']} 更新")
            print(f"   🏷️  概念处理: {stats['new_concepts']} 新增概念")
            print(f"   🔗 关联处理: {stats['new_relations']} 新增关联")
        
        print("\n✅ 重复导入测试完成!")
        
    except Exception as e:
        print(f"❌ 重复导入测试失败: {str(e)}")
        raise
    finally:
        db.close()


async def main():
    """主测试函数"""
    print("🚀 开始CSV导入逻辑测试")
    print("=" * 60)
    
    # 测试1: 基本导入功能
    await test_csv_import()
    
    # 测试2: 重复导入和更新逻辑
    await test_repeat_import()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成!")


if __name__ == "__main__":
    asyncio.run(main())