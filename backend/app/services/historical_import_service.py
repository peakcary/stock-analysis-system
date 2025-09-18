"""
历史数据导入服务
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models.historical_import import HistoricalImportRecord
from app.services.txt_processors.processor_factory import get_processor_factory
from datetime import datetime, date
import logging
import time
import json

logger = logging.getLogger(__name__)


class HistoricalImportService:
    """历史数据导入服务"""

    def __init__(self, db: Session):
        self.db = db

    def import_historical_data(self, txt_content: str, filename: str = "historical.txt",
                             file_size: int = 0, imported_by: str = "system") -> Dict:
        """
        导入历史数据

        Args:
            txt_content: TXT文件内容
            filename: 文件名
            file_size: 文件大小
            imported_by: 导入人

        Returns:
            导入结果
        """
        start_time = time.time()
        import_record = None

        try:
            # 使用历史处理器解析数据
            factory = get_processor_factory()
            processor = factory.get_processor_by_type("historical")

            if not processor:
                return {"success": False, "message": "历史数据处理器不可用"}

            # 解析文件内容
            result = processor.parse_content(txt_content)

            if not result.success:
                return {"success": False, "message": f"文件解析失败: {result.message}"}

            if not result.records:
                return {"success": False, "message": "未解析到有效数据"}

            # 分析日期范围
            dates = sorted(list(set(record.trading_date for record in result.records)))
            earliest_date = dates[0]
            latest_date = dates[-1]
            date_range = f"{earliest_date} 至 {latest_date}"

            # 创建导入记录
            import_record = HistoricalImportRecord(
                filename=filename,
                total_dates=len(dates),
                date_range=date_range,
                earliest_date=earliest_date.strftime('%Y-%m-%d'),
                latest_date=latest_date.strftime('%Y-%m-%d'),
                total_records=result.total_count,
                file_size=file_size,
                import_status="processing",
                processor_type="historical",
                imported_by=imported_by,
                import_started_at=datetime.utcnow()
            )
            self.db.add(import_record)
            self.db.commit()

            # 按日期分组处理数据（这里应该调用现有的TXT导入服务）
            from app.services.txt_import import TxtImportService
            txt_service = TxtImportService(self.db)

            total_imported = 0
            total_errors = 0
            processing_details = []

            # 按日期分组数据
            data_by_date = {}
            for record in result.records:
                date_key = record.trading_date
                if date_key not in data_by_date:
                    data_by_date[date_key] = []

                # 转换为txt_service期望的格式
                data_by_date[date_key].append({
                    'original_stock_code': record.original_stock_code,
                    'normalized_stock_code': record.normalized_stock_code,
                    'stock_code': record.stock_code,
                    'trading_date': record.trading_date,
                    'trading_volume': record.trading_volume,
                    'market_prefix': record.extra_fields.get('market_prefix', '')
                })

            # 逐日期导入
            for trading_date, daily_data in sorted(data_by_date.items()):
                try:
                    logger.info(f"正在导入 {trading_date} 的数据，共 {len(daily_data)} 条记录")

                    # 使用现有的单日期导入逻辑
                    imported_count = txt_service.insert_daily_trading(daily_data)

                    # 执行概念汇总计算
                    calculation_results = txt_service.perform_calculations(trading_date)

                    total_imported += imported_count

                    processing_details.append({
                        'date': trading_date.strftime('%Y-%m-%d'),
                        'records': len(daily_data),
                        'imported': imported_count,
                        'errors': len(daily_data) - imported_count,
                        'concept_summaries': calculation_results.get('concept_summary_count', 0),
                        'rankings': calculation_results.get('ranking_count', 0),
                        'new_highs': calculation_results.get('new_high_count', 0)
                    })

                    logger.info(f"完成导入 {trading_date}，成功 {imported_count} 条")

                except Exception as e:
                    logger.error(f"导入 {trading_date} 数据时出错: {e}")
                    total_errors += len(daily_data)
                    processing_details.append({
                        'date': trading_date.strftime('%Y-%m-%d'),
                        'records': len(daily_data),
                        'imported': 0,
                        'errors': len(daily_data),
                        'error': str(e)
                    })

            # 更新导入记录
            end_time = time.time()
            duration = end_time - start_time

            import_record.import_status = "success" if total_errors == 0 else "partial"
            import_record.imported_records = total_imported
            import_record.error_records = total_errors
            import_record.import_completed_at = datetime.utcnow()
            import_record.duration_seconds = duration
            import_record.processing_details = json.dumps(processing_details, ensure_ascii=False)

            if total_errors > 0 and total_imported == 0:
                import_record.import_status = "failed"
                import_record.error_message = "所有数据导入失败"

            self.db.commit()

            return {
                "success": True,
                "message": f"历史数据导入完成",
                "filename": filename,
                "total_dates": len(dates),
                "date_range": date_range,
                "imported_records": total_imported,
                "error_records": total_errors,
                "duration": f"{duration:.2f}秒",
                "processing_details": processing_details
            }

        except Exception as e:
            logger.error(f"历史数据导入失败: {e}")

            if import_record:
                import_record.import_status = "failed"
                import_record.error_message = str(e)
                import_record.import_completed_at = datetime.utcnow()
                if start_time:
                    import_record.duration_seconds = time.time() - start_time
                self.db.commit()

            return {"success": False, "message": f"历史数据导入失败: {str(e)}"}

    def get_import_records(self, page: int = 1, size: int = 20,
                          filename: str = None, imported_by: str = None,
                          status: str = None, start_date: str = None,
                          end_date: str = None) -> Dict:
        """
        获取历史导入记录

        Args:
            page: 页码
            size: 每页大小
            filename: 文件名过滤
            imported_by: 导入人过滤
            status: 状态过滤
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            导入记录列表和统计信息
        """
        try:
            # 构建查询条件
            query = self.db.query(HistoricalImportRecord)

            if filename:
                query = query.filter(HistoricalImportRecord.filename.like(f"%{filename}%"))

            if imported_by:
                query = query.filter(HistoricalImportRecord.imported_by.like(f"%{imported_by}%"))

            if status:
                query = query.filter(HistoricalImportRecord.import_status == status)

            if start_date:
                query = query.filter(HistoricalImportRecord.import_started_at >= start_date)

            if end_date:
                query = query.filter(HistoricalImportRecord.import_started_at <= end_date)

            # 获取总数
            total = query.count()

            # 分页查询
            records = query.order_by(desc(HistoricalImportRecord.import_started_at))\
                          .offset((page - 1) * size)\
                          .limit(size)\
                          .all()

            # 统计信息
            stats_query = self.db.query(HistoricalImportRecord)
            if start_date:
                stats_query = stats_query.filter(HistoricalImportRecord.import_started_at >= start_date)
            if end_date:
                stats_query = stats_query.filter(HistoricalImportRecord.import_started_at <= end_date)

            all_records = stats_query.all()
            stats = {
                'total_imports': len(all_records),
                'success_imports': len([r for r in all_records if r.import_status == 'success']),
                'failed_imports': len([r for r in all_records if r.import_status == 'failed']),
                'total_records': sum(r.imported_records for r in all_records)
            }

            return {
                "success": True,
                "data": {
                    "records": [record.to_dict() for record in records],
                    "total": total,
                    "page": page,
                    "size": size,
                    "stats": stats
                }
            }

        except Exception as e:
            logger.error(f"获取历史导入记录失败: {e}")
            return {"success": False, "message": f"获取记录失败: {str(e)}"}

    def get_import_stats(self) -> Dict:
        """获取导入统计信息"""
        try:
            records = self.db.query(HistoricalImportRecord).all()

            stats = {
                'total_imports': len(records),
                'success_imports': len([r for r in records if r.import_status == 'success']),
                'failed_imports': len([r for r in records if r.import_status == 'failed']),
                'processing_imports': len([r for r in records if r.import_status == 'processing']),
                'total_records': sum(r.imported_records for r in records),
                'total_dates': sum(r.total_dates for r in records),
                'avg_duration': sum(r.duration_seconds or 0 for r in records) / len(records) if records else 0
            }

            return {"success": True, "stats": stats}

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"success": False, "message": f"获取统计失败: {str(e)}"}

    def delete_import_record(self, record_id: int) -> Dict:
        """删除导入记录"""
        try:
            record = self.db.query(HistoricalImportRecord).filter(
                HistoricalImportRecord.id == record_id
            ).first()

            if not record:
                return {"success": False, "message": "记录不存在"}

            self.db.delete(record)
            self.db.commit()

            return {"success": True, "message": "删除成功"}

        except Exception as e:
            logger.error(f"删除导入记录失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}