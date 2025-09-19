"""
通用导入服务 - 支持动态文件类型的股票数据导入处理
基于原TXT导入服务的业务逻辑，支持多种文件类型
"""

from typing import Dict, List, Optional, Any, Tuple, Union, IO
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from io import StringIO
import pandas as pd
import hashlib
import logging
from datetime import datetime, date
import re
from pathlib import Path

from app.services.schema import FileTypeRegistry, FileTypeConfig
from app.core.database import get_engine

logger = logging.getLogger(__name__)

class UniversalImportService:
    """通用导入服务类"""

    def __init__(self, db: Session, file_type: str):
        """
        初始化通用导入服务

        Args:
            db: 数据库会话
            file_type: 文件类型标识 (如: txt, ttv, eee等)
        """
        self.db = db
        self.file_type = file_type
        self.engine = get_engine()

        # 初始化注册管理器
        self.registry = FileTypeRegistry(self.engine, db)

        # 获取文件类型配置
        self.config = self.registry.get_file_type_config(file_type)
        if not self.config:
            raise ValueError(f"文件类型 {file_type} 未注册或配置不存在")

        # 获取动态模型
        self.models = self.registry.model_generator.get_models_for_file_type(file_type)
        if not self.models:
            raise ValueError(f"文件类型 {file_type} 的数据模型未生成")

        # 设置模型引用
        self.DailyTrading = self.models['daily_trading']
        self.ConceptDailySummary = self.models['concept_summary']
        self.StockConceptRanking = self.models['ranking']
        self.ConceptHighRecord = self.models['high_record']
        self.ImportRecord = self.models['import_record']

        logger.info(f"初始化 {file_type} 文件类型的通用导入服务")

    def parse_file_content(self, file_content: str, filename: str) -> List[Dict]:
        """
        解析文件内容 - 与原始TXT导入逻辑保持一致

        Args:
            file_content: 文件内容字符串
            filename: 文件名

        Returns:
            解析后的交易数据列表
        """
        try:
            trading_data = []
            lines = file_content.strip().split('\n')

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    parts = line.split('\t')
                    if len(parts) != 3:
                        logger.warning(f"第{line_num}行格式不正确: {line}")
                        continue

                    stock_code, date_str, volume_str = parts

                    # 解析日期
                    trading_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # 解析交易量 (处理空值和浮点数)
                    volume_str = volume_str.strip()
                    if not volume_str:
                        logger.warning(f"第{line_num}行交易量为空: {line}")
                        continue

                    # 支持浮点数格式，转换为整数
                    try:
                        trading_volume = int(float(volume_str))
                    except ValueError:
                        logger.warning(f"第{line_num}行交易量格式错误: {volume_str}")
                        continue

                    # 解析股票代码 - 保持与原始TXT导入一致的逻辑
                    stock_info = self._normalize_stock_code(stock_code)

                    trading_data.append({
                        'original_stock_code': stock_info['original'],     # 原始代码
                        'normalized_stock_code': stock_info['normalized'], # 标准化代码
                        'stock_code': stock_info['normalized'],           # 股票代码 (保持兼容性)
                        'trading_date': trading_date,
                        'trading_volume': trading_volume,
                        'market_prefix': stock_info['prefix']             # 市场前缀 (SH/SZ/BJ)
                    })

                except Exception as e:
                    logger.error(f"解析第{line_num}行时出错: {line}, 错误: {e}")
                    continue

            logger.info(f"成功解析{len(trading_data)}条交易数据")
            return trading_data

        except Exception as e:
            logger.error(f"解析文件内容失败: {e}")
            raise


    def _normalize_stock_code(self, original_code: str) -> dict:
        """
        解析股票代码，提取原始代码和标准化代码
        与原始TXT导入服务保持完全一致的逻辑

        Args:
            original_code: 原始股票代码 (SH600000, SZ000001等)

        Returns:
            dict: {
                'original': '原始代码',
                'normalized': '标准化代码',
                'prefix': '市场前缀'
            }
        """
        original = original_code.strip().upper()

        # 提取前缀和标准化代码
        if original.startswith('SH'):
            return {
                'original': original,
                'normalized': original[2:],
                'prefix': 'SH'
            }
        elif original.startswith('SZ'):
            return {
                'original': original,
                'normalized': original[2:],
                'prefix': 'SZ'
            }
        elif original.startswith('BJ'):
            return {
                'original': original,
                'normalized': original[2:],
                'prefix': 'BJ'
            }
        else:
            # 纯数字代码，无前缀
            return {
                'original': original,
                'normalized': original,
                'prefix': ''
            }

    def _clear_daily_data(self, trading_date: date, keep_trading_data: bool = False):
        """
        清理指定日期的数据
        与原始TXT导入服务保持一致的清理逻辑

        Args:
            trading_date: 要清理的交易日期
            keep_trading_data: 是否保留交易数据（仅清理汇总数据）
        """
        try:
            # 清理汇总数据
            self.db.query(self.ConceptDailySummary).filter(
                self.ConceptDailySummary.trading_date == trading_date
            ).delete()

            self.db.query(self.StockConceptRanking).filter(
                self.StockConceptRanking.trading_date == trading_date
            ).delete()

            self.db.query(self.ConceptHighRecord).filter(
                self.ConceptHighRecord.trading_date == trading_date
            ).delete()

            # 如果不保留交易数据，也删除原始交易数据
            if not keep_trading_data:
                self.db.query(self.DailyTrading).filter(
                    self.DailyTrading.trading_date == trading_date
                ).delete()

            self.db.flush()
            logger.info(f"清理 {trading_date} 数据完成，保留交易数据: {keep_trading_data}")

        except Exception as e:
            logger.error(f"清理 {trading_date} 数据失败: {e}")
            raise

    def calculate_file_hash(self, file_content: str) -> str:
        """计算文件内容的MD5哈希值"""
        return hashlib.md5(file_content.encode('utf-8')).hexdigest()

    def import_daily_trading_data(self, trading_data: List[Dict], trading_date: date,
                                import_record_id: int, mode: str = "overwrite") -> Dict:
        """
        导入每日交易数据

        Args:
            trading_data: 解析后的交易数据列表
            trading_date: 交易日期
            import_record_id: 导入记录ID
            mode: 导入模式 (overwrite, append)

        Returns:
            导入结果字典
        """
        try:
            success_count = 0
            error_count = 0
            duplicate_count = 0

            # 如果是覆盖模式，先清理当日所有相关数据
            if mode == "overwrite":
                self._clear_daily_data(trading_date)
                logger.info(f"覆盖模式: 已清理 {trading_date} 的所有相关数据")

            # 批量插入数据
            batch_size = 1000  # 使用固定批次大小
            total_rows = len(trading_data)

            for i in range(0, total_rows, batch_size):
                batch_data = trading_data[i:i + batch_size]
                batch_records = []

                for row in batch_data:
                    try:
                        # 检查是否已存在（仅在append模式下）
                        if mode == "append":
                            existing = self.db.query(self.DailyTrading).filter(
                                self.DailyTrading.stock_code == row['stock_code'],
                                self.DailyTrading.trading_date == trading_date
                            ).first()

                            if existing:
                                duplicate_count += 1
                                continue

                        # 创建记录对象 - 添加市场前缀字段
                        record = self.DailyTrading(
                            original_stock_code=row['original_stock_code'],
                            normalized_stock_code=row['normalized_stock_code'],
                            stock_code=row['stock_code'],
                            trading_date=trading_date,
                            trading_volume=int(row['trading_volume']),
                            created_at=datetime.utcnow()
                        )

                        # 如果动态表支持市场前缀字段，则添加
                        if hasattr(record, 'market_prefix') and 'market_prefix' in row:
                            record.market_prefix = row['market_prefix']

                        batch_records.append(record)

                    except Exception as e:
                        logger.error(f"处理数据行失败: {e}")
                        error_count += 1

                # 批量插入
                if batch_records:
                    try:
                        self.db.add_all(batch_records)
                        self.db.flush()
                        success_count += len(batch_records)
                        logger.info(f"成功插入批次: {len(batch_records)} 条记录")
                    except Exception as e:
                        logger.error(f"批量插入失败: {e}")
                        self.db.rollback()
                        error_count += len(batch_records)

            result = {
                'success_records': success_count,
                'error_records': error_count,
                'duplicate_records': duplicate_count,
                'total_processed': success_count + error_count + duplicate_count
            }

            logger.info(f"导入完成: 成功{success_count}, 错误{error_count}, 重复{duplicate_count}")
            return result

        except Exception as e:
            logger.error(f"导入每日交易数据失败: {e}")
            self.db.rollback()
            raise

    def perform_calculations(self, trading_date: date, import_record_id: int) -> Dict:
        """
        执行各种计算（概念汇总、排名、创新高等）
        基于原TXT导入服务的计算逻辑

        Args:
            trading_date: 交易日期
            import_record_id: 导入记录ID

        Returns:
            计算结果字典
        """
        calculation_results = {
            'concept_count': 0,
            'ranking_count': 0,
            'new_high_count': 0
        }

        try:
            # 1. 概念汇总计算
            if self.config.enable_concept_summary:
                concept_result = self._calculate_concept_summary(trading_date)
                calculation_results['concept_count'] = concept_result['count']
                logger.info(f"概念汇总计算完成: {concept_result['count']} 个概念")

            # 2. 排名计算
            if self.config.enable_ranking:
                ranking_result = self._calculate_rankings(trading_date)
                calculation_results['ranking_count'] = ranking_result['count']
                logger.info(f"排名计算完成: {ranking_result['count']} 条排名记录")

            # 3. 创新高记录计算
            if self.config.enable_high_record:
                high_record_result = self._calculate_high_records(trading_date)
                calculation_results['new_high_count'] = high_record_result['count']
                logger.info(f"创新高计算完成: {high_record_result['count']} 条创新高记录")

            return calculation_results

        except Exception as e:
            logger.error(f"执行计算失败: {e}")
            raise

    def _calculate_concept_summary(self, trading_date: date) -> Dict:
        """计算概念每日汇总 - 基于原TXT服务逻辑"""
        try:
            # 这里需要实现概念映射逻辑
            # 由于原系统复杂性，这里提供框架，具体实现需要根据概念映射文件来完成

            concept_count = 0
            # TODO: 实现具体的概念汇总计算逻辑
            # 1. 读取概念映射文件
            # 2. 为每只股票分配概念
            # 3. 按概念计算汇总数据
            # 4. 插入概念汇总表

            logger.info("概念汇总计算需要进一步实现具体逻辑")

            return {'count': concept_count}

        except Exception as e:
            logger.error(f"概念汇总计算失败: {e}")
            raise

    def _calculate_rankings(self, trading_date: date) -> Dict:
        """计算股票概念排名 - 基于原TXT服务逻辑"""
        try:
            ranking_count = 0
            # TODO: 实现排名计算逻辑
            # 1. 基于概念汇总数据计算每个概念内的股票排名
            # 2. 计算排名变化
            # 3. 插入排名表

            logger.info("排名计算需要进一步实现具体逻辑")

            return {'count': ranking_count}

        except Exception as e:
            logger.error(f"排名计算失败: {e}")
            raise

    def _calculate_high_records(self, trading_date: date) -> Dict:
        """计算创新高记录 - 基于原TXT服务逻辑"""
        try:
            high_record_count = 0
            # TODO: 实现创新高记录计算逻辑
            # 1. 计算各个时间周期的概念交易量
            # 2. 识别创新高记录
            # 3. 插入创新高记录表

            logger.info("创新高记录计算需要进一步实现具体逻辑")

            return {'count': high_record_count}

        except Exception as e:
            logger.error(f"创新高记录计算失败: {e}")
            raise

    def create_import_record(self, filename: str, file_size: int, file_hash: str,
                           trading_date: date, imported_by: str, mode: str = "overwrite") -> int:
        """创建导入记录"""
        try:
            ImportStatus = self.ImportRecord.ImportStatus
            ImportMode = self.ImportRecord.ImportMode

            import_record = self.ImportRecord(
                filename=filename,
                trading_date=trading_date,
                file_size=file_size,
                file_hash=file_hash,
                import_status=ImportStatus.PROCESSING,
                imported_by=imported_by,
                import_mode=ImportMode.OVERWRITE if mode == "overwrite" else ImportMode.APPEND,
                import_started_at=datetime.utcnow()
            )

            self.db.add(import_record)
            self.db.flush()

            logger.info(f"创建导入记录: ID={import_record.id}")
            return import_record.id

        except Exception as e:
            logger.error(f"创建导入记录失败: {e}")
            raise

    def update_import_record(self, import_record_id: int, update_data: Dict):
        """更新导入记录"""
        try:
            import_record = self.db.query(self.ImportRecord).filter(
                self.ImportRecord.id == import_record_id
            ).first()

            if not import_record:
                raise ValueError(f"导入记录 {import_record_id} 不存在")

            for key, value in update_data.items():
                setattr(import_record, key, value)

            self.db.flush()
            logger.info(f"更新导入记录: ID={import_record_id}")

        except Exception as e:
            logger.error(f"更新导入记录失败: {e}")
            raise

    def import_file(self, file_content: str, filename: str, trading_date: date,
                   imported_by: str, mode: str = "overwrite") -> Dict:
        """
        完整的文件导入流程

        Args:
            file_content: 文件内容
            filename: 文件名
            trading_date: 交易日期
            imported_by: 导入用户
            mode: 导入模式

        Returns:
            导入结果字典
        """
        start_time = datetime.utcnow()
        import_record_id = None

        try:
            # 1. 计算文件哈希
            file_hash = self.calculate_file_hash(file_content)
            file_size = len(file_content.encode('utf-8'))

            # 检查是否已有该日期的数据，与原始TXT导入保持一致
            existing_records = self.db.query(self.ImportRecord).filter(
                self.ImportRecord.trading_date == trading_date
            ).count()

            if existing_records > 0:
                logger.info(f"检测到{trading_date}已有导入记录，将进行覆盖导入")
                # 删除该日期的所有导入记录
                self.db.query(self.ImportRecord).filter(
                    self.ImportRecord.trading_date == trading_date
                ).delete()
                self.db.commit()

            # 2. 创建导入记录
            import_record_id = self.create_import_record(
                filename, file_size, file_hash, trading_date, imported_by, mode
            )

            # 3. 解析文件内容
            trading_data = self.parse_file_content(file_content, filename)

            # 验证是否有有效数据
            if not trading_data:
                raise ValueError("未解析到有效数据")

            # 获取交易日期（假设所有数据是同一天的）
            trading_dates = list(set(item['trading_date'] for item in trading_data))
            if len(trading_dates) > 1:
                raise ValueError("数据包含多个交易日期，请分别导入")

            # 使用文件中的日期而不是用户指定的日期
            file_trading_date = trading_dates[0]

            # 如果用户指定的日期与文件中的日期不一致，使用文件中的日期
            if trading_date != file_trading_date:
                logger.warning(f"用户指定日期 {trading_date} 与文件数据日期 {file_trading_date} 不一致，使用文件数据日期")
                trading_date = file_trading_date

            # 4. 导入交易数据
            import_result = self.import_daily_trading_data(trading_data, trading_date, import_record_id, mode)

            # 5. 执行计算
            calculation_result = self.perform_calculations(trading_date, import_record_id)

            # 6. 计算耗时
            end_time = datetime.utcnow()
            calculation_time = (end_time - start_time).total_seconds()

            # 创建解析信息
            parse_info = {
                'filename': filename,
                'total_lines': len(file_content.strip().split('\n')),
                'parsed_rows': len(trading_data),
                'trading_date': trading_date.isoformat()
            }

            # 7. 更新导入记录为成功
            ImportStatus = self.ImportRecord.ImportStatus
            self.update_import_record(import_record_id, {
                'import_status': ImportStatus.SUCCESS,
                'total_records': len(trading_data),
                'success_records': import_result['success_records'],
                'error_records': import_result['error_records'],
                'duplicate_records': import_result['duplicate_records'],
                'concept_count': calculation_result['concept_count'],
                'ranking_count': calculation_result['ranking_count'],
                'new_high_count': calculation_result['new_high_count'],
                'import_completed_at': end_time,
                'calculation_time': calculation_time
            })

            # 8. 提交事务
            self.db.commit()

            # 9. 返回结果
            return {
                'success': True,
                'message': f'{self.file_type.upper()}文件导入成功',
                'file_type': self.file_type,
                'import_record_id': import_record_id,
                'filename': filename,
                'trading_date': trading_date.isoformat(),
                'file_size': file_size,
                'file_hash': file_hash,
                'parse_info': parse_info,
                'import_result': import_result,
                'calculation_result': calculation_result,
                'calculation_time': round(calculation_time, 3),
                'imported_by': imported_by
            }

        except Exception as e:
            # 回滚事务
            self.db.rollback()

            # 更新导入记录为失败
            if import_record_id:
                try:
                    ImportStatus = self.ImportRecord.ImportStatus
                    self.update_import_record(import_record_id, {
                        'import_status': ImportStatus.FAILED,
                        'error_message': str(e),
                        'import_completed_at': datetime.utcnow()
                    })
                    self.db.commit()
                except Exception as update_error:
                    logger.error(f"更新失败记录时出错: {update_error}")

            logger.error(f"{self.file_type.upper()}文件导入失败: {e}")
            return {
                'success': False,
                'message': f'{self.file_type.upper()}文件导入失败: {str(e)}',
                'file_type': self.file_type,
                'import_record_id': import_record_id,
                'error': str(e)
            }

    def get_import_records(self, limit: int = 50, offset: int = 0) -> Dict:
        """获取导入记录列表"""
        try:
            query = self.db.query(self.ImportRecord).order_by(
                self.ImportRecord.import_started_at.desc()
            )

            total = query.count()
            records = query.offset(offset).limit(limit).all()

            return {
                'success': True,
                'file_type': self.file_type,
                'total': total,
                'records': [
                    {
                        'id': record.id,
                        'filename': record.filename,
                        'trading_date': record.trading_date.isoformat(),
                        'file_size': record.file_size,
                        'import_status': record.import_status.value,
                        'imported_by': record.imported_by,
                        'total_records': record.total_records,
                        'success_records': record.success_records,
                        'error_records': record.error_records,
                        'import_started_at': record.import_started_at.isoformat(),
                        'import_completed_at': record.import_completed_at.isoformat() if record.import_completed_at else None,
                        'calculation_time': float(record.calculation_time) if record.calculation_time else 0,
                        'error_message': record.error_message
                    }
                    for record in records
                ]
            }

        except Exception as e:
            logger.error(f"获取导入记录失败: {e}")
            return {
                'success': False,
                'message': f'获取导入记录失败: {str(e)}',
                'file_type': self.file_type
            }