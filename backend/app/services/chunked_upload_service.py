from typing import List, Dict, Optional, BinaryIO
from fastapi import UploadFile
from sqlalchemy.orm import Session
import os
import tempfile
import hashlib
import logging
from pathlib import Path
import aiofiles
import asyncio

logger = logging.getLogger(__name__)

class ChunkedUploadService:
    """分块上传服务 - 处理大文件上传"""

    def __init__(self, upload_dir: str = "/tmp/stock_uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.chunk_size = 1024 * 1024  # 1MB 分块大小
        self.max_file_size = 500 * 1024 * 1024  # 最大文件大小 500MB

    async def initiate_upload(self, filename: str, file_size: int,
                            file_hash: str) -> Dict[str, any]:
        """初始化分块上传"""
        if file_size > self.max_file_size:
            raise ValueError(f"文件大小超过限制 ({self.max_file_size / 1024 / 1024:.0f}MB)")

        upload_id = hashlib.md5(f"{filename}_{file_size}_{file_hash}".encode()).hexdigest()
        upload_path = self.upload_dir / upload_id
        upload_path.mkdir(exist_ok=True)

        # 计算需要的分块数
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size

        return {
            "upload_id": upload_id,
            "chunk_size": self.chunk_size,
            "total_chunks": total_chunks,
            "upload_path": str(upload_path)
        }

    async def upload_chunk(self, upload_id: str, chunk_number: int,
                          chunk_data: bytes) -> Dict[str, any]:
        """上传单个分块"""
        upload_path = self.upload_dir / upload_id
        if not upload_path.exists():
            raise ValueError("上传会话不存在")

        chunk_file = upload_path / f"chunk_{chunk_number:06d}"

        async with aiofiles.open(chunk_file, 'wb') as f:
            await f.write(chunk_data)

        return {
            "chunk_number": chunk_number,
            "chunk_size": len(chunk_data),
            "status": "uploaded"
        }

    async def complete_upload(self, upload_id: str, filename: str) -> str:
        """完成上传，合并所有分块"""
        upload_path = self.upload_dir / upload_id
        if not upload_path.exists():
            raise ValueError("上传会话不存在")

        # 获取所有分块文件
        chunk_files = sorted(upload_path.glob("chunk_*"))

        # 合并文件
        final_file = upload_path / filename
        async with aiofiles.open(final_file, 'wb') as output_file:
            for chunk_file in chunk_files:
                async with aiofiles.open(chunk_file, 'rb') as input_file:
                    while True:
                        data = await input_file.read(8192)
                        if not data:
                            break
                        await output_file.write(data)

        # 清理分块文件
        for chunk_file in chunk_files:
            chunk_file.unlink()

        return str(final_file)

    async def cleanup_upload(self, upload_id: str):
        """清理上传临时文件"""
        upload_path = self.upload_dir / upload_id
        if upload_path.exists():
            import shutil
            shutil.rmtree(upload_path)


class StreamingTxtProcessor:
    """流式TXT文件处理器 - 避免内存溢出"""

    def __init__(self, chunk_size: int = 64 * 1024):  # 64KB 读取块
        self.chunk_size = chunk_size

    async def process_large_file(self, file_path: str,
                               progress_callback: Optional[callable] = None) -> Dict:
        """流式处理大型TXT文件"""
        total_size = os.path.getsize(file_path)
        processed_size = 0
        date_groups = {}
        line_count = 0
        error_count = 0

        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            buffer = ""

            while True:
                chunk = await file.read(self.chunk_size)
                if not chunk:
                    # 处理最后的缓冲区
                    if buffer.strip():
                        lines = buffer.split('\n')
                        for line in lines:
                            if line.strip():
                                result = self._process_line(line.strip(), line_count)
                                if result:
                                    date_str, processed_line = result
                                    if date_str not in date_groups:
                                        date_groups[date_str] = []
                                    date_groups[date_str].append(processed_line)
                                    line_count += 1
                                else:
                                    error_count += 1
                    break

                buffer += chunk
                processed_size += len(chunk.encode('utf-8'))

                # 处理完整的行
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        result = self._process_line(line.strip(), line_count)
                        if result:
                            date_str, processed_line = result
                            if date_str not in date_groups:
                                date_groups[date_str] = []
                            date_groups[date_str].append(processed_line)
                            line_count += 1
                        else:
                            error_count += 1

                # 报告进度
                if progress_callback:
                    progress = (processed_size / total_size) * 100
                    await progress_callback(progress, line_count, len(date_groups))

                # 避免阻塞事件循环
                await asyncio.sleep(0)

        return {
            "date_groups": date_groups,
            "total_lines": line_count,
            "error_lines": error_count,
            "total_dates": len(date_groups)
        }

    def _process_line(self, line: str, line_num: int) -> Optional[tuple]:
        """处理单行数据"""
        try:
            parts = line.split('\t')
            if len(parts) != 3:
                return None

            stock_code, date_str, volume_str = parts

            # 验证日期格式
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')

            # 验证交易量
            try:
                int(float(volume_str))
            except ValueError:
                return None

            return date_str, line

        except Exception as e:
            logger.warning(f"处理第{line_num}行失败: {line}, 错误: {e}")
            return None

    async def save_date_group_to_temp(self, date_str: str, lines: List[str]) -> str:
        """保存单个日期的数据到临时文件"""
        temp_dir = Path("/tmp/stock_date_groups")
        temp_dir.mkdir(exist_ok=True)

        temp_file = temp_dir / f"{date_str}.txt"

        async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
            await f.write('\n'.join(lines))

        return str(temp_file)


class LargeFileImportService:
    """大文件导入服务"""

    def __init__(self, db: Session):
        self.db = db
        self.chunked_upload = ChunkedUploadService()
        self.streaming_processor = StreamingTxtProcessor()

    async def import_large_file_streaming(self, file_path: str,
                                        filename: str = "large_file.txt",
                                        imported_by: str = "system",
                                        progress_callback: Optional[callable] = None) -> Dict:
        """流式导入大文件"""
        from app.services.historical_txt_import import HistoricalTxtImportService

        try:
            # 第一阶段：流式解析文件
            logger.info(f"开始流式解析大文件: {filename}")

            async def parse_progress(progress, line_count, date_count):
                if progress_callback:
                    await progress_callback("parsing", progress, f"已解析 {line_count} 行，发现 {date_count} 个日期")

            parse_result = await self.streaming_processor.process_large_file(
                file_path, parse_progress
            )

            if not parse_result["date_groups"]:
                return {"success": False, "message": "未找到有效数据"}

            # 第二阶段：逐日期导入
            logger.info(f"开始逐日期导入，共 {parse_result['total_dates']} 个日期")

            historical_service = HistoricalTxtImportService(self.db)
            total_results = {
                "success": True,
                "message": "大文件流式导入完成",
                "total_dates": parse_result['total_dates'],
                "success_dates": 0,
                "failed_dates": 0,
                "total_records": 0,
                "date_results": {},
                "failed_dates_detail": []
            }

            # 按日期排序导入
            sorted_dates = sorted(parse_result["date_groups"].keys())

            for current_idx, date_str in enumerate(sorted_dates, 1):
                date_lines = parse_result["date_groups"][date_str]

                if progress_callback:
                    await progress_callback("importing",
                                          (current_idx / len(sorted_dates)) * 100,
                                          f"正在导入 {date_str} ({len(date_lines)} 条记录)")

                try:
                    # 构造单日数据内容
                    single_date_content = '\n'.join(date_lines)

                    # 使用现有的单日导入服务
                    result = historical_service.import_daily_trading(
                        txt_content=single_date_content,
                        filename=f"{filename}_{date_str}",
                        file_size=len(single_date_content.encode('utf-8')),
                        imported_by=imported_by
                    )

                    if result["success"]:
                        total_results["success_dates"] += 1
                        total_results["total_records"] += result["stats"]["trading_data_count"]
                        total_results["date_results"][date_str] = {
                            "success": True,
                            "stats": result["stats"]
                        }
                    else:
                        total_results["failed_dates"] += 1
                        total_results["date_results"][date_str] = {
                            "success": False,
                            "message": result["message"]
                        }

                except Exception as e:
                    total_results["failed_dates"] += 1
                    error_msg = f"导入 {date_str} 时发生异常: {str(e)}"
                    total_results["date_results"][date_str] = {
                        "success": False,
                        "message": error_msg
                    }
                    total_results["failed_dates_detail"].append({
                        "date": date_str,
                        "error": error_msg
                    })
                    logger.error(error_msg)

            # 清理临时文件
            try:
                os.unlink(file_path)
            except:
                pass

            if total_results["failed_dates"] > 0:
                total_results["success"] = False
                total_results["message"] = f"部分导入失败: {total_results['success_dates']}/{total_results['total_dates']} 个日期成功"

            return total_results

        except Exception as e:
            logger.error(f"大文件流式导入失败: {e}")
            return {
                "success": False,
                "message": f"导入失败: {str(e)}"
            }