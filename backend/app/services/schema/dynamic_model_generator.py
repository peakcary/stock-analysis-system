from typing import Dict, Type, Any, List
from sqlalchemy import MetaData, Table, Column, Integer, String, Date, DateTime, BigInteger, DECIMAL, Boolean, Enum, Text, JSON, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import logging
from datetime import datetime, date
from enum import Enum as PyEnum

logger = logging.getLogger(__name__)

# 使用项目的Base
from app.core.database import Base

class DynamicModelGenerator:
    """动态SQLAlchemy模型生成器"""

    def __init__(self, engine):
        self.engine = engine
        self.metadata = MetaData()
        self._model_cache = {}

    def _cleanup_metadata_for_file_type(self, file_type: str, prefix: str):
        """清理指定文件类型的MetaData表定义"""
        table_names = [
            f"{prefix}daily_trading",
            f"{prefix}concept_daily_summary",
            f"{prefix}stock_concept_ranking",
            f"{prefix}concept_high_record",
            f"{prefix}import_record"
        ]

        for table_name in table_names:
            if table_name in self.metadata.tables:
                self.metadata.remove(self.metadata.tables[table_name])
                logger.debug(f"从MetaData中移除表定义: {table_name}")

    def generate_models_for_file_type(self, file_type: str) -> Dict[str, Type]:
        """为指定文件类型生成所有SQLAlchemy模型"""

        if file_type in self._model_cache:
            return self._model_cache[file_type]

        prefix = f"{file_type}_" if file_type != 'txt' else ""
        models = {}

        try:
            # 清理可能存在的表定义
            self._cleanup_metadata_for_file_type(file_type, prefix)
            # 1. 生成每日交易数据模型
            models['daily_trading'] = self._create_daily_trading_model(file_type, prefix)

            # 2. 生成概念汇总模型
            models['concept_summary'] = self._create_concept_summary_model(file_type, prefix)

            # 3. 生成排名模型
            models['ranking'] = self._create_ranking_model(file_type, prefix)

            # 4. 生成创新高记录模型
            models['high_record'] = self._create_high_record_model(file_type, prefix)

            # 5. 生成导入记录模型
            models['import_record'] = self._create_import_record_model(file_type, prefix)

            # 缓存模型
            self._model_cache[file_type] = models

            logger.info(f"成功为文件类型 {file_type} 生成 {len(models)} 个模型")
            return models

        except Exception as e:
            logger.error(f"为文件类型 {file_type} 生成模型时出错: {e}")
            return {}

    def _create_daily_trading_model(self, file_type: str, prefix: str) -> Type:
        """创建每日交易数据模型"""
        table_name = f"{prefix}daily_trading"
        class_name = f"{file_type.title()}DailyTrading"

        # 动态创建类
        attrs = {
            '__tablename__': table_name,
            '__table_args__': (
                Index(f'idx_{prefix}stock_date', 'stock_code', 'trading_date'),
                Index(f'idx_{prefix}date_volume', 'trading_date', 'trading_volume'),
                Index(f'idx_{prefix}original_code', 'original_stock_code'),
                Index(f'idx_{prefix}normalized_code', 'normalized_stock_code'),
                UniqueConstraint('stock_code', 'trading_date', name=f'uk_{prefix}stock_date'),
                {'comment': f'{prefix.upper() if prefix else "TXT"}每日交易数据表'}
            ),
            'id': Column(Integer, primary_key=True, index=True),
            'original_stock_code': Column(String(20), nullable=False, index=True, comment='原始股票代码'),
            'normalized_stock_code': Column(String(10), nullable=False, index=True, comment='标准化股票代码'),
            'stock_code': Column(String(20), nullable=False, index=True, comment='股票代码'),
            'trading_date': Column(Date, nullable=False, index=True, comment='交易日期'),
            'trading_volume': Column(Integer, nullable=False, comment='交易量'),
            'created_at': Column(DateTime, default=datetime.utcnow)
        }

        # 动态创建模型类
        # 如果类已经存在，先从Base的注册表中移除
        if hasattr(Base.registry._class_registry, class_name):
            delattr(Base.registry._class_registry, class_name)

        model_class = type(class_name, (Base,), attrs)

        return model_class

    def _create_concept_summary_model(self, file_type: str, prefix: str) -> Type:
        """创建概念汇总模型"""
        table_name = f"{prefix}concept_daily_summary"
        class_name = f"{file_type.title()}ConceptDailySummary"

        attrs = {
            '__tablename__': table_name,
            '__table_args__': (
                Index(f'idx_{prefix}concept_date', 'concept_name', 'trading_date'),
                Index(f'idx_{prefix}date_total', 'trading_date', 'total_volume'),
                Index(f'idx_{prefix}concept_volume', 'concept_name', 'total_volume'),
                UniqueConstraint('concept_name', 'trading_date', name=f'uk_{prefix}concept_date'),
                {'comment': f'{prefix.upper() if prefix else "TXT"}概念每日汇总表'}
            ),
            'id': Column(Integer, primary_key=True, index=True),
            'concept_name': Column(String(100), nullable=False, index=True, comment='概念名称'),
            'trading_date': Column(Date, nullable=False, index=True, comment='交易日期'),
            'total_volume': Column(BigInteger, nullable=False, comment='概念总交易量'),
            'stock_count': Column(Integer, nullable=False, comment='概念内股票数量'),
            'average_volume': Column(DECIMAL(15,2), nullable=False, comment='平均交易量'),
            'max_volume': Column(Integer, nullable=False, comment='最大交易量'),
            'min_volume': Column(Integer, default=0, comment='最小交易量'),
            'median_volume': Column(DECIMAL(15,2), default=0, comment='中位数交易量'),
            'std_deviation': Column(DECIMAL(15,4), default=0, comment='标准差'),
            'created_at': Column(DateTime, default=datetime.utcnow),
            'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        }

        # 如果类已经存在，先从Base的注册表中移除
        if hasattr(Base.registry._class_registry, class_name):
            delattr(Base.registry._class_registry, class_name)

        model_class = type(class_name, (Base,), attrs)
        return model_class

    def _create_ranking_model(self, file_type: str, prefix: str) -> Type:
        """创建排名模型"""
        table_name = f"{prefix}stock_concept_ranking"
        class_name = f"{file_type.title()}StockConceptRanking"

        attrs = {
            '__tablename__': table_name,
            '__table_args__': (
                Index(f'idx_{prefix}stock_concept_date', 'stock_code', 'concept_name', 'trading_date'),
                Index(f'idx_{prefix}concept_date_rank', 'concept_name', 'trading_date', 'concept_rank'),
                Index(f'idx_{prefix}stock_date_rank', 'stock_code', 'trading_date', 'concept_rank'),
                Index(f'idx_{prefix}date_volume_desc', 'trading_date', 'trading_volume'),
                UniqueConstraint('stock_code', 'concept_name', 'trading_date', name=f'uk_{prefix}stock_concept_date'),
                {'comment': f'{prefix.upper() if prefix else "TXT"}股票概念排名表'}
            ),
            'id': Column(Integer, primary_key=True, index=True),
            'stock_code': Column(String(20), nullable=False, index=True, comment='股票代码'),
            'concept_name': Column(String(100), nullable=False, index=True, comment='概念名称'),
            'trading_date': Column(Date, nullable=False, index=True, comment='交易日期'),
            'trading_volume': Column(Integer, nullable=False, comment='交易量'),
            'concept_rank': Column(Integer, nullable=False, comment='在概念中的排名'),
            'concept_total_volume': Column(BigInteger, nullable=False, comment='概念总交易量'),
            'volume_percentage': Column(DECIMAL(8,4), nullable=False, comment='占概念百分比'),
            'rank_change': Column(Integer, default=0, comment='排名变化'),
            'volume_change_percentage': Column(DECIMAL(8,4), default=0, comment='交易量变化百分比'),
            'created_at': Column(DateTime, default=datetime.utcnow)
        }

        # 如果类已经存在，先从Base的注册表中移除
        if hasattr(Base.registry._class_registry, class_name):
            delattr(Base.registry._class_registry, class_name)

        model_class = type(class_name, (Base,), attrs)
        return model_class

    def _create_high_record_model(self, file_type: str, prefix: str) -> Type:
        """创建创新高记录模型"""
        table_name = f"{prefix}concept_high_record"
        class_name = f"{file_type.title()}ConceptHighRecord"

        # 定义枚举类型
        class HighType(PyEnum):
            VOLUME = "volume"
            COUNT = "count"
            AVERAGE = "average"

        # 动态创建枚举名称
        enum_name = f'enum_{prefix}high_type' if prefix else 'enum_high_type'

        attrs = {
            '__tablename__': table_name,
            '__table_args__': (
                Index(f'idx_{prefix}concept_date_period', 'concept_name', 'trading_date', 'days_period'),
                Index(f'idx_{prefix}date_volume_active', 'trading_date', 'total_volume', 'is_active'),
                Index(f'idx_{prefix}concept_active', 'concept_name', 'is_active'),
                Index(f'idx_{prefix}period_volume', 'days_period', 'total_volume'),
                UniqueConstraint('concept_name', 'trading_date', 'days_period', name=f'uk_{prefix}concept_date_period'),
                {'comment': f'{prefix.upper() if prefix else "TXT"}概念创新高记录表'}
            ),
            'id': Column(Integer, primary_key=True, index=True),
            'concept_name': Column(String(100), nullable=False, index=True, comment='概念名称'),
            'trading_date': Column(Date, nullable=False, index=True, comment='创新高日期'),
            'total_volume': Column(BigInteger, nullable=False, comment='创新高交易量'),
            'days_period': Column(Integer, nullable=False, comment='统计周期天数'),
            'previous_high_volume': Column(BigInteger, default=0, comment='前期最高交易量'),
            'increase_percentage': Column(DECIMAL(8,4), default=0, comment='增长百分比'),
            'is_active': Column(Boolean, default=True, comment='是否为当前活跃创新高'),
            'high_type': Column(Enum(HighType, name=enum_name), default=HighType.VOLUME, comment='创新高类型'),
            'created_at': Column(DateTime, default=datetime.utcnow),
            # 添加枚举类型到类中，供外部使用
            'HighType': HighType
        }

        # 如果类已经存在，先从Base的注册表中移除
        if hasattr(Base.registry._class_registry, class_name):
            delattr(Base.registry._class_registry, class_name)

        model_class = type(class_name, (Base,), attrs)
        return model_class

    def _create_import_record_model(self, file_type: str, prefix: str) -> Type:
        """创建导入记录模型"""
        table_name = f"{prefix}import_record" if prefix else "txt_import_record"
        class_name = f"{file_type.title()}ImportRecord"

        # 定义枚举类型
        class ImportStatus(PyEnum):
            PROCESSING = "processing"
            SUCCESS = "success"
            FAILED = "failed"
            CANCELLED = "cancelled"

        class ImportMode(PyEnum):
            NEW = "new"
            OVERWRITE = "overwrite"
            APPEND = "append"

        # 动态创建枚举名称
        status_enum_name = f'enum_{prefix}import_status' if prefix else 'enum_import_status'
        mode_enum_name = f'enum_{prefix}import_mode' if prefix else 'enum_import_mode'

        attrs = {
            '__tablename__': table_name,
            '__table_args__': (
                Index(f'idx_{prefix}trading_date_status', 'trading_date', 'import_status'),
                Index(f'idx_{prefix}imported_by_date', 'imported_by', 'trading_date'),
                Index(f'idx_{prefix}filename', 'filename'),
                Index(f'idx_{prefix}status_date', 'import_status', 'import_started_at'),
                Index(f'idx_{prefix}file_hash', 'file_hash'),
                {'comment': f'{prefix.upper() if prefix else "TXT"}文件导入记录表'}
            ),
            'id': Column(Integer, primary_key=True, index=True),
            'filename': Column(String(255), nullable=False, comment='原始文件名'),
            'trading_date': Column(Date, nullable=False, index=True, comment='数据交易日期'),
            'file_size': Column(BigInteger, nullable=False, comment='文件大小(字节)'),
            'file_hash': Column(String(64), nullable=True, index=True, comment='文件MD5哈希值'),
            'import_status': Column(Enum(ImportStatus, name=status_enum_name), nullable=False, default=ImportStatus.PROCESSING),
            'imported_by': Column(String(50), nullable=False, comment='导入用户'),
            'import_mode': Column(Enum(ImportMode, name=mode_enum_name), default=ImportMode.OVERWRITE, comment='导入模式'),
            'total_records': Column(Integer, default=0, comment='文件总记录数'),
            'success_records': Column(Integer, default=0, comment='成功导入记录数'),
            'error_records': Column(Integer, default=0, comment='错误记录数'),
            'duplicate_records': Column(Integer, default=0, comment='重复记录数'),
            'concept_count': Column(Integer, default=0, comment='计算概念数量'),
            'ranking_count': Column(Integer, default=0, comment='排名记录数量'),
            'new_high_count': Column(Integer, default=0, comment='创新高记录数量'),
            'import_started_at': Column(DateTime, nullable=False, comment='导入开始时间'),
            'import_completed_at': Column(DateTime, nullable=True, comment='导入完成时间'),
            'calculation_time': Column(DECIMAL(10,3), default=0, comment='计算耗时(秒)'),
            'error_message': Column(Text, nullable=True, comment='错误信息'),
            'error_details': Column(JSON, nullable=True, comment='错误详情JSON'),
            'notes': Column(Text, nullable=True, comment='备注信息'),
            'created_at': Column(DateTime, default=datetime.utcnow),
            'updated_at': Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            # 添加枚举类型到类中，供外部使用
            'ImportStatus': ImportStatus,
            'ImportMode': ImportMode
        }

        # 如果类已经存在，先从Base的注册表中移除
        if hasattr(Base.registry._class_registry, class_name):
            delattr(Base.registry._class_registry, class_name)

        model_class = type(class_name, (Base,), attrs)
        return model_class

    def get_models_for_file_type(self, file_type: str) -> Dict[str, Type]:
        """获取指定文件类型的所有模型"""
        if file_type not in self._model_cache:
            return self.generate_models_for_file_type(file_type)
        return self._model_cache[file_type]

    def clear_model_cache(self, file_type: str = None):
        """清理模型缓存"""
        if file_type:
            self._model_cache.pop(file_type, None)
            logger.info(f"清理文件类型 {file_type} 的模型缓存")
        else:
            self._model_cache.clear()
            logger.info("清理所有模型缓存")

    def get_model_by_name(self, file_type: str, model_name: str) -> Type:
        """根据名称获取特定模型"""
        models = self.get_models_for_file_type(file_type)
        return models.get(model_name)

    def list_cached_file_types(self) -> List[str]:
        """列出已缓存的文件类型"""
        return list(self._model_cache.keys())

    def get_model_info(self, file_type: str) -> Dict[str, Any]:
        """获取模型信息"""
        models = self.get_models_for_file_type(file_type)

        model_info = {}
        for name, model_class in models.items():
            model_info[name] = {
                'class_name': model_class.__name__,
                'table_name': model_class.__tablename__,
                'columns': [col.name for col in model_class.__table__.columns],
                'indexes': len(model_class.__table__.indexes),
                'comment': getattr(model_class.__table__, 'comment', '')
            }

        return {
            'file_type': file_type,
            'models_count': len(models),
            'models': model_info
        }

    def validate_models(self, file_type: str) -> Dict[str, Any]:
        """验证模型完整性"""
        try:
            models = self.get_models_for_file_type(file_type)

            expected_models = ['daily_trading', 'concept_summary', 'ranking', 'high_record', 'import_record']

            validation_results = {
                'file_type': file_type,
                'valid': True,
                'missing_models': [],
                'model_details': {}
            }

            # 检查必需的模型是否存在
            for expected_model in expected_models:
                if expected_model not in models:
                    validation_results['missing_models'].append(expected_model)
                    validation_results['valid'] = False
                else:
                    model_class = models[expected_model]
                    validation_results['model_details'][expected_model] = {
                        'exists': True,
                        'table_name': model_class.__tablename__,
                        'columns_count': len(model_class.__table__.columns)
                    }

            return validation_results

        except Exception as e:
            return {
                'file_type': file_type,
                'valid': False,
                'error': str(e)
            }