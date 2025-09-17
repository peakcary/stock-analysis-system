from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.chunked_upload_service import ChunkedUploadService, LargeFileImportService
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
import logging
import tempfile
import os
import hashlib
import aiofiles

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务实例
chunked_service = ChunkedUploadService()

# 全局进度存储
upload_progress = {}

@router.post("/check-file")
async def check_large_file(
    filename: str = Form(...),
    file_size: int = Form(...),
    file_hash: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """检查大文件是否适合分块上传"""
    try:
        # 检查文件大小限制
        max_size_mb = 500
        file_size_mb = file_size / 1024 / 1024

        if file_size_mb > max_size_mb:
            return {
                "success": False,
                "message": f"文件过大 ({file_size_mb:.1f}MB)，超过最大限制 {max_size_mb}MB",
                "requires_chunked_upload": False
            }

        # 大于50MB建议使用分块上传
        requires_chunked = file_size_mb > 50

        return {
            "success": True,
            "file_size_mb": round(file_size_mb, 2),
            "requires_chunked_upload": requires_chunked,
            "recommended_strategy": "chunked" if requires_chunked else "direct",
            "message": f"文件大小: {file_size_mb:.1f}MB, " +
                      ("建议使用分块上传" if requires_chunked else "可以直接上传")
        }

    except Exception as e:
        logger.error(f"检查大文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")

@router.post("/initiate-chunked-upload")
async def initiate_chunked_upload(
    filename: str = Form(...),
    file_size: int = Form(...),
    file_hash: str = Form(...),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """初始化分块上传"""
    try:
        result = await chunked_service.initiate_upload(filename, file_size, file_hash)

        # 初始化进度跟踪
        upload_id = result["upload_id"]
        upload_progress[upload_id] = {
            "status": "initiated",
            "filename": filename,
            "file_size": file_size,
            "uploaded_chunks": 0,
            "total_chunks": result["total_chunks"],
            "progress_percent": 0,
            "imported_by": current_admin.username,
            "start_time": __import__('datetime').datetime.now().isoformat()
        }

        return {
            "success": True,
            "upload_id": upload_id,
            "chunk_size": result["chunk_size"],
            "total_chunks": result["total_chunks"],
            "message": "分块上传初始化成功"
        }

    except Exception as e:
        logger.error(f"初始化分块上传时出错: {e}")
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

@router.post("/upload-chunk")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_number: int = Form(...),
    chunk: UploadFile = File(...),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """上传单个分块"""
    try:
        # 检查上传会话
        if upload_id not in upload_progress:
            raise HTTPException(status_code=404, detail="上传会话不存在")

        progress_info = upload_progress[upload_id]

        # 检查权限
        if progress_info["imported_by"] != current_admin.username:
            raise HTTPException(status_code=403, detail="无权限访问此上传")

        # 读取分块数据
        chunk_data = await chunk.read()

        # 上传分块
        result = await chunked_service.upload_chunk(upload_id, chunk_number, chunk_data)

        # 更新进度
        progress_info["uploaded_chunks"] += 1
        progress_info["progress_percent"] = (progress_info["uploaded_chunks"] / progress_info["total_chunks"]) * 100
        progress_info["last_update"] = __import__('datetime').datetime.now().isoformat()

        return {
            "success": True,
            "chunk_number": chunk_number,
            "uploaded_chunks": progress_info["uploaded_chunks"],
            "total_chunks": progress_info["total_chunks"],
            "progress_percent": progress_info["progress_percent"]
        }

    except Exception as e:
        logger.error(f"上传分块时出错: {e}")
        raise HTTPException(status_code=500, detail=f"上传分块失败: {str(e)}")

@router.post("/complete-chunked-upload")
async def complete_chunked_upload(
    background_tasks: BackgroundTasks,
    upload_id: str = Form(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """完成分块上传并开始处理"""
    try:
        # 检查上传会话
        if upload_id not in upload_progress:
            raise HTTPException(status_code=404, detail="上传会话不存在")

        progress_info = upload_progress[upload_id]

        # 检查权限
        if progress_info["imported_by"] != current_admin.username:
            raise HTTPException(status_code=403, detail="无权限访问此上传")

        # 检查是否所有分块都已上传
        if progress_info["uploaded_chunks"] != progress_info["total_chunks"]:
            raise HTTPException(
                status_code=400,
                detail=f"分块上传未完成: {progress_info['uploaded_chunks']}/{progress_info['total_chunks']}"
            )

        filename = progress_info["filename"]

        # 合并分块
        final_file_path = await chunked_service.complete_upload(upload_id, filename)

        # 更新状态
        progress_info["status"] = "merging_complete"
        progress_info["final_file_path"] = final_file_path

        # 启动后台导入任务
        async def background_import():
            try:
                large_file_service = LargeFileImportService(db)

                async def import_progress_callback(stage: str, progress: float, message: str):
                    progress_info["import_stage"] = stage
                    progress_info["import_progress"] = progress
                    progress_info["import_message"] = message
                    progress_info["last_update"] = __import__('datetime').datetime.now().isoformat()

                    if stage == "parsing":
                        progress_info["status"] = "parsing"
                    elif stage == "importing":
                        progress_info["status"] = "importing"

                result = await large_file_service.import_large_file_streaming(
                    final_file_path,
                    filename,
                    current_admin.username,
                    import_progress_callback
                )

                # 保存最终结果
                progress_info["import_result"] = result
                progress_info["status"] = "completed" if result["success"] else "failed"
                progress_info["end_time"] = __import__('datetime').datetime.now().isoformat()

            except Exception as e:
                logger.error(f"大文件导入失败: {e}")
                progress_info["status"] = "failed"
                progress_info["error"] = str(e)
                progress_info["end_time"] = __import__('datetime').datetime.now().isoformat()

        # 添加后台任务
        background_tasks.add_task(background_import)

        return {
            "success": True,
            "upload_id": upload_id,
            "message": "文件合并完成，开始后台导入",
            "status": "processing",
            "progress_url": f"/api/v1/large-file-upload/progress/{upload_id}"
        }

    except Exception as e:
        logger.error(f"完成分块上传时出错: {e}")
        raise HTTPException(status_code=500, detail=f"完成上传失败: {str(e)}")

@router.get("/progress/{upload_id}")
async def get_upload_progress(
    upload_id: str,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取上传和导入进度"""
    if upload_id not in upload_progress:
        raise HTTPException(status_code=404, detail="上传会话不存在")

    progress_info = upload_progress[upload_id]

    # 检查权限
    if progress_info["imported_by"] != current_admin.username:
        raise HTTPException(status_code=403, detail="无权限访问此进度")

    return {
        "success": True,
        "upload_id": upload_id,
        "progress": progress_info
    }

@router.delete("/progress/{upload_id}")
async def cleanup_upload_progress(
    upload_id: str,
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """清理上传进度记录"""
    if upload_id not in upload_progress:
        raise HTTPException(status_code=404, detail="上传会话不存在")

    progress_info = upload_progress[upload_id]

    # 检查权限
    if progress_info["imported_by"] != current_admin.username:
        raise HTTPException(status_code=403, detail="无权限删除此记录")

    # 清理临时文件
    try:
        await chunked_service.cleanup_upload(upload_id)
    except Exception as e:
        logger.warning(f"清理临时文件失败: {e}")

    # 删除进度记录
    del upload_progress[upload_id]

    return {
        "success": True,
        "message": f"上传记录 {upload_id} 已清理"
    }

@router.get("/active-uploads")
async def list_active_uploads(
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """列出当前用户的活跃上传"""
    user_uploads = {
        upload_id: progress
        for upload_id, progress in upload_progress.items()
        if progress.get("imported_by") == current_admin.username
    }

    return {
        "success": True,
        "uploads": user_uploads,
        "count": len(user_uploads)
    }

@router.post("/direct-large-upload")
async def direct_large_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """直接上传大文件（适用于50-100MB文件）"""
    try:
        # 检查文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")

        # 生成临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='large_upload_')

        try:
            # 流式保存文件
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                while True:
                    chunk = await file.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    await temp_file.write(chunk)

            os.close(temp_fd)

            # 生成上传ID用于跟踪进度
            upload_id = hashlib.md5(f"{file.filename}_{current_admin.username}_{__import__('datetime').datetime.now()}".encode()).hexdigest()

            # 初始化进度跟踪
            upload_progress[upload_id] = {
                "status": "processing",
                "filename": file.filename,
                "file_size": os.path.getsize(temp_path),
                "imported_by": current_admin.username,
                "start_time": __import__('datetime').datetime.now().isoformat(),
                "upload_type": "direct"
            }

            # 启动后台处理
            async def background_process():
                try:
                    large_file_service = LargeFileImportService(db)

                    async def import_progress_callback(stage: str, progress: float, message: str):
                        upload_progress[upload_id]["import_stage"] = stage
                        upload_progress[upload_id]["import_progress"] = progress
                        upload_progress[upload_id]["import_message"] = message
                        upload_progress[upload_id]["last_update"] = __import__('datetime').datetime.now().isoformat()

                    result = await large_file_service.import_large_file_streaming(
                        temp_path,
                        file.filename,
                        current_admin.username,
                        import_progress_callback
                    )

                    upload_progress[upload_id]["import_result"] = result
                    upload_progress[upload_id]["status"] = "completed" if result["success"] else "failed"
                    upload_progress[upload_id]["end_time"] = __import__('datetime').datetime.now().isoformat()

                except Exception as e:
                    logger.error(f"大文件直接上传处理失败: {e}")
                    upload_progress[upload_id]["status"] = "failed"
                    upload_progress[upload_id]["error"] = str(e)
                    upload_progress[upload_id]["end_time"] = __import__('datetime').datetime.now().isoformat()

            background_tasks.add_task(background_process)

            return {
                "success": True,
                "upload_id": upload_id,
                "message": "大文件上传成功，开始后台处理",
                "progress_url": f"/api/v1/large-file-upload/progress/{upload_id}"
            }

        except Exception as e:
            os.close(temp_fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"直接上传大文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")