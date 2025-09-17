from typing import List, Dict, Optional, Tuple, Generator
from sqlalchemy.orm import Session
from app.models.daily_trading import (
    DailyTrading, ConceptDailySummary,
    StockConceptRanking, ConceptHighRecord, TxtImportRecord
)
from app.services.txt_import import TxtImportService
from datetime import datetime, date
import logging
import time
import tempfile
import os
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class HistoricalTxtImportService:
    """历史多日期TXT文件导入服务"""

    def __init__(self, db: Session):
        self.db = db
        self.txt_service = TxtImportService(db)
        self.batch_size = 10000  # 每批处理的行数
        self.max_workers = 3  # 并发处理线程数

    def parse_large_txt_by_date(self, txt_content: str) -> Dict[str, List[str]]:
        """
        按日期分组解析大型TXT文件

        Args:
            txt_content: 完整的TXT文件内容

        Returns:
            Dict[date_str, List[line]]: 按日期分组的数据行
        """
        date_groups = defaultdict(list)
        lines = txt_content.strip().split('\n')

        logger.info(f"开始解析包含 {len(lines)} 行的历史数据文件")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            try:
                parts = line.split('\t')
                if len(parts) != 3:
                    logger.warning(f"第{line_num}行格式不正确: {line}")
                    continue

                stock_code, date_str, volume_str = parts

                # 验证日期格式
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"第{line_num}行日期格式错误: {date_str}")
                    continue

                # 按日期分组
                date_groups[date_str].append(line)

            except Exception as e:
                logger.error(f"解析第{line_num}行时出错: {line}, 错误: {e}")
                continue

        logger.info(f"文件解析完成，共发现 {len(date_groups)} 个不同的交易日期")
        for date_str, lines in date_groups.items():
            logger.info(f"  {date_str}: {len(lines)} 条记录")

        return dict(date_groups)

    def stream_parse_large_txt(self, file_path: str, chunk_size: int = 8192) -> Generator[Tuple[str, str], None, None]:
        """
        流式解析大文件，逐行返回 (date, line) 元组

        Args:
            file_path: 文件路径
            chunk_size: 读取块大小

        Yields:
            Tuple[date_str, line]: 日期和对应的数据行
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            buffer = ""
            line_num = 0

            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    # 处理最后的缓冲区内容
                    if buffer.strip():
                        lines = buffer.split('\n')
                        for line in lines:
                            if line.strip():
                                line_num += 1
                                result = self._parse_line(line.strip(), line_num)
                                if result:
                                    yield result
                    break

                buffer += chunk

                # 处理完整的行
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        line_num += 1
                        result = self._parse_line(line.strip(), line_num)
                        if result:
                            yield result

    def _parse_line(self, line: str, line_num: int) -> Optional[Tuple[str, str]]:
        """解析单行数据，返回 (date, line) 或 None"""
        try:
            parts = line.split('\t')
            if len(parts) != 3:
                return None

            stock_code, date_str, volume_str = parts

            # 验证日期格式
            datetime.strptime(date_str, '%Y-%m-%d')

            return date_str, line

        except Exception as e:
            logger.warning(f"第{line_num}行解析失败: {line}, 错误: {e}")
            return None

    def create_temp_files_by_date(self, txt_content: str) -> Dict[str, str]:
        """
        将大文件按日期分割为临时文件

        Args:
            txt_content: 完整文件内容

        Returns:
            Dict[date_str, temp_file_path]: 日期到临时文件路径的映射
        """
        temp_files = {}
        date_groups = self.parse_large_txt_by_date(txt_content)

        for date_str, lines in date_groups.items():
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix=f'_{date_str}.txt', prefix='historical_')

            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                    temp_file.write('\n'.join(lines))
                temp_files[date_str] = temp_path
                logger.info(f"创建临时文件 {temp_path} for {date_str}")

            except Exception as e:
                logger.error(f"创建临时文件失败 for {date_str}: {e}")
                os.close(temp_fd)
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        return temp_files

    def import_historical_data(self, txt_content: str, filename: str = "historical.txt",
                             imported_by: str = "system",
                             progress_callback: Optional[callable] = None) -> Dict:
        """
        导入历史多日期数据

        Args:
            txt_content: 文件内容
            filename: 文件名
            imported_by: 导入人
            progress_callback: 进度回调函数 callback(current, total, date_str, status)

        Returns:
            导入结果统计
        """
        start_time = time.time()
        total_results = {
            "success": True,
            "message": "历史数据导入完成",
            "total_dates": 0,
            "success_dates": 0,
            "failed_dates": 0,
            "total_records": 0,
            "date_results": {},
            "failed_dates_detail": []
        }

        try:
            # 1. 按日期分组数据
            logger.info("开始解析历史数据文件...")
            date_groups = self.parse_large_txt_by_date(txt_content)
            total_results["total_dates"] = len(date_groups)

            if not date_groups:
                return {"success": False, "message": "未找到有效的历史数据"}

            # 2. 按日期排序，从早到晚导入
            sorted_dates = sorted(date_groups.keys())
            logger.info(f"将按以下顺序导入 {len(sorted_dates)} 个交易日的数据:")
            for i, date_str in enumerate(sorted_dates[:5]):  # 只显示前5个
                logger.info(f"  {i+1}. {date_str} ({len(date_groups[date_str])} 条记录)")
            if len(sorted_dates) > 5:
                logger.info(f"  ... 还有 {len(sorted_dates) - 5} 个日期")

            # 3. 逐日期导入
            for current_idx, date_str in enumerate(sorted_dates, 1):
                date_lines = date_groups[date_str]

                # 调用进度回调
                if progress_callback:
                    progress_callback(current_idx, len(sorted_dates), date_str, "processing")

                try:
                    # 构造单日数据内容
                    single_date_content = '\n'.join(date_lines)

                    # 使用现有的单日导入服务
                    result = self.txt_service.import_daily_trading(
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
                        logger.info(f"✅ {date_str} 导入成功: {result['stats']['trading_data_count']} 条记录")
                    else:
                        total_results["failed_dates"] += 1
                        total_results["date_results"][date_str] = {
                            "success": False,
                            "message": result["message"]
                        }
                        total_results["failed_dates_detail"].append({
                            "date": date_str,
                            "error": result["message"]
                        })
                        logger.error(f"❌ {date_str} 导入失败: {result['message']}")

                    # 调用进度回调
                    if progress_callback:
                        status = "success" if result["success"] else "failed"
                        progress_callback(current_idx, len(sorted_dates), date_str, status)

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

                    if progress_callback:
                        progress_callback(current_idx, len(sorted_dates), date_str, "failed")

            # 4. 生成最终结果
            end_time = time.time()
            total_time = round(end_time - start_time, 2)

            if total_results["failed_dates"] > 0:
                total_results["success"] = False
                total_results["message"] = f"部分导入失败: {total_results['success_dates']}/{total_results['total_dates']} 个日期成功"

            total_results["total_time"] = total_time

            logger.info(f"历史数据导入完成:")
            logger.info(f"  总日期数: {total_results['total_dates']}")
            logger.info(f"  成功: {total_results['success_dates']}")
            logger.info(f"  失败: {total_results['failed_dates']}")
            logger.info(f"  总记录数: {total_results['total_records']}")
            logger.info(f"  总耗时: {total_time} 秒")

            return total_results

        except Exception as e:
            logger.error(f"历史数据导入过程中发生严重错误: {e}")
            return {
                "success": False,
                "message": f"导入过程发生严重错误: {str(e)}",
                "total_time": round(time.time() - start_time, 2)
            }

    async def import_historical_data_async(self, txt_content: str, filename: str = "historical.txt",
                                         imported_by: str = "system",
                                         progress_callback: Optional[callable] = None) -> Dict:
        """
        异步导入历史数据（用于大文件处理）

        Args:
            txt_content: 文件内容
            filename: 文件名
            imported_by: 导入人
            progress_callback: 进度回调函数

        Returns:
            导入结果统计
        """
        loop = asyncio.get_event_loop()

        # 在线程池中执行导入操作
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self.import_historical_data,
                txt_content,
                filename,
                imported_by,
                progress_callback
            )

        return result

    def get_historical_import_preview(self, txt_content: str, preview_lines: int = 1000) -> Dict:
        """
        预览历史文件的导入情况

        Args:
            txt_content: 文件内容
            preview_lines: 预览行数

        Returns:
            预览信息
        """
        try:
            lines = txt_content.strip().split('\n')
            preview_content = '\n'.join(lines[:preview_lines])

            date_groups = self.parse_large_txt_by_date(preview_content)

            total_lines = len(lines)
            preview_stats = {
                "total_lines": total_lines,
                "preview_lines": min(preview_lines, total_lines),
                "estimated_dates": len(date_groups),
                "date_preview": {}
            }

            # 生成日期预览
            for date_str, date_lines in sorted(date_groups.items()):
                preview_stats["date_preview"][date_str] = {
                    "count": len(date_lines),
                    "sample_lines": date_lines[:3]  # 显示前3行作为样本
                }

            # 如果是部分预览，估算总日期数
            if total_lines > preview_lines:
                estimated_total_dates = int(len(date_groups) * (total_lines / preview_lines))
                preview_stats["estimated_total_dates"] = estimated_total_dates

            return {
                "success": True,
                "preview": preview_stats
            }

        except Exception as e:
            logger.error(f"生成历史文件预览失败: {e}")
            return {
                "success": False,
                "message": f"预览生成失败: {str(e)}"
            }

    def cleanup_temp_files(self, temp_files: Dict[str, str]):
        """清理临时文件"""
        for date_str, temp_path in temp_files.items():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    logger.debug(f"清理临时文件: {temp_path}")
            except Exception as e:
                logger.error(f"清理临时文件失败 {temp_path}: {e}")