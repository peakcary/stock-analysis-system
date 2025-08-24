"""
排名计算服务
"""

from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import (
    Stock, Concept, StockConcept, DailyStockData, 
    DailyConceptRanking, DailyConceptSum
)
from datetime import datetime, date, timedelta


class RankingCalculatorService:
    """排名计算服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_daily_rankings(self, trade_date: str) -> Dict[str, Any]:
        """计算指定日期的概念内排名和概念总和"""
        try:
            # 转换日期格式
            if isinstance(trade_date, str):
                trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
            
            processed_concepts = 0
            total_rankings = 0
            new_highs_found = 0
            
            # 获取所有概念
            concepts = self.db.query(Concept).all()
            
            for concept in concepts:
                # 计算概念内排名
                rankings_count = self._calculate_concept_rankings(concept.id, trade_date)
                total_rankings += rankings_count
                
                # 计算概念总和
                is_new_high = self._calculate_concept_sum(concept.id, trade_date)
                if is_new_high:
                    new_highs_found += 1
                
                processed_concepts += 1
            
            # 提交事务
            self.db.commit()
            
            return {
                "processed_concepts": processed_concepts,
                "total_rankings": total_rankings,
                "new_highs_found": new_highs_found
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"排名计算失败: {str(e)}")
    
    def _calculate_concept_rankings(self, concept_id: int, trade_date: date) -> int:
        """计算概念内股票排名"""
        # 获取概念下的所有股票及其当日数据
        stock_data = self.db.query(
            Stock.id,
            DailyStockData.heat_value
        ).join(
            StockConcept, Stock.id == StockConcept.stock_id
        ).join(
            DailyStockData, Stock.id == DailyStockData.stock_id
        ).filter(
            StockConcept.concept_id == concept_id,
            DailyStockData.trade_date == trade_date
        ).order_by(
            desc(DailyStockData.heat_value)
        ).all()
        
        # 删除该概念当日的旧排名数据
        self.db.query(DailyConceptRanking).filter(
            DailyConceptRanking.concept_id == concept_id,
            DailyConceptRanking.trade_date == trade_date
        ).delete()
        
        # 计算并插入新的排名数据
        rankings_created = 0
        for rank, (stock_id, heat_value) in enumerate(stock_data, 1):
            ranking = DailyConceptRanking(
                concept_id=concept_id,
                stock_id=stock_id,
                trade_date=trade_date,
                rank_in_concept=rank,
                heat_value=heat_value or 0
            )
            self.db.add(ranking)
            rankings_created += 1
        
        return rankings_created
    
    def _calculate_concept_sum(self, concept_id: int, trade_date: date, days_for_high_check: int = 10) -> bool:
        """计算概念总和并检查是否创新高"""
        # 获取概念下所有股票的当日热度值
        heat_values = self.db.query(
            DailyStockData.heat_value
        ).join(
            StockConcept, DailyStockData.stock_id == StockConcept.stock_id
        ).filter(
            StockConcept.concept_id == concept_id,
            DailyStockData.trade_date == trade_date,
            DailyStockData.heat_value.isnot(None)
        ).all()
        
        if not heat_values:
            return False
        
        # 计算统计数据
        heat_list = [float(hv[0]) for hv in heat_values if hv[0] is not None]
        if not heat_list:
            return False
            
        total_heat_value = sum(heat_list)
        stock_count = len(heat_list)
        average_heat_value = total_heat_value / stock_count
        
        # 检查是否创新高
        is_new_high = self._check_is_new_high(
            concept_id, trade_date, total_heat_value, days_for_high_check
        )
        
        # 删除该概念当日的旧总和数据
        self.db.query(DailyConceptSum).filter(
            DailyConceptSum.concept_id == concept_id,
            DailyConceptSum.trade_date == trade_date
        ).delete()
        
        # 创建新的概念总和记录
        concept_sum = DailyConceptSum(
            concept_id=concept_id,
            trade_date=trade_date,
            total_heat_value=total_heat_value,
            stock_count=stock_count,
            average_heat_value=average_heat_value,
            is_new_high=is_new_high,
            days_for_high_check=days_for_high_check
        )
        self.db.add(concept_sum)
        
        return is_new_high
    
    def _check_is_new_high(self, concept_id: int, trade_date: date, current_total: float, days: int = 10) -> bool:
        """检查是否为创新高"""
        # 计算检查的起始日期
        start_date = trade_date - timedelta(days=days)
        
        # 查询过去N天的最大总热度值
        max_heat = self.db.query(
            func.max(DailyConceptSum.total_heat_value)
        ).filter(
            DailyConceptSum.concept_id == concept_id,
            DailyConceptSum.trade_date >= start_date,
            DailyConceptSum.trade_date < trade_date
        ).scalar()
        
        # 如果没有历史数据或当前值大于历史最大值，则为创新高
        return max_heat is None or current_total > float(max_heat)
    
    def calculate_concept_rankings_for_period(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """计算一段时间内的排名数据"""
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        total_days_processed = 0
        current_date = start
        
        while current_date <= end:
            try:
                self.calculate_daily_rankings(current_date.isoformat())
                total_days_processed += 1
                print(f"完成日期: {current_date}")
            except Exception as e:
                print(f"日期 {current_date} 处理失败: {str(e)}")
            
            current_date += timedelta(days=1)
        
        return {
            "total_days_processed": total_days_processed,
            "start_date": start_date,
            "end_date": end_date
        }