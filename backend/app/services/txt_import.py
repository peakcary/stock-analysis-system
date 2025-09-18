from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.daily_trading import (
    DailyTrading, ConceptDailySummary,
    StockConceptRanking, ConceptHighRecord, TxtImportRecord
)
from app.models.stock import Stock
from app.models.concept import Concept, StockConcept
from app.services.txt_processors.processor_factory import get_processor_factory
from datetime import datetime, date, timedelta
import logging
import csv
import io
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class TxtImportService:
    """TXT文件导入和数据汇总服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _normalize_stock_code(self, original_code: str) -> dict:
        """
        解析股票代码，提取原始代码和标准化代码
        
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
    
    def parse_txt_content_with_processor(self, txt_content: str, filename: str = None,
                                       processor_type: str = "auto") -> List[Dict]:
        """使用处理器工厂解析TXT文件内容

        Args:
            txt_content: TXT文件内容
            filename: 文件名
            processor_type: 处理器类型

        Returns:
            解析后的交易数据列表
        """
        try:
            # 获取处理器工厂
            factory = get_processor_factory()

            # 选择处理器
            if processor_type == "auto":
                processor = factory.get_best_processor(txt_content, filename)
                if not processor:
                    logger.error("未找到合适的处理器")
                    return []
            else:
                processor = factory.get_processor_by_type(processor_type)
                if not processor:
                    logger.error(f"找不到指定的处理器类型: {processor_type}")
                    return []

            # 使用处理器解析内容
            result = processor.parse_content(txt_content)

            if not result.success:
                logger.error(f"处理器解析失败: {result.message}")
                return []

            # 转换为原始格式以保持兼容性
            trading_data = []
            for record in result.records:
                trading_data.append({
                    'original_stock_code': record.original_stock_code,
                    'normalized_stock_code': record.normalized_stock_code,
                    'stock_code': record.stock_code,
                    'trading_date': record.trading_date,
                    'trading_volume': record.trading_volume,
                    'market_prefix': record.extra_fields.get('market_prefix', ''),
                    'extra_fields': record.extra_fields
                })

            logger.info(f"使用处理器 {processor.processor_type} 成功解析{len(trading_data)}条交易数据")
            return trading_data

        except Exception as e:
            logger.error(f"使用处理器解析内容时出错: {e}")
            # 回退到原始解析方法
            return self.parse_txt_content(txt_content)

    def parse_txt_content(self, txt_content: str) -> List[Dict]:
        """解析TXT文件内容（原始方法，用作回退）

        Args:
            txt_content: TXT文件内容

        Returns:
            解析后的交易数据列表
        """
        trading_data = []
        lines = txt_content.strip().split('\n')

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
                
                # 解析股票代码
                stock_info = self._normalize_stock_code(stock_code)
                
                trading_data.append({
                    'original_stock_code': stock_info['original'],    # 原始代码
                    'normalized_stock_code': stock_info['normalized'], # 标准化代码
                    'stock_code': stock_info['normalized'],           # 股票代码 (保持兼容性)
                    'trading_date': trading_date,
                    'trading_volume': trading_volume,
                    'market_prefix': stock_info['prefix']             # SH (可用于统计分析)
                })
                
            except Exception as e:
                logger.error(f"解析第{line_num}行时出错: {line}, 错误: {e}")
                continue
        
        logger.info(f"成功解析{len(trading_data)}条交易数据")
        return trading_data

    def _import_historical_data(self, trading_data: List[Dict], filename: str,
                              file_size: int, imported_by: str) -> Dict:
        """导入历史多日期数据

        Args:
            trading_data: 解析后的交易数据
            filename: 文件名
            file_size: 文件大小
            imported_by: 导入人

        Returns:
            导入结果
        """
        start_time = time.time()
        total_imported = 0
        total_errors = 0
        imported_dates = []

        try:
            # 按日期分组数据
            data_by_date = defaultdict(list)
            for item in trading_data:
                data_by_date[item['trading_date']].append(item)

            logger.info(f"开始导入历史数据，共 {len(data_by_date)} 个交易日期")

            # 逐日期导入
            for trading_date, daily_data in sorted(data_by_date.items()):
                try:
                    logger.info(f"正在导入 {trading_date} 的数据，共 {len(daily_data)} 条记录")

                    # 检查该日期是否已有数据
                    existing_records = self.db.query(TxtImportRecord).filter(
                        TxtImportRecord.trading_date == trading_date
                    ).count()

                    if existing_records > 0:
                        logger.info(f"检测到{trading_date}已有导入记录，将进行覆盖导入")
                        self.db.query(TxtImportRecord).filter(
                            TxtImportRecord.trading_date == trading_date
                        ).delete()
                        self.db.commit()

                    # 创建导入记录
                    import_record = TxtImportRecord(
                        filename=f"{filename} ({trading_date})",
                        trading_date=trading_date,
                        file_size=file_size // len(data_by_date),  # 按日期分摊文件大小
                        import_status="processing",
                        imported_by=imported_by,
                        total_records=len(daily_data),
                        import_started_at=datetime.utcnow()
                    )
                    self.db.add(import_record)
                    self.db.commit()

                    # 清理当天数据
                    self.clear_daily_data(trading_date)

                    # 导入交易数据
                    imported_count = self.insert_daily_trading(daily_data)

                    # 计算汇总数据
                    calculation_results = self.perform_calculations(trading_date)

                    # 更新导入记录
                    import_record.import_status = "success"
                    import_record.success_records = imported_count
                    import_record.error_records = len(daily_data) - imported_count
                    import_record.import_completed_at = datetime.utcnow()
                    import_record.concept_summary_count = calculation_results['concept_summary_count']
                    import_record.ranking_count = calculation_results['ranking_count']
                    import_record.new_high_count = calculation_results['new_high_count']
                    self.db.commit()

                    total_imported += imported_count
                    imported_dates.append(trading_date)
                    logger.info(f"完成导入 {trading_date}，成功 {imported_count} 条")

                except Exception as e:
                    logger.error(f"导入 {trading_date} 数据时出错: {e}")
                    total_errors += len(daily_data)
                    if import_record:
                        import_record.import_status = "failed"
                        import_record.error_message = str(e)
                        self.db.commit()

            end_time = time.time()
            duration = end_time - start_time

            return {
                "success": True,
                "message": f"历史数据导入完成",
                "trading_dates": [d.strftime('%Y-%m-%d') for d in sorted(imported_dates)],
                "imported_records": total_imported,
                "error_records": total_errors,
                "total_dates": len(imported_dates),
                "duration": f"{duration:.2f}秒",
                "filename": filename
            }

        except Exception as e:
            logger.error(f"历史数据导入失败: {e}")
            return {"success": False, "message": f"历史数据导入失败: {str(e)}"}
    
    def import_daily_trading(self, txt_content: str, filename: str = "unknown.txt",
                           file_size: int = 0, imported_by: str = "system",
                           processor_type: str = "auto") -> Dict:
        """导入TXT交易数据并进行汇总计算
        
        Args:
            txt_content: TXT文件内容
            filename: 文件名
            file_size: 文件大小
            imported_by: 导入人
            
        Returns:
            导入结果统计
        """
        import_record = None
        start_time = time.time()
        
        try:
            # 使用新的处理器工厂解析数据
            trading_data = self.parse_txt_content_with_processor(
                txt_content, filename, processor_type
            )
            if not trading_data:
                return {"success": False, "message": "未解析到有效数据"}
            
            # 获取交易日期
            trading_dates = list(set(item['trading_date'] for item in trading_data))

            # 检查是否为历史多日期文件
            if len(trading_dates) > 1:
                if processor_type in ["historical", "auto"]:
                    # 历史文件支持多日期导入
                    logger.info(f"检测到历史多日期文件，包含 {len(trading_dates)} 个交易日期")
                    return self._import_historical_data(trading_data, filename, file_size, imported_by)
                else:
                    return {"success": False, "message": f"数据包含多个交易日期({len(trading_dates)}个)，请使用历史数据导入模式"}
            
            current_date = trading_dates[0]
            
            # 检查是否已有该日期的数据，如果有则先清理
            existing_records = self.db.query(TxtImportRecord).filter(
                TxtImportRecord.trading_date == current_date
            ).count()
            
            if existing_records > 0:
                logger.info(f"检测到{current_date}已有导入记录，将进行覆盖导入")
                # 删除该日期的所有导入记录
                self.db.query(TxtImportRecord).filter(
                    TxtImportRecord.trading_date == current_date
                ).delete()
                self.db.commit()
            
            # 创建新的导入记录
            import_record = TxtImportRecord(
                filename=filename,
                trading_date=current_date,
                file_size=file_size,
                import_status="processing",
                imported_by=imported_by,
                total_records=len(trading_data),
                import_started_at=datetime.utcnow()
            )
            self.db.add(import_record)
            self.db.commit()
            
            # 清理当天已有的其他数据表
            self.clear_daily_data(current_date)
            
            # 导入原始交易数据
            imported_count = self.insert_daily_trading(trading_data)
            
            # 使用统一的计算方法
            calculation_results = self.perform_calculations(current_date)
            concept_summary_count = calculation_results['concept_summary_count']
            ranking_count = calculation_results['ranking_count']
            high_record_count = calculation_results['new_high_count']
            
            # 更新导入记录
            end_time = time.time()
            if import_record:
                import_record.import_status = "success"
                import_record.success_records = imported_count
                import_record.error_records = len(trading_data) - imported_count
                import_record.concept_count = concept_summary_count
                import_record.ranking_count = ranking_count
                import_record.new_high_count = high_record_count
                import_record.import_completed_at = datetime.utcnow()
                import_record.calculation_time = round(end_time - start_time, 2)
                self.db.commit()
            
            return {
                "success": True,
                "message": "数据导入和计算完成",
                "import_record_id": import_record.id if import_record else None,
                "stats": {
                    "trading_data_count": imported_count,
                    "concept_summary_count": concept_summary_count,
                    "ranking_count": ranking_count,
                    "new_high_count": high_record_count,
                    "trading_date": current_date.strftime('%Y-%m-%d'),
                    "calculation_time": round(end_time - start_time, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"导入TXT数据时出错: {e}")
            
            # 更新导入记录为失败状态
            if import_record:
                try:
                    import_record.import_status = "failed"
                    import_record.error_message = str(e)
                    import_record.import_completed_at = datetime.utcnow()
                    import_record.calculation_time = round(time.time() - start_time, 2)
                    self.db.commit()
                except:
                    pass
            
            self.db.rollback()
            return {
                "success": False, 
                "message": f"导入失败: {str(e)}",
                "import_record_id": import_record.id if import_record else None
            }
    
    def clear_daily_data(self, trading_date: date, keep_trading_data: bool = False):
        """清理指定日期的数据"""
        # 清理汇总数据
        self.db.query(ConceptDailySummary).filter(
            ConceptDailySummary.trading_date == trading_date
        ).delete()
        
        self.db.query(StockConceptRanking).filter(
            StockConceptRanking.trading_date == trading_date
        ).delete()
        
        self.db.query(ConceptHighRecord).filter(
            ConceptHighRecord.trading_date == trading_date
        ).delete()
        
        # 根据参数决定是否清理基础交易数据
        if not keep_trading_data:
            self.db.query(DailyTrading).filter(
                DailyTrading.trading_date == trading_date
            ).delete()
        
        self.db.commit()
        logger.info(f"已清理{trading_date}的{'汇总' if keep_trading_data else '所有'}数据")
    
    def insert_daily_trading(self, trading_data: List[Dict]) -> int:
        """插入每日交易数据 - 支持原始代码和标准化代码"""
        count = 0
        for item in trading_data:
            trading_record = DailyTrading(
                original_stock_code=item['original_stock_code'],
                normalized_stock_code=item['normalized_stock_code'],
                stock_code=item['stock_code'],
                trading_date=item['trading_date'],
                trading_volume=item['trading_volume']
            )
            self.db.add(trading_record)
            count += 1

        self.db.commit()
        logger.info(f"插入{count}条交易数据（原始代码 + 标准化代码）")
        return count
    
    def _get_stock_trading_records(self, stock_codes: List[str], trading_date: date) -> List[DailyTrading]:
        """
        统一的股票代码匹配逻辑，支持多种股票代码格式
        确保概念汇总和排名数据使用相同的匹配标准
        """
        from sqlalchemy import or_
        
        if not stock_codes:
            return []
        
        # 生成各种可能的股票代码格式进行匹配
        all_possible_codes = []
        
        for stock_code in stock_codes:
            # 原始代码
            all_possible_codes.append(stock_code)
            
            # 如果是6位数字代码，生成带前缀的版本
            if stock_code.isdigit() and len(stock_code) == 6:
                if stock_code.startswith('6'):
                    all_possible_codes.append(f'SH{stock_code}')
                elif stock_code.startswith('0') or stock_code.startswith('3'):
                    all_possible_codes.append(f'SZ{stock_code}')
            
            # 如果有SH/SZ前缀，生成无前缀版本
            elif stock_code.startswith(('SH', 'SZ')) and len(stock_code) == 8:
                all_possible_codes.append(stock_code[2:])
            
            # 如果是类似 "1" 这样的错误格式，尝试通过股票名称反向查找正确代码
            elif stock_code.isdigit() and len(stock_code) < 6:
                logger.warning(f"发现异常股票代码格式: {stock_code}")
        
        # 去重
        all_possible_codes = list(set(all_possible_codes))
        
        logger.debug(f"股票代码匹配 - 原始代码: {stock_codes[:5]}{'...' if len(stock_codes) > 5 else ''}")
        logger.debug(f"生成的匹配代码: {all_possible_codes[:10]}{'...' if len(all_possible_codes) > 10 else ''}")
        
        # 查询匹配的交易记录
        trading_records = self.db.query(DailyTrading).filter(
            DailyTrading.trading_date == trading_date,
            DailyTrading.stock_code.in_(all_possible_codes)
        ).all()
        
        logger.debug(f"找到匹配的交易记录: {len(trading_records)} 条 (预期: {len(stock_codes)} 条)")
        
        return trading_records
    
    def calculate_concept_summary(self, trading_date: date) -> int:
        """计算概念每日汇总数据"""
        # 获取所有概念及其包含的股票
        concepts = self.db.query(Concept).all()
        concept_summaries = []
        
        for concept in concepts:
            # 获取概念包含的股票代码 - 需要通过Stock表关联获取
            stock_concepts = self.db.query(StockConcept).filter(
                StockConcept.concept_id == concept.id
            ).all()
            
            # 获取stock_id列表，然后查询对应的stock_code
            stock_ids = [sc.stock_id for sc in stock_concepts]
            if not stock_ids:
                continue
            
            # 通过stock_id获取stock_code
            from app.models.stock import Stock
            stocks = self.db.query(Stock).filter(Stock.id.in_(stock_ids)).all()
            stock_codes = [stock.stock_code for stock in stocks]
            
            if not stock_codes:
                continue
            
            # 获取这些股票在交易日的数据，使用统一的匹配逻辑
            trading_records = self._get_stock_trading_records(stock_codes, trading_date)
            
            # 记录匹配信息以便调试
            if len(trading_records) != len(stock_codes):
                logger.warning(f"概念{concept.concept_name}: 定义了{len(stock_codes)}只股票，但只匹配到{len(trading_records)}只股票的交易数据")
            
            if not trading_records:
                continue
            
            # 计算汇总数据
            volumes = [record.trading_volume for record in trading_records]
            total_volume = sum(volumes)
            stock_count = len(volumes)
            average_volume = total_volume / stock_count if stock_count > 0 else 0
            max_volume = max(volumes) if volumes else 0
            
            summary = ConceptDailySummary(
                concept_name=concept.concept_name,
                trading_date=trading_date,
                total_volume=total_volume,
                stock_count=stock_count,
                average_volume=average_volume,
                max_volume=max_volume
            )
            concept_summaries.append(summary)
        
        # 批量插入
        self.db.add_all(concept_summaries)
        self.db.commit()
        
        logger.info(f"计算{len(concept_summaries)}个概念的汇总数据")
        return len(concept_summaries)
    
    def calculate_stock_concept_ranking(self, trading_date: date) -> int:
        """计算股票在概念中的排名"""
        rankings = []
        
        # 获取所有概念的汇总数据
        concept_summaries = self.db.query(ConceptDailySummary).filter(
            ConceptDailySummary.trading_date == trading_date
        ).all()
        
        for summary in concept_summaries:
            concept_name = summary.concept_name
            concept_total_volume = summary.total_volume
            
            # 获取概念对应的股票交易数据
            concept = self.db.query(Concept).filter(
                Concept.concept_name == concept_name
            ).first()
            
            if not concept:
                continue
            
            stock_concepts = self.db.query(StockConcept).filter(
                StockConcept.concept_id == concept.id
            ).all()
            
            # 获取stock_id列表，然后查询对应的stock_code
            stock_ids = [sc.stock_id for sc in stock_concepts]
            if not stock_ids:
                continue
            
            # 通过stock_id获取stock_code
            from app.models.stock import Stock
            stocks = self.db.query(Stock).filter(Stock.id.in_(stock_ids)).all()
            stock_codes = [stock.stock_code for stock in stocks]
            
            # 获取股票交易数据并按交易量排序，使用统一的匹配逻辑
            trading_records = self._get_stock_trading_records(stock_codes, trading_date)
            
            # 按交易量排序
            trading_records.sort(key=lambda x: x.trading_volume, reverse=True)
            
            # 计算排名
            for rank, record in enumerate(trading_records, 1):
                volume_percentage = (record.trading_volume / concept_total_volume * 100) if concept_total_volume > 0 else 0
                
                ranking = StockConceptRanking(
                    stock_code=record.stock_code,
                    concept_name=concept_name,
                    trading_date=trading_date,
                    trading_volume=record.trading_volume,
                    concept_rank=rank,
                    concept_total_volume=concept_total_volume,
                    volume_percentage=volume_percentage
                )
                rankings.append(ranking)
        
        # 批量插入
        self.db.add_all(rankings)
        self.db.commit()
        
        logger.info(f"计算{len(rankings)}条排名数据")
        return len(rankings)
    
    def detect_concept_new_highs(self, trading_date: date, periods: List[int] = [5, 10, 20, 30]) -> int:
        """检测概念创新高"""
        new_highs = []
        
        # 获取当天的概念汇总数据
        today_summaries = self.db.query(ConceptDailySummary).filter(
            ConceptDailySummary.trading_date == trading_date
        ).all()
        
        for summary in today_summaries:
            concept_name = summary.concept_name
            today_volume = summary.total_volume
            
            # 对每个周期进行检测
            for period in periods:
                start_date = trading_date - timedelta(days=period)
                
                # 获取周期内的最高交易量
                max_volume_record = self.db.query(ConceptDailySummary).filter(
                    ConceptDailySummary.concept_name == concept_name,
                    ConceptDailySummary.trading_date >= start_date,
                    ConceptDailySummary.trading_date < trading_date
                ).order_by(ConceptDailySummary.total_volume.desc()).first()
                
                # 如果当天交易量创新高
                if not max_volume_record or today_volume > max_volume_record.total_volume:
                    high_record = ConceptHighRecord(
                        concept_name=concept_name,
                        trading_date=trading_date,
                        total_volume=today_volume,
                        days_period=period,
                        is_active=True
                    )
                    new_highs.append(high_record)
        
        # 批量插入
        if new_highs:
            self.db.add_all(new_highs)
            self.db.commit()
        
        logger.info(f"检测到{len(new_highs)}条概念创新高记录")
        return len(new_highs)
    
    def recalculate_daily_summary(self, trading_date: date) -> Dict:
        """重新计算指定日期的概念汇总和排名数据"""
        try:
            # 检查是否有基础交易数据
            trading_count = self.db.query(DailyTrading).filter(
                DailyTrading.trading_date == trading_date
            ).count()
            
            if trading_count == 0:
                return {"success": False, "message": f"日期{trading_date}没有基础交易数据"}
            
            # 清理汇总数据，保留基础交易数据
            self.clear_daily_data(trading_date, keep_trading_data=True)
            
            # 重新计算
            calculation_results = self.perform_calculations(trading_date)
            
            # 更新导入记录
            self.update_import_record_after_recalculation(trading_date, calculation_results, trading_count)
            
            # Session会自动提交
            self.db.commit()
            
            return {
                "success": True,
                "message": f"重新计算{trading_date}完成",
                "stats": {
                    "trading_data_count": trading_count,
                    "concept_summary_count": calculation_results['concept_summary_count'],
                    "ranking_count": calculation_results['ranking_count'],
                    "new_high_count": calculation_results['new_high_count'],
                    "trading_date": trading_date.strftime('%Y-%m-%d')
                }
            }
            
        except Exception as e:
            logger.error(f"重新计算失败: {e}")
            self.db.rollback()
            return {"success": False, "message": f"重新计算失败: {str(e)}"}

    def update_import_record_after_recalculation(self, trading_date: date, 
                                                calculation_results: Dict[str, int], 
                                                trading_count: int) -> None:
        """重新计算后更新导入记录"""
        latest_record = self.db.query(TxtImportRecord).filter(
            TxtImportRecord.trading_date == trading_date,
            TxtImportRecord.import_status == 'success'
        ).order_by(TxtImportRecord.import_started_at.desc()).first()
        
        if latest_record:
            latest_record.concept_count = calculation_results['concept_summary_count']
            latest_record.ranking_count = calculation_results['ranking_count']  
            latest_record.new_high_count = calculation_results['new_high_count']
            # 添加重新计算备注
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if latest_record.notes:
                latest_record.notes += f"\n重新计算于: {current_time}"
            else:
                latest_record.notes = f"重新计算于: {current_time}"
            self.db.commit()

    def perform_calculations(self, trading_date: date) -> Dict[str, int]:
        """执行概念计算的统一方法 - 确保导入和重新计算使用相同逻辑
        
        Args:
            trading_date: 交易日期
            
        Returns:
            包含计算结果的字典: {
                'concept_summary_count': int,
                'ranking_count': int, 
                'new_high_count': int
            }
        """
        try:
            logger.info(f"开始执行 {trading_date} 的概念计算")
            
            # 1. 计算概念汇总数据
            logger.info(f"计算概念汇总数据 for {trading_date}")
            concept_summary_count = self.calculate_concept_summary(trading_date)
            logger.info(f"概念汇总数据计算完成: {concept_summary_count}")
            
            # 2. 计算股票在概念中的排名
            logger.info(f"计算股票排名数据 for {trading_date}")
            ranking_count = self.calculate_stock_concept_ranking(trading_date)
            logger.info(f"股票排名数据计算完成: {ranking_count}")
            
            # 3. 检测概念创新高
            logger.info(f"检测概念创新高 for {trading_date}")
            high_record_count = self.detect_concept_new_highs(trading_date)
            logger.info(f"概念创新高检测完成: {high_record_count}")
            
            logger.info(f"{trading_date} 概念计算总结 - 汇总:{concept_summary_count}, 排名:{ranking_count}, 创新高:{high_record_count}")
            
            return {
                'concept_summary_count': concept_summary_count,
                'ranking_count': ranking_count,
                'new_high_count': high_record_count
            }
        except Exception as e:
            logger.error(f"执行概念计算时出错 {trading_date}: {e}")
            raise e

    def get_import_records(self, page: int = 1, size: int = 20, 
                          trading_date: Optional[date] = None) -> Dict:
        """获取TXT导入记录
        
        Args:
            page: 页码
            size: 每页大小
            trading_date: 可选的交易日期过滤
            
        Returns:
            导入记录列表和分页信息
        """
        try:
            query = self.db.query(TxtImportRecord)
            
            # 日期过滤
            if trading_date:
                query = query.filter(TxtImportRecord.trading_date == trading_date)
            
            # 总数统计
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * size
            records = query.order_by(TxtImportRecord.import_started_at.desc()).offset(offset).limit(size).all()
            
            # 格式化结果
            record_list = []
            for record in records:
                record_data = {
                    "id": record.id,
                    "filename": record.filename,
                    "trading_date": record.trading_date.strftime('%Y-%m-%d'),
                    "file_size": record.file_size,
                    "file_size_mb": round(record.file_size / 1024 / 1024, 2),
                    "import_status": record.import_status,
                    "imported_by": record.imported_by,
                    "total_records": record.total_records,
                    "success_records": record.success_records,
                    "error_records": record.error_records,
                    "concept_count": record.concept_count,
                    "ranking_count": record.ranking_count,
                    "new_high_count": record.new_high_count,
                    "import_started_at": record.import_started_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "import_completed_at": record.import_completed_at.strftime('%Y-%m-%d %H:%M:%S') if record.import_completed_at else None,
                    "calculation_time": record.calculation_time,
                    "error_message": record.error_message,
                    "notes": record.notes
                }
                record_list.append(record_data)
            
            return {
                "success": True,
                "data": {
                    "records": record_list,
                    "pagination": {
                        "page": page,
                        "size": size,
                        "total": total,
                        "pages": (total + size - 1) // size
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"获取导入记录失败: {e}")
            return {"success": False, "message": f"获取记录失败: {str(e)}"}

    def get_import_stats(self, trading_date: date) -> Dict:
        """获取导入统计信息"""
        stats = {}
        
        # 交易数据统计
        trading_count = self.db.query(DailyTrading).filter(
            DailyTrading.trading_date == trading_date
        ).count()
        
        # 概念汇总统计
        concept_count = self.db.query(ConceptDailySummary).filter(
            ConceptDailySummary.trading_date == trading_date
        ).count()
        
        # 排名数据统计
        ranking_count = self.db.query(StockConceptRanking).filter(
            StockConceptRanking.trading_date == trading_date
        ).count()
        
        # 创新高统计
        high_count = self.db.query(ConceptHighRecord).filter(
            ConceptHighRecord.trading_date == trading_date
        ).count()
        
        return {
            "trading_date": trading_date.strftime('%Y-%m-%d'),
            "trading_records": trading_count,
            "concept_summaries": concept_count,
            "ranking_records": ranking_count,
            "new_high_records": high_count
        }