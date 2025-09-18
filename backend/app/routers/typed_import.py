"""
类型化导入相关的API路由
使用type1、type2、type3等简洁命名的API接口
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.typed_import_service import TypedImportService
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/typed-import", tags=["typed-import"])


@router.get("/types", response_model=Dict[str, Any])
async def get_import_types():
    """获取支持的导入类型"""
    try:
        service = TypedImportService(None)
        result = service.get_import_types()
        return result
    except Exception as e:
        logger.error(f"获取导入类型时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取类型失败: {str(e)}")


@router.post("/import/{import_type}", response_model=Dict[str, Any])
async def import_data(
    import_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """导入指定类型的数据文件"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 验证导入类型
        from app.services.typed_import_service import IMPORT_TYPES
        if import_type not in IMPORT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的导入类型: {import_type}, 支持的类型: {list(IMPORT_TYPES.keys())}"
            )

        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')

        # 执行导入
        import_service = TypedImportService(db)
        result = import_service.import_data(
            txt_content=txt_content,
            import_type=import_type,
            filename=file.filename,
            file_size=len(content),
            imported_by=current_admin.username
        )

        return result

    except Exception as e:
        logger.error(f"导入{import_type}数据文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/records", response_model=Dict[str, Any])
async def get_import_records(
    import_type: Optional[str] = Query(None, description="导入类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取导入记录 - 复用TXT导入的成熟逻辑"""
    try:
        # 处理日期转换
        parsed_trading_date = None
        if trading_date:
            from datetime import datetime
            parsed_trading_date = datetime.strptime(trading_date, '%Y-%m-%d').date()

        import_service = TypedImportService(db)
        result = import_service.get_import_records(
            import_type=import_type,
            page=page,
            size=size,
            trading_date=parsed_trading_date
        )

        if result["success"]:
            return result["data"]
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_import_stats(
    import_type: Optional[str] = Query(None, description="导入类型过滤"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取导入统计信息"""
    try:
        import_service = TypedImportService(db)
        result = import_service.get_import_stats(import_type=import_type)

        if result["success"]:
            return result["stats"]
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        logger.error(f"获取导入统计时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.delete("/records/{record_id}")
async def delete_import_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """删除导入记录"""
    try:
        import_service = TypedImportService(db)
        result = import_service.delete_import_record(record_id)

        if result["success"]:
            logger.info(f"管理员{current_admin.username}删除了导入记录{record_id}")
            return {"success": True, "message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/processing-details/{record_id}")
async def get_processing_details(
    record_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取导入处理详情"""
    try:
        from app.models.daily_trading import TxtImportRecord
        import json

        record = db.query(TxtImportRecord).filter(
            TxtImportRecord.id == record_id
        ).first()

        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")

        processing_details = {}
        if record.processing_details:
            try:
                processing_details = json.loads(record.processing_details)
            except json.JSONDecodeError:
                logger.warning(f"解析处理详情失败: {record.processing_details}")

        metadata = {}
        if record.import_metadata:
            try:
                metadata = json.loads(record.import_metadata)
            except json.JSONDecodeError:
                logger.warning(f"解析元数据失败: {record.import_metadata}")

        return {
            "success": True,
            "record_id": record_id,
            "filename": record.filename,
            "import_type": record.import_type,
            "processing_details": processing_details,
            "metadata": metadata
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取处理详情时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")


@router.get("/data-stats/{import_type}")
async def get_data_stats(
    import_type: str,
    trading_date: Optional[str] = Query(None, description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定类型的数据统计"""
    try:
        from app.services.typed_data_service import TypedDataService
        from datetime import datetime

        # 验证导入类型
        from app.services.typed_import_service import IMPORT_TYPES
        if import_type not in IMPORT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的导入类型: {import_type}, 支持的类型: {list(IMPORT_TYPES.keys())}"
            )

        data_service = TypedDataService(db, import_type)

        # 转换日期参数
        date_filter = None
        if trading_date:
            try:
                date_filter = datetime.strptime(trading_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")

        stats = data_service.get_data_stats(trading_date=date_filter)

        return {
            "success": True,
            "import_type": import_type,
            "stats": stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取{import_type}数据统计时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/data-integrity/{import_type}/{trading_date}")
async def check_data_integrity(
    import_type: str,
    trading_date: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """检查指定类型和日期的数据完整性"""
    try:
        from app.services.typed_data_service import TypedDataService
        from datetime import datetime

        # 验证导入类型
        from app.services.typed_import_service import IMPORT_TYPES
        if import_type not in IMPORT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的导入类型: {import_type}, 支持的类型: {list(IMPORT_TYPES.keys())}"
            )

        # 转换日期参数
        try:
            check_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")

        data_service = TypedDataService(db, import_type)
        integrity_report = data_service.validate_data_integrity(check_date)

        return {
            "success": True,
            "integrity_report": integrity_report
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查{import_type}数据完整性时出错: {e}")
        raise HTTPException(status_code=500, detail=f"完整性检查失败: {str(e)}")


@router.post("/add-type/{type_number}")
async def add_new_type_template(
    type_number: int,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """添加新类型的扩展模板说明"""
    try:
        from app.models.typed_trading import add_new_type

        if type_number <= 3:
            raise HTTPException(
                status_code=400,
                detail=f"类型{type_number}已存在，请使用4或更大的数字"
            )

        # 生成扩展模板说明
        add_new_type(type_number)

        return {
            "success": True,
            "message": f"Type{type_number}扩展模板已生成",
            "type_name": f"type{type_number}",
            "steps": [
                f"1. 在 typed_trading.py 中添加 Type{type_number} 相关的4个模型类",
                f"2. 在 TYPED_MODELS 中注册 'type{type_number}' 配置",
                f"3. 在 typed_import_service.py 的 IMPORT_TYPES 中添加配置",
                f"4. 运行数据库迁移创建表结构",
                "5. 重启服务即可使用"
            ]
        }

    except Exception as e:
        logger.error(f"生成Type{type_number}扩展模板时出错: {e}")
        raise HTTPException(status_code=500, detail=f"生成模板失败: {str(e)}")