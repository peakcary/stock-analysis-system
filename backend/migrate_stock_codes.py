#!/usr/bin/env python3
"""
股票代码字段升级迁移脚本
为开发阶段设计 - 添加 original_stock_code 和 normalized_stock_code 字段

使用方法:
python backend/database/migrate_stock_codes.py

迁移内容:
1. 添加 original_stock_code 和 normalized_stock_code 字段
2. 迁移现有数据
3. 验证迁移结果
"""

import sys
import os
from pathlib import Path

# 当前已经在backend目录下，不需要额外设置路径
# 只需要添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from sqlalchemy import text
from app.core.database import engine, get_db
from app.models.daily_trading import DailyTrading
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def add_new_columns():
    """添加新字段到数据库"""
    logger.info("🔧 开始添加新字段...")
    
    with engine.connect() as connection:
        try:
            # 检查字段是否已存在
            result = connection.execute(text("""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_NAME = 'daily_trading' 
                AND COLUMN_NAME IN ('original_stock_code', 'normalized_stock_code')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            if 'original_stock_code' not in existing_columns:
                logger.info("📝 添加 original_stock_code 字段...")
                connection.execute(text("""
                    ALTER TABLE daily_trading 
                    ADD COLUMN original_stock_code VARCHAR(20) DEFAULT '' COMMENT '原始股票代码 (如: SH600000)'
                """))
            else:
                logger.info("✅ original_stock_code 字段已存在")
            
            if 'normalized_stock_code' not in existing_columns:
                logger.info("📝 添加 normalized_stock_code 字段...")
                connection.execute(text("""
                    ALTER TABLE daily_trading 
                    ADD COLUMN normalized_stock_code VARCHAR(10) DEFAULT '' COMMENT '标准化股票代码 (如: 600000)'
                """))
            else:
                logger.info("✅ normalized_stock_code 字段已存在")
            
            connection.commit()
            logger.info("✅ 新字段添加完成!")
            
        except Exception as e:
            logger.error(f"❌ 添加字段失败: {e}")
            connection.rollback()
            raise

def migrate_existing_data():
    """迁移现有数据"""
    logger.info("🔄 开始数据迁移...")
    
    db = next(get_db())
    try:
        # 查询需要迁移的记录（original_stock_code为空的记录）
        records = db.query(DailyTrading).filter(
            (DailyTrading.original_stock_code == '') | 
            (DailyTrading.original_stock_code.is_(None))
        ).all()
        
        if not records:
            logger.info("✅ 没有需要迁移的数据")
            return
        
        logger.info(f"📊 找到 {len(records)} 条需要迁移的记录")
        
        updated_count = 0
        for record in records:
            original_code = record.stock_code
            
            # 解析股票代码
            if original_code.startswith('SH'):
                record.original_stock_code = original_code
                record.normalized_stock_code = original_code[2:]
            elif original_code.startswith('SZ'):
                record.original_stock_code = original_code
                record.normalized_stock_code = original_code[2:]
            elif original_code.startswith('BJ'):
                record.original_stock_code = original_code
                record.normalized_stock_code = original_code[2:]
            else:
                # 纯数字代码
                record.original_stock_code = original_code
                record.normalized_stock_code = original_code
            
            # 更新 stock_code 为标准化代码（保持向后兼容）
            record.stock_code = record.normalized_stock_code
            
            updated_count += 1
            
            # 批量提交，每1000条记录提交一次
            if updated_count % 1000 == 0:
                db.commit()
                logger.info(f"⏳ 已迁移 {updated_count}/{len(records)} 条记录...")
        
        # 最终提交
        db.commit()
        logger.info(f"✅ 数据迁移完成! 共更新 {updated_count} 条记录")
        
    except Exception as e:
        logger.error(f"❌ 数据迁移失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_indexes():
    """创建索引优化查询性能"""
    logger.info("🔍 创建优化索引...")
    
    with engine.connect() as connection:
        try:
            # 检查索引是否已存在
            indexes_to_create = [
                ('idx_original_stock_date', 'original_stock_code', 'trading_date'),
                ('idx_normalized_stock_date', 'normalized_stock_code', 'trading_date'),
            ]
            
            for index_name, *columns in indexes_to_create:
                # 检查索引是否存在
                result = connection.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.statistics 
                    WHERE table_name = 'daily_trading' AND index_name = '{index_name}'
                """))
                
                if result.fetchone()[0] == 0:
                    columns_str = ', '.join(columns)
                    logger.info(f"📝 创建索引 {index_name}...")
                    connection.execute(text(f"""
                        CREATE INDEX {index_name} ON daily_trading ({columns_str})
                    """))
                else:
                    logger.info(f"✅ 索引 {index_name} 已存在")
            
            connection.commit()
            logger.info("✅ 索引创建完成!")
            
        except Exception as e:
            logger.error(f"❌ 索引创建失败: {e}")
            connection.rollback()
            raise

