#!/usr/bin/env python3
"""
测试TXT文件导入功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.txt_import import TxtImportService

def test_txt_import():
    """测试TXT导入功能"""
    
    # 准备测试数据（从示例文件中提取一小部分）
    sample_txt_content = """SH600000	2025-09-02	612563
SH600004	2025-09-02	114398
SH600006	2025-09-02	227005
SH600007	2025-09-02	13970
SH600008	2025-09-02	1134357
SZ000001	2025-09-02	500000
SZ000002	2025-09-02	750000
SZ300001	2025-09-02	300000"""
    
    try:
        print("📊 开始测试TXT文件导入...")
        
        # 获取数据库连接
        db = next(get_db())
        
        try:
            # 创建导入服务实例
            import_service = TxtImportService(db)
            
            # 执行导入
            result = import_service.import_daily_trading(sample_txt_content)
            
            print("\n导入结果:")
            print(f"成功: {result['success']}")
            print(f"消息: {result['message']}")
            
            if result['success']:
                stats = result['stats']
                print("\n统计信息:")
                print(f"  交易数据: {stats['trading_data_count']} 条")
                print(f"  概念汇总: {stats['concept_summary_count']} 个")
                print(f"  排名数据: {stats['ranking_count']} 条")
                print(f"  创新高记录: {stats['new_high_count']} 条")
                print(f"  交易日期: {stats['trading_date']}")
            
        finally:
            db.close()
            
        print("\n✅ TXT导入功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_txt_import()
