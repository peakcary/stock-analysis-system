"""
通用导入API端点 - 支持多种文件类型的导入
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging
from datetime import date, datetime

from app.core.database import get_db
from app.services.universal_import_service import UniversalImportService
from app.services.schema import FileTypeRegistry
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ========================= 请求/响应模型 =========================

class ImportRequest(BaseModel):
    """导入请求模型"""
    file_type: str = Field(..., description="文件类型", pattern="^[a-zA-Z0-9_-]+$")
    trading_date: date = Field(..., description="交易日期")
    mode: str = Field("overwrite", description="导入模式", pattern="^(overwrite|append)$")

class ImportResponse(BaseModel):
    """导入响应模型"""
    success: bool
    message: str
    file_type: str
    import_record_id: Optional[int] = None
    filename: Optional[str] = None
    trading_date: Optional[str] = None
    file_size: Optional[int] = None
    parse_info: Optional[Dict[str, Any]] = None
    import_result: Optional[Dict[str, Any]] = None
    calculation_result: Optional[Dict[str, Any]] = None
    calculation_time: Optional[float] = None
    error: Optional[str] = None

class RecalculateRequest(BaseModel):
    """重新计算请求模型"""
    file_type: str = Field(..., description="文件类型", pattern="^[a-zA-Z0-9_-]+$")
    trading_date: date = Field(..., description="交易日期")

# ========================= 依赖注入 =========================

def get_universal_import_service(
    file_type: str,
    db: Session = Depends(get_db)
) -> UniversalImportService:
    """获取通用导入服务实例"""
    try:
        return UniversalImportService(db, file_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建通用导入服务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务初始化失败: {str(e)}"
        )

def get_registry(db: Session = Depends(get_db)) -> FileTypeRegistry:
    """获取文件类型注册管理器"""
    from app.core.database import get_engine
    engine = get_engine()
    return FileTypeRegistry(engine, db)

def ensure_file_type_ready(file_type: str, registry: FileTypeRegistry) -> None:
    """确保文件类型的表与模型处于健康状态。必要时自动修复模型。"""
    try:
        health = registry.validate_file_type_health(file_type)
        # 条件：配置存在、表存在、模型已生成
        config_ok = health.get('config_valid', True)
        tables_ok = health.get('tables_exist', True)
        models_ok = health.get('models_generated', True)
        if not (config_ok and tables_ok and models_ok):
            # 只重建模型，避免有数据时重建表
            registry.repair_file_type(file_type, {
                'rebuild_models': True,
                'rebuild_tables': False,
                'force': False
            })
    except Exception as e:
        logger.warning(f"文件类型 {file_type} 健康检查失败，继续尝试: {e}")

# ========================= API 端点 =========================

@router.get("/supported-types", response_model=Dict[str, Any], summary="获取支持的文件类型")
async def get_supported_file_types(registry: FileTypeRegistry = Depends(get_registry)):
    """获取所有支持导入的文件类型"""
    try:
        enabled_types = registry.get_enabled_file_types()
        configs = registry.config_manager.get_enabled_configs()

        return {
            "success": True,
            "supported_types": enabled_types,
            "type_configs": {
                file_type: {
                    "display_name": config.display_name,
                    "description": config.description,
                    "file_extensions": config.file_extensions,
                    "max_file_size": config.max_file_size
                }
                for file_type, config in configs.items()
            },
            "total_count": len(enabled_types)
        }
    except Exception as e:
        logger.error(f"获取支持的文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取支持的文件类型失败: {str(e)}"
        )

@router.post("/import", response_model=ImportResponse, summary="通用文件导入")
async def import_file(
    file: UploadFile = File(..., description="上传的文件"),
    file_type: str = Form(..., description="文件类型"),
    trading_date: date = Form(..., description="交易日期"),
    mode: str = Form("overwrite", description="导入模式"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    通用文件导入接口
    支持多种文件类型的股票数据导入
    """
    try:
        # 1. 验证文件类型是否支持
        registry = get_registry(db)
        config = registry.get_file_type_config(file_type)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_type}"
            )

        if not config.enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件类型 {file_type} 已被禁用"
            )

        # 2. 验证文件扩展名
        file_extension = f".{file.filename.split('.')[-1].lower()}" if '.' in file.filename else ""
        if file_extension not in config.file_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件扩展名: {file_extension}，支持的扩展名: {config.file_extensions}"
            )

        # 3. 验证文件大小
        if file.size and file.size > config.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制: {file.size} > {config.max_file_size}"
            )

        # 4. 读取文件内容
        try:
            file_content = await file.read()
            file_content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                file_content_str = file_content.decode('gbk')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="文件编码不支持，请使用UTF-8或GBK编码"
                )

        # 5. 创建导入服务并执行导入
        import_service = get_universal_import_service(file_type, db)
        result = import_service.import_file(
            file_content=file_content_str,
            filename=file.filename,
            trading_date=trading_date,
            imported_by=current_user,
            mode=mode
        )

        # 6. 返回结果
        return ImportResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"通用文件导入失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件导入失败: {str(e)}"
        )

