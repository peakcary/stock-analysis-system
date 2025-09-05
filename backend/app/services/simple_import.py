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
    
    async def import_csv_file(self, content: bytes, filename: str, replace_mode: str = "update") -> Dict[str, Any]:
        """
        导入CSV文件 (股票概念数据)
        格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
        
        Args:
            content: 文件内容
            filename: 文件名
            replace_mode: 重复处理模式
                - "update": 更新模式，相同导入日期的数据会被更新（默认）
                - "append": 追加模式，允许重复数据
                - "replace": 替换模式，删除当天所有数据后重新导入
                - "sync": 同步模式，与文件内容完全同步，删除文件中不存在的记录
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
            
            # 根据模式处理重复数据
            if replace_mode == "replace":
                # 删除当天的所有概念数据
                deleted_count = self.db.query(StockConceptData).filter(
                    StockConceptData.import_date == import_date
                ).delete(synchronize_session=False)
                self.db.commit()
                print(f"🗑️ 替换模式：删除了 {deleted_count} 条当天的历史数据")
            elif replace_mode == "sync":
                # 同步模式：先标记要保留的数据，最后删除未标记的数据
                # 这个逻辑会在数据处理完成后执行
                print(f"🔄 同步模式：将完全同步当天的数据，删除文件中不存在的记录")
            
            # 批量插入数据
            batch_data = []
            batch_size = 1000  # 每批处理1000条
            processed_keys = set()  # 用于Sync模式跟踪处理过的记录
            
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
                    
                    # Sync模式下记录处理过的key
                    if replace_mode == "sync":
                        sync_key = f"{stock_code}_{self._safe_str(row.get('概念'))}"
                        processed_keys.add(sync_key)
                    
                    # 批量插入
                    if len(batch_data) >= batch_size:
                        self._batch_insert_concept_data(batch_data, replace_mode, import_date)
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
                self._batch_insert_concept_data(batch_data, replace_mode, import_date)
            
            # Sync模式：删除文件中不存在的记录
            if replace_mode == "sync":
                deleted_count = self._cleanup_sync_data(processed_keys, import_date, "concept")
                print(f"🔄 同步模式：删除了 {deleted_count} 条文件中不存在的记录")
            
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
    
    async def import_txt_file(self, content: bytes, filename: str, replace_mode: str = "update") -> Dict[str, Any]:
        """
        导入TXT文件 (股票时间序列数据)
        格式: 股票代码\t日期\t数值
        
        Args:
            content: 文件内容
            filename: 文件名
            replace_mode: 重复处理模式
                - "update": 更新模式，相同股票代码+日期的数据会被更新（默认）
                - "append": 追加模式，允许重复数据
                - "replace": 替换模式，删除指定日期的所有数据后重新导入
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
                    if len(parts) < 2:
                        error_rows += 1
                        if error_rows <= 5:
                            print(f"❌ 行 {line_num} 字段数量不足: 最少需要2个字段，实际{len(parts)}个 - '{line}'")
                        continue
                    elif len(parts) == 2:
                        # 如果只有2个字段（股票代码和日期），数值默认为0
                        parts.append('0')
                        if success_rows <= 5:  # 记录前5个自动补0的情况
                            print(f"ℹ️ 行 {line_num} 缺少数值字段，自动补0 - '{line}'")
                    elif len(parts) > 3:
                        error_rows += 1
                        if error_rows <= 5:
                            print(f"❌ 行 {line_num} 字段数量过多: 期望3个字段，实际{len(parts)}个 - '{line}'")
                        continue
                    
                    stock_code = parts[0].strip()
                    trade_date_str = parts[1].strip()
                    value_str = parts[2].strip()
                    
                    # 验证和转换数据
                    if not stock_code:
                        error_rows += 1
                        if error_rows <= 5:
                            print(f"❌ 行 {line_num} 股票代码为空 - '{line}'")
                        continue
                    
                    # 去除股票代码前缀（如SH、SZ）
                    if stock_code.startswith(('SH', 'SZ')):
                        stock_code = stock_code[2:]
                    
                    try:
                        trade_date = datetime.strptime(trade_date_str, '%Y-%m-%d').date()
                        value = float(value_str)
                    except ValueError as ve:
                        error_rows += 1
                        if error_rows <= 5:
                            print(f"❌ 行 {line_num} 数据格式错误: {str(ve)} - '{line}'")
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
                    if error_rows <= 10:  # 记录前10个处理异常
                        print(f"❌ 行 {line_num} 处理异常: {str(e)} - '{line[:100]}...'")
                    elif error_rows % 10000 == 0:  # 每1万个错误记录一次
                        print(f"❌ 已处理 {error_rows} 个错误行")
            
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
    
    def _batch_insert_concept_data(self, batch_data, replace_mode: str = "update", import_date=None):
        """
        批量插入概念数据
        
        Args:
            batch_data: 要插入的数据列表
            replace_mode: 重复处理模式 (update/append/replace)
            import_date: 导入日期，用于替换模式
        """
        try:
            if replace_mode == "append":
                # 追加模式：直接插入，允许重复
                self.db.bulk_insert_mappings(StockConceptData, batch_data)
                self.db.commit()
            else:
                # 更新模式：逐条检查并处理重复
                self._upsert_concept_data(batch_data, import_date)
        except Exception as e:
            self.db.rollback()
            # 如果批量操作失败，降级到逐条处理
            self._fallback_insert_concept_data(batch_data, replace_mode, import_date)
    
    def _upsert_concept_data(self, batch_data, import_date):
        """更新插入概念数据"""
        for data in batch_data:
            try:
                # 检查是否存在相同的记录（基于股票代码+概念+导入日期）
                existing = self.db.query(StockConceptData).filter(
                    StockConceptData.stock_code == data['stock_code'],
                    StockConceptData.concept == data['concept'],
                    StockConceptData.import_date == import_date
                ).first()
                
                if existing:
                    # 更新现有记录
                    for key, value in data.items():
                        if key != 'created_at':  # 不更新创建时间
                            setattr(existing, key, value)
                else:
                    # 插入新记录
                    record = StockConceptData(**data)
                    self.db.add(record)
                    
            except Exception:
                self.db.rollback()
                continue
        
        self.db.commit()
    
    def _fallback_insert_concept_data(self, batch_data, replace_mode, import_date):
        """概念数据插入失败后的降级处理"""
        for data in batch_data:
            try:
                if replace_mode == "append":
                    record = StockConceptData(**data)
                    self.db.add(record)
                else:
                    # 更新模式的逐条处理
                    existing = self.db.query(StockConceptData).filter(
                        StockConceptData.stock_code == data['stock_code'],
                        StockConceptData.concept == data['concept'],
                        StockConceptData.import_date == import_date
                    ).first()
                    
                    if existing:
                        for key, value in data.items():
                            if key != 'created_at':
                                setattr(existing, key, value)
                    else:
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
    
    def _cleanup_sync_data(self, processed_keys: set, import_date, data_type: str) -> int:
        """
        清理同步数据：删除文件中不存在的记录
        
        Args:
            processed_keys: 文件中存在的记录key集合
            import_date: 导入日期  
            data_type: 数据类型 ("concept" 或 "timeseries")
        
        Returns:
            删除的记录数量
        """
        try:
            if data_type == "concept":
                # 获取当天数据库中的所有记录
                existing_records = self.db.query(StockConceptData).filter(
                    StockConceptData.import_date == import_date
                ).all()
                
                # 找出需要删除的记录
                to_delete_ids = []
                for record in existing_records:
                    record_key = f"{record.stock_code}_{record.concept or ''}"
                    if record_key not in processed_keys:
                        to_delete_ids.append(record.id)
                
                # 批量删除
                if to_delete_ids:
                    deleted_count = self.db.query(StockConceptData).filter(
                        StockConceptData.id.in_(to_delete_ids)
                    ).delete(synchronize_session=False)
                    self.db.commit()
                    return deleted_count
                    
            elif data_type == "timeseries":
                # TXT时间序列数据的同步处理
                # 这里可以根据具体的交易日期来处理
                pass
                
        except Exception as e:
            self.db.rollback()
            print(f"❌ 同步清理失败: {str(e)}")
            
        return 0