def set_not_null_constraints():
    """设置非空约束"""
    logger.info("🔒 设置字段约束...")
    
    with engine.connect() as connection:
        try:
            logger.info("📝 设置 original_stock_code 为非空...")
            connection.execute(text("""
                ALTER TABLE daily_trading 
                MODIFY COLUMN original_stock_code VARCHAR(20) NOT NULL COMMENT '原始股票代码 (如: SH600000)'
            """))
            
            logger.info("📝 设置 normalized_stock_code 为非空...")
            connection.execute(text("""
                ALTER TABLE daily_trading 
                MODIFY COLUMN normalized_stock_code VARCHAR(10) NOT NULL COMMENT '标准化股票代码 (如: 600000)'
            """))
            
            connection.commit()
            logger.info("✅ 字段约束设置完成!")
            
        except Exception as e:
            logger.error(f"❌ 约束设置失败: {e}")
            connection.rollback()
            raise

def verify_migration():
    """验证迁移结果"""
    logger.info("🔎 验证迁移结果...")
    
    db = next(get_db())
    try:
        # 统计记录数
        total_records = db.query(DailyTrading).count()
        migrated_records = db.query(DailyTrading).filter(
            DailyTrading.original_stock_code != '',
            DailyTrading.normalized_stock_code != ''
        ).count()
        
        logger.info(f"📊 总记录数: {total_records}")
        logger.info(f"📊 已迁移记录数: {migrated_records}")
        
        if total_records > 0:
            completion_rate = (migrated_records / total_records) * 100
            logger.info(f"📊 迁移完成率: {completion_rate:.2f}%")
            
            if completion_rate < 100:
                logger.warning("⚠️ 部分记录未完成迁移!")
                return False
        
        # 验证数据一致性
        logger.info("🔍 验证数据一致性...")
        
        # 检查标准化代码是否正确
        sample_records = db.query(DailyTrading).limit(10).all()
        for record in sample_records:
            original = record.original_stock_code
            normalized = record.normalized_stock_code
            
            if original.startswith(('SH', 'SZ', 'BJ')):
                expected_normalized = original[2:]
            else:
                expected_normalized = original
            
            if normalized != expected_normalized:
                logger.error(f"❌ 数据不一致: {original} -> {normalized}, 期望: {expected_normalized}")
                return False
        
        logger.info("✅ 迁移验证通过!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return False
    finally:
        db.close()

def main():
    """主迁移流程"""
    logger.info("🚀 开始股票代码字段升级迁移...")
    logger.info(f"⏰ 开始时间: {datetime.now()}")
    
    try:
        # 步骤1: 添加新字段
        add_new_columns()
        
        # 步骤2: 迁移现有数据
        migrate_existing_data()
        
        # 步骤3: 创建索引
        create_indexes()
        
        # 步骤4: 设置约束
        set_not_null_constraints()
        
        # 步骤5: 验证结果
        if verify_migration():
            logger.info("🎉 股票代码字段升级迁移完成!")
            logger.info("📝 迁移内容:")
            logger.info("   ✅ 添加 original_stock_code 字段 (存储原始代码如SH600000)")
            logger.info("   ✅ 添加 normalized_stock_code 字段 (存储标准化代码如600000)")
            logger.info("   ✅ 迁移所有现有数据")
            logger.info("   ✅ 创建优化索引")
            logger.info("   ✅ 设置字段约束")
            logger.info("")
            logger.info("🔧 下一步:")
            logger.info("   1. 重启应用服务")
            logger.info("   2. 测试TXT文件导入功能")
            logger.info("   3. 验证概念汇总计算")
        else:
            logger.error("❌ 迁移验证失败，请检查日志!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 迁移失败: {e}")
        logger.error("请检查错误信息并修复问题后重试")
        sys.exit(1)
    
    logger.info(f"⏰ 完成时间: {datetime.now()}")

if __name__ == "__main__":
    main()