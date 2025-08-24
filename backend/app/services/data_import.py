"""
数据导入服务
"""

import pandas as pd
import io
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models import Stock, Concept, StockConcept, DailyStockData, DataImportRecord
from datetime import datetime, date


class DataImportService:
    """数据导入服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_existing_import(self, import_date: date, import_type: str, file_name: str) -> Optional[DataImportRecord]:
        """检查指定日期和类型的导入记录"""
        return self.db.query(DataImportRecord).filter(
            DataImportRecord.import_date == import_date,
            DataImportRecord.import_type == import_type,
            DataImportRecord.file_name == file_name
        ).first()
    
    def create_import_record(self, import_date: date, import_type: str, file_name: str, 
                           imported_records: int = 0, skipped_records: int = 0,
                           import_status: str = 'success', error_message: str = None) -> DataImportRecord:
        """创建导入记录"""
        record = DataImportRecord(
            import_date=import_date,
            import_type=import_type,
            file_name=file_name,
            imported_records=imported_records,
            skipped_records=skipped_records,
            import_status=import_status,
            error_message=error_message
        )
        self.db.add(record)
        return record
    
    def update_import_record(self, record: DataImportRecord, imported_records: int = 0, 
                           skipped_records: int = 0, import_status: str = 'success', 
                           error_message: str = None):
        """更新导入记录"""
        record.imported_records = imported_records
        record.skipped_records = skipped_records
        record.import_status = import_status
        record.error_message = error_message
        record.updated_at = datetime.now()
    
    async def import_csv_data(self, content: bytes, filename: str, allow_overwrite: bool = False) -> Dict[str, Any]:
        """
        导入CSV格式的股票数据
        支持两种格式:
        1. 英文格式: stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow
        2. 中文格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
        """
        import_date = date.today()
        import_type = 'csv'
        
        try:
            # 检查是否已经导入过
            existing_record = self.check_existing_import(import_date, import_type, filename)
            if existing_record and not allow_overwrite:
                return {
                    "message": "今日已导入该文件，如需覆盖请设置allow_overwrite=True",
                    "imported_records": existing_record.imported_records,
                    "skipped_records": existing_record.skipped_records,
                    "import_date": import_date.isoformat(),
                    "already_exists": True
                }
            
            # 解析CSV内容
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            
            # 检测CSV格式并进行列名映射
            df = self._normalize_csv_columns(df)
            
            imported_records = 0
            skipped_records = 0
            errors = []
            
            # 检查必需的列是否存在
            required_columns = ['stock_code', 'stock_name', 'concept']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise Exception(f"CSV文件缺少必需的列: {', '.join(missing_columns)}")
            
            # 如果是覆盖导入，先删除当天的相关数据
            if allow_overwrite and existing_record:
                # 删除当天导入的股票数据
                deleted_count = self.db.query(DailyStockData).filter(
                    DailyStockData.trade_date == import_date
                ).delete(synchronize_session=False)
                self.db.flush()  # 刷新但不提交，确保删除操作在后续插入前生效
                print(f"🗑️ 已删除 {deleted_count} 条当天数据记录")
            
            # 用于跟踪已处理的股票-日期组合，避免重复插入DailyStockData
            processed_stock_dates = set()
            
            for index, row in df.iterrows():
                try:
                    # 跳过空行或无效行
                    if pd.isna(row.get('stock_code')) or pd.isna(row.get('stock_name')):
                        skipped_records += 1
                        continue
                    
                    # 处理股票信息
                    stock_code = str(row['stock_code']).strip()
                    stock_name = str(row['stock_name']).strip()
                    industry = str(row.get('industry', '')).strip() if not pd.isna(row.get('industry')) else ''
                    concept_name = str(row['concept']).strip()
                    
                    # 验证数据有效性
                    if not stock_code or not stock_name or not concept_name:
                        skipped_records += 1
                        continue
                    
                    # 检查是否为转债（以1开头的6位代码）
                    is_convertible_bond = (
                        len(stock_code) == 6 and 
                        stock_code.startswith('1') and 
                        stock_code.isdigit()
                    )
                    
                    # 获取或创建股票记录
                    stock = self.db.query(Stock).filter(
                        Stock.stock_code == stock_code
                    ).first()
                    
                    if not stock:
                        stock = Stock(
                            stock_code=stock_code,
                            stock_name=stock_name,
                            industry=industry if industry else None,
                            is_convertible_bond=is_convertible_bond
                        )
                        self.db.add(stock)
                        self.db.flush()  # 获取ID
                    
                    # 获取或创建概念记录
                    concept = self.db.query(Concept).filter(
                        Concept.concept_name == concept_name
                    ).first()
                    
                    if not concept:
                        concept = Concept(concept_name=concept_name)
                        self.db.add(concept)
                        self.db.flush()  # 获取ID
                    
                    # 创建股票概念关联（如果不存在）
                    stock_concept = self.db.query(StockConcept).filter(
                        StockConcept.stock_id == stock.id,
                        StockConcept.concept_id == concept.id
                    ).first()
                    
                    if not stock_concept:
                        stock_concept = StockConcept(
                            stock_id=stock.id,
                            concept_id=concept.id
                        )
                        self.db.add(stock_concept)
                    
                    # 处理每日数据（现在总是有日期信息）
                    if 'date' in df.columns:
                        trade_date = pd.to_datetime(row['date']).date()
                        stock_date_key = (stock.id, trade_date)
                        
                        # 只有在未处理过该股票-日期组合时才处理DailyStockData
                        if stock_date_key not in processed_stock_dates:
                            price = float(row.get('price', 0)) if pd.notna(row.get('price')) else 0
                            turnover_rate = float(row.get('turnover_rate', 0)) if pd.notna(row.get('turnover_rate')) else 0
                            net_inflow = float(row.get('net_inflow', 0)) if pd.notna(row.get('net_inflow')) else 0
                            pages_count = int(row.get('pages_count', 0)) if pd.notna(row.get('pages_count')) else 0
                            total_reads = int(row.get('total_reads', 0)) if pd.notna(row.get('total_reads')) else 0
                            
                            # 检查是否已存在该日期的数据
                            existing_data = self.db.query(DailyStockData).filter(
                                DailyStockData.stock_id == stock.id,
                                DailyStockData.trade_date == trade_date
                            ).first()
                            
                            if existing_data:
                                # 更新现有记录
                                existing_data.price = price
                                existing_data.turnover_rate = turnover_rate
                                existing_data.net_inflow = net_inflow
                                existing_data.pages_count = pages_count
                                existing_data.total_reads = total_reads
                            else:
                                # 创建新记录
                                daily_data = DailyStockData(
                                    stock_id=stock.id,
                                    trade_date=trade_date,
                                    price=price,
                                    turnover_rate=turnover_rate,
                                    net_inflow=net_inflow,
                                    pages_count=pages_count,
                                    total_reads=total_reads,
                                    heat_value=0  # 默认热度值为0
                                )
                                self.db.add(daily_data)
                            
                            # 标记该股票-日期组合已处理
                            processed_stock_dates.add(stock_date_key)
                    
                    imported_records += 1
                    
                except Exception as e:
                    skipped_records += 1
                    errors.append(f"第{index+1}行: {str(e)}")
                    continue
            
            # 创建或更新导入记录
            if existing_record and allow_overwrite:
                self.update_import_record(
                    existing_record, imported_records, skipped_records, 
                    'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None  # 只保存前5个错误
                )
            else:
                self.create_import_record(
                    import_date, import_type, filename, imported_records, 
                    skipped_records, 'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None
                )
            
            # 提交事务
            self.db.commit()
            
            return {
                "imported_records": imported_records,
                "skipped_records": skipped_records,
                "errors": errors,
                "import_date": import_date.isoformat(),
                "overwrite": allow_overwrite and existing_record is not None
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"CSV解析失败: {str(e)}")
    
    async def import_txt_data(self, content: bytes, filename: str, allow_overwrite: bool = False) -> Dict[str, Any]:
        """
        导入TXT格式的热度数据
        TXT格式: 每行包含股票代码和热度值，用制表符或空格分隔
        """
        # 从文件名尝试解析日期（假设格式如：data_20240821.txt）
        trade_date = self._extract_date_from_filename(filename)
        if not trade_date:
            trade_date = date.today()
        
        import_type = 'txt'
        
        try:
            # 检查是否已经导入过
            existing_record = self.check_existing_import(trade_date, import_type, filename)
            if existing_record and not allow_overwrite:
                return {
                    "message": "今日已导入该文件，如需覆盖请设置allow_overwrite=True",
                    "imported_records": existing_record.imported_records,
                    "skipped_records": existing_record.skipped_records,
                    "import_date": trade_date.isoformat(),
                    "already_exists": True
                }
            
            # 解析TXT内容
            text_content = content.decode('utf-8')
            lines = text_content.strip().split('\n')
            
            imported_records = 0
            skipped_records = 0
            errors = []
            
            # 如果是覆盖导入，先删除当天的热度数据
            if allow_overwrite and existing_record:
                # 只删除热度值，不删除其他数据
                self.db.query(DailyStockData).filter(
                    DailyStockData.trade_date == trade_date
                ).update({"heat_value": 0}, synchronize_session=False)
            
            for line_num, line in enumerate(lines, 1):
                try:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 分割数据部分
                    parts = line.split()
                    if len(parts) < 2:
                        skipped_records += 1
                        continue
                    
                    # 尝试不同的格式
                    stock_code = None
                    heat_value = None
                    
                    # 格式1: 股票代码 热度值
                    # 格式2: 日期 股票代码 热度值 等其他字段
                    if len(parts) == 2:
                        # 格式1: stock_code heat_value
                        try:
                            stock_code = parts[0].strip()
                            heat_value = float(parts[1])
                        except ValueError:
                            skipped_records += 1
                            continue
                    elif len(parts) >= 3:
                        # 格式2: date stock_code heat_value ...
                        try:
                            # 尝试第二个字段作为股票代码，第三个作为热度值
                            stock_code = parts[1].strip()
                            heat_value = float(parts[2])
                        except ValueError:
                            try:
                                # 如果失败，尝试第一个字段作为股票代码，第二个作为热度值
                                stock_code = parts[0].strip()
                                heat_value = float(parts[1])
                            except ValueError:
                                skipped_records += 1
                                continue
                    else:
                        skipped_records += 1
                        continue
                    
                    # 验证股票代码格式（6位数字）
                    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
                        skipped_records += 1
                        errors.append(f"第{line_num}行: 股票代码格式无效 {stock_code}")
                        continue
                    
                    # 查找股票记录
                    stock = self.db.query(Stock).filter(
                        Stock.stock_code == stock_code
                    ).first()
                    
                    if not stock:
                        errors.append(f"第{line_num}行: 股票代码 {stock_code} 不存在")
                        skipped_records += 1
                        continue
                    
                    # 更新或创建每日数据
                    daily_data = self.db.query(DailyStockData).filter(
                        DailyStockData.stock_id == stock.id,
                        DailyStockData.trade_date == trade_date
                    ).first()
                    
                    if daily_data:
                        # 更新现有记录的热度值
                        daily_data.heat_value = heat_value
                    else:
                        # 创建新的每日数据记录
                        daily_data = DailyStockData(
                            stock_id=stock.id,
                            trade_date=trade_date,
                            heat_value=heat_value
                        )
                        self.db.add(daily_data)
                    
                    imported_records += 1
                    
                except Exception as e:
                    skipped_records += 1
                    errors.append(f"第{line_num}行: {str(e)}")
                    continue
            
            # 创建或更新导入记录
            if existing_record and allow_overwrite:
                self.update_import_record(
                    existing_record, imported_records, skipped_records,
                    'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None
                )
            else:
                self.create_import_record(
                    trade_date, import_type, filename, imported_records,
                    skipped_records, 'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None
                )
            
            # 提交事务
            self.db.commit()
            
            return {
                "imported_records": imported_records,
                "skipped_records": skipped_records,
                "errors": errors,
                "import_date": trade_date.isoformat(),
                "overwrite": allow_overwrite and existing_record is not None
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"TXT解析失败: {str(e)}")
    
    def _extract_date_from_filename(self, filename: str) -> date:
        """从文件名中提取日期"""
        import re
        
        # 匹配 YYYYMMDD 格式
        date_pattern = r'(\d{8})'
        match = re.search(date_pattern, filename)
        
        if match:
            date_str = match.group(1)
            try:
                return datetime.strptime(date_str, '%Y%m%d').date()
            except ValueError:
                pass
        
        return None
    
    def _normalize_csv_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化CSV列名，支持中英文格式自动转换
        """
        # 中文到英文的列名映射
        chinese_to_english = {
            '股票代码': 'stock_code',
            '股票名称': 'stock_name',
            '概念': 'concept',
            '行业': 'industry',
            '价格': 'price',
            '换手': 'turnover_rate',
            '净流入': 'net_inflow',
            '全部页数': 'pages_count',
            '热帖首页页阅读总数': 'total_reads'
        }
        
        # 检测是否为中文格式
        columns = df.columns.tolist()
        is_chinese_format = any(col in chinese_to_english for col in columns)
        
        if is_chinese_format:
            # 重命名列
            df = df.rename(columns=chinese_to_english)
            
            # 添加date列（如果不存在）
            if 'date' not in df.columns:
                df['date'] = date.today().strftime('%Y-%m-%d')
            
            # 处理数据类型和清理
            if 'industry' in df.columns:
                df['industry'] = df['industry'].replace('None', '').fillna('')
            
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
                
            if 'turnover_rate' in df.columns:
                df['turnover_rate'] = pd.to_numeric(df['turnover_rate'], errors='coerce').fillna(0)
                
            if 'net_inflow' in df.columns:
                df['net_inflow'] = pd.to_numeric(df['net_inflow'], errors='coerce').fillna(0)
        
        return df