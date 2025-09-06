"""
概念分析服务 - 提供概念数据查询和分析功能
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from app.models import (
    Stock, DailyStockData, Concept, StockConcept,
    DailyConceptRanking, DailyConceptSummary
)
import logging

logger = logging.getLogger(__name__)


class ConceptAnalysisService:
    """概念分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_stock_concepts_ranking(self, stock_id: int, trade_date: date = None) -> List[Dict]:
        """获取股票在各概念中的排名"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        rankings = self.db.query(
            DailyConceptRanking,
            Concept.concept_name,
            DailyConceptSummary.stock_count
        ).join(
            Concept, DailyConceptRanking.concept_id == Concept.id
        ).join(
            DailyConceptSummary, 
            and_(
                DailyConceptSummary.concept_id == DailyConceptRanking.concept_id,
                DailyConceptSummary.trade_date == DailyConceptRanking.trade_date
            )
        ).filter(
            DailyConceptRanking.stock_id == stock_id,
            DailyConceptRanking.trade_date == trade_date
        ).order_by(DailyConceptRanking.rank_in_concept).all()
        
        return [
            {
                "concept_id": ranking.concept_id,
                "concept_name": concept_name,
                "rank": ranking.rank_in_concept,
                "total_stocks": stock_count,
                "heat_value": float(ranking.heat_value),
                "rank_percentage": round((ranking.rank_in_concept / stock_count) * 100, 2)
            }
            for ranking, concept_name, stock_count in rankings
        ]
    
    def get_concept_top_stocks(self, concept_id: int, trade_date: date = None, limit: int = 20) -> Dict[str, Any]:
        """获取概念内排名靠前的股票"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 获取概念信息和汇总数据
        concept_info = self.db.query(
            Concept,
            DailyConceptSummary
        ).outerjoin(
            DailyConceptSummary,
            and_(
                DailyConceptSummary.concept_id == Concept.id,
                DailyConceptSummary.trade_date == trade_date
            )
        ).filter(Concept.id == concept_id).first()
        
        if not concept_info:
            return None
        
        concept, summary = concept_info
        
        # 获取排名数据
        rankings = self.db.query(
            DailyConceptRanking,
            Stock.stock_code,
            Stock.stock_name
        ).join(
            Stock, DailyConceptRanking.stock_id == Stock.id
        ).filter(
            DailyConceptRanking.concept_id == concept_id,
            DailyConceptRanking.trade_date == trade_date
        ).order_by(DailyConceptRanking.rank_in_concept).limit(limit).all()
        
        top_stocks = []
        for ranking, stock_code, stock_name in rankings:
            top_stocks.append({
                "stock_id": ranking.stock_id,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "rank": ranking.rank_in_concept,
                "heat_value": float(ranking.heat_value)
            })
        
        return {
            "concept_id": concept_id,
            "concept_name": concept.concept_name,
            "trade_date": trade_date.isoformat(),
            "summary": {
                "total_heat_value": float(summary.total_heat_value) if summary else 0,
                "stock_count": summary.stock_count if summary else 0,
                "avg_heat_value": float(summary.avg_heat_value) if summary else 0,
                "is_new_high": summary.is_new_high if summary else False,
                "new_high_days": summary.new_high_days if summary else 0
            },
            "top_stocks": top_stocks
        }
    
    def get_innovation_concepts_list(self, trade_date: date = None, days_back: int = 10) -> List[Dict]:
        """获取创新高概念列表"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        innovations = self.db.query(
            DailyConceptSummary,
            Concept.concept_name
        ).join(
            Concept, DailyConceptSummary.concept_id == Concept.id
        ).filter(
            DailyConceptSummary.trade_date == trade_date,
            DailyConceptSummary.is_new_high == True
        ).order_by(desc(DailyConceptSummary.total_heat_value)).all()
        
        innovation_list = []
        for summary, concept_name in innovations:
            # 获取概念前3只热度股票
            top_stocks = self.db.query(
                Stock.stock_code,
                Stock.stock_name,
                DailyConceptRanking.heat_value
            ).join(
                DailyConceptRanking, Stock.id == DailyConceptRanking.stock_id
            ).filter(
                DailyConceptRanking.concept_id == summary.concept_id,
                DailyConceptRanking.trade_date == trade_date
            ).order_by(desc(DailyConceptRanking.heat_value)).limit(3).all()
            
            innovation_list.append({
                "concept_id": summary.concept_id,
                "concept_name": concept_name,
                "total_heat_value": float(summary.total_heat_value),
                "stock_count": summary.stock_count,
                "avg_heat_value": float(summary.avg_heat_value),
                "new_high_days": summary.new_high_days,
                "top_stocks": [
                    {
                        "stock_code": code,
                        "stock_name": name,
                        "heat_value": float(heat)
                    } for code, name, heat in top_stocks
                ]
            })
        
        return innovation_list
    
    def get_convertible_bonds_analysis(self, trade_date: date = None) -> Dict[str, Any]:
        """获取可转债分析数据"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 查询1开头的股票（可转债）
        bonds_data = self.db.query(
            Stock,
            DailyStockData.heat_value
        ).join(
            DailyStockData, Stock.id == DailyStockData.stock_id
        ).filter(
            Stock.stock_code.like('1%'),
            DailyStockData.trade_date == trade_date,
            DailyStockData.heat_value > 0
        ).order_by(desc(DailyStockData.heat_value)).all()
        
        # 计算统计数据
        total_bonds = len(bonds_data)
        if total_bonds == 0:
            return {
                "trade_date": trade_date.isoformat(),
                "statistics": {
                    "total_bonds": 0,
                    "avg_heat_value": 0,
                    "max_heat_value": 0,
                    "total_heat_value": 0
                },
                "bonds": []
            }
        
        heat_values = [float(heat) for _, heat in bonds_data]
        avg_heat = sum(heat_values) / len(heat_values)
        max_heat = max(heat_values)
        total_heat = sum(heat_values)
        
        bonds_list = []
        for stock, heat_value in bonds_data:
            # 获取该债券的概念信息
            concepts = self.db.query(Concept.concept_name).join(
                StockConcept, Concept.id == StockConcept.concept_id
            ).filter(StockConcept.stock_id == stock.id).limit(5).all()
            
            bonds_list.append({
                "stock_id": stock.id,
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "heat_value": float(heat_value),
                "concepts": [concept.concept_name for concept in concepts]
            })
        
        return {
            "trade_date": trade_date.isoformat(),
            "statistics": {
                "total_bonds": total_bonds,
                "avg_heat_value": round(avg_heat, 2),
                "max_heat_value": max_heat,
                "total_heat_value": round(total_heat, 2)
            },
            "bonds": bonds_list
        }
    
    def search_stocks_by_concept(self, concept_name: str, trade_date: date = None) -> Dict[str, Any]:
        """根据概念名称搜索相关股票"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 模糊搜索概念
        concepts = self.db.query(Concept).filter(
            Concept.concept_name.like(f'%{concept_name}%')
        ).all()
        
        if not concepts:
            return {"concepts": [], "stocks": []}
        
        concept_results = []
        all_stocks = []
        
        for concept in concepts:
            # 获取概念下的股票排名
            stocks = self.db.query(
                DailyConceptRanking,
                Stock.stock_code,
                Stock.stock_name
            ).join(
                Stock, DailyConceptRanking.stock_id == Stock.id
            ).filter(
                DailyConceptRanking.concept_id == concept.id,
                DailyConceptRanking.trade_date == trade_date
            ).order_by(DailyConceptRanking.rank_in_concept).limit(10).all()
            
            stock_list = []
            for ranking, stock_code, stock_name in stocks:
                stock_info = {
                    "stock_id": ranking.stock_id,
                    "stock_code": stock_code,
                    "stock_name": stock_name,
                    "rank": ranking.rank_in_concept,
                    "heat_value": float(ranking.heat_value)
                }
                stock_list.append(stock_info)
                all_stocks.append({**stock_info, "concept_name": concept.concept_name})
            
            # 获取概念汇总数据
            summary = self.db.query(DailyConceptSummary).filter(
                DailyConceptSummary.concept_id == concept.id,
                DailyConceptSummary.trade_date == trade_date
            ).first()
            
            concept_results.append({
                "concept_id": concept.id,
                "concept_name": concept.concept_name,
                "summary": {
                    "total_heat_value": float(summary.total_heat_value) if summary else 0,
                    "stock_count": summary.stock_count if summary else 0,
                    "is_new_high": summary.is_new_high if summary else False
                },
                "top_stocks": stock_list
            })
        
        return {
            "trade_date": trade_date.isoformat(),
            "search_keyword": concept_name,
            "concepts": concept_results,
            "all_stocks": sorted(all_stocks, key=lambda x: x["heat_value"], reverse=True)[:50]
        }
    
    def get_concept_history_trend(self, concept_id: int, days: int = 30) -> Dict[str, Any]:
        """获取概念历史趋势数据"""
        
        end_date = self._get_latest_trade_date()
        start_date = end_date - timedelta(days=days)
        
        # 获取概念信息
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            return None
        
        # 获取历史汇总数据
        history_data = self.db.query(DailyConceptSummary).filter(
            DailyConceptSummary.concept_id == concept_id,
            DailyConceptSummary.trade_date >= start_date,
            DailyConceptSummary.trade_date <= end_date
        ).order_by(DailyConceptSummary.trade_date).all()
        
        trend_data = []
        for summary in history_data:
            trend_data.append({
                "date": summary.trade_date.isoformat(),
                "total_heat_value": float(summary.total_heat_value),
                "stock_count": summary.stock_count,
                "avg_heat_value": float(summary.avg_heat_value),
                "is_new_high": summary.is_new_high
            })
        
        return {
            "concept_id": concept_id,
            "concept_name": concept.concept_name,
            "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
            "trend_data": trend_data
        }
    
    def _get_latest_trade_date(self) -> date:
        """获取最新交易日期"""
        latest = self.db.query(DailyStockData.trade_date).order_by(
            desc(DailyStockData.trade_date)
        ).first()
        
        if not latest:
            return date.today()
        
        return latest.trade_date
    
    def get_hot_concepts_ranking(self, trade_date: date = None, limit: int = 50) -> List[Dict]:
        """获取热门概念排行"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        hot_concepts = self.db.query(
            DailyConceptSummary,
            Concept.concept_name
        ).join(
            Concept, DailyConceptSummary.concept_id == Concept.id
        ).filter(
            DailyConceptSummary.trade_date == trade_date
        ).order_by(desc(DailyConceptSummary.total_heat_value)).limit(limit).all()
        
        ranking_list = []
        for rank, (summary, concept_name) in enumerate(hot_concepts, 1):
            ranking_list.append({
                "rank": rank,
                "concept_id": summary.concept_id,
                "concept_name": concept_name,
                "total_heat_value": float(summary.total_heat_value),
                "stock_count": summary.stock_count,
                "avg_heat_value": float(summary.avg_heat_value),
                "is_new_high": summary.is_new_high,
                "new_high_days": summary.new_high_days if summary.is_new_high else 0
            })
        
        return ranking_list