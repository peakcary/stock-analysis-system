#!/usr/bin/env python3
"""
清理测试数据脚本
清理测试过程中创建的表和数据
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def cleanup_test_data():
    """清理测试数据"""
    print("=== 清理测试数据 ===")

    try:
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # 获取所有表名
            result = conn.execute(text("SHOW TABLES"))
            all_tables = [row[0] for row in result]

            # 识别测试相关的表
            test_tables = []
            test_prefixes = ['ttv_', 'eee_', 'test_', 'daily_type_']

            for table in all_tables:
                for prefix in test_prefixes:
                    if table.startswith(prefix):
                        test_tables.append(table)
                        break

            if test_tables:
                print(f"发现测试表: {test_tables}")

                # 删除表
                for table in test_tables:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                        print(f"删除表: {table}")
                    except Exception as e:
                        print(f"删除表 {table} 失败: {e}")

                # 提交事务
                conn.commit()
                print(f"✅ 成功清理 {len(test_tables)} 个测试表")
            else:
                print("未找到需要清理的测试表")

        return True

    except Exception as e:
        print(f"❌ 清理测试数据失败: {e}")
        return False

if __name__ == "__main__":
    success = cleanup_test_data()
    sys.exit(0 if success else 1)