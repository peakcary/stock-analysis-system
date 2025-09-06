"""
图表数据服务 - 为前端图表组件提供数据支持
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


class ChartDataService:
    """图表数据服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_concept_heat_trend_chart(self, concept_id: int, days: int = 30) -> Dict[str, Any]:
        """获取概念热度趋势图表数据"""
        
        end_date = self._get_latest_trade_date()
        start_date = end_date - timedelta(days=days)
        
        # 获取概念信息
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            return None
        
        # 获取历史数据
        history_data = self.db.query(DailyConceptSummary).filter(
            DailyConceptSummary.concept_id == concept_id,
            DailyConceptSummary.trade_date >= start_date,
            DailyConceptSummary.trade_date <= end_date
        ).order_by(DailyConceptSummary.trade_date).all()
        
        # 构建图表数据
        dates = []
        total_heat_values = []
        avg_heat_values = []
        stock_counts = []
        new_high_markers = []
        
        for summary in history_data:
            dates.append(summary.trade_date.isoformat())
            total_heat_values.append(float(summary.total_heat_value))
            avg_heat_values.append(float(summary.avg_heat_value))
            stock_counts.append(summary.stock_count)
            new_high_markers.append(1 if summary.is_new_high else 0)
        
        return {
            "concept_id": concept_id,
            "concept_name": concept.concept_name,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "chart_data": {
                "dates": dates,
                "series": [
                    {
                        "name": "总热度值",
                        "data": total_heat_values,
                        "type": "line",
                        "yAxisIndex": 0
                    },
                    {
                        "name": "平均热度值",
                        "data": avg_heat_values,
                        "type": "line",
                        "yAxisIndex": 0
                    },
                    {
                        "name": "股票数量",
                        "data": stock_counts,
                        "type": "bar",
                        "yAxisIndex": 1
                    },
                    {
                        "name": "创新高",
                        "data": new_high_markers,
                        "type": "scatter",
                        "yAxisIndex": 2
                    }
                ]
            }
        }
    
    def get_daily_hot_concepts_chart(self, trade_date: date = None, top_n: int = 20) -> Dict[str, Any]:
        """获取每日热门概念柱状图数据"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 获取热门概念数据
        hot_concepts = self.db.query(
            DailyConceptSummary,
            Concept.concept_name
        ).join(
            Concept, DailyConceptSummary.concept_id == Concept.id
        ).filter(
            DailyConceptSummary.trade_date == trade_date
        ).order_by(desc(DailyConceptSummary.total_heat_value)).limit(top_n).all()
        
        # 构建图表数据
        concept_names = []
        heat_values = []
        stock_counts = []
        new_high_flags = []
        
        for summary, concept_name in hot_concepts:
            concept_names.append(concept_name)
            heat_values.append(float(summary.total_heat_value))
            stock_counts.append(summary.stock_count)
            new_high_flags.append(summary.is_new_high)
        
        return {
            "trade_date": trade_date.isoformat(),
            "chart_data": {
                "categories": concept_names,
                "series": [
                    {
                        "name": "总热度值",
                        "data": heat_values,
                        "type": "bar"
                    },
                    {
                        "name": "股票数量",
                        "data": stock_counts,
                        "type": "line",
                        "yAxisIndex": 1
                    }
                ],
                "new_high_concepts": [
                    {"name": name, "value": heat, "is_new_high": flag}
                    for name, heat, flag in zip(concept_names, heat_values, new_high_flags)
                    if flag
                ]
            }
        }
    
    def get_stock_heat_distribution_chart(self, concept_id: int, trade_date: date = None) -> Dict[str, Any]:
        """获取概念内股票热度分布图表数据"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 获取概念信息
        concept = self.db.query(Concept).filter(Concept.id == concept_id).first()
        if not concept:
            return None
        
        # 获取股票排名数据
        rankings = self.db.query(
            DailyConceptRanking,
            Stock.stock_code,
            Stock.stock_name
        ).join(
            Stock, DailyConceptRanking.stock_id == Stock.id
        ).filter(
            DailyConceptRanking.concept_id == concept_id,
            DailyConceptRanking.trade_date == trade_date
        ).order_by(DailyConceptRanking.rank_in_concept).all()
        
        # 构建分布数据
        heat_ranges = {
            "0-10": 0, "10-20": 0, "20-30": 0, "30-50": 0, 
            "50-100": 0, "100-200": 0, "200+": 0
        }
        
        stock_data = []
        for ranking, stock_code, stock_name in rankings:
            heat_value = float(ranking.heat_value)
            stock_data.append({
                "stock_code": stock_code,
                "stock_name": stock_name,
                "rank": ranking.rank_in_concept,
                "heat_value": heat_value
            })
            
            # 统计热度区间分布
            if heat_value < 10:
                heat_ranges["0-10"] += 1
            elif heat_value < 20:
                heat_ranges["10-20"] += 1
            elif heat_value < 30:
                heat_ranges["20-30"] += 1
            elif heat_value < 50:
                heat_ranges["30-50"] += 1
            elif heat_value < 100:
                heat_ranges["50-100"] += 1
            elif heat_value < 200:
                heat_ranges["100-200"] += 1
            else:
                heat_ranges["200+"] += 1
        
        return {
            "concept_id": concept_id,
            "concept_name": concept.concept_name,
            "trade_date": trade_date.isoformat(),
            "distribution_chart": {
                "categories": list(heat_ranges.keys()),
                "data": list(heat_ranges.values())
            },
            "scatter_chart": {
                "data": [
                    {"x": stock["rank"], "y": stock["heat_value"], "name": stock["stock_name"]}
                    for stock in stock_data
                ]
            },
            "stock_count": len(stock_data)
        }
    
    def get_innovation_concepts_timeline_chart(self, days: int = 30) -> Dict[str, Any]:
        """获取创新高概念时间线图表数据"""
        
        end_date = self._get_latest_trade_date()
        start_date = end_date - timedelta(days=days)
        
        # 获取时间段内的创新高数据
        innovation_data = self.db.query(
            DailyConceptSummary,
            Concept.concept_name
        ).join(
            Concept, DailyConceptSummary.concept_id == Concept.id
        ).filter(
            DailyConceptSummary.trade_date >= start_date,
            DailyConceptSummary.trade_date <= end_date,
            DailyConceptSummary.is_new_high == True
        ).order_by(DailyConceptSummary.trade_date).all()
        
        # 按日期分组
        daily_innovations = {}
        for summary, concept_name in innovation_data:
            date_str = summary.trade_date.isoformat()
            if date_str not in daily_innovations:
                daily_innovations[date_str] = {
                    "date": date_str,
                    "count": 0,
                    "concepts": [],
                    "total_heat": 0
                }
            
            daily_innovations[date_str]["count"] += 1
            daily_innovations[date_str]["concepts"].append({
                "concept_id": summary.concept_id,
                "concept_name": concept_name,
                "heat_value": float(summary.total_heat_value),
                "new_high_days": summary.new_high_days
            })
            daily_innovations[date_str]["total_heat"] += float(summary.total_heat_value)
        
        # 构建时间线数据
        timeline_data = list(daily_innovations.values())
        timeline_data.sort(key=lambda x: x["date"])
        
        # 构建图表数据
        dates = []
        counts = []
        total_heats = []
        
        for item in timeline_data:
            dates.append(item["date"])
            counts.append(item["count"])
            total_heats.append(item["total_heat"])
        
        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "chart_data": {
                "dates": dates,
                "series": [
                    {
                        "name": "创新高概念数量",
                        "data": counts,
                        "type": "bar",
                        "yAxisIndex": 0
                    },
                    {
                        "name": "总热度值",
                        "data": total_heats,
                        "type": "line",
                        "yAxisIndex": 1
                    }
                ]
            },
            "timeline_details": timeline_data
        }
    
    def get_convertible_bonds_analysis_chart(self, trade_date: date = None) -> Dict[str, Any]:
        """获取可转债分析图表数据"""
        
        if not trade_date:
            trade_date = self._get_latest_trade_date()
        
        # 获取可转债数据
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
        
        if not bonds_data:
            return {"error": "暂无可转债数据"}
        
        # 热度分布统计
        heat_ranges = {
            "0-5": 0, "5-10": 0, "10-20": 0, "20-50": 0, "50+": 0
        }
        
        bond_list = []
        heat_values = []
        
        for stock, heat_value in bonds_data:
            heat = float(heat_value)
            bond_list.append({
                "stock_code": stock.stock_code,
                "stock_name": stock.stock_name,
                "heat_value": heat
            })
            heat_values.append(heat)
            
            # 统计热度分布
            if heat < 5:
                heat_ranges["0-5"] += 1
            elif heat < 10:
                heat_ranges["5-10"] += 1
            elif heat < 20:
                heat_ranges["10-20"] += 1
            elif heat < 50:
                heat_ranges["20-50"] += 1
            else:
                heat_ranges["50+"] += 1
        
        # 计算统计数据
        avg_heat = sum(heat_values) / len(heat_values)
        max_heat = max(heat_values)
        
        return {
            "trade_date": trade_date.isoformat(),
            "statistics": {
                "total_bonds": len(bond_list),
                "avg_heat_value": round(avg_heat, 2),
                "max_heat_value": max_heat
            },
            "distribution_chart": {
                "categories": list(heat_ranges.keys()),
                "data": list(heat_ranges.values())
            },
            "top_bonds_chart": {
                "categories": [bond["stock_name"][:6] for bond in bond_list[:20]],
                "data": [bond["heat_value"] for bond in bond_list[:20]]
            },
            "all_bonds": bond_list
        }
    
    def get_multi_concept_comparison_chart(self, concept_ids: List[int], days: int = 30) -> Dict[str, Any]:
        """获取多概念对比图表数据"""
        
        end_date = self._get_latest_trade_date()
        start_date = end_date - timedelta(days=days)
        
        # 获取概念信息
        concepts = self.db.query(Concept).filter(Concept.id.in_(concept_ids)).all()
        concept_dict = {c.id: c.concept_name for c in concepts}
        
        # 获取历史数据
        comparison_data = {}
        for concept_id in concept_ids:
            history = self.db.query(DailyConceptSummary).filter(
                DailyConceptSummary.concept_id == concept_id,
                DailyConceptSummary.trade_date >= start_date,
                DailyConceptSummary.trade_date <= end_date
            ).order_by(DailyConceptSummary.trade_date).all()
            
            comparison_data[concept_id] = {
                "concept_name": concept_dict.get(concept_id, f"概念{concept_id}"),
                "dates": [h.trade_date.isoformat() for h in history],
                "heat_values": [float(h.total_heat_value) for h in history],
                "avg_heat_values": [float(h.avg_heat_value) for h in history],
                "stock_counts": [h.stock_count for h in history]
            }
        
        # 构建对比图表数据
        all_dates = set()
        for data in comparison_data.values():
            all_dates.update(data["dates"])
        
        sorted_dates = sorted(list(all_dates))
        
        series_data = []
        for concept_id, data in comparison_data.items():
            # 补齐缺失日期的数据
            aligned_heat_values = []
            date_heat_map = dict(zip(data["dates"], data["heat_values"]))
            
            for date_str in sorted_dates:
                aligned_heat_values.append(date_heat_map.get(date_str, 0))
            
            series_data.append({
                "name": data["concept_name"],
                "data": aligned_heat_values,
                "type": "line"
            })
        
        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "concept_ids": concept_ids,
            "chart_data": {
                "dates": sorted_dates,
                "series": series_data
            },
            "comparison_summary": {
                concept_id: {
                    "concept_name": data["concept_name"],
                    "latest_heat": data["heat_values"][-1] if data["heat_values"] else 0,
                    "avg_heat": round(sum(data["heat_values"]) / len(data["heat_values"]), 2) if data["heat_values"] else 0,
                    "max_heat": max(data["heat_values"]) if data["heat_values"] else 0
                }
                for concept_id, data in comparison_data.items()
            }
        }
    
    def _get_latest_trade_date(self) -> date:
        """获取最新交易日期"""
        latest = self.db.query(DailyStockData.trade_date).order_by(
            desc(DailyStockData.trade_date)
        ).first()
        
        if not latest:
            return date.today()
        
        return latest.trade_date