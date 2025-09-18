"""
历史数据导入相关的API路由
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.historical_import_service import HistoricalImportService
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/historical-import", tags=["historical-import"])


@router.post("/import", response_model=Dict[str, Any])
async def import_historical_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """导入历史数据文件"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')

        # 执行导入
        import_service = HistoricalImportService(db)
        result = import_service.import_historical_data(
            txt_content=txt_content,
            filename=file.filename,
            file_size=len(content),
            imported_by=current_admin.username
        )

        return result

    except Exception as e:
        logger.error(f"导入历史数据文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/records")
async def get_import_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    filename: Optional[str] = Query(None, description="文件名过滤"),
    imported_by: Optional[str] = Query(None, description="导入人过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取历史数据导入记录"""
    try:
        import_service = HistoricalImportService(db)
        result = import_service.get_import_records(
            page=page,
            size=size,
            filename=filename,
            imported_by=imported_by,
            status=status,
            start_date=start_date,
            end_date=end_date
        )

        if result["success"]:
            return result["data"]
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取历史导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")


@router.get("/stats")
async def get_import_stats(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取历史数据导入统计信息"""
    try:
        import_service = HistoricalImportService(db)
        result = import_service.get_import_stats()

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
    """删除历史导入记录"""
    try:
        import_service = HistoricalImportService(db)
        result = import_service.delete_import_record(record_id)

        if result["success"]:
            logger.info(f"管理员{current_admin.username}删除了历史导入记录{record_id}")
            return {"success": True, "message": "删除成功"}
        else:
            raise HTTPException(status_code=404, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除历史导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/reimport/{record_id}")
async def reimport_historical_data(
    record_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """重新导入历史数据"""
    try:
        # 获取原始导入记录
        from app.models.historical_import import HistoricalImportRecord
        record = db.query(HistoricalImportRecord).filter(
            HistoricalImportRecord.id == record_id
        ).first()

        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")

        # 这里需要重新读取原始文件或者从记录中恢复数据
        # 由于没有保存原始文件内容，这个功能需要额外的设计
        # 暂时返回一个提示信息

        return {
            "success": False,
            "message": "重新导入功能需要保存原始文件内容，当前版本暂不支持"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新导入历史数据时出错: {e}")
        raise HTTPException(status_code=500, detail=f"重新导入失败: {str(e)}")


@router.get("/processing-details/{record_id}")
async def get_processing_details(
    record_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取导入处理详情"""
    try:
        from app.models.historical_import import HistoricalImportRecord
        import json

        record = db.query(HistoricalImportRecord).filter(
            HistoricalImportRecord.id == record_id
        ).first()

        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")

        processing_details = []
        if record.processing_details:
            try:
                processing_details = json.loads(record.processing_details)
            except json.JSONDecodeError:
                logger.warning(f"解析处理详情失败: {record.processing_details}")

        return {
            "success": True,
            "record_id": record_id,
            "filename": record.filename,
            "processing_details": processing_details
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取处理详情时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取详情失败: {str(e)}")