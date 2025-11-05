from typing import Dict, List, Optional
from sqlalchemy import text, MetaData, Table, Column, Integer, String, Date, DateTime, Boolean, Float, BigInteger, DECIMAL, Enum, JSON, Text, Index, UniqueConstraint
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
import logging

logger = logging.getLogger(__name__)

class DynamicTableManager:
    """动态表创建和管理器"""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.metadata = MetaData()

    def create_file_type_tables(self, file_type: str, force_recreate: bool = False) -> bool:
        """为指定文件类型创建完整的表结构"""

        try:
            table_prefix = f"{file_type}_" if file_type != 'txt' else ""

            # 检查表是否已存在
            if not force_recreate and self._tables_exist(file_type):
                logger.info(f"文件类型 {file_type} 的表已存在，跳过创建")
                return True

            # 重新初始化metadata以避免重复定义
            self.metadata = MetaData()

            # 1. 创建每日交易数据表
            self._create_daily_trading_table(table_prefix)

            # 2. 创建概念每日汇总表
            self._create_concept_summary_table(table_prefix)

            # 3. 创建股票概念排名表
            self._create_ranking_table(table_prefix)

            # 4. 创建概念创新高记录表
            self._create_high_record_table(table_prefix)

            # 5. 创建导入记录表
            self._create_import_record_table(table_prefix)

            # 6. 执行表创建
            self.metadata.create_all(self.engine)

            logger.info(f"成功为文件类型 {file_type} 创建所有表")
            return True

        except Exception as e:
            logger.error(f"创建文件类型 {file_type} 的表时出错: {e}")
            return False

    def _create_daily_trading_table(self, prefix: str):
        """创建每日交易数据表"""
        table_name = f"{prefix}daily_trading"

        table = Table(
            table_name, self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('original_stock_code', String(20), nullable=False, index=True, comment='原始股票代码'),
            Column('normalized_stock_code', String(10), nullable=False, index=True, comment='标准化股票代码'),
            Column('stock_code', String(20), nullable=False, index=True, comment='股票代码'),
            Column('trading_date', Date, nullable=False, index=True, comment='交易日期'),
            Column('trading_volume', Integer, nullable=False, comment='交易量'),
            Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),

            # 索引
            Index(f'idx_{prefix}stock_date', 'stock_code', 'trading_date'),
            Index(f'idx_{prefix}date_volume', 'trading_date', 'trading_volume'),
            Index(f'idx_{prefix}original_code', 'original_stock_code'),
            Index(f'idx_{prefix}normalized_code', 'normalized_stock_code'),

            # 唯一约束
            UniqueConstraint('stock_code', 'trading_date', name=f'uk_{prefix}stock_date'),

            comment=f'{prefix.upper() if prefix else "TXT"}每日交易数据表'
        )

        return table

    def _create_concept_summary_table(self, prefix: str):
        """创建概念每日汇总表"""
        table_name = f"{prefix}concept_daily_summary"

        table = Table(
            table_name, self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('concept_name', String(100), nullable=False, index=True, comment='概念名称'),
            Column('trading_date', Date, nullable=False, index=True, comment='交易日期'),
            Column('total_volume', BigInteger, nullable=False, comment='概念总交易量'),
            Column('stock_count', Integer, nullable=False, comment='概念内股票数量'),
            Column('average_volume', DECIMAL(15,2), nullable=False, comment='平均交易量'),
            Column('max_volume', Integer, nullable=False, comment='最大交易量'),
            Column('min_volume', Integer, server_default='0', comment='最小交易量'),
            Column('median_volume', DECIMAL(15,2), server_default='0', comment='中位数交易量'),
            Column('std_deviation', DECIMAL(15,4), server_default='0', comment='标准差'),
            Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
            Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),

            # 索引
            Index(f'idx_{prefix}concept_date', 'concept_name', 'trading_date'),
            Index(f'idx_{prefix}date_total', 'trading_date', 'total_volume'),
            Index(f'idx_{prefix}concept_volume', 'concept_name', 'total_volume'),

            # 唯一约束
            UniqueConstraint('concept_name', 'trading_date', name=f'uk_{prefix}concept_date'),

            comment=f'{prefix.upper() if prefix else "TXT"}概念每日汇总表'
        )

        return table

    def _create_ranking_table(self, prefix: str):
        """创建股票概念排名表"""
        table_name = f"{prefix}stock_concept_ranking"

        table = Table(
            table_name, self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('stock_code', String(20), nullable=False, index=True, comment='股票代码'),
            Column('concept_name', String(100), nullable=False, index=True, comment='概念名称'),
            Column('trading_date', Date, nullable=False, index=True, comment='交易日期'),
            Column('trading_volume', Integer, nullable=False, comment='交易量'),
            Column('concept_rank', Integer, nullable=False, comment='在概念中的排名'),
            Column('concept_total_volume', BigInteger, nullable=False, comment='概念总交易量'),
            Column('volume_percentage', DECIMAL(8,4), nullable=False, comment='占概念百分比'),
            Column('rank_change', Integer, server_default='0', comment='排名变化'),
            Column('volume_change_percentage', DECIMAL(8,4), server_default='0', comment='交易量变化百分比'),
            Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),

            # 索引
            Index(f'idx_{prefix}stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
            Index(f'idx_{prefix}concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
            Index(f'idx_{prefix}stock_date_rank', 'stock_code', 'trading_date', 'concept_rank'),
            Index(f'idx_{prefix}date_volume_desc', 'trading_date', text('trading_volume DESC')),

            # 唯一约束
            UniqueConstraint('stock_code', 'concept_name', 'trading_date', name=f'uk_{prefix}stock_concept_date'),

            comment=f'{prefix.upper() if prefix else "TXT"}股票概念排名表'
        )

        return table

    def _create_high_record_table(self, prefix: str):
        """创建概念创新高记录表"""
        table_name = f"{prefix}concept_high_record"

        # 创建枚举类型名称
        enum_name = f'enum_{prefix}high_type' if prefix else 'enum_high_type'

        table = Table(
            table_name, self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('concept_name', String(100), nullable=False, index=True, comment='概念名称'),
            Column('trading_date', Date, nullable=False, index=True, comment='创新高日期'),
            Column('total_volume', BigInteger, nullable=False, comment='创新高交易量'),
            Column('days_period', Integer, nullable=False, comment='统计周期天数'),
            Column('previous_high_volume', BigInteger, server_default='0', comment='前期最高交易量'),
            Column('increase_percentage', DECIMAL(8,4), server_default='0', comment='增长百分比'),
            Column('is_active', Boolean, server_default='1', comment='是否为当前活跃创新高'),
            Column('high_type', Enum('volume', 'count', 'average', name=enum_name), server_default='volume', comment='创新高类型'),
            Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),

            # 索引
            Index(f'idx_{prefix}concept_date_period', 'concept_name', 'trading_date', 'days_period'),
            Index(f'idx_{prefix}date_volume_active', 'trading_date', 'total_volume', 'is_active'),
            Index(f'idx_{prefix}concept_active', 'concept_name', 'is_active'),
            Index(f'idx_{prefix}period_volume', 'days_period', text('total_volume DESC')),

            # 唯一约束
            UniqueConstraint('concept_name', 'trading_date', 'days_period', name=f'uk_{prefix}concept_date_period'),

            comment=f'{prefix.upper() if prefix else "TXT"}概念创新高记录表'
        )

        return table

    def _create_import_record_table(self, prefix: str):
        """创建导入记录表"""
        table_name = f"{prefix}import_record" if prefix else "txt_import_record"

        # 创建枚举类型名称
        status_enum_name = f'enum_{prefix}import_status' if prefix else 'enum_import_status'
        mode_enum_name = f'enum_{prefix}import_mode' if prefix else 'enum_import_mode'

        table = Table(
            table_name, self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('filename', String(255), nullable=False, comment='原始文件名'),
            Column('trading_date', Date, nullable=False, index=True, comment='数据交易日期'),
            Column('file_size', BigInteger, nullable=False, comment='文件大小(字节)'),
            Column('file_hash', String(64), nullable=True, index=True, comment='文件MD5哈希值'),
            Column('import_status', Enum('processing', 'success', 'failed', 'cancelled', name=status_enum_name), nullable=False, server_default='processing'),
            Column('imported_by', String(50), nullable=False, comment='导入用户'),
            Column('import_mode', Enum('new', 'overwrite', 'append', name=mode_enum_name), server_default='overwrite', comment='导入模式'),
            Column('total_records', Integer, server_default='0', comment='文件总记录数'),
            Column('success_records', Integer, server_default='0', comment='成功导入记录数'),
            Column('error_records', Integer, server_default='0', comment='错误记录数'),
            Column('duplicate_records', Integer, server_default='0', comment='重复记录数'),
            Column('concept_count', Integer, server_default='0', comment='计算概念数量'),
            Column('ranking_count', Integer, server_default='0', comment='排名记录数量'),
            Column('new_high_count', Integer, server_default='0', comment='创新高记录数量'),
            Column('import_started_at', DateTime, nullable=False, comment='导入开始时间'),
            Column('import_completed_at', DateTime, nullable=True, comment='导入完成时间'),
            Column('calculation_time', DECIMAL(10,3), server_default='0', comment='计算耗时(秒)'),
            Column('error_message', Text, nullable=True, comment='错误信息'),
            Column('error_details', JSON, nullable=True, comment='错误详情JSON'),
            Column('notes', Text, nullable=True, comment='备注信息'),
            Column('created_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
            Column('updated_at', DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),

            # 索引
            Index(f'idx_{prefix}trading_date_status', 'trading_date', 'import_status'),
            Index(f'idx_{prefix}imported_by_date', 'imported_by', 'trading_date'),
            Index(f'idx_{prefix}filename', 'filename'),
            Index(f'idx_{prefix}status_date', 'import_status', 'import_started_at'),
            Index(f'idx_{prefix}file_hash', 'file_hash'),

            comment=f'{prefix.upper() if prefix else "TXT"}文件导入记录表'
        )

        return table

    def _tables_exist(self, file_type: str) -> bool:
        """检查指定文件类型的表是否已存在"""
        prefix = f"{file_type}_" if file_type != 'txt' else ""

        table_names = [
            f"{prefix}daily_trading",
            f"{prefix}concept_daily_summary",
            f"{prefix}stock_concept_ranking",
            f"{prefix}concept_high_record",
            f"{prefix}import_record" if prefix else "txt_import_record"
        ]

        try:
            with self.engine.connect() as conn:
                for table_name in table_names:
                    result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                    if not result.fetchone():
                        return False
            return True
        except Exception as e:
            logger.error(f"检查表是否存在时出错: {e}")
            return False

    def drop_file_type_tables(self, file_type: str) -> bool:
        """删除指定文件类型的所有表"""
        try:
            prefix = f"{file_type}_" if file_type != 'txt' else ""

            table_names = [
                f"{prefix}import_record" if prefix else "txt_import_record",
                f"{prefix}concept_high_record",
                f"{prefix}stock_concept_ranking",
                f"{prefix}concept_daily_summary",
                f"{prefix}daily_trading"
            ]

            with self.engine.connect() as conn:
                # 禁用外键检查
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

                for table_name in table_names:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                        logger.info(f"删除表 {table_name}")
                    except Exception as e:
                        logger.warning(f"删除表 {table_name} 时出错: {e}")

                # 删除相关的枚举类型（如果数据库支持）
                try:
                    enum_names = [
                        f'enum_{prefix}high_type' if prefix else 'enum_high_type',
                        f'enum_{prefix}import_status' if prefix else 'enum_import_status',
                        f'enum_{prefix}import_mode' if prefix else 'enum_import_mode'
                    ]
                    # MySQL 不需要手动删除枚举，它们会随表自动清理
                except Exception as e:
                    logger.debug(f"清理枚举类型时出错（可忽略）: {e}")

                # 恢复外键检查
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                conn.commit()

            logger.info(f"成功删除文件类型 {file_type} 的所有表")
            return True

        except Exception as e:
            logger.error(f"删除文件类型 {file_type} 的表时出错: {e}")
            return False

    def get_table_info(self, file_type: str) -> Dict:
        """获取指定文件类型的表信息"""
        prefix = f"{file_type}_" if file_type != 'txt' else ""

        table_info = {}
        table_names = [
            f"{prefix}daily_trading",
            f"{prefix}concept_daily_summary",
            f"{prefix}stock_concept_ranking",
            f"{prefix}concept_high_record",
            f"{prefix}import_record" if prefix else "txt_import_record"
        ]

        try:
            with self.engine.connect() as conn:
                for table_name in table_names:
                    try:
                        # 检查表是否存在
                        result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))
                        exists = result.fetchone() is not None

                        if exists:
                            # 获取表行数
                            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                            row_count = count_result.fetchone()[0]

                            # 获取表大小信息
                            size_result = conn.execute(text(f"""
                                SELECT
                                    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
                                FROM information_schema.tables
                                WHERE table_schema = DATABASE() AND table_name = '{table_name}'
                            """))
                            size_info = size_result.fetchone()
                            size_mb = size_info[0] if size_info else 0

                            table_info[table_name] = {
                                'exists': True,
                                'row_count': row_count,
                                'size_mb': size_mb
                            }
                        else:
                            table_info[table_name] = {
                                'exists': False,
                                'row_count': 0,
                                'size_mb': 0
                            }

                    except Exception as e:
                        table_info[table_name] = {
                            'exists': False,
                            'row_count': 0,
                            'size_mb': 0,
                            'error': str(e)
                        }
        except Exception as e:
            logger.error(f"获取表信息时出错: {e}")

        return table_info

    def recreate_file_type_tables(self, file_type: str) -> bool:
        """重新创建文件类型的所有表（先删除再创建）"""
        try:
            # 先删除表
            if not self.drop_file_type_tables(file_type):
                logger.warning(f"删除文件类型 {file_type} 的表时出现问题，继续尝试创建")

            # 再创建表
            return self.create_file_type_tables(file_type, force_recreate=True)

        except Exception as e:
            logger.error(f"重新创建文件类型 {file_type} 的表时出错: {e}")
            return False