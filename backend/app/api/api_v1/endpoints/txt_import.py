from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.txt_import import TxtImportService
from app.core.admin_auth import get_current_admin_user
from app.models.admin_user import AdminUser
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/records")
async def get_import_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    trading_date: Optional[str] = Query(None, description="交易日期过滤 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取TXT文件导入记录"""
    try:
        # 解析日期过滤条件
        parsed_date = None
        if trading_date:
            try:
                parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
        
        # 创建TXT导入服务实例
        txt_service = TxtImportService(db)
        
        # 获取导入记录
        result = txt_service.get_import_records(
            page=page,
            size=size,
            trading_date=parsed_date
        )
        
        if result["success"]:
            return result["data"]
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")

@router.get("/dates")
async def get_import_dates(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取所有有导入记录的日期列表"""
    try:
        txt_service = TxtImportService(db)
        
        # 查询所有不同的交易日期
        from app.models.daily_trading import TxtImportRecord
        dates = db.query(TxtImportRecord.trading_date).distinct().order_by(TxtImportRecord.trading_date.desc()).all()
        
        date_list = [d[0].strftime('%Y-%m-%d') for d in dates if d[0]]
        
        return {
            "success": True,
            "dates": date_list,
            "total": len(date_list)
        }
        
    except Exception as e:
        logger.error(f"获取导入日期列表时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取日期失败: {str(e)}")

@router.post("/recalculate")
async def recalculate_daily_summary(
    trading_date: str = Query(..., description="交易日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """重新计算指定日期的概念汇总和排名数据"""
    try:
        # 解析日期
        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        
        # 创建TXT导入服务实例
        txt_service = TxtImportService(db)
        
        # 重新计算
        result = txt_service.recalculate_daily_summary(parsed_date)
        
        if result["success"]:
            logger.info(f"管理员{current_admin.username}重新计算了{trading_date}的数据")
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"重新计算数据时出错: {e}")
        raise HTTPException(status_code=500, detail=f"重新计算失败: {str(e)}")

@router.post("/check-date")
async def check_import_date(
    request: Dict[str, str],
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """检查指定日期是否已有导入记录"""
    try:
        trading_date = request.get('trading_date', '')
        if not trading_date:
            raise HTTPException(status_code=400, detail="缺少交易日期参数")
        
        # 解析日期
        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        
        # 检查是否存在记录
        from app.models.daily_trading import TxtImportRecord
        existing_count = db.query(TxtImportRecord).filter(
            TxtImportRecord.trading_date == parsed_date
        ).count()
        
        return {
            "success": True,
            "exists": existing_count > 0,
            "trading_date": trading_date,
            "count": existing_count
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"检查导入日期时出错: {e}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")

@router.post("/import", response_model=Dict[str, Any])
async def import_txt_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """导入TXT交易数据文件"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.txt'):
            raise HTTPException(status_code=400, detail="只支持TXT格式文件")
        
        # 读取文件内容
        content = await file.read()
        txt_content = content.decode('utf-8')
        
        # 执行导入（传递文件信息）
        import_service = TxtImportService(db)
        result = import_service.import_daily_trading(
            txt_content=txt_content,
            filename=file.filename,
            file_size=len(content),
            imported_by=current_admin.username
        )
        
        return result
        
    except Exception as e:
        logger.error(f"导入TXT文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.post("/import-content", response_model=Dict[str, Any])
async def import_txt_content(
    request: Dict[str, str],
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """导入TXT内容（通过文本直接提交）"""
    try:
        txt_content = request.get('content', '')
        if not txt_content.strip():
            raise HTTPException(status_code=400, detail="文件内容不能为空")
        
        # 执行导入
        import_service = TxtImportService(db)
        result = import_service.import_daily_trading(txt_content)
        
        return result
        
    except Exception as e:
        logger.error(f"导入TXT内容时出错: {e}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@router.get("/stats/{trading_date}")
async def get_import_stats(
    trading_date: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取指定日期的导入统计"""
    try:
        # 解析日期
        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        
        import_service = TxtImportService(db)
        stats = import_service.get_import_stats(parsed_date)
        
        return stats
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"获取导入统计时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.get("/recent-imports")
async def get_recent_imports(
    limit: int = Query(10, description="返回记录数量"),
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """获取最近的导入记录"""
    try:
        from app.models.daily_trading import DailyTrading
        
        # 获取最近的交易日期
        recent_dates = db.query(DailyTrading.trading_date).distinct().order_by(
            DailyTrading.trading_date.desc()
        ).limit(limit).all()
        
        import_service = TxtImportService(db)
        results = []
        
        for (trading_date,) in recent_dates:
            stats = import_service.get_import_stats(trading_date)
            results.append(stats)
        
        return results
        
    except Exception as e:
        logger.error(f"获取最近导入记录时出错: {e}")
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")

@router.delete("/clear/{trading_date}")
async def clear_daily_data(
    trading_date: str,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user)
):
    """清理指定日期的数据"""
    try:
        # 解析日期
        parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
        
        import_service = TxtImportService(db)
        import_service.clear_daily_data(parsed_date)
        
        return {"success": True, "message": f"已清理{trading_date}的数据"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    except Exception as e:
        logger.error(f"清理数据时出错: {e}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")