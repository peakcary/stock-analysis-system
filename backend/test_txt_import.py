#!/usr/bin/env python3
"""
测试优化后的TXT导入逻辑
"""
import asyncio
import sys
import os
from datetime import date

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.data_import import DataImportService


async def test_txt_import():
    """测试TXT导入功能 - 基于日期的完全覆盖"""
    print("🧪 开始测试TXT导入功能...")
    
    # 创建第一批测试TXT数据 (2025-09-06的数据)
    test_txt_data_1 = """SH600000	2025-09-06	743024
SZ000001	2025-09-06	440932
SH600036	2025-09-06	523100
SZ000002	2025-09-06	389750
BJ430000	2025-09-06	125680"""
    
    txt_bytes_1 = test_txt_data_1.encode('utf-8')
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 创建导入服务
        service = DataImportService(db)
        
        print("📁 第一批测试数据准备完成")
        print(f"   - TXT行数: {len(test_txt_data_1.split(chr(10)))}")
        print(f"   - 包含日期: 2025-09-06")
        print(f"   - 包含股票: 600000, 000001, 600036, 000002, 430000")
        
        # 执行第一次导入
        print("\n🔄 开始执行TXT导入 (第一次)...")
        result1 = await service.import_txt_data(
            content=txt_bytes_1,
            filename="test_heat_2025_09_06.txt",
            allow_overwrite=True
        )
        
        print(f"\n📊 第一次导入结果:")
        print(f"   ✅ 导入成功: {result1['imported_records']} 条记录")
        print(f"   ⚠️  跳过记录: {result1['skipped_records']} 条记录")
        if result1.get('stats'):
            stats = result1['stats']
            print(f"   🗑️  删除记录: {stats['deleted_records']} 条")
            print(f"   ✨ 新增记录: {stats['new_records']} 条")
        print(f"   📅 导入日期: {result1['import_date']}")
        
        # 创建第二批测试数据 (相同日期，但数据不同 - 模拟数据纠正)
        test_txt_data_2 = """SH600000	2025-09-06	850000
SZ000001	2025-09-06	520000
SH600036	2025-09-06	680000
SZ000002	2025-09-06	420000
SH601318	2025-09-06	750000
SZ123456	2025-09-06	95000"""
        
        txt_bytes_2 = test_txt_data_2.encode('utf-8')
        
        print("\n📁 第二批测试数据准备完成 (数据纠正场景)")
        print("   - 相同日期: 2025-09-06")
        print("   - 更新了前4只股票的热度值")
        print("   - 新增了2只股票: 601318, 123456")
        print("   - 移除了1只股票: 430000")
        
        # 执行第二次导入 (覆盖模式)
        print("\n🔄 开始执行TXT导入 (第二次 - 覆盖模式)...")
        result2 = await service.import_txt_data(
            content=txt_bytes_2,
            filename="corrected_heat_2025_09_06.txt",
            allow_overwrite=True
        )
        
        print(f"\n📊 第二次导入结果:")
        print(f"   ✅ 导入成功: {result2['imported_records']} 条记录")
        print(f"   ⚠️  跳过记录: {result2['skipped_records']} 条记录")
        if result2.get('stats'):
            stats = result2['stats']
            print(f"   🗑️  删除记录: {stats['deleted_records']} 条 (覆盖之前的数据)")
            print(f"   ✨ 新增记录: {stats['new_records']} 条")
        print(f"   📅 导入日期: {result2['import_date']}")
        print(f"   🔄 覆盖模式: {result2.get('overwrite', False)}")
        
        print("\n✅ TXT导入测试完成!")
        
        return result1, result2
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        raise
    finally:
        db.close()


async def test_multi_date_txt():
    """测试包含多个日期的TXT文件"""
    print("\n🔄 测试多日期TXT文件处理...")
    
    # 创建包含多个日期的TXT数据
    multi_date_txt = """SH600000	2025-09-05	500000
SH600000	2025-09-06	600000
SH600000	2025-09-07	700000
SZ000001	2025-09-05	300000
SZ000001	2025-09-06	400000
SZ000001	2025-09-07	500000"""
    
    txt_bytes = multi_date_txt.encode('utf-8')
    db = next(get_db())
    
    try:
        service = DataImportService(db)
        
        print("📁 多日期数据准备:")
        print("   - 包含日期: 2025-09-05, 2025-09-06, 2025-09-07")
        print("   - 每个日期包含2只股票")
        
        # 执行导入
        result = await service.import_txt_data(
            content=txt_bytes,
            filename="multi_date_heat.txt",
            allow_overwrite=True
        )
        
        print(f"\n📊 多日期导入结果:")
        print(f"   ✅ 导入成功: {result['imported_records']} 条记录") 
        print(f"   📅 选定日期: {result['import_date']}")
        if result.get('stats'):
            print(f"   ✨ 新增记录: {result['stats']['new_records']} 条")
        
        print("\n✅ 多日期测试完成!")
        
    except Exception as e:
        print(f"❌ 多日期测试失败: {str(e)}")
        raise
    finally:
        db.close()


async def main():
    """主测试函数"""
    print("🚀 开始TXT导入逻辑测试")
    print("=" * 60)
    
    # 测试1: 基于日期的完全覆盖导入
    await test_txt_import()
    
    # 测试2: 多日期文件处理
    await test_multi_date_txt()
    
    print("\n" + "=" * 60)
    print("🎉 所有TXT导入测试完成!")


if __name__ == "__main__":
    asyncio.run(main())