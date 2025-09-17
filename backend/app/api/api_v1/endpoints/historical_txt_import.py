from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.historical_txt_import import HistoricalTxtImportService
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
from datetime import date, datetime
import logging
import asyncio
from fastapi.responses import StreamingResponse
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局进度存储 (生产环境建议使用Redis)
import_progress = {}

@router.post("/preview")
async def preview_historical_file(
    file: UploadFile = File(...),
    preview_lines: int = Query(1000, ge=100, le=10000, description="预览行数"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """预览历史TXT文件内容和导入信息"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')

        # 生成预览
        historical_service = HistoricalTxtImportService(db)
        preview_result = historical_service.get_historical_import_preview(
            txt_content, preview_lines
        )

        if preview_result["success"]:
            return {
                "success": True,
                "filename": file.filename,
                "file_size": len(content),
                "file_size_mb": round(len(content) / 1024 / 1024, 2),
                "preview": preview_result["preview"]
            }
        else:
            raise HTTPException(status_code=400, detail=preview_result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览历史文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@router.post("/import-sync")
async def import_historical_file_sync(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """同步导入历史TXT文件（适用于中小型文件）"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')

        # 执行导入
        historical_service = HistoricalTxtImportService(db)
        result = historical_service.import_historical_data(
            txt_content=txt_content,
            filename=file.filename,
            imported_by=current_admin.username
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"同步导入历史文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.post("/import-async")
async def import_historical_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """异步导入历史TXT文件（适用于大型文件）"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 生成任务ID
        import datetime
        task_id = f"historical_import_{current_admin.username}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')

        # 初始化进度
        import_progress[task_id] = {
            "status": "started",
            "current": 0,
            "total": 0,
            "current_date": "",
            "completed_dates": [],
            "failed_dates": [],
            "start_time": datetime.datetime.now().isoformat(),
            "filename": file.filename,
            "imported_by": current_admin.username
        }

        # 定义进度回调函数
        def progress_callback(current: int, total: int, date_str: str, status: str):
            import_progress[task_id].update({
                "current": current,
                "total": total,
                "current_date": date_str,
                "last_update": datetime.datetime.now().isoformat()
            })

            if status == "success":
                import_progress[task_id]["completed_dates"].append(date_str)
            elif status == "failed":
                import_progress[task_id]["failed_dates"].append(date_str)

            # 如果完成了，更新最终状态
            if current >= total:
                import_progress[task_id]["status"] = "completed"
                import_progress[task_id]["end_time"] = datetime.datetime.now().isoformat()

        # 在后台任务中执行导入
        async def background_import():
            try:
                historical_service = HistoricalTxtImportService(db)
                result = await historical_service.import_historical_data_async(
                    txt_content=txt_content,
                    filename=file.filename,
                    imported_by=current_admin.username,
                    progress_callback=progress_callback
                )

                # 更新最终结果
                import_progress[task_id]["result"] = result
                import_progress[task_id]["status"] = "completed"

            except Exception as e:
                logger.error(f"后台导入任务失败: {e}")
                import_progress[task_id]["status"] = "failed"
                import_progress[task_id]["error"] = str(e)

        # 添加后台任务
        background_tasks.add_task(background_import)

        return {
            "success": True,
            "task_id": task_id,
            "message": "历史数据导入任务已启动",
            "progress_url": f"/api/v1/historical-txt-import/progress/{task_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动异步导入时出错: {e}")
        raise HTTPException(status_code=500, detail=f"启动导入失败: {str(e)}")

@router.get("/progress/{task_id}")
async def get_import_progress(
    task_id: str,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取导入进度"""
    if task_id not in import_progress:
        raise HTTPException(status_code=404, detail="任务不存在")

    progress_info = import_progress[task_id]

    # 检查权限（只能查看自己的任务）
    if progress_info.get("imported_by") != current_admin.username:
        raise HTTPException(status_code=403, detail="无权限查看此任务")

    return {
        "success": True,
        "task_id": task_id,
        "progress": progress_info
    }

@router.get("/progress/{task_id}/stream")
async def stream_import_progress(
    task_id: str,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """流式获取导入进度（Server-Sent Events）"""
    if task_id not in import_progress:
        raise HTTPException(status_code=404, detail="任务不存在")

    progress_info = import_progress[task_id]

    # 检查权限
    if progress_info.get("imported_by") != current_admin.username:
        raise HTTPException(status_code=403, detail="无权限查看此任务")

    async def generate_progress_stream():
        last_update = None

        while True:
            current_progress = import_progress.get(task_id, {})
            current_update = current_progress.get("last_update")

            # 只在有更新时发送数据
            if current_update != last_update:
                yield f"data: {json.dumps(current_progress)}\n\n"
                last_update = current_update

            # 如果任务完成，发送最终数据并结束
            if current_progress.get("status") in ["completed", "failed"]:
                break

            await asyncio.sleep(1)  # 每秒检查一次

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.delete("/progress/{task_id}")
async def clear_import_progress(
    task_id: str,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """清理导入进度记录"""
    if task_id not in import_progress:
        raise HTTPException(status_code=404, detail="任务不存在")

    progress_info = import_progress[task_id]

    # 检查权限
    if progress_info.get("imported_by") != current_admin.username:
        raise HTTPException(status_code=403, detail="无权限删除此任务")

    del import_progress[task_id]

    return {
        "success": True,
        "message": f"任务 {task_id} 的进度记录已清理"
    }

@router.get("/tasks")
async def list_import_tasks(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """列出当前用户的所有导入任务"""
    user_tasks = {
        task_id: progress
        for task_id, progress in import_progress.items()
        if progress.get("imported_by") == current_admin.username
    }

    return {
        "success": True,
        "tasks": user_tasks,
        "count": len(user_tasks)
    }

@router.post("/import-content")
async def import_historical_content(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """通过内容直接导入历史数据"""
    try:
        txt_content = request.get('content', '')
        if not txt_content.strip():
            raise HTTPException(status_code=400, detail="文件内容不能为空")

        # 判断数据规模，选择同步或异步处理
        line_count = len(txt_content.split('\n'))

        if line_count <= 10000:  # 小于1万行使用同步处理
            historical_service = HistoricalTxtImportService(db)
            result = historical_service.import_historical_data(
                txt_content=txt_content,
                filename="uploaded_content.txt",
                imported_by=current_admin.username
            )
            return result
        else:  # 大于1万行使用异步处理
            # 生成任务ID
            import datetime
            task_id = f"historical_content_{current_admin.username}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 初始化进度
            import_progress[task_id] = {
                "status": "started",
                "current": 0,
                "total": 0,
                "current_date": "",
                "completed_dates": [],
                "failed_dates": [],
                "start_time": datetime.datetime.now().isoformat(),
                "filename": "uploaded_content.txt",
                "imported_by": current_admin.username
            }

            # 异步处理
            async def background_import():
                try:
                    def progress_callback(current: int, total: int, date_str: str, status: str):
                        import_progress[task_id].update({
                            "current": current,
                            "total": total,
                            "current_date": date_str,
                            "last_update": datetime.datetime.now().isoformat()
                        })

                    historical_service = HistoricalTxtImportService(db)
                    result = await historical_service.import_historical_data_async(
                        txt_content=txt_content,
                        filename="uploaded_content.txt",
                        imported_by=current_admin.username,
                        progress_callback=progress_callback
                    )

                    import_progress[task_id]["result"] = result
                    import_progress[task_id]["status"] = "completed"

                except Exception as e:
                    logger.error(f"内容导入任务失败: {e}")
                    import_progress[task_id]["status"] = "failed"
                    import_progress[task_id]["error"] = str(e)

            background_tasks.add_task(background_import)

            return {
                "success": True,
                "task_id": task_id,
                "message": f"大文件内容导入任务已启动（{line_count} 行）",
                "progress_url": f"/api/v1/historical-txt-import/progress/{task_id}"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入历史内容时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

# 定期清理超过24小时的进度记录
@router.post("/cleanup-old-tasks")
async def cleanup_old_tasks(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """清理超过24小时的旧任务记录"""
    if current_admin.username != "admin":  # 只有管理员可以执行清理
        raise HTTPException(status_code=403, detail="需要管理员权限")

    from datetime import datetime, timedelta
    cutoff_time = datetime.now() - timedelta(hours=24)

    cleaned_count = 0
    to_remove = []

    for task_id, progress in import_progress.items():
        start_time_str = progress.get("start_time")
        if start_time_str:
            start_time = datetime.fromisoformat(start_time_str)
            if start_time < cutoff_time:
                to_remove.append(task_id)

    for task_id in to_remove:
        del import_progress[task_id]
        cleaned_count += 1

    return {
        "success": True,
        "message": f"已清理 {cleaned_count} 个超过24小时的旧任务记录"
    }