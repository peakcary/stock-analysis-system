"""
统一时间序列数据导入框架
支持 EEE.txt、TTV.txt 和未来扩展的其他时间序列数据源

设计原则：
1. 原始数据保留：完整保存导入的原始数据用于审计和重新计算
2. 规范化存储：处理后的数据统一存储到指定的表中
3. 处理器模式：基于处理器架构，支持灵活扩展新的数据源
4. 计算支持：保持原始数据，支持重新计算和数据更正
"""

from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.models import Stock, StockDailyMetrics
from app.models.stock import RawImportData, ImportBatch

logger = logging.getLogger(__name__)


class TimeSeriesImportHandler(ABC):
    """时间序列导入处理器基类"""

    def __init__(self, db: Session):
        """
        初始化处理器

        Args:
            db: 数据库会话
        """
        self.db = db

    @property
    @abstractmethod
    def metric_type(self) -> str:
        """
        返回指标类型标识符
        如: 'eee_heat', 'ttv_trading_volume' 等
        """
        pass

    @abstractmethod
    def parse_file(self, content: bytes, filename: str) -> Tuple[List[Dict], List[str]]:
        """
        解析文件内容

        Args:
            content: 文件内容（字节）
            filename: 文件名

        Returns:
            (解析成功的记录列表, 解析错误列表)
            每条记录格式: {
                'stock_code_raw': str,      # 原始代码如 'SH600000'
                'stock_code': str,          # 规范化代码如 '600000'
                'trade_date': date,         # 交易日期
                'value': float              # 指标值
            }
        """
        pass

    @abstractmethod
    def validate_record(self, record: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证单条记录的有效性

        Returns:
            (是否有效, 错误信息)
        """
        pass

    def normalize_stock_code(self, code_with_prefix: str) -> Tuple[str, Optional[str]]:
        """
        规范化股票代码：去掉前缀

        Args:
            code_with_prefix: 原始代码如 'SH600000' 或 '600000'

        Returns:
            (规范化代码, 前缀) 如 ('600000', 'SH') 或 ('600000', None)
        """
        code_with_prefix = code_with_prefix.strip().upper()

        # 识别前缀
        for prefix in ['SH', 'SZ', 'BJ', 'HK']:
            if code_with_prefix.startswith(prefix):
                normalized = code_with_prefix[len(prefix):]
                return normalized, prefix

        return code_with_prefix, None

    def save_raw_data(
        self,
        records: List[Dict],
        filename: str,
        import_date: date
    ) -> int:
        """
        保存原始导入数据

        Args:
            records: 解析后的记录列表
            filename: 源文件名
            import_date: 导入日期

        Returns:
            创建的批次ID
        """
        # 创建导入批次记录
        import_batch = ImportBatch(
            import_date=import_date,
            import_type='txt',
            file_name=filename,
            record_count=len(records),
            status='pending'
        )
        self.db.add(import_batch)
        self.db.flush()

        # 保存原始数据
        raw_import_records = []
        for idx, record in enumerate(records, 1):
            normalized_code, prefix = self.normalize_stock_code(record['stock_code_raw'])

            raw_record = RawImportData(
                import_batch_id=import_batch.id,
                row_number=idx,
                trade_date=record['trade_date'],
                stock_code_raw=record['stock_code_raw'],
                stock_code_normalized=normalized_code,
                stock_code_prefix=prefix,
                stock_name='',  # 稍后会更新
                industry=None,
                price=0,
                turnover_rate=0,
                net_inflow=0,
                pages_count=0,
                total_reads=0,
                heat_value=record.get('value', 0) if self.metric_type == 'eee_heat' else None,
                source_type='txt',
                source_file=filename
            )
            raw_import_records.append(raw_record)

        if raw_import_records:
            self.db.bulk_save_objects(raw_import_records)
            self.db.flush()

        logger.info(f"保存原始导入数据: {len(raw_import_records)} 条记录")
        return import_batch.id

    def save_normalized_data(self, records: List[Dict], target_date: date) -> Dict[str, int]:
        """
        保存规范化数据到业务表

        要在子类中实现具体的保存逻辑

        Returns:
            统计信息: {
                'imported': 新增/更新的记录数,
                'skipped': 跳过的记录数 (如股票不存在),
                'errors': 错误记录数
            }
        """
        stats = {
            'imported': 0,
            'skipped': 0,
            'errors': 0
        }
        return stats


class EeeImportHandler(TimeSeriesImportHandler):
    """EEE热度数据导入处理器"""

    @property
    def metric_type(self) -> str:
        return 'eee_heat'

    def parse_file(self, content: bytes, filename: str) -> Tuple[List[Dict], List[str]]:
        """解析EEE.txt文件"""
        records = []
        errors = []

        text_content = content.decode('utf-8')
        lines = text_content.strip().split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t') if '\t' in line else line.split()
            if len(parts) < 3:
                errors.append(f"第{line_num}行: 数据格式不正确 (需要3列)")
                continue

            try:
                stock_code_raw = parts[0].strip()
                date_str = parts[1].strip()
                value_str = parts[2].strip()

                # 解析日期
                try:
                    trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"第{line_num}行: 日期格式无效 {date_str}")
                    continue

                # 解析热度值
                try:
                    heat_value = float(value_str)
                except ValueError:
                    errors.append(f"第{line_num}行: 热度值无效 {value_str}")
                    continue

                records.append({
                    'stock_code_raw': stock_code_raw,
                    'stock_code': None,  # 稍后设置
                    'trade_date': trade_date,
                    'value': heat_value
                })

            except Exception as e:
                errors.append(f"第{line_num}行: 处理错误 {str(e)}")

        return records, errors

    def validate_record(self, record: Dict) -> Tuple[bool, Optional[str]]:
        """验证记录有效性"""
        # 验证股票代码
        normalized_code, _ = self.normalize_stock_code(record['stock_code_raw'])
        if not normalized_code or not normalized_code.isdigit() or len(normalized_code) != 6:
            return False, f"股票代码格式无效: {record['stock_code_raw']}"

        # 验证日期
        if not isinstance(record['trade_date'], date):
            return False, "交易日期格式无效"

        # 验证热度值
        if not isinstance(record['value'], (int, float)) or record['value'] < 0:
            return False, "热度值无效"

        return True, None

    def save_normalized_data(self, records: List[Dict], target_date: date) -> Dict[str, int]:
        """保存规范化的热度数据"""
        stats = {'imported': 0, 'skipped': 0, 'errors': 0}

        for record in records:
            try:
                # 验证记录
                is_valid, error_msg = self.validate_record(record)
                if not is_valid:
                    stats['errors'] += 1
                    logger.warning(f"记录验证失败: {error_msg}")
                    continue

                normalized_code, _ = self.normalize_stock_code(record['stock_code_raw'])

                # 检查股票是否存在
                stock = self.db.query(Stock).filter(
                    Stock.stock_code == normalized_code
                ).first()

                if not stock:
                    stats['skipped'] += 1
                    logger.debug(f"股票不存在: {normalized_code}")
                    continue

                # 保存到统一的 StockDailyMetrics 表
                metric = StockDailyMetrics(
                    stock_id=stock.id,
                    trade_date=target_date,
                    metric_type=self.metric_type,  # 'eee_heat'
                    metric_value=record['value'],
                    data_source='eee',
                    is_recalculated=False
                )
                self.db.add(metric)
                stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"保存记录失败: {str(e)}")

        return stats


class TtvImportHandler(TimeSeriesImportHandler):
    """TTV交易数据导入处理器"""

    @property
    def metric_type(self) -> str:
        return 'ttv_trading_volume'

    def parse_file(self, content: bytes, filename: str) -> Tuple[List[Dict], List[str]]:
        """解析TTV.txt文件 - 格式与EEE相同"""
        # TTV.txt 的格式与 EEE.txt 相同，只是数据含义不同
        records = []
        errors = []

        text_content = content.decode('utf-8')
        lines = text_content.strip().split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t') if '\t' in line else line.split()
            if len(parts) < 3:
                errors.append(f"第{line_num}行: 数据格式不正确 (需要3列)")
                continue

            try:
                stock_code_raw = parts[0].strip()
                date_str = parts[1].strip()
                value_str = parts[2].strip()

                # 解析日期
                try:
                    trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"第{line_num}行: 日期格式无效 {date_str}")
                    continue

                # 解析交易量
                try:
                    trading_volume = float(value_str)
                except ValueError:
                    errors.append(f"第{line_num}行: 交易量值无效 {value_str}")
                    continue

                records.append({
                    'stock_code_raw': stock_code_raw,
                    'stock_code': None,
                    'trade_date': trade_date,
                    'value': trading_volume
                })

            except Exception as e:
                errors.append(f"第{line_num}行: 处理错误 {str(e)}")

        return records, errors

    def validate_record(self, record: Dict) -> Tuple[bool, Optional[str]]:
        """验证记录有效性"""
        # 验证股票代码
        normalized_code, _ = self.normalize_stock_code(record['stock_code_raw'])
        if not normalized_code or not normalized_code.isdigit() or len(normalized_code) != 6:
            return False, f"股票代码格式无效: {record['stock_code_raw']}"

        # 验证日期
        if not isinstance(record['trade_date'], date):
            return False, "交易日期格式无效"

        # 验证交易量
        if not isinstance(record['value'], (int, float)) or record['value'] < 0:
            return False, "交易量值无效"

        return True, None

    def save_normalized_data(self, records: List[Dict], target_date: date) -> Dict[str, int]:
        """保存规范化的交易数据"""
        stats = {'imported': 0, 'skipped': 0, 'errors': 0}

        for record in records:
            try:
                # 验证记录
                is_valid, error_msg = self.validate_record(record)
                if not is_valid:
                    stats['errors'] += 1
                    logger.warning(f"记录验证失败: {error_msg}")
                    continue

                normalized_code, _ = self.normalize_stock_code(record['stock_code_raw'])

                # 检查股票是否存在
                stock = self.db.query(Stock).filter(
                    Stock.stock_code == normalized_code
                ).first()

                if not stock:
                    stats['skipped'] += 1
                    logger.debug(f"股票不存在: {normalized_code}")
                    continue

                # 保存到统一的 StockDailyMetrics 表
                metric = StockDailyMetrics(
                    stock_id=stock.id,
                    trade_date=target_date,
                    metric_type=self.metric_type,  # 'ttv_trading_volume'
                    metric_value=record['value'],
                    data_source='ttv',
                    is_recalculated=False
                )
                self.db.add(metric)
                stats['imported'] += 1

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"保存记录失败: {str(e)}")

        return stats


class TimeSeriesImportService:
    """统一时间序列导入服务"""

    def __init__(self, db: Session):
        """
        初始化服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self._handlers: Dict[str, TimeSeriesImportHandler] = {
            'eee': EeeImportHandler(db),
            'ttv': TtvImportHandler(db)
        }

    def register_handler(self, name: str, handler: TimeSeriesImportHandler):
        """
        注册新的导入处理器

        Args:
            name: 处理器名称 (如 'eee', 'ttv')
            handler: 处理器实例
        """
        self._handlers[name] = handler
        logger.info(f"注册导入处理器: {name}")

    def import_timeseries_data(
        self,
        handler_name: str,
        content: bytes,
        filename: str,
        allow_overwrite: bool = False,
        trade_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        导入时间序列数据

        Args:
            handler_name: 处理器名称 ('eee' 或 'ttv')
            content: 文件内容（字节）
            filename: 文件名
            allow_overwrite: 是否允许覆盖已有数据
            trade_date: 交易日期（可选，从文件内容推断）

        Returns:
            导入结果字典
        """
        if handler_name not in self._handlers:
            raise ValueError(f"未注册的处理器: {handler_name}")

        handler = self._handlers[handler_name]
        logger.info(f"开始导入数据: {handler_name} - {filename}")

        try:
            # 1. 解析文件
            records, parse_errors = handler.parse_file(content, filename)
            logger.info(f"解析完成: {len(records)} 条有效记录, {len(parse_errors)} 个错误")

            if not records:
                return {
                    'success': False,
                    'message': '文件中没有有效的数据记录',
                    'errors': parse_errors
                }

            # 2. 推断交易日期
            if trade_date is None:
                dates_in_records = set(r['trade_date'] for r in records)
                if len(dates_in_records) == 1:
                    trade_date = list(dates_in_records)[0]
                elif len(dates_in_records) > 1:
                    # 使用最常见的日期
                    from collections import Counter
                    date_counter = Counter(dates_in_records)
                    trade_date = date_counter.most_common(1)[0][0]
                else:
                    trade_date = date.today()

            logger.info(f"目标交易日期: {trade_date}")

            # 3. 保存原始数据
            batch_id = handler.save_raw_data(records, filename, trade_date)

            # 4. 保存规范化数据
            stats = handler.save_normalized_data(records, trade_date)

            # 5. 提交事务
            self.db.commit()

            return {
                'success': True,
                'message': f'成功导入 {stats["imported"]} 条记录',
                'batch_id': batch_id,
                'trade_date': trade_date.isoformat(),
                'stats': stats,
                'parse_errors': parse_errors[:10] if parse_errors else []
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"导入失败: {str(e)}")
            return {
                'success': False,
                'message': f'导入失败: {str(e)}',
                'errors': [str(e)]
            }
