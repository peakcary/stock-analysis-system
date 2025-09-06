"""
数据导入相关API端点
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.data_import import DataImportService
from app.services.ranking_calculator import RankingCalculatorService
from app.models import DataImportRecord
from datetime import date, datetime
from typing import Optional, List

router = APIRouter()


@router.post("/import-csv")
async def import_csv_data(
    file: UploadFile = File(...),
    allow_overwrite: bool = False,
    db: Session = Depends(get_db)
):
    """导入CSV格式的股票数据（重构版本 - 增强错误处理）"""
    
    # 验证文件基本信息
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="文件必须是CSV格式")
    
    # 验证文件大小 (限制100MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过100MB")
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 验证文件内容不为空
        if not content:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 验证文件大小（实际读取后）
        if len(content) > 100 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件内容超过100MB限制")
        
        print(f"📄 开始处理CSV文件: {file.filename}, 大小: {len(content)} bytes")
        
        # 使用数据导入服务处理文件
        import_service = DataImportService(db)
        result = await import_service.import_csv_data(content, file.filename, allow_overwrite)
        
        print(f"✅ CSV处理完成: 导入{result.get('imported_records', 0)}条, 跳过{result.get('skipped_records', 0)}条")
        
        if result.get("already_exists"):
            return {
                "message": result["message"],
                "filename": file.filename,
                "imported_records": result["imported_records"],
                "skipped_records": result["skipped_records"],
                "import_date": result["import_date"],
                "already_exists": True
            }
        
        return {
            "message": "CSV数据导入成功" + ("（覆盖模式）" if result.get("overwrite") else ""),
            "filename": file.filename,
            "imported_records": result["imported_records"],
            "skipped_records": result["skipped_records"],
            "import_date": result["import_date"],
            "overwrite": result.get("overwrite", False),
            "errors": result.get("errors", [])
        }
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"❌ CSV导入异常: {str(e)}")
        error_detail = str(e)
        if "CSV解析失败" in error_detail:
            raise HTTPException(status_code=400, detail=error_detail)
        else:
            raise HTTPException(status_code=500, detail=f"导入失败: {error_detail}")


@router.post("/import-txt")
async def import_txt_data(
    file: UploadFile = File(...),
    allow_overwrite: bool = False,
    db: Session = Depends(get_db)
):
    """导入TXT格式的热度数据（重构版本 - 增强错误处理）"""
    
    # 验证文件基本信息
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="文件必须是TXT格式")
    
    # 验证文件大小 (限制50MB)
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 验证文件内容不为空
        if not content:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        # 验证文件大小（实际读取后）
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件内容超过50MB限制")
        
        print(f"📄 开始处理TXT文件: {file.filename}, 大小: {len(content)} bytes")
        
        # 使用数据导入服务处理文件
        import_service = DataImportService(db)
        result = await import_service.import_txt_data(content, file.filename, allow_overwrite)
        
        print(f"✅ TXT处理完成: 导入{result.get('imported_records', 0)}条, 跳过{result.get('skipped_records', 0)}条")
        
        if result.get("already_exists"):
            return {
                "message": result["message"],
                "filename": file.filename,
                "imported_records": result["imported_records"],
                "skipped_records": result["skipped_records"],
                "import_date": result["import_date"],
                "already_exists": True
            }
        
        return {
            "message": "TXT热度数据导入成功" + ("（覆盖模式）" if result.get("overwrite") else ""),
            "filename": file.filename,
            "imported_records": result["imported_records"],
            "skipped_records": result["skipped_records"],
            "import_date": result["import_date"],
            "overwrite": result.get("overwrite", False),
            "errors": result.get("errors", [])
        }
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        print(f"❌ TXT导入异常: {str(e)}")
        error_detail = str(e)
        if "TXT解析失败" in error_detail:
            raise HTTPException(status_code=400, detail=error_detail)
        else:
            raise HTTPException(status_code=500, detail=f"导入失败: {error_detail}")


@router.post("/calculate-rankings")
def calculate_rankings(
    trade_date: str,
    db: Session = Depends(get_db)
):
    """计算指定日期的排名和概念总和"""
    try:
        # 使用排名计算服务
        calculator = RankingCalculatorService(db)
        result = calculator.calculate_daily_rankings(trade_date)
        
        return {
            "message": "排名计算完成",
            "trade_date": trade_date,
            "processed_concepts": result["processed_concepts"],
            "total_rankings": result["total_rankings"],
            "new_highs_found": result["new_highs_found"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/import-history")
def get_import_history(
    import_date: Optional[str] = Query(None, description="查询指定日期的导入记录 (YYYY-MM-DD)"),
    limit: int = Query(10, description="返回记录数量限制"),
    db: Session = Depends(get_db)
):
    """获取数据导入历史记录"""
    try:
        query = db.query(DataImportRecord)
        
        if import_date:
            try:
                query_date = datetime.strptime(import_date, '%Y-%m-%d').date()
                query = query.filter(DataImportRecord.import_date == query_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        records = query.order_by(DataImportRecord.created_at.desc()).limit(limit).all()
        
        result = []
        for record in records:
            result.append({
                "id": record.id,
                "import_date": record.import_date.isoformat(),
                "import_type": record.import_type,
                "file_name": record.file_name,
                "imported_records": record.imported_records,
                "skipped_records": record.skipped_records,
                "import_status": record.import_status,
                "error_message": record.error_message,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            })
        
        return {
            "records": result,
            "total": len(result)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/import-status/{import_date}")
def check_import_status(
    import_date: str,
    db: Session = Depends(get_db)
):
    """检查指定日期的导入状态"""
    try:
        try:
            query_date = datetime.strptime(import_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        records = db.query(DataImportRecord).filter(
            DataImportRecord.import_date == query_date
        ).all()
        
        status = {
            "import_date": import_date,
            "csv_imported": False,
            "txt_imported": False,
            "csv_record": None,
            "txt_record": None
        }
        
        for record in records:
            record_data = {
                "id": record.id,
                "file_name": record.file_name,
                "imported_records": record.imported_records,
                "skipped_records": record.skipped_records,
                "import_status": record.import_status,
                "error_message": record.error_message,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            }
            
            if record.import_type == 'csv':
                status["csv_imported"] = True
                status["csv_record"] = record_data
            elif record.import_type == 'txt':
                status["txt_imported"] = True
                status["txt_record"] = record_data
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/import-daily-batch")
async def import_daily_batch(
    csv_file: UploadFile = File(..., description="CSV文件 - 包含股票代码、名称、行业、概念等信息"),
    txt_file: UploadFile = File(..., description="TXT文件 - 包含股票代码和热度数据"),
    trade_date: Optional[str] = Form(None, description="交易日期 (YYYY-MM-DD)，不提供则自动从文件名解析"),
    allow_overwrite: bool = Form(False, description="是否覆盖已存在的数据"),
    db: Session = Depends(get_db)
):
    """
    每日批量导入接口
    同时导入CSV和TXT文件，确保数据完整性
    """
    
    # 验证文件类型
    if not csv_file.filename or not csv_file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="第一个文件必须是CSV格式")
    
    if not txt_file.filename or not txt_file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="第二个文件必须是TXT格式")
    
    # 验证文件大小
    if csv_file.size and csv_file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="CSV文件不能超过100MB")
    
    if txt_file.size and txt_file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="TXT文件不能超过50MB")
    
    try:
        # 解析交易日期
        parsed_trade_date = None
        if trade_date:
            try:
                parsed_trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        # 读取文件内容
        csv_content = await csv_file.read()
        txt_content = await txt_file.read()
        
        # 验证文件内容不为空
        if not csv_content:
            raise HTTPException(status_code=400, detail="CSV文件内容为空")
        
        if not txt_content:
            raise HTTPException(status_code=400, detail="TXT文件内容为空")
        
        print(f"📄 开始批量导入: CSV({csv_file.filename}, {len(csv_content)} bytes) + TXT({txt_file.filename}, {len(txt_content)} bytes)")
        
        # 使用数据导入服务处理批量导入
        import_service = DataImportService(db)
        result = await import_service.import_daily_batch(
            csv_content, csv_file.filename,
            txt_content, txt_file.filename,
            parsed_trade_date, allow_overwrite
        )
        
        print(f"✅ 批量导入完成: {result['message']}")
        
        return {
            "message": result["message"],
            "success": result["success"],
            "trade_date": result["trade_date"],
            "csv_file": csv_file.filename,
            "txt_file": txt_file.filename,
            "csv_result": result["csv_result"],
            "txt_result": result["txt_result"],
            "overwrite": allow_overwrite
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 批量导入异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量导入失败: {str(e)}")


@router.get("/check-completeness/{trade_date}")
def check_import_completeness(
    trade_date: str,
    db: Session = Depends(get_db)
):
    """
    检查指定日期的数据导入完整性
    返回CSV和TXT是否都已导入，是否可以进行分析
    """
    try:
        try:
            parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
        
        import_service = DataImportService(db)
        result = import_service.check_daily_import_completeness(parsed_date)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询完整性失败: {str(e)}")


@router.post("/auto-extract-date")
async def auto_extract_date_from_files(
    csv_file: UploadFile = File(...),
    txt_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    从文件名自动提取日期信息
    用于前端预览将要导入的日期
    """
    try:
        import_service = DataImportService(db)
        
        # 从CSV文件名提取日期
        csv_date = import_service._extract_date_from_filename(csv_file.filename or "")
        txt_date = import_service._extract_date_from_filename(txt_file.filename or "")
        
        # 选择最合适的日期
        extracted_date = csv_date or txt_date or date.today()
        
        # 检查该日期是否已导入数据
        completeness = import_service.check_daily_import_completeness(extracted_date)
        
        return {
            "csv_filename": csv_file.filename,
            "txt_filename": txt_file.filename,
            "csv_extracted_date": csv_date.isoformat() if csv_date else None,
            "txt_extracted_date": txt_date.isoformat() if txt_date else None,
            "recommended_date": extracted_date.isoformat(),
            "already_imported": completeness
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"日期提取失败: {str(e)}")