@router.get("/{file_type}/records", response_model=Dict[str, Any], summary="获取导入记录")
async def get_import_records(
    file_type: str,
    limit: int = 50,
    offset: int = 0,
    trading_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """获取指定文件类型的导入记录"""
    try:
        registry = get_registry(db)
        ensure_file_type_ready(file_type, registry)
        import_service = get_universal_import_service(file_type, db)
        result = import_service.get_import_records(limit=limit, offset=offset, trading_date=trading_date)

        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导入记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导入记录失败: {str(e)}"
        )

@router.get("/{file_type}/dates", response_model=Dict[str, Any], summary="获取可用交易日期")
async def get_available_dates(
    file_type: str,
    limit: int = 365,
    db: Session = Depends(get_db)
):
    """获取指定文件类型的可用交易日期列表"""
    try:
        registry = get_registry(db)
        ensure_file_type_ready(file_type, registry)
        import_service = get_universal_import_service(file_type, db)
        result = import_service.get_available_dates(limit=limit)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取日期列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日期列表失败: {str(e)}"
        )

@router.post("/{file_type}/recalculate", response_model=Dict[str, Any], summary="重新计算指定日期数据")
async def recalculate_date_data(
    file_type: str,
    trading_date: date,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重新计算指定日期的汇总数据"""
    try:
        import_service = get_universal_import_service(file_type, db)

        # 执行重新计算
        start_time = datetime.utcnow()
        calculation_result = import_service.perform_calculations(trading_date, None)
        end_time = datetime.utcnow()

        calculation_time = (end_time - start_time).total_seconds()

        return {
            'success': True,
            'message': f'{file_type.upper()}文件 {trading_date} 数据重新计算完成',
            'file_type': file_type,
            'trading_date': trading_date.isoformat(),
            'calculation_result': calculation_result,
            'calculation_time': round(calculation_time, 3),
            'recalculated_by': current_user,
            'recalculated_at': end_time.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新计算失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新计算失败: {str(e)}"
        )

@router.get("/{file_type}/validate", response_model=Dict[str, Any], summary="验证文件类型状态")
async def validate_file_type_status(
    file_type: str,
    db: Session = Depends(get_db)
):
    """验证文件类型的状态和健康度"""
    try:
        registry = get_registry(db)

        # 检查配置
        config = registry.get_file_type_config(file_type)
        if not config:
            return {
                'success': False,
                'message': f'文件类型 {file_type} 未注册'
            }

        # 健康检查
        health_result = registry.validate_file_type_health(file_type)

        # 获取基本信息
        try:
            import_service = get_universal_import_service(file_type, db)
            service_status = "healthy"
        except Exception as e:
            service_status = f"error: {str(e)}"

        return {
            'success': True,
            'file_type': file_type,
            'config': config.to_dict(),
            'service_status': service_status,
            'health_check': health_result,
            'validated_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"验证文件类型状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证失败: {str(e)}"
        )

@router.get("/{file_type}/statistics", response_model=Dict[str, Any], summary="获取文件类型统计信息")
async def get_file_type_statistics(
    file_type: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """获取文件类型的统计信息"""
    try:
        import_service = get_universal_import_service(file_type, db)

        # 获取最近的导入记录
        records_result = import_service.get_import_records(limit=days)

        if not records_result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=records_result['message']
            )

        records = records_result['records']

        # 计算统计信息
        total_imports = len(records)
        successful_imports = len([r for r in records if r['import_status'] == 'success'])
        failed_imports = len([r for r in records if r['import_status'] == 'failed'])
        total_records_imported = sum(r.get('success_records', 0) for r in records)
        total_file_size = sum(r.get('file_size', 0) for r in records)

        avg_calculation_time = 0
        if records:
            calc_times = [r.get('calculation_time', 0) for r in records if r.get('calculation_time')]
            if calc_times:
                avg_calculation_time = sum(calc_times) / len(calc_times)

        return {
            'success': True,
            'file_type': file_type,
            'period_days': days,
            'statistics': {
                'total_imports': total_imports,
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'success_rate': round(successful_imports / total_imports * 100, 2) if total_imports > 0 else 0,
                'total_records_imported': total_records_imported,
                'total_file_size_mb': round(total_file_size / 1024 / 1024, 2),
                'avg_calculation_time': round(avg_calculation_time, 3)
            },
            'recent_records': records[:10],  # 最近10条记录
            'generated_at': datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )

@router.get("/{file_type}/debug/check", response_model=Dict[str, Any], summary="调试: 校验指定文件类型的数据写入")
async def debug_check_file_type(
    file_type: str,
    trading_date: Optional[date] = None,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    调试用接口：核对指定文件类型的数据写入是否正常。
    返回导入记录计数、各相关表在给定日期的数据条数，以及最近的导入记录与日期列表。
    """
    try:
        svc = get_universal_import_service(file_type, db)

        # 动态模型
        ImportRecord = svc.ImportRecord
        DailyTrading = svc.DailyTrading
        ConceptSummary = svc.ConceptDailySummary
        Ranking = svc.StockConceptRanking
        HighRecord = svc.ConceptHighRecord

        # 统计整体
        total_import_records = db.query(ImportRecord).count()

        # 统计指定日期
        date_counts = None
        if trading_date:
            date_counts = {
                'import_records': db.query(ImportRecord).filter(ImportRecord.trading_date == trading_date).count(),
                'daily_trading': db.query(DailyTrading).filter(DailyTrading.trading_date == trading_date).count(),
                'concept_summary': db.query(ConceptSummary).filter(ConceptSummary.trading_date == trading_date).count(),
                'ranking': db.query(Ranking).filter(Ranking.trading_date == trading_date).count(),
                'high_record': db.query(HighRecord).filter(HighRecord.trading_date == trading_date).count(),
            }

        # 最近导入记录
        recent = db.query(ImportRecord).order_by(ImportRecord.import_started_at.desc()).limit(limit).all()
        recent_records = [
            {
                'id': r.id,
                'filename': r.filename,
                'trading_date': r.trading_date.isoformat(),
                'status': r.import_status.value if hasattr(r.import_status, 'value') else str(r.import_status),
                'total_records': r.total_records,
                'success_records': r.success_records,
                'error_records': r.error_records,
                'concept_count': getattr(r, 'concept_count', 0),
                'ranking_count': getattr(r, 'ranking_count', 0),
                'new_high_count': getattr(r, 'new_high_count', 0),
                'started_at': r.import_started_at.isoformat(),
                'completed_at': r.import_completed_at.isoformat() if r.import_completed_at else None,
            }
            for r in recent
        ]

        # 日期列表
        dates_result = svc.get_available_dates(limit=365)

        return {
            'success': True,
            'file_type': file_type,
            'total_import_records': total_import_records,
            'date_counts': date_counts,
            'recent_records': recent_records,
            'dates': dates_result.get('dates', []),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"调试检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调试检查失败: {str(e)}"
        )
