"""
排名计算服务 - 负责计算每日概念排名和统计数据
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import (
    Stock, DailyStockData, Concept, StockConcept, 
    DailyConceptRanking, DailyConceptSummary, DailyAnalysisTask
)
import logging

logger = logging.getLogger(__name__)


class RankingCalculatorService:
    """排名计算服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_daily_rankings(self, trade_date: date = None) -> Dict[str, Any]:
        """
        计算指定日期的概念排名
        为每个概念内的股票按热度值排名
        """
        if not trade_date:
            trade_date = date.today()
        
        logger.info(f"🚀 开始计算 {trade_date} 的概念排名")
        
        try:
            # 删除当日已存在的排名数据
            self.db.query(DailyConceptRanking).filter(
                DailyConceptRanking.trade_date == trade_date
            ).delete(synchronize_session=False)
            
            total_rankings = 0
            
            # 获取所有概念
            concepts = self.db.query(Concept).all()
            
            for concept in concepts:
                # 获取该概念下的股票及其热度数据
                concept_stocks = self.db.query(
                    StockConcept.stock_id,
                    DailyStockData.heat_value
                ).join(DailyStockData, StockConcept.stock_id == DailyStockData.stock_id).filter(
                    StockConcept.concept_id == concept.id,
                    DailyStockData.trade_date == trade_date,
                    DailyStockData.heat_value > 0
                ).order_by(desc(DailyStockData.heat_value)).all()
                
                if not concept_stocks:
                    continue
                
                # 为该概念的股票分配排名
                rankings_to_insert = []
                for rank, (stock_id, heat_value) in enumerate(concept_stocks, 1):
                    ranking = DailyConceptRanking(
                        concept_id=concept.id,
                        stock_id=stock_id,
                        trade_date=trade_date,
                        rank_in_concept=rank,
                        heat_value=float(heat_value)
                    )
                    rankings_to_insert.append(ranking)
                
                # 批量插入排名数据
                self.db.bulk_save_objects(rankings_to_insert)
                total_rankings += len(rankings_to_insert)
            
            self.db.commit()
            
            logger.info(f"✅ 完成 {trade_date} 的排名计算，共处理 {total_rankings} 条排名记录")
            
            return {
                "success": True,
                "trade_date": trade_date.isoformat(),
                "total_rankings_created": total_rankings,
                "concepts_processed": len(concepts),
                "message": f"成功计算 {len(concepts)} 个概念的股票排名"
            }
            
        except Exception as e:
            logger.error(f"❌ 排名计算失败: {str(e)}")
            raise Exception(f"排名计算失败: {str(e)}")
    
    async def calculate_concept_summaries(self, trade_date: date = None) -> Dict[str, Any]:
        """
        计算概念汇总统计数据
        包括总热度、平均热度、股票数量等
        """
        if not trade_date:
            trade_date = date.today()
        
        logger.info(f"🚀 开始计算 {trade_date} 的概念汇总")
        
        try:
            # 删除当日已存在的汇总数据
            self.db.query(DailyConceptSummary).filter(
                DailyConceptSummary.trade_date == trade_date
            ).delete(synchronize_session=False)
            
            # 计算每个概念的汇总数据
            concept_summaries = self.db.query(
                DailyConceptRanking.concept_id,
                func.sum(DailyConceptRanking.heat_value).label('total_heat'),
                func.count(DailyConceptRanking.stock_id).label('stock_count'),
                func.avg(DailyConceptRanking.heat_value).label('avg_heat'),
                func.max(DailyConceptRanking.heat_value).label('max_heat'),
                func.min(DailyConceptRanking.heat_value).label('min_heat')
            ).filter(
                DailyConceptRanking.trade_date == trade_date
            ).group_by(
                DailyConceptRanking.concept_id
            ).all()
            
            summaries_to_insert = []
            concepts_processed = 0
            
            for summary in concept_summaries:
                concept_id = summary.concept_id
                total_heat = float(summary.total_heat)
                stock_count = summary.stock_count
                avg_heat = float(summary.avg_heat)
                max_heat = float(summary.max_heat)
                min_heat = float(summary.min_heat)
                
                # 检查是否创新高（默认检查10天）
                is_new_high, new_high_days = await self._check_innovation_high(
                    concept_id, total_heat, trade_date, days_back=10
                )
                
                summary_record = DailyConceptSummary(
                    concept_id=concept_id,
                    trade_date=trade_date,
                    total_heat_value=total_heat,
                    stock_count=stock_count,
                    avg_heat_value=avg_heat,
                    max_heat_value=max_heat,
                    min_heat_value=min_heat,
                    is_new_high=is_new_high,
                    new_high_days=new_high_days
                )
                
                summaries_to_insert.append(summary_record)
                concepts_processed += 1
            
            # 批量插入汇总数据
            self.db.bulk_save_objects(summaries_to_insert)
            self.db.commit()
            
            logger.info(f"✅ 完成 {trade_date} 的概念汇总计算，共处理 {concepts_processed} 个概念")
            
            return {
                "success": True,
                "trade_date": trade_date.isoformat(),
                "concepts_processed": concepts_processed,
                "new_high_concepts": len([s for s in summaries_to_insert if s.is_new_high]),
                "message": f"成功计算 {concepts_processed} 个概念的汇总数据"
            }
            
        except Exception as e:
            logger.error(f"❌ 概念汇总计算失败: {str(e)}")
            raise Exception(f"概念汇总计算失败: {str(e)}")
    
    async def _check_innovation_high(self, concept_id: int, current_total_heat: float, 
                                   trade_date: date, days_back: int = 10) -> Tuple[bool, int]:
        """
        检查概念是否创新高
        返回 (是否创新高, 创新高天数)
        """
        # 获取过去N天的概念总热度数据
        start_date = trade_date - timedelta(days=days_back)
        
        historical_data = self.db.query(DailyConceptSummary.total_heat_value).filter(
            DailyConceptSummary.concept_id == concept_id,
            DailyConceptSummary.trade_date >= start_date,
            DailyConceptSummary.trade_date < trade_date
        ).order_by(desc(DailyConceptSummary.total_heat_value)).all()
        
        if not historical_data:
            # 没有历史数据，认为是新高
            return True, days_back
        
        # 获取历史最高值
        max_historical_heat = max(float(record.total_heat_value) for record in historical_data)
        
        # 检查是否创新高
        is_new_high = current_total_heat > max_historical_heat
        
        # 如果创新高，计算创了多少天的新高
        if is_new_high:
            # 倒序查找，找到第一个不小于当前值的记录
            for i in range(len(historical_data)):
                if float(historical_data[i].total_heat_value) >= current_total_heat:
                    return True, i + 1
            return True, days_back
        else:
            return False, 0
    
    def _create_simple_task_log(self, trade_date: date, task_type: str, message: str):
        """创建简单的任务日志记录（适配现有表结构）"""
        try:
            # 这里可以记录到日志或者适配现有的任务表
            logger.info(f"📝 任务记录: {trade_date} - {task_type} - {message}")
        except Exception as e:
            logger.warning(f"⚠️ 任务记录失败: {str(e)}")
    
    async def trigger_full_analysis(self, trade_date: date = None) -> Dict[str, Any]:
        """
        触发完整的每日分析流程
        1. 计算排名 2. 计算汇总 3. 检测创新高
        """
        if not trade_date:
            trade_date = date.today()
        
        logger.info(f"🚀 开始 {trade_date} 的完整分析流程")
        
        results = {
            "trade_date": trade_date.isoformat(),
            "ranking_result": None,
            "summary_result": None,
            "innovation_concepts": [],
            "success": False,
            "message": ""
        }
        
        try:
            # 1. 计算排名
            ranking_result = await self.calculate_daily_rankings(trade_date)
            results["ranking_result"] = ranking_result
            
            # 2. 计算汇总
            summary_result = await self.calculate_concept_summaries(trade_date)
            results["summary_result"] = summary_result
            
            # 3. 检测创新高
            innovation_concepts = await self.detect_innovation_highs(trade_date)
            results["innovation_concepts"] = innovation_concepts
            
            results["success"] = True
            results["message"] = f"✅ 完成 {trade_date} 的完整分析：{summary_result['concepts_processed']} 个概念，{len(innovation_concepts)} 个创新高"
            
            logger.info(results["message"])
            
            return results
            
        except Exception as e:
            results["message"] = f"❌ 分析流程失败: {str(e)}"
            logger.error(results["message"])
            raise Exception(results["message"])
    
    async def detect_innovation_highs(self, trade_date: date = None, days_back: int = 10) -> List[int]:
        """
        检测创新高概念
        返回创新高的概念ID列表
        """
        if not trade_date:
            trade_date = date.today()
        
        # 获取创新高的概念
        innovation_concepts = self.db.query(DailyConceptSummary.concept_id).filter(
            DailyConceptSummary.trade_date == trade_date,
            DailyConceptSummary.is_new_high == True
        ).all()
        
        concept_ids = [concept.concept_id for concept in innovation_concepts]
        
        logger.info(f"✅ 检测到 {len(concept_ids)} 个创新高概念")
        
        return concept_ids