"""
每日分析服务 - 生成个股排名和概念汇总
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, asc, func
import pandas as pd

from app.models.simple_import import StockConceptData
from app.models.daily_analysis import DailyConceptRanking, DailyConceptSummary, DailyAnalysisTask


class DailyAnalysisService:
    """每日分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_daily_analysis(self, analysis_date: Optional[date] = None) -> Dict[str, Any]:
        """
        生成指定日期的完整分析报告
        
        Args:
            analysis_date: 分析日期，默认为今天
            
        Returns:
            分析结果统计
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        print(f"🔍 开始生成 {analysis_date} 的每日分析报告...")
        
        # 创建分析任务记录
        ranking_task = DailyAnalysisTask(
            analysis_date=analysis_date,
            task_type='concept_ranking',
            start_time=datetime.now()
        )
        summary_task = DailyAnalysisTask(
            analysis_date=analysis_date, 
            task_type='concept_summary',
            start_time=datetime.now()
        )
        
        self.db.add(ranking_task)
        self.db.add(summary_task)
        self.db.commit()
        
        try:
            # 1. 生成个股概念排名
            ranking_result = self._generate_concept_rankings(analysis_date, ranking_task)
            
            # 2. 生成概念汇总统计
            summary_result = self._generate_concept_summaries(analysis_date, summary_task)
            
            print(f"✅ {analysis_date} 每日分析报告生成完成")
            
            return {
                "success": True,
                "analysis_date": analysis_date.isoformat(),
                "concept_rankings": ranking_result,
                "concept_summaries": summary_result,
                "message": f"{analysis_date} 每日分析报告生成完成"
            }
            
        except Exception as e:
            # 更新任务失败状态
            ranking_task.status = 'failed'
            ranking_task.error_message = str(e)
            ranking_task.end_time = datetime.now()
            
            summary_task.status = 'failed'
            summary_task.error_message = str(e)
            summary_task.end_time = datetime.now()
            
            self.db.commit()
            
            raise Exception(f"每日分析失败: {str(e)}")
    
    def _generate_concept_rankings(self, analysis_date: date, task: DailyAnalysisTask) -> Dict[str, Any]:
        """生成概念内个股排名（优化版）"""
        
        print(f"📊 正在生成概念内个股排名...")
        
        try:
            # 清除该日期的旧排名数据
            self.db.query(DailyConceptRanking).filter(
                DailyConceptRanking.analysis_date == analysis_date
            ).delete(synchronize_session=False)
            self.db.commit()
            
            # 使用SQL直接计算排名，避免全量加载到内存
            ranking_sql = text("""
                INSERT INTO daily_stock_concept_rankings (
                    analysis_date, concept, stock_code, stock_name,
                    net_inflow_rank, price_rank, turnover_rate_rank, total_reads_rank,
                    net_inflow, price, turnover_rate, total_reads, page_count, industry,
                    created_at
                )
                SELECT 
                    :analysis_date as analysis_date,
                    concept,
                    stock_code,
                    stock_name,
                    ROW_NUMBER() OVER (PARTITION BY concept ORDER BY COALESCE(net_inflow, 0) DESC) as net_inflow_rank,
                    ROW_NUMBER() OVER (PARTITION BY concept ORDER BY COALESCE(price, 0) DESC) as price_rank,
                    ROW_NUMBER() OVER (PARTITION BY concept ORDER BY COALESCE(turnover_rate, 0) DESC) as turnover_rate_rank,
                    ROW_NUMBER() OVER (PARTITION BY concept ORDER BY COALESCE(total_reads, 0) DESC) as total_reads_rank,
                    net_inflow,
                    price,
                    turnover_rate,
                    total_reads,
                    page_count,
                    industry,
                    datetime('now') as created_at
                FROM stock_concept_data 
                WHERE import_date = :analysis_date
                  AND concept IS NOT NULL 
                  AND concept != ''
            """)
            
            # 执行SQL插入排名数据
            result = self.db.execute(ranking_sql, {"analysis_date": analysis_date})
            total_rankings = result.rowcount
            self.db.commit()
            
            # 统计处理的概念数量
            concept_count_sql = text("""
                SELECT COUNT(DISTINCT concept) as concept_count,
                       COUNT(*) as total_records
                FROM stock_concept_data 
                WHERE import_date = :analysis_date
                  AND concept IS NOT NULL 
                  AND concept != ''
            """)
            
            count_result = self.db.execute(concept_count_sql, {"analysis_date": analysis_date})
            stats = count_result.fetchone()
            processed_concepts = stats.concept_count
            source_data_count = stats.total_records
            
            # 更新任务状态
            task.status = 'completed'
            task.processed_concepts = processed_concepts
            task.processed_stocks = total_rankings
            task.source_data_count = source_data_count
            task.end_time = datetime.now()
            self.db.commit()
            
            print(f"✅ 概念内个股排名完成: {processed_concepts}个概念, {total_rankings}条排名记录")
            
            return {
                "processed_concepts": processed_concepts,
                "total_rankings": total_rankings,
                "source_data_count": source_data_count
            }
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = datetime.now()
            self.db.commit()
            raise e
    
    def _generate_concept_summaries(self, analysis_date: date, task: DailyAnalysisTask) -> Dict[str, Any]:
        """生成概念每日汇总统计"""
        
        print(f"📈 正在生成概念汇总统计...")
        
        try:
            # 清除该日期的旧汇总数据
            self.db.query(DailyConceptSummary).filter(
                DailyConceptSummary.analysis_date == analysis_date
            ).delete(synchronize_session=False)
            self.db.commit()
            
            # 使用SQL查询按概念分组汇总
            sql_query = text("""
                SELECT 
                    concept,
                    COUNT(*) as stock_count,
                    SUM(net_inflow) as total_net_inflow,
                    AVG(net_inflow) as avg_net_inflow,
                    AVG(price) as avg_price,
                    AVG(turnover_rate) as avg_turnover_rate,
                    SUM(total_reads) as total_reads,
                    SUM(page_count) as total_pages
                FROM stock_concept_data 
                WHERE import_date = :analysis_date
                  AND concept IS NOT NULL 
                  AND concept != ''
                GROUP BY concept
                ORDER BY SUM(net_inflow) DESC
            """)
            
            result = self.db.execute(sql_query, {"analysis_date": analysis_date})
            concept_stats = result.fetchall()
            
            if not concept_stats:
                raise Exception(f"没有找到 {analysis_date} 的概念数据进行汇总")
            
            # 生成概念排名并插入数据
            summaries = []
            for rank, row in enumerate(concept_stats, 1):
                summary = DailyConceptSummary(
                    analysis_date=analysis_date,
                    concept=row.concept,
                    stock_count=row.stock_count,
                    total_net_inflow=row.total_net_inflow or 0,
                    avg_net_inflow=row.avg_net_inflow or 0,
                    avg_price=row.avg_price or 0,
                    avg_turnover_rate=row.avg_turnover_rate or 0,
                    total_reads=row.total_reads or 0,
                    total_pages=row.total_pages or 0,
                    concept_rank=rank
                )
                summaries.append(summary)
            
            # 批量插入
            self.db.bulk_save_objects(summaries)
            self.db.commit()
            
            # 更新任务状态
            task.status = 'completed'
            task.processed_concepts = len(summaries)
            task.source_data_count = sum(row.stock_count for row in concept_stats)
            task.end_time = datetime.now()
            self.db.commit()
            
            print(f"✅ 概念汇总统计完成: {len(summaries)}个概念")
            
            return {
                "processed_concepts": len(summaries),
                "total_stocks": sum(row.stock_count for row in concept_stats),
                "top_concept": concept_stats[0].concept if concept_stats else None,
                "top_concept_net_inflow": float(concept_stats[0].total_net_inflow) if concept_stats else 0
            }
            
        except Exception as e:
            task.status = 'failed'
            task.error_message = str(e)
            task.end_time = datetime.now()
            self.db.commit()
            raise e
    
    def get_concept_rankings(self, analysis_date: date, concept: Optional[str] = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """获取概念内个股排名"""
        
        query = self.db.query(DailyConceptRanking).filter(
            DailyConceptRanking.analysis_date == analysis_date
        )
        
        if concept:
            query = query.filter(DailyConceptRanking.concept == concept)
        
        rankings = query.order_by(
            DailyConceptRanking.concept,
            DailyConceptRanking.net_inflow_rank
        ).limit(limit).all()
        
        return [
            {
                "concept": r.concept,
                "stock_code": r.stock_code,
                "stock_name": r.stock_name,
                "net_inflow_rank": r.net_inflow_rank,
                "price_rank": r.price_rank,
                "turnover_rate_rank": r.turnover_rate_rank,
                "total_reads_rank": r.total_reads_rank,
                "net_inflow": float(r.net_inflow) if r.net_inflow else 0,
                "price": float(r.price) if r.price else 0,
                "turnover_rate": float(r.turnover_rate) if r.turnover_rate else 0,
                "total_reads": r.total_reads or 0,
                "industry": r.industry
            }
            for r in rankings
        ]
    
    def get_concept_summaries(self, analysis_date: date, limit: int = 50) -> List[Dict[str, Any]]:
        """获取概念汇总排名"""
        
        summaries = self.db.query(DailyConceptSummary).filter(
            DailyConceptSummary.analysis_date == analysis_date
        ).order_by(DailyConceptSummary.concept_rank).limit(limit).all()
        
        return [
            {
                "concept": s.concept,
                "concept_rank": s.concept_rank,
                "stock_count": s.stock_count,
                "total_net_inflow": float(s.total_net_inflow) if s.total_net_inflow else 0,
                "avg_net_inflow": float(s.avg_net_inflow) if s.avg_net_inflow else 0,
                "avg_price": float(s.avg_price) if s.avg_price else 0,
                "avg_turnover_rate": float(s.avg_turnover_rate) if s.avg_turnover_rate else 0,
                "total_reads": s.total_reads or 0,
                "total_pages": s.total_pages or 0
            }
            for s in summaries
        ]