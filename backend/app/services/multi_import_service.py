"""
多类型导入服务
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models.import_record import ImportRecord
from app.services.txt_processors.processor_factory import get_processor_factory
from app.services.multi_type_data_service import MultiTypeDataService
from datetime import datetime, date
import logging
import time
import json

logger = logging.getLogger(__name__)


# 导入类型配置
IMPORT_TYPES = {
    'daily': {
        'name': '日常交易数据',
        'description': '每日股票交易数据导入',
        'category': 'daily_trading'
    },
    'batch': {
        'name': '批量交易数据',
        'description': '批量股票交易数据导入',
        'category': 'batch_trading'
    },
    'special': {
        'name': '特殊交易数据',
        'description': '特殊情况股票交易数据导入',
        'category': 'special_trading'
    },
    'experimental': {
        'name': '实验交易数据',
        'description': '实验性股票交易数据导入',
        'category': 'experimental_trading'
    }
}


class MultiImportService:
    """多类型导入服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_import_types(self) -> Dict:
        """获取支持的导入类型"""
        return {
            "success": True,
            "types": IMPORT_TYPES
        }

    def import_data(self, txt_content: str, import_type: str, filename: str = "data.txt",
                   file_size: int = 0, imported_by: str = "system") -> Dict:
        """
        导入数据

        Args:
            txt_content: TXT文件内容
            import_type: 导入类型
            filename: 文件名
            file_size: 文件大小
            imported_by: 导入人

        Returns:
            导入结果
        """
        start_time = time.time()
        import_record = None

        try:
            # 验证导入类型
            if import_type not in IMPORT_TYPES:
                return {"success": False, "message": f"不支持的导入类型: {import_type}"}

            type_config = IMPORT_TYPES[import_type]

            # 使用处理器解析数据
            factory = get_processor_factory()
            processor = factory.get_processor_by_type("standard")

            if not processor:
                return {"success": False, "message": "数据处理器不可用"}

            # 解析文件内容
            result = processor.parse_content(txt_content)

            if not result.success:
                return {"success": False, "message": f"文件解析失败: {result.message}"}

            if not result.records:
                return {"success": False, "message": "未解析到有效数据"}

            # 获取交易日期
            trading_date = result.trading_date
            if not trading_date:
                return {"success": False, "message": "无法确定交易日期"}

            # 创建导入记录
            import_record = ImportRecord(
                filename=filename,
                import_type=import_type,
                import_category=type_config['category'],
                trading_date=trading_date.strftime('%Y-%m-%d'),
                total_records=result.total_count,
                file_size=file_size,
                import_status="processing",
                processor_type="standard",
                imported_by=imported_by,
                import_started_at=datetime.utcnow(),
                import_metadata=json.dumps({
                    'type_name': type_config['name'],
                    'type_description': type_config['description'],
                    'trading_date': trading_date.strftime('%Y-%m-%d')
                }, ensure_ascii=False)
            )
            self.db.add(import_record)
            self.db.commit()

            # 使用独立的多类型数据服务
            data_service = MultiTypeDataService(self.db, import_type)

            # 清理当天已有的同类型数据
            data_service.clear_daily_data(trading_date)

            # 转换为导入服务期望的格式
            import_data = []
            for record in result.records:
                import_data.append({
                    'original_stock_code': record.original_stock_code,
                    'normalized_stock_code': record.normalized_stock_code,
                    'stock_code': record.stock_code,
                    'trading_date': record.trading_date,
                    'trading_volume': record.trading_volume,
                    'market_prefix': record.extra_fields.get('market_prefix', '')
                })

            # 导入交易数据到独立的表
            imported_count = data_service.insert_daily_trading(import_data)

            # 执行概念汇总计算（独立的表）
            calculation_results = data_service.perform_calculations(trading_date)

            # 更新导入记录
            end_time = time.time()
            duration = end_time - start_time

            import_record.import_status = "success"
            import_record.imported_records = imported_count
            import_record.error_records = result.total_count - imported_count
            import_record.import_completed_at = datetime.utcnow()
            import_record.duration_seconds = duration
            import_record.processing_details = json.dumps({
                'imported_count': imported_count,
                'calculation_results': calculation_results,
                'trading_date': trading_date.strftime('%Y-%m-%d')
            }, ensure_ascii=False)

            if imported_count == 0:
                import_record.import_status = "failed"
                import_record.error_message = "所有数据导入失败"

            self.db.commit()

            return {
                "success": True,
                "message": f"{type_config['name']}导入完成",
                "import_type": import_type,
                "type_name": type_config['name'],
                "filename": filename,
                "trading_date": trading_date.strftime('%Y-%m-%d'),
                "imported_records": imported_count,
                "error_records": result.total_count - imported_count,
                "duration": f"{duration:.2f}秒",
                "calculation_results": calculation_results
            }

        except Exception as e:
            logger.error(f"数据导入失败: {e}")

            if import_record:
                import_record.import_status = "failed"
                import_record.error_message = str(e)
                import_record.import_completed_at = datetime.utcnow()
                if start_time:
                    import_record.duration_seconds = time.time() - start_time
                self.db.commit()

            return {"success": False, "message": f"数据导入失败: {str(e)}"}

    def get_import_records(self, import_type: str = None, page: int = 1, size: int = 20,
                          filename: str = None, imported_by: str = None,
                          status: str = None, start_date: str = None,
                          end_date: str = None) -> Dict:
        """
        获取导入记录

        Args:
            import_type: 导入类型过滤
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
            query = self.db.query(ImportRecord)

            if import_type:
                query = query.filter(ImportRecord.import_type == import_type)

            if filename:
                query = query.filter(ImportRecord.filename.like(f"%{filename}%"))

            if imported_by:
                query = query.filter(ImportRecord.imported_by.like(f"%{imported_by}%"))

            if status:
                query = query.filter(ImportRecord.import_status == status)

            if start_date:
                query = query.filter(ImportRecord.import_started_at >= start_date)

            if end_date:
                query = query.filter(ImportRecord.import_started_at <= end_date)

            # 获取总数
            total = query.count()

            # 分页查询
            records = query.order_by(desc(ImportRecord.import_started_at))\
                          .offset((page - 1) * size)\
                          .limit(size)\
                          .all()

            # 统计信息
            stats_query = self.db.query(ImportRecord)
            if import_type:
                stats_query = stats_query.filter(ImportRecord.import_type == import_type)
            if start_date:
                stats_query = stats_query.filter(ImportRecord.import_started_at >= start_date)
            if end_date:
                stats_query = stats_query.filter(ImportRecord.import_started_at <= end_date)

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
                    "stats": stats,
                    "import_type": import_type
                }
            }

        except Exception as e:
            logger.error(f"获取导入记录失败: {e}")
            return {"success": False, "message": f"获取记录失败: {str(e)}"}

    def get_import_stats(self, import_type: str = None) -> Dict:
        """获取导入统计信息"""
        try:
            query = self.db.query(ImportRecord)
            if import_type:
                query = query.filter(ImportRecord.import_type == import_type)

            records = query.all()

            # 按类型分组统计
            type_stats = {}
            for type_key, type_config in IMPORT_TYPES.items():
                type_records = [r for r in records if r.import_type == type_key]
                type_stats[type_key] = {
                    'name': type_config['name'],
                    'total_imports': len(type_records),
                    'success_imports': len([r for r in type_records if r.import_status == 'success']),
                    'failed_imports': len([r for r in type_records if r.import_status == 'failed']),
                    'total_records': sum(r.imported_records for r in type_records)
                }

            overall_stats = {
                'total_imports': len(records),
                'success_imports': len([r for r in records if r.import_status == 'success']),
                'failed_imports': len([r for r in records if r.import_status == 'failed']),
                'processing_imports': len([r for r in records if r.import_status == 'processing']),
                'total_records': sum(r.imported_records for r in records),
                'avg_duration': sum(r.duration_seconds or 0 for r in records) / len(records) if records else 0
            }

            return {
                "success": True,
                "stats": {
                    "overall": overall_stats,
                    "by_type": type_stats
                }
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {"success": False, "message": f"获取统计失败: {str(e)}"}

    def delete_import_record(self, record_id: int) -> Dict:
        """删除导入记录"""
        try:
            record = self.db.query(ImportRecord).filter(
                ImportRecord.id == record_id
            ).first()

            if not record:
                return {"success": False, "message": "记录不存在"}

            self.db.delete(record)
            self.db.commit()

            return {"success": True, "message": "删除成功"}

        except Exception as e:
            logger.error(f"删除导入记录失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}