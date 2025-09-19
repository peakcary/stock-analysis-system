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

    def parse_file_content(self, file_content: str, filename: str) -> Tuple[pd.DataFrame, Dict]:
        """
        解析文件内容

        Args:
            file_content: 文件内容字符串
            filename: 文件名

        Returns:
            (DataFrame, 解析信息字典)
        """
        try:
            # 基于原TXT解析逻辑，使用配置中的列名
            lines = file_content.strip().split('\n')

            if len(lines) < 2:
                raise ValueError("文件内容不足，至少需要标题行和一行数据")

            # 解析标题行
            header = lines[0].strip()
            headers = [col.strip() for col in header.split('\t')]

            # 验证必需列是否存在
            for required_col in self.config.required_columns:
                if required_col not in headers:
                    raise ValueError(f"缺少必需列: {required_col}")

            # 解析数据行
            data_rows = []
            for i, line in enumerate(lines[1:], start=2):
                if line.strip():
                    values = [val.strip() for val in line.split('\t')]
                    if len(values) != len(headers):
                        logger.warning(f"第{i}行列数不匹配，跳过: {line[:50]}...")
                        continue
                    data_rows.append(values)

            # 创建DataFrame
            df = pd.DataFrame(data_rows, columns=headers)

            # 数据清理和标准化
            df = self._clean_and_standardize_data(df)

            parse_info = {
                'filename': filename,
                'total_lines': len(lines),
                'header_line': header,
                'data_rows': len(data_rows),
                'columns': headers,
                'parsed_rows': len(df)
            }

            logger.info(f"成功解析 {filename}: {len(df)} 条记录")
            return df, parse_info

        except Exception as e:
            logger.error(f"解析文件内容失败: {e}")
            raise

    def _clean_and_standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理和标准化数据
        基于原TXT导入服务的数据处理逻辑
        """
        try:
            # 获取配置中的列名映射
            stock_code_col = self.config.stock_code_column
            volume_col = self.config.volume_column

            # 复制数据以避免修改原始数据
            df = df.copy()

            # 标准化股票代码
            if stock_code_col in df.columns:
                df['original_stock_code'] = df[stock_code_col].astype(str)
                df['normalized_stock_code'] = df[stock_code_col].apply(self._normalize_stock_code)
                df['stock_code'] = df['normalized_stock_code']

            # 处理交易量数据
            if volume_col in df.columns:
                df['trading_volume'] = pd.to_numeric(df[volume_col], errors='coerce').fillna(0).astype(int)

            # 移除无效行
            initial_count = len(df)
            df = df.dropna(subset=['stock_code', 'trading_volume'])
            df = df[df['stock_code'].str.len() > 0]
            df = df[df['trading_volume'] > 0]

            final_count = len(df)
            if final_count < initial_count:
                logger.info(f"数据清理: 移除 {initial_count - final_count} 条无效记录")

            return df

        except Exception as e:
            logger.error(f"数据清理失败: {e}")
            raise

    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码
        基于原TXT导入服务的标准化逻辑
        """
        if pd.isna(code) or not isinstance(code, str):
            return ""

        # 移除空格和特殊字符
        code = str(code).strip()
        code = re.sub(r'[^\w.]', '', code)

        # 处理不同格式的股票代码
        if '.' in code:
            # 处理如 "000001.SZ" 格式
            base_code = code.split('.')[0]
            if len(base_code) == 6 and base_code.isdigit():
                return base_code

        # 如果是6位纯数字，直接返回
        if len(code) == 6 and code.isdigit():
            return code

        # 尝试提取6位数字
        digits = re.findall(r'\d+', code)
        if digits:
            main_code = digits[0]
            if len(main_code) == 6:
                return main_code

        return code

    def calculate_file_hash(self, file_content: str) -> str:
        """计算文件内容的MD5哈希值"""
        return hashlib.md5(file_content.encode('utf-8')).hexdigest()

    def import_daily_trading_data(self, df: pd.DataFrame, trading_date: date,
                                import_record_id: int, mode: str = "overwrite") -> Dict:
        """
        导入每日交易数据

        Args:
            df: 处理后的数据DataFrame
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

            # 如果是覆盖模式，先删除当日数据
            if mode == "overwrite":
                deleted_count = self.db.query(self.DailyTrading).filter(
                    self.DailyTrading.trading_date == trading_date
                ).delete()
                if deleted_count > 0:
                    logger.info(f"覆盖模式: 删除了 {deleted_count} 条旧数据")

            # 批量插入数据
            batch_size = self.config.batch_size
            total_rows = len(df)

            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i + batch_size]
                batch_records = []

                for _, row in batch_df.iterrows():
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

                        # 创建记录对象
                        record = self.DailyTrading(
                            original_stock_code=row['original_stock_code'],
                            normalized_stock_code=row['normalized_stock_code'],
                            stock_code=row['stock_code'],
                            trading_date=trading_date,
                            trading_volume=int(row['trading_volume']),
                            created_at=datetime.utcnow()
                        )

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

            # 2. 创建导入记录
            import_record_id = self.create_import_record(
                filename, file_size, file_hash, trading_date, imported_by, mode
            )

            # 3. 解析文件内容
            df, parse_info = self.parse_file_content(file_content, filename)

            # 4. 导入交易数据
            import_result = self.import_daily_trading_data(df, trading_date, import_record_id, mode)

            # 5. 执行计算
            calculation_result = self.perform_calculations(trading_date, import_record_id)

            # 6. 计算耗时
            end_time = datetime.utcnow()
            calculation_time = (end_time - start_time).total_seconds()

            # 7. 更新导入记录为成功
            ImportStatus = self.ImportRecord.ImportStatus
            self.update_import_record(import_record_id, {
                'import_status': ImportStatus.SUCCESS,
                'total_records': parse_info['parsed_rows'],
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