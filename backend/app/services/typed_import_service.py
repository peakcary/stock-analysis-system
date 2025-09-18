"""
类型化导入服务
使用type1、type2、type3等简洁命名的导入服务
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from app.models.import_record import ImportRecord
from app.services.txt_processors.processor_factory import get_processor_factory
from app.services.typed_data_service import TypedDataService
from datetime import datetime, date
import logging
import time
import json

logger = logging.getLogger(__name__)


# 导入类型配置 - 使用简洁的type1、type2、type3命名
IMPORT_TYPES = {
    'type1': {
        'name': 'Type1数据',
        'description': 'Type1类型TXT文件导入',
        'category': 'type1_trading'
    },
    'type2': {
        'name': 'Type2数据',
        'description': 'Type2类型TXT文件导入',
        'category': 'type2_trading'
    },
    'type3': {
        'name': 'Type3数据',
        'description': 'Type3类型TXT文件导入',
        'category': 'type3_trading'
    },
    'eee': {
        'name': 'EEE数据',
        'description': 'EEE类型TXT文件导入',
        'category': 'eee_trading'
    },
    'ttv': {
        'name': 'TTV数据',
        'description': 'TTV类型TXT文件导入',
        'category': 'ttv_trading'
    }
}


class TypedImportService:
    """类型化导入服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_import_types(self) -> Dict:
        """获取支持的导入类型"""
        return {
            "success": True,
            "types": IMPORT_TYPES
        }

    def import_data(
        self,
        txt_content: str,
        import_type: str,
        filename: str,
        file_size: int,
        imported_by: str,
        processor_type: str = "standard"
    ) -> Dict:
        """导入数据"""
        try:
            # 验证导入类型
            if import_type not in IMPORT_TYPES:
                return {
                    "success": False,
                    "message": f"不支持的导入类型: {import_type}",
                    "supported_types": list(IMPORT_TYPES.keys())
                }

            # 预处理：检查导入内容的交易日期，判断是否会覆盖
            from app.services.txt_processors.processor_factory import get_processor_factory
            factory = get_processor_factory()
            processor = factory.get_processor_by_type(processor_type)

            # 检查处理器是否存在
            if processor is None:
                return {
                    "success": False,
                    "message": f"不支持的处理器类型: {processor_type}"
                }

            # 预解析以获取交易日期
            parse_result = processor.parse_content(txt_content)
            if not parse_result.success:
                return {
                    "success": False,
                    "message": f"文件解析失败: {parse_result.message}"
                }

            trading_date = parse_result.trading_date

            # 检查类型化表是否已有该日期的数据
            data_service = TypedDataService(self.db, import_type)
            existing_typed_data = data_service.check_existing_data(trading_date)

            will_override_message = ""
            if existing_typed_data > 0:
                will_override_message = f"检测到{trading_date}已有{import_type}类型数据({existing_typed_data}条)，将进行覆盖导入。"
                logger.info(will_override_message)

            # 直接复用成熟的通用TXT导入逻辑
            from app.services.txt_import import TxtImportService

            # 创建通用导入服务实例
            txt_service = TxtImportService(self.db)

            # 直接调用成熟的导入方法，获取完整的业务逻辑
            start_time = time.time()
            import_result = txt_service.import_daily_trading(
                txt_content=txt_content,
                filename=filename,
                file_size=file_size,
                imported_by=imported_by,
                processor_type=processor_type
            )

            if not import_result["success"]:
                return import_result

            # 获取导入的交易日期和统计信息
            trading_date_str = import_result["stats"]["trading_date"]
            trading_date = datetime.strptime(trading_date_str, '%Y-%m-%d').date()

            # 现在将通用表的数据复制到类型化表中
            data_service = TypedDataService(self.db, import_type)

            # 获取刚导入到通用表的数据
            from app.models.daily_trading import DailyTrading
            general_trading_data = self.db.query(DailyTrading).filter(
                DailyTrading.trading_date == trading_date
            ).all()

            # 转换为字典格式
            trading_data = []
            for record in general_trading_data:
                trading_data.append({
                    'original_stock_code': record.original_stock_code,
                    'normalized_stock_code': record.normalized_stock_code,
                    'stock_code': record.stock_code,
                    'trading_date': record.trading_date,
                    'trading_volume': record.trading_volume
                })

            try:
                # 清除类型化表的同日期旧数据
                data_service.clear_daily_data(trading_date)

                # 插入到类型化表
                inserted_count = data_service.insert_daily_trading(trading_data)

                # 执行类型化的概念计算
                calc_results = data_service.perform_calculations(trading_date)

                # 在通用导入记录的processing_details中添加类型化信息
                general_import_id = import_result.get("import_record_id")
                if general_import_id:
                    self._add_typed_info_to_general_record(
                        general_import_id, import_type, calc_results, inserted_count
                    )

                # 基于通用导入结果构建类型化导入结果
                duration = time.time() - start_time

                # 构建完整的成功消息
                success_message = f"{import_type}数据导入成功"
                if will_override_message:
                    success_message = will_override_message + success_message

                return {
                    "success": True,
                    "message": success_message,
                    "data": {
                        "import_type": import_type,
                        "filename": filename,
                        "total_records": import_result["stats"]["trading_data_count"],
                        "imported_records": inserted_count,
                        "trading_date": trading_date_str,
                        "duration_seconds": round(duration, 2),
                        "calculations": calc_results,
                        "general_import": import_result["stats"],  # 包含通用导入的完整统计
                        "general_import_id": general_import_id  # 关联的通用导入记录ID
                    }
                }

            except Exception as e:
                logger.error(f"类型化导入失败: {e}")
                return {
                    "success": False,
                    "message": f"类型化导入失败: {str(e)}",
                    "general_import": import_result  # 包含通用导入的结果
                }
                raise

        except Exception as e:
            logger.error(f"数据导入失败: {e}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }

    def _create_import_record(
        self,
        filename: str,
        import_type: str,
        file_size: int,
        imported_by: str,
        processor_type: str,
        process_result,
        start_time: float
    ) -> ImportRecord:
        """创建导入记录"""
        try:
            type_config = IMPORT_TYPES[import_type]

            # 准备元数据
            metadata = {
                "type_name": type_config['name'],
                "type_description": type_config['description'],
                "trading_date": process_result.trading_date.isoformat()
            }

            import_record = ImportRecord(
                filename=filename,
                import_type=import_type,
                import_category=type_config['category'],
                total_records=len(process_result.records),
                imported_records=0,
                error_records=0,
                skipped_records=0,
                trading_date=process_result.trading_date.isoformat(),
                file_size=file_size,
                import_status='processing',
                processor_type=processor_type,
                import_started_at=datetime.fromtimestamp(start_time),
                imported_by=imported_by,
                import_metadata=json.dumps(metadata, ensure_ascii=False)
            )

            self.db.add(import_record)
            self.db.commit()
            self.db.refresh(import_record)

            return import_record

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建导入记录失败: {e}")
            raise

    def _update_import_record_success(
        self,
        import_record: ImportRecord,
        imported_count: int,
        duration: float,
        calc_results: Dict
    ):
        """更新导入记录为成功状态"""
        try:
            processing_details = {
                "calculations": calc_results,
                "processing_steps": [
                    "数据清理完成",
                    f"插入{imported_count}条交易数据",
                    "概念计算完成",
                    "排名统计完成"
                ]
            }

            import_record.imported_records = imported_count
            import_record.import_status = 'completed'
            import_record.import_completed_at = datetime.utcnow()
            import_record.duration_seconds = round(duration, 2)
            import_record.processing_details = json.dumps(processing_details, ensure_ascii=False)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新导入记录失败: {e}")
            raise

    def _update_import_record_error(self, import_record: ImportRecord, error_message: str):
        """更新导入记录为错误状态"""
        try:
            import_record.import_status = 'failed'
            import_record.error_message = error_message
            import_record.import_completed_at = datetime.utcnow()

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新导入记录错误状态失败: {e}")

    def _add_typed_info_to_general_record(
        self,
        general_import_id: int,
        import_type: str,
        calc_results: Dict,
        inserted_count: int
    ):
        """在通用导入记录中添加类型化信息"""
        try:
            from app.models.daily_trading import TxtImportRecord
            general_record = self.db.query(TxtImportRecord).filter(
                TxtImportRecord.id == general_import_id
            ).first()

            if general_record:
                # 创建类型化处理详情
                typed_info = {
                    "typed_import": {
                        "type": import_type,
                        "inserted_count": inserted_count,
                        "calculations": calc_results,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }

                # 更新备注字段
                if general_record.notes:
                    general_record.notes += f"\n类型化导入({import_type}): {inserted_count}条记录"
                else:
                    general_record.notes = f"类型化导入({import_type}): {inserted_count}条记录"

                self.db.commit()
                logger.info(f"已在通用导入记录{general_import_id}中添加{import_type}类型信息")

        except Exception as e:
            logger.error(f"添加类型化信息失败: {e}")

    def get_import_records(
        self,
        import_type: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        trading_date: Optional[date] = None
    ) -> Dict:
        """获取导入记录 - 直接复用TXT导入的成熟逻辑"""
        try:
            from app.models.daily_trading import TxtImportRecord

            # 构建查询 - 完全按照TXT导入的逻辑
            query = self.db.query(TxtImportRecord)

            # 如果指定了import_type，只显示包含该类型的记录
            if import_type:
                query = query.filter(TxtImportRecord.notes.like(f"%{import_type}%"))

            # 日期过滤
            if trading_date:
                query = query.filter(TxtImportRecord.trading_date == trading_date)

            # 总数统计
            total = query.count()

            # 分页查询 - 完全复用TXT导入的排序和分页逻辑
            offset = (page - 1) * size
            records = query.order_by(TxtImportRecord.import_started_at.desc()).offset(offset).limit(size).all()

            # 格式化结果 - 完全复用TXT导入的格式化逻辑
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

            # 返回格式 - 完全复用TXT导入的返回格式
            return {
                "success": True,
                "data": {
                    "records": record_list,
                    "pagination": {
                        "page": page,
                        "size": size,
                        "total": total
                    }
                }
            }

        except Exception as e:
            logger.error(f"获取导入记录失败: {e}")
            return {
                "success": False,
                "message": f"查询失败: {str(e)}"
            }

    def get_import_stats(self, import_type: Optional[str] = None) -> Dict:
        """获取导入统计"""
        try:
            query = self.db.query(ImportRecord)

            if import_type:
                query = query.filter(ImportRecord.import_type == import_type)

            # 基础统计
            total_imports = query.count()
            successful_imports = query.filter(ImportRecord.import_status == 'completed').count()
            failed_imports = query.filter(ImportRecord.import_status == 'failed').count()

            # 按类型分组统计
            type_stats = {}
            for type_key in IMPORT_TYPES.keys():
                type_query = self.db.query(ImportRecord).filter(ImportRecord.import_type == type_key)
                type_stats[type_key] = {
                    "total": type_query.count(),
                    "successful": type_query.filter(ImportRecord.import_status == 'completed').count(),
                    "failed": type_query.filter(ImportRecord.import_status == 'failed').count(),
                    "name": IMPORT_TYPES[type_key]['name']
                }

            return {
                "success": True,
                "stats": {
                    "total_imports": total_imports,
                    "successful_imports": successful_imports,
                    "failed_imports": failed_imports,
                    "success_rate": round(successful_imports / total_imports * 100, 2) if total_imports > 0 else 0,
                    "by_type": type_stats
                }
            }

        except Exception as e:
            logger.error(f"获取导入统计失败: {e}")
            return {
                "success": False,
                "message": f"统计查询失败: {str(e)}"
            }

    def delete_import_record(self, record_id: int) -> Dict:
        """删除导入记录"""
        try:
            from app.models.daily_trading import TxtImportRecord
            record = self.db.query(TxtImportRecord).filter(TxtImportRecord.id == record_id).first()

            if not record:
                return {
                    "success": False,
                    "message": "导入记录不存在"
                }

            self.db.delete(record)
            self.db.commit()

            return {
                "success": True,
                "message": "导入记录删除成功"
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除导入记录失败: {e}")
            return {
                "success": False,
                "message": f"删除失败: {str(e)}"
            }