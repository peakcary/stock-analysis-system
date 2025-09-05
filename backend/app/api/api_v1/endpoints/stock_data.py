"""
股票概念数据API接口
Stock Concept Data API endpoints
"""

import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.core.logging import logger
from app.models.user import User
from app.models.stock_data import (
    StockInfo, DailyStockConceptData, StockConceptCategory, DailyStockConcept,
    ConceptDailyStats, StockConceptRanking, DataImportLog
)
from app.services.stock_data_import import stock_data_import_service

router = APIRouter()


@router.post("/import/csv")
async def import_csv_data(
    trade_date: str = Form(..., description="交易日期，格式YYYY-MM-DD"),
    file: UploadFile = File(..., description="CSV文件"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导入CSV概念数据"""
    try:
        # 解析交易日期
        trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
        
        # 检查文件类型
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件必须是CSV格式"
            )
        
        # 保存上传的文件
        upload_dir = "uploads/stock_data"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"csv_{trade_date}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 调用导入服务
        result = await stock_data_import_service.import_csv_data(
            file_path=file_path,
            trade_date=trade_date_obj,
            db=db
        )
        
        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        if result['success']:
            return {
                "success": True,
                "message": "CSV数据导入成功",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"导入CSV数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post("/import/txt")
async def import_txt_data(
    trade_date: str = Form(..., description="交易日期，格式YYYY-MM-DD"),
    file: UploadFile = File(..., description="TXT文件"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导入TXT成交量数据"""
    try:
        # 解析交易日期
        trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
        
        # 检查文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件必须是TXT格式"
            )
        
        # 保存上传的文件
        upload_dir = "uploads/stock_data"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"txt_{trade_date}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 调用导入服务
        result = await stock_data_import_service.import_txt_data(
            file_path=file_path,
            trade_date=trade_date_obj,
            db=db
        )
        
        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        if result['success']:
            return {
                "success": True,
                "message": "TXT数据导入成功",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"导入TXT数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


@router.post("/import/files")
async def import_files_from_path(
    csv_file_path: str = Form(..., description="CSV文件路径"),
    txt_file_path: str = Form(..., description="TXT文件路径"),
    trade_date: str = Form(..., description="交易日期，格式YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """从指定路径导入文件"""
    try:
        # 解析交易日期
        trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
        
        # 检查文件是否存在
        if not os.path.exists(csv_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV文件不存在: {csv_file_path}"
            )
        
        if not os.path.exists(txt_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TXT文件不存在: {txt_file_path}"
            )
        
        results = {}
        
        # 导入CSV数据
        csv_result = await stock_data_import_service.import_csv_data(
            file_path=csv_file_path,
            trade_date=trade_date_obj,
            db=db
        )
        results['csv_import'] = csv_result
        
        # 导入TXT数据
        txt_result = await stock_data_import_service.import_txt_data(
            file_path=txt_file_path,
            trade_date=trade_date_obj,
            db=db
        )
        results['txt_import'] = txt_result
        
        # 计算概念排名
        if csv_result['success'] and txt_result['success']:
            ranking_result = await stock_data_import_service.calculate_concept_rankings(
                trade_date=trade_date_obj,
                db=db
            )
            results['ranking_calculation'] = ranking_result
        
        return {
            "success": True,
            "message": "数据导入和计算完成",
            "data": results
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        error_msg = str(e) if str(e) else repr(e)
        logger.error(f"导入文件失败: {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {error_msg}"
        )


@router.post("/calculate/rankings")
async def calculate_concept_rankings(
    trade_date: str = Form(..., description="交易日期，格式YYYY-MM-DD"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """计算概念排名"""
    try:
        # 解析交易日期
        trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
        
        # 调用排名计算服务
        result = await stock_data_import_service.calculate_concept_rankings(
            trade_date=trade_date_obj,
            db=db
        )
        
        if result['success']:
            return {
                "success": True,
                "message": "概念排名计算成功",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"计算概念排名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"计算失败: {str(e)}"
        )


@router.get("/concepts")
async def get_concepts(
    trade_date: Optional[str] = Query(None, description="交易日期，格式YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """获取概念列表"""
    try:
        if trade_date:
            trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
            
            # 获取特定日期的概念统计
            query = db.query(ConceptDailyStats).filter(
                ConceptDailyStats.trade_date == trade_date_obj
            ).order_by(desc(ConceptDailyStats.total_volume))
            
            total = query.count()
            concepts = query.offset((page - 1) * size).limit(size).all()
            
            return {
                "success": True,
                "data": {
                    "concepts": [
                        {
                            "concept_name": c.concept_name,
                            "total_volume": c.total_volume,
                            "stock_count": c.stock_count,
                            "avg_volume": c.avg_volume,
                            "total_hot_views": c.total_hot_views,
                            "avg_hot_views": c.avg_hot_views,
                            "trade_date": c.trade_date.strftime("%Y-%m-%d")
                        } for c in concepts
                    ],
                    "pagination": {
                        "page": page,
                        "size": size,
                        "total": total,
                        "pages": (total + size - 1) // size
                    }
                }
            }
        else:
            # 获取所有概念
            query = db.query(Concept).filter(Concept.is_active == True).order_by(Concept.name)
            
            total = query.count()
            concepts = query.offset((page - 1) * size).limit(size).all()
            
            return {
                "success": True,
                "data": {
                    "concepts": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "category": c.category,
                            "description": c.description
                        } for c in concepts
                    ],
                    "pagination": {
                        "page": page,
                        "size": size,
                        "total": total,
                        "pages": (total + size - 1) // size
                    }
                }
            }
            
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"获取概念列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/concepts/{concept_name}/rankings")
async def get_concept_stock_rankings(
    concept_name: str,
    trade_date: str = Query(..., description="交易日期，格式YYYY-MM-DD"),
    order_by: str = Query("volume", description="排序字段(volume/hot_views)"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: Session = Depends(get_db)
):
    """获取概念内股票排名"""
    try:
        trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
        
        query = db.query(StockConceptRanking).filter(
            and_(
                StockConceptRanking.concept_name == concept_name,
                StockConceptRanking.trade_date == trade_date_obj
            )
        )
        
        # 排序
        if order_by == "hot_views":
            query = query.order_by(StockConceptRanking.hot_views_rank.asc())
        else:
            query = query.order_by(StockConceptRanking.volume_rank.asc())
        
        total = query.count()
        rankings = query.offset((page - 1) * size).limit(size).all()
        
        return {
            "success": True,
            "data": {
                "concept_name": concept_name,
                "trade_date": trade_date,
                "rankings": [
                    {
                        "stock_code": r.stock_code,
                        "stock_name": r.stock_name,
                        "volume_rank": r.volume_rank,
                        "volume": r.volume,
                        "volume_ratio": r.volume_ratio,
                        "hot_views_rank": r.hot_views_rank,
                        "hot_page_views": r.hot_page_views,
                        "hot_views_ratio": r.hot_views_ratio
                    } for r in rankings
                ],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="交易日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"获取概念排名失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/import-logs")
async def get_import_logs(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    import_type: Optional[str] = Query(None, description="导入类型"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取导入日志"""
    try:
        query = db.query(DataImportLog)
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(DataImportLog.import_date >= start_date_obj)
            
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(DataImportLog.import_date <= end_date_obj)
            
        if import_type:
            query = query.filter(DataImportLog.import_type == import_type)
            
        if status:
            query = query.filter(DataImportLog.status == status)
        
        query = query.order_by(desc(DataImportLog.created_at))
        
        total = query.count()
        logs = query.offset((page - 1) * size).limit(size).all()
        
        return {
            "success": True,
            "data": {
                "logs": [
                    {
                        "id": log.id,
                        "import_date": log.import_date.strftime("%Y-%m-%d"),
                        "import_type": log.import_type,
                        "file_name": log.file_name,
                        "status": log.status,
                        "total_records": log.total_records,
                        "success_records": log.success_records,
                        "failed_records": log.failed_records,
                        "processing_time": log.processing_time,
                        "error_message": log.error_message,
                        "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
                        "completed_at": log.completed_at.strftime("%Y-%m-%d %H:%M:%S") if log.completed_at else None
                    } for log in logs
                ],
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，请使用YYYY-MM-DD格式"
        )
    except Exception as e:
        logger.error(f"获取导入日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取失败: {str(e)}"
        )