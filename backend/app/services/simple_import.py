"""
简化导入服务 - 专注于快速导入大数据量文件
"""

import pandas as pd
import io
from datetime import datetime, date
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.simple_import import StockConceptData, StockTimeseriesData, ImportTask, FileType, ImportStatus


class SimpleImportService:
    """简化导入服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def import_csv_file(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        导入CSV文件 (股票概念数据)
        格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
        """
        import_task = ImportTask(
            file_name=filename,
            file_type='csv',  # 直接使用字符串值
            file_size=len(content),
            start_time=datetime.now(),
            status='processing'  # 直接使用字符串值
        )
        self.db.add(import_task)
        self.db.commit()
        self.db.refresh(import_task)
        
        try:
            # 解析CSV
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            total_rows = len(df)
            
            # 更新总行数
            import_task.total_rows = total_rows
            self.db.commit()
            
            success_rows = 0
            error_rows = 0
            import_date = date.today()
            
            # 批量插入数据
            batch_data = []
            batch_size = 1000  # 每批处理1000条
            
            for index, row in df.iterrows():
                try:
                    # 清理数据
                    stock_code = str(row.get('股票代码', '')).strip()
                    stock_name = str(row.get('股票名称', '')).strip()
                    
                    if not stock_code or not stock_name or stock_code == 'nan' or stock_name == 'nan':
                        error_rows += 1
                        continue
                    
                    # 准备数据
                    data_item = {
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'page_count': self._safe_int(row.get('全部页数', 0)),
                        'total_reads': self._safe_int(row.get('热帖首页页阅读总数', 0)),
                        'price': self._safe_float(row.get('价格', 0)),
                        'industry': self._safe_str(row.get('行业')),
                        'concept': self._safe_str(row.get('概念')),
                        'turnover_rate': self._safe_float(row.get('换手', 0)),
                        'net_inflow': self._safe_float(row.get('净流入', 0)),
                        'import_date': import_date,
                        'created_at': datetime.now()
                    }
                    
                    batch_data.append(data_item)
                    success_rows += 1
                    
                    # 批量插入
                    if len(batch_data) >= batch_size:
                        self._batch_insert_concept_data(batch_data)
                        batch_data = []
                        
                        # 更新进度
                        import_task.success_rows = success_rows
                        import_task.error_rows = error_rows
                        self.db.commit()
                        
                        print(f"📊 已处理 {success_rows + error_rows}/{total_rows} 行")
                        
                except Exception as e:
                    error_rows += 1
                    print(f"行 {index + 1} 处理错误: {str(e)}")
            
            # 处理剩余数据
            if batch_data:
                self._batch_insert_concept_data(batch_data)
            
            # 更新任务状态
            import_task.success_rows = success_rows
            import_task.error_rows = error_rows
            import_task.status = 'completed'
            import_task.end_time = datetime.now()
            self.db.commit()
            
            return {
                "task_id": import_task.id,
                "success": True,
                "total_rows": total_rows,
                "success_rows": success_rows,
                "error_rows": error_rows,
                "message": f"CSV文件导入完成：成功{success_rows}条，失败{error_rows}条"
            }
            
        except Exception as e:
            # 更新任务失败状态
            import_task.status = 'failed'
            import_task.error_message = str(e)
            import_task.end_time = datetime.now()
            self.db.commit()
            
            raise Exception(f"CSV导入失败: {str(e)}")
    
    async def import_txt_file(self, content: bytes, filename: str) -> Dict[str, Any]:
        """
        导入TXT文件 (股票时间序列数据)
        格式: 股票代码\t日期\t数值
        """
        import_task = ImportTask(
            file_name=filename,
            file_type='txt',  # 直接使用字符串值
            file_size=len(content),
            start_time=datetime.now(),
            status='processing'  # 直接使用字符串值
        )
        self.db.add(import_task)
        self.db.commit()
        self.db.refresh(import_task)
        
        try:
            # 解析TXT内容
            text_content = content.decode('utf-8')
            lines = text_content.strip().split('\n')
            total_rows = len(lines)
            
            # 更新总行数
            import_task.total_rows = total_rows
            self.db.commit()
            
            success_rows = 0
            error_rows = 0
            import_date = date.today()
            
            # 批量插入数据
            batch_data = []
            batch_size = 5000  # TXT文件数据量大，增大批次
            
            for line_num, line in enumerate(lines, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 分割数据：股票代码\t日期\t数值
                    parts = line.split('\t')
                    if len(parts) != 3:
                        error_rows += 1
                        continue
                    
                    stock_code = parts[0].strip()
                    trade_date_str = parts[1].strip()
                    value_str = parts[2].strip()
                    
                    # 验证和转换数据
                    if not stock_code:
                        error_rows += 1
                        continue
                    
                    # 去除股票代码前缀（如SH、SZ）
                    if stock_code.startswith(('SH', 'SZ')):
                        stock_code = stock_code[2:]
                    
                    try:
                        trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()
                        value = float(value_str)
                    except ValueError:
                        error_rows += 1
                        continue
                    
                    # 准备数据
                    data_item = {
                        'stock_code': stock_code,
                        'trade_date': trade_date,
                        'value': value,
                        'import_date': import_date,
                        'created_at': datetime.now()
                    }
                    
                    batch_data.append(data_item)
                    success_rows += 1
                    
                    # 批量插入
                    if len(batch_data) >= batch_size:
                        self._batch_insert_timeseries_data(batch_data)
                        batch_data = []
                        
                        # 更新进度
                        import_task.success_rows = success_rows
                        import_task.error_rows = error_rows
                        self.db.commit()
                        
                        if success_rows % 50000 == 0:  # 每5万条打印一次进度
                            print(f"📊 已处理 {success_rows + error_rows}/{total_rows} 行")
                        
                except Exception as e:
                    error_rows += 1
                    if error_rows % 10000 == 0:  # 避免日志过多
                        print(f"行 {line_num} 处理错误: {str(e)}")
            
            # 处理剩余数据
            if batch_data:
                self._batch_insert_timeseries_data(batch_data)
            
            # 更新任务状态
            import_task.success_rows = success_rows
            import_task.error_rows = error_rows
            import_task.status = 'completed'
            import_task.end_time = datetime.now()
            self.db.commit()
            
            return {
                "task_id": import_task.id,
                "success": True,
                "total_rows": total_rows,
                "success_rows": success_rows,
                "error_rows": error_rows,
                "message": f"TXT文件导入完成：成功{success_rows}条，失败{error_rows}条"
            }
            
        except Exception as e:
            # 更新任务失败状态
            import_task.status = 'failed'
            import_task.error_message = str(e)
            import_task.end_time = datetime.now()
            self.db.commit()
            
            raise Exception(f"TXT导入失败: {str(e)}")
    
    def _batch_insert_concept_data(self, batch_data):
        """批量插入概念数据"""
        try:
            self.db.bulk_insert_mappings(StockConceptData, batch_data)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # 如果批量插入失败，尝试逐条插入
            for data in batch_data:
                try:
                    record = StockConceptData(**data)
                    self.db.add(record)
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    continue
    
    def _batch_insert_timeseries_data(self, batch_data):
        """批量插入时间序列数据"""
        try:
            # 使用ON DUPLICATE KEY UPDATE处理重复数据
            self.db.bulk_insert_mappings(StockTimeseriesData, batch_data)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            # 如果批量插入失败，尝试逐条插入
            for data in batch_data:
                try:
                    # 检查是否存在
                    existing = self.db.query(StockTimeseriesData).filter(
                        StockTimeseriesData.stock_code == data['stock_code'],
                        StockTimeseriesData.trade_date == data['trade_date']
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.value = data['value']
                        existing.import_date = data['import_date']
                    else:
                        # 插入新记录
                        record = StockTimeseriesData(**data)
                        self.db.add(record)
                    
                    self.db.commit()
                except Exception:
                    self.db.rollback()
                    continue
    
    def get_import_task_status(self, task_id: int) -> Dict[str, Any]:
        """获取导入任务状态"""
        task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
        if not task:
            return {"error": "任务不存在"}
        
        duration = None
        if task.start_time and task.end_time:
            duration = (task.end_time - task.start_time).total_seconds()
        
        return {
            "task_id": task.id,
            "file_name": task.file_name,
            "file_type": task.file_type,
            "file_size": task.file_size,
            "total_rows": task.total_rows,
            "success_rows": task.success_rows,
            "error_rows": task.error_rows,
            "status": task.status,
            "error_message": task.error_message,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "duration_seconds": duration,
            "progress_percent": round((task.success_rows + task.error_rows) / task.total_rows * 100, 2) if task.total_rows > 0 else 0
        }
    
    @staticmethod
    def _safe_int(value) -> int:
        """安全转换整数"""
        try:
            if pd.isna(value) or value == 'None':
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _safe_float(value) -> float:
        """安全转换浮点数"""
        try:
            if pd.isna(value) or value == 'None':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def _safe_str(value) -> str:
        """安全转换字符串"""
        try:
            if pd.isna(value) or value == 'None':
                return ''
            return str(value).strip()
        except (ValueError, TypeError):
            return ''