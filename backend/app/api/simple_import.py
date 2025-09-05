"""
简化导入API接口
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.simple_import import SimpleImportService
from typing import Dict, Any, Optional
import asyncio

router = APIRouter()


@router.post("/simple-csv")
async def import_csv_simple(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    replace_mode: Optional[str] = Form("update"),
    db: Session = Depends(get_db)
):
    """
    简化CSV导入接口
    
    Parameters:
    - file: CSV文件
    - replace_mode: 重复数据处理模式
        - "update": 更新模式，相同导入日期的数据会被更新（默认）
        - "append": 追加模式，允许重复数据
        - "replace": 替换模式，删除当天所有数据后重新导入
        - "sync": 同步模式，与文件内容完全同步，删除文件中不存在的记录
    """
    
    # 验证重复处理模式
    if replace_mode not in ["update", "append", "replace", "sync"]:
        raise HTTPException(status_code=400, detail="replace_mode必须是update、append、replace或sync")
    
    # 验证文件格式
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="文件必须是CSV格式")
    
    # 验证文件大小 (最大50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    print(f"📄 开始处理CSV文件: {file.filename}, 大小: {len(content)} bytes, 模式: {replace_mode}")
    
    try:
        # 创建导入服务实例
        import_service = SimpleImportService(db)
        
        # 执行导入
        result = await import_service.import_csv_file(content, file.filename, replace_mode)
        
        return {
            "success": True,
            "message": "CSV文件导入完成",
            "data": result
        }
        
    except Exception as e:
        print(f"❌ CSV导入异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/simple-txt")
async def import_txt_simple(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    replace_mode: Optional[str] = Form("update"),
    db: Session = Depends(get_db)
):
    """
    简化TXT导入接口
    
    Parameters:
    - file: TXT文件
    - replace_mode: 重复数据处理模式
        - "update": 更新模式，相同股票代码+日期的数据会被更新（默认）
        - "append": 追加模式，允许重复数据
        - "replace": 替换模式，删除指定日期的所有数据后重新导入
    """
    
    # 验证重复处理模式
    if replace_mode not in ["update", "append", "replace", "sync"]:
        raise HTTPException(status_code=400, detail="replace_mode必须是update、append、replace或sync")
    
    # 验证文件格式
    if not file.filename or not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="文件必须是TXT格式")
    
    # 验证文件大小 (最大100MB)
    content = await file.read()
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过100MB")
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    print(f"📄 开始处理TXT文件: {file.filename}, 大小: {len(content)} bytes, 模式: {replace_mode}")
    
    try:
        # 创建导入服务实例
        import_service = SimpleImportService(db)
        
        # 执行导入
        result = await import_service.import_txt_file(content, file.filename, replace_mode)
        
        return {
            "success": True,
            "message": "TXT文件导入完成", 
            "data": result
        }
        
    except Exception as e:
        print(f"❌ TXT导入异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/task/{task_id}")
async def get_import_task_status(
    task_id: int,
    db: Session = Depends(get_db)
):
    """获取导入任务状态"""
    
    try:
        import_service = SimpleImportService(db)
        result = import_service.get_import_task_status(task_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats")
async def get_import_stats(db: Session = Depends(get_db)):
    """获取导入统计信息"""
    
    try:
        from app.models.simple_import import StockConceptData, StockTimeseriesData, ImportTask
        
        # 统计数据
        concept_count = db.query(StockConceptData).count()
        timeseries_count = db.query(StockTimeseriesData).count()
        task_count = db.query(ImportTask).count()
        
        # 最近任务
        recent_tasks = db.query(ImportTask).order_by(ImportTask.created_at.desc()).limit(5).all()
        
        tasks_info = []
        for task in recent_tasks:
            tasks_info.append({
                "id": task.id,
                "file_name": task.file_name,
                "file_type": task.file_type,
                "status": task.status,
                "success_rows": task.success_rows,
                "created_at": task.created_at.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "concept_data_count": concept_count,
                "timeseries_data_count": timeseries_count,
                "total_tasks": task_count,
                "recent_tasks": tasks_info
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")