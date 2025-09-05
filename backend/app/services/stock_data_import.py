"""
股票概念数据导入服务
Stock Concept Data Import Service
"""

import csv
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
import logging
import re
from pathlib import Path

from app.core.database import get_db
from app.core.logging import logger
from app.models.stock_data import (
    StockInfo, DailyStockConceptData, StockConceptCategory, DailyStockConcept, 
    ConceptDailyStats, StockConceptRanking, DataImportLog
)


class StockDataImportService:
    """股票概念数据导入服务"""
    
    def __init__(self):
        self.logger = logger
        
    def parse_stock_code(self, code: str) -> Tuple[str, str]:
        """解析股票代码，返回(纯代码, 市场)"""
        if code.startswith('SH'):
            return code[2:], 'SH'
        elif code.startswith('SZ'):
            return code[2:], 'SZ'
        else:
            # 纯数字代码，根据规则判断市场
            if code.startswith('6'):
                return code, 'SH'
            elif code.startswith(('0', '3')):
                return code, 'SZ'
            elif code.startswith('1'):
                # 转债，需要更细致的判断
                if len(code) == 6:
                    if code.startswith('11'):
                        return code, 'SH'  # 上交所转债
                    elif code.startswith('12'):
                        return code, 'SZ'  # 深交所转债
            return code, 'UNKNOWN'
    
    async def import_csv_data(
        self, 
        file_path: str, 
        trade_date: date,
        db: Session
    ) -> Dict[str, Any]:
        """导入CSV文件数据"""
        
        start_time = datetime.now()
        
        # 创建导入日志
        import_log = DataImportLog(
            import_date=trade_date,
            import_type='csv',
            file_name=Path(file_path).name,
            status='processing'
        )
        db.add(import_log)
        db.commit()
        
        try:
            total_records = 0
            success_records = 0
            failed_records = 0
            
            # 读取CSV文件
            df = pd.read_csv(file_path)
            total_records = len(df)
            
            # 数据清理和处理
            stock_data_map = {}  # 股票代码 -> 股票基础信息
            stock_concepts_map = {}  # 股票代码 -> [概念列表]
            concepts_set = set()  # 所有概念的集合
            
            for index, row in df.iterrows():
                try:
                    stock_code = str(row['股票代码']).strip()
                    stock_name = str(row['股票名称']).strip() if pd.notna(row['股票名称']) else ''
                    concept_name = str(row['概念']).strip() if pd.notna(row['概念']) else ''
                    
                    # 跳过无效数据
                    if not stock_code or not concept_name or concept_name == 'None':
                        continue
                    
                    # 收集股票基础信息
                    if stock_code not in stock_data_map:
                        stock_data_map[stock_code] = {
                            'name': stock_name,
                            'total_pages': int(row['全部页数']) if pd.notna(row['全部页数']) else 0,
                            'hot_page_views': int(row['热帖首页页阅读总数']) if pd.notna(row['热帖首页页阅读总数']) else 0,
                            'price': float(row['价格']) if pd.notna(row['价格']) and row['价格'] != 0 else None,
                            'industry': str(row['行业']).strip() if pd.notna(row['行业']) and str(row['行业']) != 'None' else '',
                            'turnover_rate': float(row['换手']) if pd.notna(row['换手']) else 0.0,
                            'net_inflow': float(row['净流入']) if pd.notna(row['净流入']) else 0.0,
                        }
                    
                    # 收集概念信息
                    if stock_code not in stock_concepts_map:
                        stock_concepts_map[stock_code] = []
                    stock_concepts_map[stock_code].append(concept_name)
                    concepts_set.add(concept_name)
                    
                    success_records += 1
                    
                except Exception as e:
                    failed_records += 1
                    self.logger.warning(f"处理CSV行数据失败: {index}, 错误: {e}")
            
            # 批量插入/更新数据
            await self._bulk_upsert_stocks(stock_data_map, db)
            await self._bulk_upsert_concepts(concepts_set, db)
            await self._bulk_upsert_daily_stock_data(stock_data_map, trade_date, db)
            await self._bulk_upsert_stock_concepts(stock_concepts_map, trade_date, db)
            
            # 更新导入日志
            processing_time = (datetime.now() - start_time).total_seconds()
            import_log.status = 'success'
            import_log.total_records = total_records
            import_log.success_records = success_records
            import_log.failed_records = failed_records
            import_log.processing_time = processing_time
            import_log.completed_at = datetime.now()
            db.commit()
            
            self.logger.info(f"CSV数据导入完成: 总计{total_records}条, 成功{success_records}条, 失败{failed_records}条")
            
            return {
                'success': True,
                'message': f'CSV数据导入成功',
                'total_records': total_records,
                'success_records': success_records,
                'failed_records': failed_records,
                'processing_time': processing_time
            }
            
        except Exception as e:
            # 更新导入日志为失败
            import_log.status = 'failed'
            import_log.error_message = str(e)
            import_log.completed_at = datetime.now()
            db.commit()
            
            self.logger.error(f"CSV数据导入失败: {e}")
            return {
                'success': False,
                'message': f'CSV数据导入失败: {str(e)}',
                'total_records': 0,
                'success_records': 0,
                'failed_records': 0
            }
    
    async def import_txt_data(
        self, 
        file_path: str, 
        trade_date: date,
        db: Session
    ) -> Dict[str, Any]:
        """导入TXT文件数据(成交量数据)"""
        
        start_time = datetime.now()
        
        # 创建导入日志
        import_log = DataImportLog(
            import_date=trade_date,
            import_type='txt',
            file_name=Path(file_path).name,
            status='processing'
        )
        db.add(import_log)
        db.commit()
        
        try:
            total_records = 0
            success_records = 0
            failed_records = 0
            
            volume_data = {}  # 股票代码 -> 成交量
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 解析格式: SH600000	2025-08-21	459400
                        parts = line.split('\t')
                        if len(parts) != 3:
                            continue
                        
                        full_code, date_str, volume_str = parts
                        stock_code, market = self.parse_stock_code(full_code)
                        volume = int(volume_str)
                        
                        volume_data[stock_code] = volume
                        total_records += 1
                        success_records += 1
                        
                    except Exception as e:
                        failed_records += 1
                        self.logger.warning(f"处理TXT行数据失败: 第{line_num}行, 错误: {e}")
            
            # 批量更新成交量数据
            await self._bulk_update_volume_data(volume_data, trade_date, db)
            
            # 更新导入日志
            processing_time = (datetime.now() - start_time).total_seconds()
            import_log.status = 'success'
            import_log.total_records = total_records
            import_log.success_records = success_records
            import_log.failed_records = failed_records
            import_log.processing_time = processing_time
            import_log.completed_at = datetime.now()
            db.commit()
            
            self.logger.info(f"TXT数据导入完成: 总计{total_records}条, 成功{success_records}条, 失败{failed_records}条")
            
            return {
                'success': True,
                'message': f'TXT数据导入成功',
                'total_records': total_records,
                'success_records': success_records,
                'failed_records': failed_records,
                'processing_time': processing_time
            }
            
        except Exception as e:
            # 更新导入日志为失败
            import_log.status = 'failed'
            import_log.error_message = str(e)
            import_log.completed_at = datetime.now()
            db.commit()
            
            self.logger.error(f"TXT数据导入失败: {e}")
            return {
                'success': False,
                'message': f'TXT数据导入失败: {str(e)}',
                'total_records': 0,
                'success_records': 0,
                'failed_records': 0
            }
    
    async def calculate_concept_rankings(
        self, 
        trade_date: date,
        db: Session
    ) -> Dict[str, Any]:
        """计算概念排名和统计数据"""
        
        start_time = datetime.now()
        
        try:
            # 删除当日旧的计算结果
            db.query(ConceptDailyStats).filter(ConceptDailyStats.trade_date == trade_date).delete()
            db.query(StockConceptRanking).filter(StockConceptRanking.trade_date == trade_date).delete()
            db.commit()
            
            # 获取当日所有概念
            concepts = db.query(DailyStockConcept.concept_name).filter(
                DailyStockConcept.trade_date == trade_date
            ).distinct().all()
            
            total_concepts = len(concepts)
            processed_concepts = 0
            
            for (concept_name,) in concepts:
                # 计算概念统计数据和排名
                await self._calculate_concept_stats_and_rankings(concept_name, trade_date, db)
                processed_concepts += 1
                
                if processed_concepts % 100 == 0:
                    self.logger.info(f"概念计算进度: {processed_concepts}/{total_concepts}")
            
            db.commit()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"概念排名计算完成: 处理了{processed_concepts}个概念, 耗时{processing_time:.2f}秒")
            
            return {
                'success': True,
                'message': f'概念排名计算成功',
                'processed_concepts': processed_concepts,
                'processing_time': processing_time
            }
            
        except Exception as e:
            db.rollback()
            self.logger.error(f"概念排名计算失败: {e}")
            return {
                'success': False,
                'message': f'概念排名计算失败: {str(e)}',
                'processed_concepts': 0
            }
    
    async def _bulk_upsert_stocks(self, stock_data_map: Dict, db: Session):
        """批量插入/更新股票基础信息"""
        for stock_code, data in stock_data_map.items():
            pure_code, market = self.parse_stock_code(stock_code)
            
            stock = db.query(StockInfo).filter(StockInfo.code == pure_code).first()
            if not stock:
                stock = StockInfo(
                    code=pure_code,
                    name=data['name'],
                    market=market,
                    current_industry=data['industry']
                )
                db.add(stock)
            else:
                stock.name = data['name'] or stock.name
                stock.current_industry = data['industry'] or stock.current_industry
                stock.updated_at = datetime.now()
    
    async def _bulk_upsert_concepts(self, concepts_set: set, db: Session):
        """批量插入概念"""
        existing_concepts = set(db.query(StockConceptCategory.name).all())
        existing_concepts = {c[0] for c in existing_concepts}
        
        new_concepts = concepts_set - existing_concepts
        
        for concept_name in new_concepts:
            concept = StockConceptCategory(name=concept_name)
            db.add(concept)
    
    async def _bulk_upsert_daily_stock_data(self, stock_data_map: Dict, trade_date: date, db: Session):
        """批量插入每日股票数据"""
        for stock_code, data in stock_data_map.items():
            pure_code, _ = self.parse_stock_code(stock_code)
            
            # 使用ON DUPLICATE KEY UPDATE语法或先查询再插入
            existing = db.query(DailyStockConceptData).filter(
                and_(
                    DailyStockConceptData.stock_code == pure_code,
                    DailyStockConceptData.trade_date == trade_date
                )
            ).first()
            
            if not existing:
                daily_data = DailyStockConceptData(
                    stock_code=pure_code,
                    stock_name=data['name'],
                    trade_date=trade_date,
                    total_pages=data['total_pages'],
                    hot_page_views=data['hot_page_views'],
                    price=data['price'],
                    industry=data['industry'],
                    turnover_rate=data['turnover_rate'],
                    net_inflow=data['net_inflow']
                )
                db.add(daily_data)
            else:
                # 更新现有记录
                existing.stock_name = data['name']
                existing.total_pages = data['total_pages']
                existing.hot_page_views = data['hot_page_views']
                existing.price = data['price']
                existing.industry = data['industry']
                existing.turnover_rate = data['turnover_rate']
                existing.net_inflow = data['net_inflow']
    
    async def _bulk_upsert_stock_concepts(self, stock_concepts_map: Dict, trade_date: date, db: Session):
        """批量插入股票概念关联"""
        # 先删除当日旧的关联数据
        db.query(DailyStockConcept).filter(DailyStockConcept.trade_date == trade_date).delete()
        
        # 插入新的关联数据
        for stock_code, concepts in stock_concepts_map.items():
            pure_code, _ = self.parse_stock_code(stock_code)
            
            for concept_name in concepts:
                stock_concept = DailyStockConcept(
                    stock_code=pure_code,
                    concept_name=concept_name,
                    trade_date=trade_date
                )
                db.add(stock_concept)
    
    async def _bulk_update_volume_data(self, volume_data: Dict, trade_date: date, db: Session):
        """批量更新成交量数据"""
        for stock_code, volume in volume_data.items():
            pure_code, _ = self.parse_stock_code(stock_code)
            
            # 更新当日股票数据的成交量
            daily_data = db.query(DailyStockConceptData).filter(
                and_(
                    DailyStockConceptData.stock_code == pure_code,
                    DailyStockConceptData.trade_date == trade_date
                )
            ).first()
            
            if daily_data:
                daily_data.volume = volume
            else:
                # 如果不存在对应的每日数据，创建一个只有成交量的记录
                daily_data = DailyStockConceptData(
                    stock_code=pure_code,
                    trade_date=trade_date,
                    volume=volume
                )
                db.add(daily_data)
    
    async def _calculate_concept_stats_and_rankings(self, concept_name: str, trade_date: date, db: Session):
        """计算单个概念的统计数据和排名"""
        
        # 获取概念下所有股票的数据
        concept_stocks_query = text("""
            SELECT 
                dsd.stock_code,
                dsd.stock_name,
                dsd.volume,
                dsd.hot_page_views
            FROM stock_concept_daily_data dsd
            INNER JOIN stock_concept_daily_relations dsc ON dsd.stock_code = dsc.stock_code AND dsd.trade_date = dsc.trade_date
            WHERE dsc.concept_name = :concept_name AND dsd.trade_date = :trade_date
            AND dsd.volume IS NOT NULL
            ORDER BY dsd.volume DESC
        """)
        
        results = db.execute(concept_stocks_query, {
            'concept_name': concept_name, 
            'trade_date': trade_date
        }).fetchall()
        
        if not results:
            return
        
        # 计算概念统计数据
        volumes = [r.volume for r in results if r.volume]
        hot_views = [r.hot_page_views for r in results if r.hot_page_views]
        
        total_volume = sum(volumes) if volumes else 0
        stock_count = len(results)
        avg_volume = total_volume / stock_count if stock_count > 0 else 0
        max_volume = max(volumes) if volumes else 0
        min_volume = min(volumes) if volumes else 0
        total_hot_views = sum(hot_views) if hot_views else 0
        avg_hot_views = total_hot_views / len(hot_views) if hot_views else 0
        
        # 插入概念统计数据
        concept_stats = ConceptDailyStats(
            concept_name=concept_name,
            trade_date=trade_date,
            total_volume=total_volume,
            stock_count=stock_count,
            avg_volume=avg_volume,
            max_volume=max_volume,
            min_volume=min_volume,
            total_hot_views=total_hot_views,
            avg_hot_views=avg_hot_views
        )
        db.add(concept_stats)
        
        # 计算排名数据
        volume_rankings = []
        hot_rankings = []
        
        # 成交量排名
        for rank, result in enumerate(results, 1):
            if result.volume:
                volume_ratio = (result.volume / total_volume * 100) if total_volume > 0 else 0
                volume_rankings.append({
                    'stock_code': result.stock_code,
                    'stock_name': result.stock_name,
                    'rank': rank,
                    'volume': result.volume,
                    'ratio': round(volume_ratio, 2)
                })
        
        # 热度排名
        hot_sorted = sorted([r for r in results if r.hot_page_views], 
                           key=lambda x: x.hot_page_views, reverse=True)
        
        for rank, result in enumerate(hot_sorted, 1):
            hot_ratio = (result.hot_page_views / total_hot_views * 100) if total_hot_views > 0 else 0
            hot_rankings.append({
                'stock_code': result.stock_code,
                'stock_name': result.stock_name,
                'rank': rank,
                'hot_views': result.hot_page_views,
                'ratio': round(hot_ratio, 2)
            })
        
        # 合并排名数据并插入
        hot_rank_map = {r['stock_code']: r for r in hot_rankings}
        
        for vol_rank in volume_rankings:
            hot_rank_info = hot_rank_map.get(vol_rank['stock_code'], {})
            
            ranking = StockConceptRanking(
                stock_code=vol_rank['stock_code'],
                stock_name=vol_rank['stock_name'],
                concept_name=concept_name,
                trade_date=trade_date,
                volume_rank=vol_rank['rank'],
                volume=vol_rank['volume'],
                volume_ratio=vol_rank['ratio'],
                hot_views_rank=hot_rank_info.get('rank'),
                hot_page_views=hot_rank_info.get('hot_views'),
                hot_views_ratio=hot_rank_info.get('ratio')
            )
            db.add(ranking)


# 创建服务实例
stock_data_import_service = StockDataImportService()