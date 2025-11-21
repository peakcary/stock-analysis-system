"""
数据导入服务
"""

import pandas as pd
import io
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models import Stock, Concept, StockConcept, DailyStockData, DataImportRecord
from app.models.stock import StockConceptRawData, ImportBatch, RawImportData, RawDataMapping
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
    
    async def import_csv_data(self, content: bytes, filename: str, allow_overwrite: bool = False, trade_date: date = None) -> Dict[str, Any]:
        """
        导入CSV格式的股票数据
        支持两种格式:
        1. 英文格式: stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow
        2. 中文格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
        """
        # 如果没有提供交易日期，从文件名尝试解析日期
        if not trade_date:
            import_date = self._extract_date_from_filename(filename)
            if not import_date:
                import_date = date.today()
        else:
            import_date = trade_date
        
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
            
            # 统计信息
            stats = {
                'new_stocks': 0,
                'updated_stocks': 0,
                'new_concepts': 0,
                'new_relations': 0,
                'updated_daily_data': 0,
                'new_daily_data': 0
            }
            
            # 检查必需的列是否存在
            required_columns = ['stock_code', 'stock_name', 'concept']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise Exception(f"CSV文件缺少必需的列: {', '.join(missing_columns)}")
            
            # 如果是覆盖导入，先删除相关数据
            if allow_overwrite and existing_record:
                # 获取CSV文件中涉及的股票代码（需要规范化）
                stock_codes_in_csv = set(
                    self._normalize_stock_code(str(row['stock_code']).strip())
                    for _, row in df.iterrows()
                    if pd.notna(row.get('stock_code'))
                )
                
                # 只删除CSV中涉及的股票在该日期的数据
                if stock_codes_in_csv:
                    # 先获取需要删除的股票ID
                    stock_objects = self.db.query(Stock).filter(
                        Stock.stock_code.in_(stock_codes_in_csv)
                    ).all()
                    
                    stock_ids = [stock.id for stock in stock_objects]
                    
                    if stock_ids:
                        # 使用股票ID直接删除，避免join操作
                        deleted_count = self.db.query(DailyStockData).filter(
                            DailyStockData.trade_date == import_date,
                            DailyStockData.stock_id.in_(stock_ids)
                        ).delete(synchronize_session=False)
                        self.db.flush()
                        print(f"🗑️ 已删除 {len(stock_codes_in_csv)} 只股票在 {import_date} 的 {deleted_count} 条数据记录")
                
                # 清理可能过时的股票概念关联（可选）
                # 注意：这里不删除概念关联，因为其他日期可能仍然有效
            
            # 用于跟踪已处理的股票-日期组合，避免重复插入DailyStockData
            processed_stock_dates = set()
            
            # 用于跟踪本次CSV中的股票和概念关系
            csv_stock_concepts = {}  # {stock_code: [concept_names]}
            csv_stocks_info = {}     # {stock_code: {'name': ..., 'industry': ...}}
            
            # 第一遍：收集CSV中的所有股票和概念信息
            print(f"📊 第一步：分析CSV文件中的股票和概念关系...")
            for index, row in df.iterrows():
                try:
                    if pd.isna(row.get('stock_code')) or pd.isna(row.get('stock_name')):
                        continue

                    # 规范化股票代码，去掉SH/SZ等前缀
                    stock_code_raw = str(row['stock_code']).strip()
                    stock_code = self._normalize_stock_code(stock_code_raw)
                    stock_name = str(row['stock_name']).strip()
                    industry = str(row.get('industry', '')).strip() if not pd.isna(row.get('industry')) else ''
                    concept_name = str(row['concept']).strip()
                    
                    if not stock_code or not stock_name or not concept_name:
                        continue
                    
                    # 收集股票基本信息（总是使用最新的）
                    csv_stocks_info[stock_code] = {
                        'name': stock_name,
                        'industry': industry
                    }
                    
                    # 收集概念关系
                    if stock_code not in csv_stock_concepts:
                        csv_stock_concepts[stock_code] = set()
                    csv_stock_concepts[stock_code].add(concept_name)
                    
                except Exception as e:
                    continue
            
            print(f"📈 CSV中包含 {len(csv_stocks_info)} 只股票，{sum(len(concepts) for concepts in csv_stock_concepts.values())} 个股票-概念关系")

            # 创建导入批次记录
            import_batch = ImportBatch(
                import_date=import_date,
                import_type='csv',
                file_name=filename,
                record_count=len(df),
                status='pending'
            )
            self.db.add(import_batch)
            self.db.flush()  # 获取批次ID
            print(f"📦 创建导入批次: ID={import_batch.id}, 记录数={len(df)}")

            # 用于收集原始数据（双写到不拆分的表）
            raw_data_records = []
            raw_import_records = []
            raw_mapping_records = []

            # 第二遍：处理股票基础信息和概念关系
            for index, row in df.iterrows():
                try:
                    # 跳过空行或无效行
                    if pd.isna(row.get('stock_code')) or pd.isna(row.get('stock_name')):
                        skipped_records += 1
                        continue

                    # 处理股票信息 - 规范化股票代码
                    stock_code_raw = str(row['stock_code']).strip()
                    stock_code = self._normalize_stock_code(stock_code_raw)
                    stock_code_prefix = self._extract_prefix(stock_code_raw)
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
                        # 创建新股票
                        stock = Stock(
                            stock_code=stock_code,
                            original_stock_code=stock_code_raw,
                            stock_code_prefix=stock_code_prefix,
                            stock_name=stock_name,
                            industry=industry if industry else None,
                            is_convertible_bond=is_convertible_bond
                        )
                        self.db.add(stock)
                        self.db.flush()  # 获取ID
                        stats['new_stocks'] += 1
                        print(f"✨ 创建新股票: {stock_code} (原始: {stock_code_raw}, 前缀: {stock_code_prefix}) - {stock_name}")
                    else:
                        # 更新现有股票的基本信息（总是使用最新CSV的数据）
                        updated_fields = []
                        if stock.stock_name != stock_name:
                            stock.stock_name = stock_name
                            updated_fields.append(f"名称: {stock_name}")
                        if stock.industry != (industry if industry else None):
                            stock.industry = industry if industry else None
                            updated_fields.append(f"行业: {industry or '无'}")
                        if stock.original_stock_code != stock_code_raw:
                            stock.original_stock_code = stock_code_raw
                            updated_fields.append(f"原始代码: {stock_code_raw}")
                        if stock.stock_code_prefix != stock_code_prefix:
                            stock.stock_code_prefix = stock_code_prefix
                            updated_fields.append(f"前缀: {stock_code_prefix}")
                        if updated_fields:
                            stats['updated_stocks'] += 1
                            print(f"🔄 更新股票 {stock_code}: {', '.join(updated_fields)}")
                    
                    # 获取或创建概念记录
                    concept = self.db.query(Concept).filter(
                        Concept.concept_name == concept_name
                    ).first()
                    
                    if not concept:
                        concept = Concept(concept_name=concept_name)
                        self.db.add(concept)
                        self.db.flush()  # 获取ID
                        stats['new_concepts'] += 1
                        print(f"✨ 创建新概念: {concept_name}")
                    
                    # 创建股票概念关联（增量模式：只添加，不删除旧关系）
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
                        stats['new_relations'] += 1
                        print(f"🔗 添加关联: {stock_code} -> {concept_name}")
                    
                    # 处理每日数据（现在总是有日期信息）
                    if 'date' in df.columns:
                        trade_date = pd.to_datetime(row['date']).date()
                        stock_date_key = (stock.id, trade_date)

                        # 提取交易数据（用于拆分表和原始表）
                        price = float(row.get('price', 0)) if pd.notna(row.get('price')) else 0
                        turnover_rate = float(row.get('turnover_rate', 0)) if pd.notna(row.get('turnover_rate')) else 0
                        net_inflow = float(row.get('net_inflow', 0)) if pd.notna(row.get('net_inflow')) else 0
                        pages_count = int(row.get('pages_count', 0)) if pd.notna(row.get('pages_count')) else 0
                        total_reads = int(row.get('total_reads', 0)) if pd.notna(row.get('total_reads')) else 0

                        # 创建原始导入数据记录
                        raw_import_record = RawImportData(
                            import_batch_id=import_batch.id,
                            row_number=index + 2,  # CSV行号从2开始（包含表头）
                            trade_date=trade_date,
                            stock_code_raw=stock_code_raw,
                            stock_code_normalized=stock_code,
                            stock_code_prefix=stock_code_prefix,
                            stock_name=stock_name,
                            industry=industry if industry else None,
                            price=price,
                            turnover_rate=turnover_rate,
                            net_inflow=net_inflow,
                            pages_count=pages_count,
                            total_reads=total_reads,
                            concept=concept_name,
                            source_type='csv',
                            source_file=filename
                        )
                        raw_import_records.append(raw_import_record)

                        # 双写：保存到原始数据表（每行都保存，包括股票-概念组合）
                        raw_record = StockConceptRawData(
                            import_date=import_date,
                            trade_date=trade_date,
                            stock_code=stock_code,
                            original_stock_code=stock_code_raw,
                            stock_code_prefix=stock_code_prefix,
                            stock_name=stock_name,
                            concept=concept_name,
                            industry=industry if industry else None,
                            price=price,
                            turnover_rate=turnover_rate,
                            net_inflow=net_inflow,
                            pages_count=pages_count,
                            total_reads=total_reads,
                            file_name=filename,
                            row_number=index + 2  # CSV行号从2开始（包含表头）
                        )
                        raw_data_records.append(raw_record)

                        # 只有在未处理过该股票-日期组合时才处理DailyStockData
                        if stock_date_key not in processed_stock_dates:

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
                                stats['updated_daily_data'] += 1
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
                                stats['new_daily_data'] += 1

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

            # 批量插入原始导入数据到 raw_import_data 表
            if raw_import_records:
                self.db.bulk_save_objects(raw_import_records)
                print(f"📥 批量保存原始导入数据: {len(raw_import_records)} 条记录")
                stats['raw_import_records'] = len(raw_import_records)

            # 更新导入批次状态
            import_batch.record_count = len(raw_import_records)
            import_batch.status = 'success' if not errors else 'partial'

            # 批量插入原始数据到不拆分的表
            if raw_data_records:
                # 如果是覆盖模式，先删除该日期的原始数据
                if allow_overwrite and existing_record:
                    deleted_raw = self.db.query(StockConceptRawData).filter(
                        StockConceptRawData.trade_date == import_date
                    ).delete(synchronize_session=False)
                    if deleted_raw > 0:
                        print(f"🗑️ 已删除原始数据表中 {import_date} 的 {deleted_raw} 条记录")

                # 批量插入原始数据
                self.db.bulk_save_objects(raw_data_records)
                print(f"💾 同步写入原始数据表: {len(raw_data_records)} 条记录")
                stats['raw_data_records'] = len(raw_data_records)

            # 打印导入总结
            print(f"\n📈 CSV导入完成总结:")
            print(f"   📋 文件名: {filename}")
            print(f"   📅 导入日期: {import_date}")
            print(f"   📊 处理记录: {imported_records} 成功, {skipped_records} 跳过")
            print(f"   🏢 股票信息: {stats['new_stocks']} 新增, {stats['updated_stocks']} 更新")
            print(f"   🏷️  概念信息: {stats['new_concepts']} 新增概念")
            print(f"   🔗 关联关系: {stats['new_relations']} 新增关联")
            print(f"   📈 每日数据: {stats['new_daily_data']} 新增, {stats['updated_daily_data']} 更新")
            print(f"   💾 原始数据: {stats.get('raw_data_records', 0)} 条记录（未拆分）")
            if errors:
                print(f"   ⚠️  错误数量: {len(errors)} 个")
            print(f"   ✅ 导入状态: {'完全成功' if not errors else '部分成功'}")

            # 提交事务
            self.db.commit()

            # 触发每日分析计算 - 生成概念汇总和排名数据
            try:
                print(f"🚀 触发 {import_date} 的每日分析计算...")
                from app.services.ranking_calculator import RankingCalculatorService
                ranking_service = RankingCalculatorService(self.db)
                analysis_result = await ranking_service.calculate_daily_rankings(import_date)
                print(f"✅ 分析计算完成: {analysis_result.get('message', '成功')}")
            except Exception as e:
                print(f"⚠️ 分析计算失败（但导入成功）: {str(e)}")
                # 不影响导入结果，只记录警告

            return {
                "imported_records": imported_records,
                "skipped_records": skipped_records,
                "errors": errors,
                "import_date": import_date.isoformat(),
                "overwrite": allow_overwrite and existing_record is not None,
                "stats": stats
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"CSV解析失败: {str(e)}")
    
    async def import_txt_data(self, content: bytes, filename: str, allow_overwrite: bool = False, trade_date: date = None) -> Dict[str, Any]:
        """
        导入TXT格式的每日交易数据
        
        TXT文件特点：
        1. 包含每日交易数据，每行格式: 股票代码\t日期\t热度值
        2. 支持基于日期的完全覆盖导入
        3. 日期来源：优先使用文件内容中的日期，其次是参数，最后是文件名
        
        导入策略：
        - 如果是同一日期的重复导入，完全覆盖该日期的所有数据
        - 支持数据纠正：重新导入可以覆盖之前错误的数据
        """
        
        # 第一步：预解析TXT内容以确定日期和数据范围
        text_content = content.decode('utf-8')
        lines = text_content.strip().split('\n')
        
        # 从文件内容中提取日期
        detected_dates = set()
        valid_lines = []
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t') if '\t' in line else line.split()
            if len(parts) >= 3:
                try:
                    # 尝试解析日期 (第二个字段应该是日期)
                    date_str = parts[1].strip()
                    parsed_date = self._parse_date_from_string(date_str)
                    if parsed_date:
                        detected_dates.add(parsed_date)
                        valid_lines.append((line_num, line, parsed_date))
                except:
                    continue
        
        # 确定导入的目标日期
        if trade_date:
            target_date = trade_date
            print(f"📅 使用指定日期: {target_date}")
        elif len(detected_dates) == 1:
            target_date = list(detected_dates)[0]
            print(f"📅 从文件内容检测到日期: {target_date}")
        elif len(detected_dates) > 1:
            # 如果检测到多个日期，使用最常见的日期
            from collections import Counter
            date_counts = Counter([line[2] for line in valid_lines])
            target_date = date_counts.most_common(1)[0][0]
            print(f"📅 检测到多个日期，使用最常见的: {target_date} (出现{date_counts[target_date]}次)")
        else:
            # 从文件名提取日期
            target_date = self._extract_date_from_filename(filename)
            if not target_date:
                target_date = date.today()
            print(f"📅 从文件名提取日期: {target_date}")
        
        import_type = 'txt'
        
        print(f"📊 TXT文件预分析:")
        print(f"   📋 文件名: {filename}")
        print(f"   📅 目标日期: {target_date}")  
        print(f"   📝 有效行数: {len(valid_lines)}")
        print(f"   🔍 检测到日期: {sorted(detected_dates)}")
        
        try:
            # 检查是否已经导入过该日期的数据
            existing_record = self.check_existing_import(target_date, import_type, filename)
            
            # TXT文件支持重复导入和覆盖（用于数据纠正）
            if existing_record and not allow_overwrite:
                print(f"⚠️  该日期 {target_date} 已有TXT数据，如需覆盖请设置allow_overwrite=True")
                return {
                    "message": f"该日期 {target_date} 已有数据，如需覆盖请设置allow_overwrite=True",
                    "imported_records": existing_record.imported_records,
                    "skipped_records": existing_record.skipped_records,
                    "import_date": target_date.isoformat(),
                    "already_exists": True
                }
            
            imported_records = 0
            skipped_records = 0
            errors = []
            
            # 统计信息
            stats = {
                'target_date': target_date.isoformat(),
                'deleted_records': 0,
                'updated_records': 0,
                'new_records': 0,
                'error_records': 0
            }

            # 创建导入批次记录
            import_batch = ImportBatch(
                import_date=target_date,
                import_type='txt',
                file_name=filename,
                record_count=len(valid_lines),
                status='pending'
            )
            self.db.add(import_batch)
            self.db.flush()  # 获取批次ID
            print(f"📦 创建导入批次: ID={import_batch.id}, 记录数={len(valid_lines)}")

            # 用于收集原始导入数据
            raw_import_records = []

            # 核心策略：基于日期的完全覆盖
            # 1. 收集要处理的股票代码
            txt_stock_codes = set()
            for line_num, line, line_date in valid_lines:
                if line_date != target_date:
                    continue
                
                parts = line.split('\t') if '\t' in line else line.split()
                if len(parts) >= 3:
                    stock_code_with_prefix = parts[0].strip()
                    stock_code = self._normalize_stock_code(stock_code_with_prefix)
                    if stock_code.isdigit() and len(stock_code) == 6:
                        txt_stock_codes.add(stock_code)
            
            print(f"🔄 准备处理 {len(txt_stock_codes)} 只股票在 {target_date} 的热度数据")
            
            # 2. 如果是覆盖模式或已存在数据，先删除该日期的相关数据
            if allow_overwrite or existing_record:
                if txt_stock_codes:
                    # 先获取要删除的股票ID
                    stock_objects = self.db.query(Stock).filter(
                        Stock.stock_code.in_(txt_stock_codes)
                    ).all()
                    
                    stock_ids = [stock.id for stock in stock_objects]
                    
                    if stock_ids:
                        # 删除该日期下这些股票的现有数据
                        deleted_count = self.db.query(DailyStockData).filter(
                            DailyStockData.trade_date == target_date,
                            DailyStockData.stock_id.in_(stock_ids)
                        ).delete(synchronize_session=False)
                        
                        stats['deleted_records'] = deleted_count
                        self.db.flush()
                        
                        if deleted_count > 0:
                            print(f"🗑️  删除了 {deleted_count} 条 {target_date} 的旧数据，准备导入新数据")
            
            # 3. 处理每一行数据
            print(f"📝 开始处理TXT数据...")
            
            for line_num, line, line_date in valid_lines:
                try:
                    # 只处理目标日期的数据
                    if line_date != target_date:
                        skipped_records += 1
                        continue
                        
                    # 分割数据部分 - 支持制表符分隔
                    parts = line.split('\t') if '\t' in line else line.split()
                    if len(parts) < 3:
                        skipped_records += 1
                        errors.append(f"第{line_num}行: 数据格式不正确，需要至少3个字段")
                        continue
                    
                    # 解析字段：股票代码、日期、热度值
                    stock_code_with_prefix = parts[0].strip()
                    date_str = parts[1].strip()
                    heat_value_str = parts[2].strip()
                    
                    # 解析热度值
                    try:
                        heat_value = float(heat_value_str)
                    except ValueError:
                        skipped_records += 1
                        errors.append(f"第{line_num}行: 无法解析热度值 '{heat_value_str}'")
                        stats['error_records'] += 1
                        continue
                    
                    # 处理股票代码 - 去掉SH/SZ前缀
                    stock_code = self._normalize_stock_code(stock_code_with_prefix)
                    
                    # 验证股票代码格式（6位数字）
                    if not stock_code or not stock_code.isdigit() or len(stock_code) != 6:
                        skipped_records += 1
                        errors.append(f"第{line_num}行: 股票代码格式无效 {stock_code_with_prefix} -> {stock_code}")
                        stats['error_records'] += 1
                        continue
                    
                    # 查找股票记录
                    stock = self.db.query(Stock).filter(
                        Stock.stock_code == stock_code
                    ).first()
                    
                    if not stock:
                        # 为不存在的股票创建基础记录
                        is_convertible_bond = (
                            len(stock_code) == 6 and
                            stock_code.startswith('1') and
                            stock_code.isdigit()
                        )

                        stock_prefix = self._extract_prefix(stock_code_with_prefix)

                        stock = Stock(
                            stock_code=stock_code,
                            original_stock_code=stock_code_with_prefix,
                            stock_code_prefix=stock_prefix,
                            stock_name=f"股票{stock_code}",  # 临时名称
                            is_convertible_bond=is_convertible_bond
                        )
                        self.db.add(stock)
                        self.db.flush()  # 获取ID
                        print(f"💫 自动创建股票记录: {stock_code} (原始: {stock_code_with_prefix}, 前缀: {stock_prefix})")
                    
                    # 创建每日数据记录（因为之前已删除，这里都是新建）
                    daily_data = DailyStockData(
                        stock_id=stock.id,
                        trade_date=target_date,
                        heat_value=heat_value,
                        # 其他字段使用默认值
                        price=0,
                        turnover_rate=0,
                        net_inflow=0,
                        pages_count=0,
                        total_reads=0
                    )
                    self.db.add(daily_data)
                    stats['new_records'] += 1
                    imported_records += 1

                    # 创建原始导入数据记录
                    stock_code_prefix = self._extract_prefix(stock_code_with_prefix)
                    raw_import_record = RawImportData(
                        import_batch_id=import_batch.id,
                        row_number=line_num,
                        trade_date=target_date,
                        stock_code_raw=stock_code_with_prefix,
                        stock_code_normalized=stock_code,
                        stock_code_prefix=stock_code_prefix,
                        stock_name=stock.stock_name,
                        industry=None,  # TXT格式不包含行业信息
                        price=0,  # TXT格式不包含价格
                        turnover_rate=0,  # TXT格式不包含换手率
                        net_inflow=0,  # TXT格式不包含净流入
                        pages_count=0,  # TXT格式不包含页数
                        total_reads=0,  # TXT格式不包含总阅读数
                        heat_value=heat_value,
                        source_type='txt',
                        source_file=filename
                    )
                    raw_import_records.append(raw_import_record)

                    if imported_records % 100 == 0:
                        print(f"   ... 已处理 {imported_records} 条记录")
                    
                except Exception as e:
                    skipped_records += 1
                    stats['error_records'] += 1
                    errors.append(f"第{line_num}行: {str(e)}")
                    continue

            # 批量插入原始导入数据到 raw_import_data 表
            if raw_import_records:
                self.db.bulk_save_objects(raw_import_records)
                print(f"📥 批量保存原始导入数据: {len(raw_import_records)} 条记录")
                stats['raw_import_records'] = len(raw_import_records)

            # 更新导入批次状态
            import_batch.record_count = len(raw_import_records) if raw_import_records else imported_records
            import_batch.status = 'success' if not errors else 'partial'

            # 打印导入总结
            print(f"\n📈 TXT导入完成总结:")
            print(f"   📋 文件名: {filename}")
            print(f"   📅 目标日期: {target_date}")
            print(f"   📊 处理记录: {imported_records} 成功, {skipped_records} 跳过")
            print(f"   🗑️  删除记录: {stats['deleted_records']} 条旧数据")
            print(f"   ✨ 新增记录: {stats['new_records']} 条热度数据")
            print(f"   📥 原始数据: {stats.get('raw_import_records', 0)} 条记录（已保存）")
            print(f"   ❌ 错误记录: {stats['error_records']} 条")
            if errors:
                print(f"   ⚠️  错误详情: 显示前3个")
                for error in errors[:3]:
                    print(f"      - {error}")
            print(f"   ✅ 导入状态: {'完全成功' if not errors else '部分成功'}")
            print(f"   🔄 覆盖模式: {'是' if (allow_overwrite or existing_record) else '否'}")
            
            # 创建或更新导入记录
            if existing_record and allow_overwrite:
                self.update_import_record(
                    existing_record, imported_records, skipped_records,
                    'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None
                )
            else:
                self.create_import_record(
                    target_date, import_type, filename, imported_records,
                    skipped_records, 'success' if not errors else 'partial',
                    '\n'.join(errors[:5]) if errors else None
                )
            
            # 提交事务
            self.db.commit()

            # 触发每日分析计算 - 生成概念汇总和排名数据
            try:
                print(f"🚀 触发 {target_date} 的每日分析计算...")
                from app.services.ranking_calculator import RankingCalculatorService
                ranking_service = RankingCalculatorService(self.db)
                analysis_result = ranking_service.calculate_daily_rankings(target_date.isoformat())
                print(f"✅ 分析计算完成: {analysis_result.get('message', '成功')}")
            except Exception as e:
                print(f"⚠️ 分析计算失败（但导入成功）: {str(e)}")
                # 不影响导入结果，只记录警告

            return {
                "imported_records": imported_records,
                "skipped_records": skipped_records,
                "errors": errors,
                "import_date": target_date.isoformat(),
                "overwrite": allow_overwrite or existing_record is not None,
                "stats": stats
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"TXT解析失败: {str(e)}")
    
    def _extract_date_from_filename(self, filename: str) -> date:
        """从文件名中提取日期，支持多种格式"""
        import re
        
        # 支持的日期格式模式
        patterns = [
            (r'(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),  # 2025-08-28
            (r'(\d{4}_\d{2}_\d{2})', '%Y_%m_%d'),  # 2025_08_28
            (r'(\d{8})', '%Y%m%d'),                # 20250828
            (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),  # 分组形式的20250828
            (r'(\d{2}-\d{2}-\d{4})', '%m-%d-%Y'),  # MM-DD-YYYY
            (r'(\d{2}/\d{2}/\d{4})', '%m/%d/%Y'),  # MM/DD/YYYY
        ]
        
        for pattern, date_format in patterns:
            match = re.search(pattern, filename)
            if match:
                if len(match.groups()) == 1:
                    date_str = match.group(1)
                else:
                    # 处理分组匹配，如(\d{4})(\d{2})(\d{2})
                    date_str = ''.join(match.groups())
                    
                try:
                    return datetime.strptime(date_str, date_format).date()
                except ValueError:
                    continue
        
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
    
    def _parse_date_from_string(self, date_str: str) -> date:
        """从字符串中解析日期，支持多种格式"""
        from datetime import datetime
        
        # 支持的日期格式
        formats = [
            '%Y-%m-%d',    # 2025-08-28
            '%Y/%m/%d',    # 2025/08/28
            '%Y%m%d',      # 20250828
            '%m/%d/%Y',    # 08/28/2025
            '%d/%m/%Y',    # 28/08/2025
            '%m-%d-%Y',    # 08-28-2025
            '%d-%m-%Y',    # 28-08-2025
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _normalize_stock_code(self, stock_code_with_prefix: str) -> str:
        """
        规范化股票代码，去掉SH/SZ等前缀
        SH600000 -> 600000
        SZ000001 -> 000001
        600000 -> 600000
        """
        stock_code = stock_code_with_prefix.strip().upper()

        # 去掉常见前缀
        if stock_code.startswith('SH'):
            return stock_code[2:]
        elif stock_code.startswith('SZ'):
            return stock_code[2:]
        elif stock_code.startswith('BJ'):  # 北交所
            return stock_code[2:]
        elif stock_code.startswith('HK'):  # 港股
            return stock_code[2:]

        return stock_code

    def _extract_prefix(self, stock_code_with_prefix: str) -> str:
        """
        提取股票代码前缀
        SH600000 -> SH
        SZ000001 -> SZ
        600000 -> None
        """
        stock_code = stock_code_with_prefix.strip().upper()

        if stock_code.startswith('SH'):
            return 'SH'
        elif stock_code.startswith('SZ'):
            return 'SZ'
        elif stock_code.startswith('BJ'):
            return 'BJ'
        elif stock_code.startswith('HK'):
            return 'HK'

        return None
    
    async def import_daily_batch(self, csv_content: bytes, csv_filename: str, 
                                txt_content: bytes, txt_filename: str, 
                                trade_date: date = None, allow_overwrite: bool = False,
                                import_mode: str = "smart") -> Dict[str, Any]:
        """
        批量导入每日数据（CSV + TXT）
        确保两个文件都成功导入才算完成
        
        参数:
            import_mode: 导入模式
                - "smart": 智能模式，自动判断是否需要导入
                - "skip": 跳过已存在的文件
                - "update": 更新模式，只更新已存在的数据
                - "overwrite": 完全覆盖模式
        """
        if not trade_date:
            # 优先从CSV文件名解析日期
            trade_date = self._extract_date_from_filename(csv_filename)
            if not trade_date:
                trade_date = self._extract_date_from_filename(txt_filename)
            if not trade_date:
                trade_date = date.today()
        
        results = {
            "trade_date": trade_date.isoformat(),
            "csv_result": None,
            "txt_result": None,
            "success": False,
            "message": ""
        }
        
        try:
            # 1. 先导入CSV数据（股票基础信息和概念）
            print(f"🔄 开始导入CSV数据: {csv_filename}")
            csv_result = await self.import_csv_data(csv_content, csv_filename, allow_overwrite)
            results["csv_result"] = csv_result
            
            if csv_result.get("already_exists") and not allow_overwrite:
                # CSV已存在，继续检查TXT是否也存在
                print(f"⚠️ CSV文件已存在，检查TXT文件状态...")
                txt_existing = self.check_existing_import(trade_date, 'txt', txt_filename)
                if txt_existing:
                    results["message"] = "CSV和TXT文件都已存在，如需重新导入请设置allow_overwrite=True"
                    results["txt_result"] = {
                        "already_exists": True,
                        "imported_records": txt_existing.imported_records,
                        "skipped_records": txt_existing.skipped_records,
                        "import_date": trade_date.isoformat()
                    }
                    return results
                else:
                    # 只导入TXT文件
                    print(f"🔄 CSV已存在，仅导入TXT数据...")
                    txt_result = await self.import_txt_data(txt_content, txt_filename, allow_overwrite, trade_date)
                    results["txt_result"] = txt_result
                    
                    txt_success = not txt_result.get("already_exists", False) or txt_result.get("imported_records", 0) > 0
                    if txt_success:
                        results["success"] = True
                        results["message"] = f"✅ CSV已存在，仅导入TXT数据({txt_result.get('imported_records', 0)}条)"
                    else:
                        results["message"] = f"⚠️ CSV已存在，TXT导入失败"
                    return results
            
            # 2. 再导入TXT数据（热度数据）
            print(f"🔄 开始导入TXT数据: {txt_filename}")
            txt_result = await self.import_txt_data(txt_content, txt_filename, allow_overwrite, trade_date)
            results["txt_result"] = txt_result
            
            # 3. 检查两个文件是否都成功导入
            csv_success = not csv_result.get("already_exists", False) or csv_result.get("imported_records", 0) > 0
            txt_success = not txt_result.get("already_exists", False) or txt_result.get("imported_records", 0) > 0
            
            if csv_success and txt_success:
                results["success"] = True
                results["message"] = f"✅ 成功导入 {trade_date} 的数据：CSV({csv_result.get('imported_records', 0)}条) + TXT({txt_result.get('imported_records', 0)}条)"
                
                # 创建批量导入记录
                batch_record = self.create_import_record(
                    trade_date, 'both', f"{csv_filename}+{txt_filename}",
                    csv_result.get('imported_records', 0) + txt_result.get('imported_records', 0),
                    csv_result.get('skipped_records', 0) + txt_result.get('skipped_records', 0),
                    'success'
                )
                self.db.commit()
                
                # 触发每日分析计算
                try:
                    print(f"🚀 触发 {trade_date} 的每日分析计算...")
                    from app.services.ranking_calculator import RankingCalculatorService
                    ranking_service = RankingCalculatorService(self.db)
                    analysis_result = await ranking_service.trigger_full_analysis(trade_date)
                    print(f"✅ 分析计算完成: {analysis_result['message']}")
                except Exception as e:
                    print(f"⚠️ 分析计算失败（但导入成功）: {str(e)}")
                    # 不影响导入结果，只记录警告
                
            else:
                results["message"] = f"⚠️ 部分导入失败：CSV({'成功' if csv_success else '失败'}) + TXT({'成功' if txt_success else '失败'})"
            
            return results
            
        except Exception as e:
            self.db.rollback()
            results["message"] = f"❌ 批量导入失败: {str(e)}"
            raise Exception(f"批量导入失败: {str(e)}")
    
    def check_daily_import_completeness(self, trade_date: date) -> Dict[str, Any]:
        """
        检查指定日期的导入完整性
        确保CSV和TXT数据都已导入
        """
        csv_records = self.db.query(DataImportRecord).filter(
            DataImportRecord.import_date == trade_date,
            DataImportRecord.import_type == 'csv',
            DataImportRecord.import_status.in_(['success', 'partial'])
        ).all()
        
        txt_records = self.db.query(DataImportRecord).filter(
            DataImportRecord.import_date == trade_date,
            DataImportRecord.import_type == 'txt',
            DataImportRecord.import_status.in_(['success', 'partial'])
        ).all()
        
        batch_records = self.db.query(DataImportRecord).filter(
            DataImportRecord.import_date == trade_date,
            DataImportRecord.import_type == 'both'
        ).all()
        
        return {
            "trade_date": trade_date.isoformat(),
            "csv_imported": len(csv_records) > 0,
            "txt_imported": len(txt_records) > 0,
            "batch_imported": len(batch_records) > 0,
            "complete": len(csv_records) > 0 and len(txt_records) > 0,
            "csv_records": len(csv_records),
            "txt_records": len(txt_records),
            "batch_records": len(batch_records),
            "ready_for_analysis": len(csv_records) > 0 and len(txt_records) > 0
        }