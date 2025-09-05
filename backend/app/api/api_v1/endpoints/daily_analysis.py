"""
每日分析API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.daily_analysis import DailyAnalysisService
from typing import Dict, Any, Optional, List
from datetime import date

router = APIRouter()


@router.post("/generate-analysis")
async def generate_daily_analysis(
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    db: Session = Depends(get_db)
):
    """
    生成每日分析报告
    
    - 分析指定日期导入的概念数据
    - 生成概念内个股排名（按净流入、价格、换手率、阅读量）
    - 生成概念汇总统计（个股数量、净流入总和、平均值等）
    - 为概念按净流入总和排名
    """
    try:
        # 解析日期
        target_date = None
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 创建分析服务
        analysis_service = DailyAnalysisService(db)
        
        # 执行分析
        result = analysis_service.generate_daily_analysis(target_date)
        
        return {
            "success": True,
            "message": "每日分析报告生成完成",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成分析报告失败: {str(e)}")


@router.get("/concept-rankings")
async def get_concept_rankings(
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    concept: Optional[str] = Query(None, description="指定概念名称，为空则返回所有概念"),
    limit: int = Query(50, description="返回记录数限制", ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    获取概念内个股排名
    
    返回指定日期、指定概念（可选）的个股排名数据，包括：
    - 净流入排名
    - 价格排名  
    - 换手率排名
    - 阅读量排名
    """
    try:
        # 解析日期
        target_date = date.today()
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 获取排名数据
        analysis_service = DailyAnalysisService(db)
        rankings = analysis_service.get_concept_rankings(target_date, concept, limit)
        
        return {
            "success": True,
            "data": {
                "analysis_date": target_date.isoformat(),
                "concept": concept,
                "total_count": len(rankings),
                "rankings": rankings
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排名数据失败: {str(e)}")


@router.get("/concept-summaries")
async def get_concept_summaries(
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    limit: int = Query(50, description="返回记录数限制", ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    获取概念汇总排名
    
    返回指定日期的概念汇总统计，按净流入总和排名，包括：
    - 概念排名
    - 个股数量
    - 净流入总和与平均值
    - 平均价格、换手率
    - 总阅读量、页面数
    """
    try:
        # 解析日期
        target_date = date.today()
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 获取汇总数据
        analysis_service = DailyAnalysisService(db)
        summaries = analysis_service.get_concept_summaries(target_date, limit)
        
        return {
            "success": True,
            "data": {
                "analysis_date": target_date.isoformat(),
                "total_count": len(summaries),
                "summaries": summaries
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取汇总数据失败: {str(e)}")


@router.get("/top-concepts")
async def get_top_concepts(
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    limit: int = Query(10, description="返回顶部概念数量", ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取顶部概念简要信息
    
    返回净流入总和排名前N的概念基本信息，用于快速预览
    """
    try:
        # 解析日期
        target_date = date.today()
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 获取顶部概念
        analysis_service = DailyAnalysisService(db)
        summaries = analysis_service.get_concept_summaries(target_date, limit)
        
        # 简化返回数据
        top_concepts = [
            {
                "rank": s["concept_rank"],
                "concept": s["concept"],
                "stock_count": s["stock_count"],
                "total_net_inflow": s["total_net_inflow"],
                "avg_net_inflow": s["avg_net_inflow"]
            }
            for s in summaries
        ]
        
        return {
            "success": True,
            "data": {
                "analysis_date": target_date.isoformat(),
                "top_concepts": top_concepts
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取顶部概念失败: {str(e)}")


@router.get("/concept-detail/{concept}")
async def get_concept_detail(
    concept: str,
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    db: Session = Depends(get_db)
):
    """
    获取指定概念的详细分析
    
    返回指定概念的汇总信息 + 该概念下所有个股的详细排名
    """
    try:
        # 解析日期
        target_date = date.today()
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        analysis_service = DailyAnalysisService(db)
        
        # 获取概念汇总信息
        concept_summaries = analysis_service.get_concept_summaries(target_date, 1000)
        concept_summary = next((s for s in concept_summaries if s["concept"] == concept), None)
        
        if not concept_summary:
            raise HTTPException(status_code=404, detail=f"未找到概念 '{concept}' 的分析数据")
        
        # 获取该概念下的个股排名
        stock_rankings = analysis_service.get_concept_rankings(target_date, concept, 1000)
        
        return {
            "success": True,
            "data": {
                "analysis_date": target_date.isoformat(),
                "concept_summary": concept_summary,
                "stock_rankings": stock_rankings
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概念详情失败: {str(e)}")


@router.get("/analysis-status")
async def get_analysis_status(
    analysis_date: Optional[str] = Query(None, description="分析日期 (YYYY-MM-DD)，默认为今天"),
    db: Session = Depends(get_db)
):
    """
    获取分析任务状态
    
    检查指定日期的分析任务是否已完成，返回任务执行情况
    """
    try:
        from app.models.daily_analysis import DailyAnalysisTask
        
        # 解析日期
        target_date = date.today()
        if analysis_date:
            try:
                target_date = date.fromisoformat(analysis_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        # 查询分析任务状态
        tasks = db.query(DailyAnalysisTask).filter(
            DailyAnalysisTask.analysis_date == target_date
        ).order_by(DailyAnalysisTask.created_at.desc()).all()
        
        task_status = []
        for task in tasks:
            duration = None
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
            
            task_status.append({
                "task_type": task.task_type,
                "status": task.status,
                "processed_concepts": task.processed_concepts,
                "processed_stocks": task.processed_stocks,
                "source_data_count": task.source_data_count,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "duration_seconds": duration,
                "error_message": task.error_message
            })
        
        # 判断整体状态
        if not tasks:
            overall_status = "not_started"
        elif all(task.status == "completed" for task in tasks):
            overall_status = "completed"
        elif any(task.status == "failed" for task in tasks):
            overall_status = "failed"
        else:
            overall_status = "processing"
        
        return {
            "success": True,
            "data": {
                "analysis_date": target_date.isoformat(),
                "overall_status": overall_status,
                "tasks": task_status
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析状态失败: {str(e)}")