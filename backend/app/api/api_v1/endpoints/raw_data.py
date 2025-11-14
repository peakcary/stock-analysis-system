"""
原始数据查看器 API 端点
支持查询 CSV 原始数据表和 TTV/EEE 原始交易数据表
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import inspect, text, desc
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.models.stock import StockConceptRawData, RawImportData
from app.models.daily_trading import DailyTrading
from datetime import datetime, date
from pydantic import BaseModel

router = APIRouter()


class ColumnInfo(BaseModel):
    """列信息"""
    name: str
    type: str
    nullable: bool


class TableInfo(BaseModel):
    """表信息"""
    name: str
    display_name: str
    record_count: int
    columns: List[ColumnInfo]


class RawDataRow(BaseModel):
    """原始数据行 - 动态字段"""
    class Config:
        extra = "allow"  # 允许动态字段


class RawDataResponse(BaseModel):
    """原始数据查询响应"""
    table_name: str
    total_count: int
    page: int
    page_size: int
    data: List[Dict[str, Any]]
    columns: List[ColumnInfo]


# 支持的原始数据表映射
# 注意：TTV和EEE是动态表，table_name字段表示实际的表名
RAW_TABLES = {
    'stock_concept_raw_data': {
        'model': StockConceptRawData,
        'display_name': 'CSV概念股原始数据',
        'description': '来自 CSV 文件的原始概念股数据',
        'type': 'static',  # 静态模型表
        'table_name': 'stock_concept_raw_data',
        'date_field': 'trade_date'
    },
    'ttv_daily_trading': {
        'model': None,  # 动态表，无静态模型
        'display_name': 'TTV交易数据',
        'description': 'TTV 格式的原始交易数据',
        'type': 'dynamic',  # 动态表
        'table_name': 'ttv_daily_trading',
        'date_field': 'trading_date'
    },
    'eee_daily_trading': {
        'model': None,  # 动态表，无静态模型
        'display_name': 'EEE交易数据',
        'description': 'EEE 格式的原始交易数据',
        'type': 'dynamic',  # 动态表
        'table_name': 'eee_daily_trading',
        'date_field': 'trading_date'
    },
}


def get_columns_info_from_table(db: Session, table_name: str) -> List[ColumnInfo]:
    """从数据库获取表的列信息（适用于动态表）"""
    columns = []
    try:
        # 使用information_schema获取列信息
        query = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
        """
        result = db.execute(text(query)).fetchall()
        for row in result:
            columns.append(ColumnInfo(
                name=row[0],
                type=row[1],
                nullable=row[2] == 'YES'
            ))
    except Exception as e:
        # 如果查询失败，返回空列表
        pass
    return columns


def get_columns_info(model) -> List[ColumnInfo]:
    """获取静态模型的列信息"""
    columns = []
    try:
        mapper = inspect(model)
        for column in mapper.columns:
            col_type = str(column.type).split('(')[0]  # 简化类型显示
            columns.append(ColumnInfo(
                name=column.name,
                type=col_type,
                nullable=column.nullable
            ))
    except Exception:
        pass
    return columns


@router.get("/tables", response_model=List[TableInfo])
async def get_raw_tables(db: Session = Depends(get_db)):
    """
    获取所有可用的原始数据表列表

    返回：
    - table_name: 表名
    - display_name: 显示名称
    - record_count: 记录数
    - columns: 列信息列表
    """
    tables_info = []

    for table_key, table_config in RAW_TABLES.items():
        table_name = table_config['table_name']
        display_name = table_config['display_name']

        # 获取表的记录数
        try:
            if table_config['type'] == 'static':
                # 静态表使用ORM查询
                model = table_config['model']
                count = db.query(model).count()
                columns = get_columns_info(model)
            else:
                # 动态表使用SQL查询
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                count = result if result else 0
                columns = get_columns_info_from_table(db, table_name)
        except Exception as e:
            count = 0
            columns = []

        tables_info.append(TableInfo(
            name=table_key,
            display_name=display_name,
            record_count=count,
            columns=columns
        ))

    return tables_info


@router.post("/{table_name}/query", response_model=RawDataResponse)
async def query_raw_data(
    table_name: str,
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=1000, description="每页记录数"),
    sort_by: Optional[str] = Query(None, description="排序字段名"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="排序顺序"),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> RawDataResponse:
    """
    查询原始数据表

    参数：
    - table_name: 表名 (stock_concept_raw_data, ttv_daily_trading, eee_daily_trading)
    - page: 页码（从1开始）
    - page_size: 每页记录数（1-1000）
    - sort_by: 排序字段名（可选）
    - sort_order: 排序顺序 (asc/desc)
    - start_date: 开始日期 (YYYY-MM-DD, 可选)
    - end_date: 结束日期 (YYYY-MM-DD, 可选)

    返回：
    - table_name: 表名
    - total_count: 总记录数
    - page: 当前页码
    - page_size: 每页记录数
    - data: 数据行列表
    - columns: 列信息
    """

    # 验证表名
    if table_name not in RAW_TABLES:
        raise HTTPException(
            status_code=404,
            detail=f"表不存在: {table_name}。支持的表: {list(RAW_TABLES.keys())}"
        )

    table_config = RAW_TABLES[table_name]
    actual_table_name = table_config['table_name']
    date_field = table_config['date_field']

    try:
        if table_config['type'] == 'static':
            # 使用ORM查询静态表
            model = table_config['model']

            # 构建基础查询
            base_query = db.query(model)

            # 日期范围过滤
            if start_date or end_date:
                date_column = getattr(model, date_field, None)
                if date_column is not None:
                    if start_date:
                        base_query = base_query.filter(date_column >= start_date)
                    if end_date:
                        base_query = base_query.filter(date_column <= end_date)

            # 获取总记录数
            total_count = base_query.count()

            # 排序
            query = base_query
            if sort_by and hasattr(model, sort_by):
                order_column = getattr(model, sort_by)
                query = query.order_by(desc(order_column) if sort_order.lower() == "desc" else order_column)
            else:
                # 默认按 ID 倒序
                if hasattr(model, 'id'):
                    query = query.order_by(desc(model.id))

            # 分页
            offset = (page - 1) * page_size
            records = query.offset(offset).limit(page_size).all()

            # 转换为字典列表
            data = []
            for record in records:
                row = {}
                mapper = inspect(model)
                for column in mapper.columns:
                    value = getattr(record, column.name)
                    # 处理日期/时间类型
                    if isinstance(value, (datetime, date)):
                        value = value.isoformat() if value else None
                    row[column.name] = value
                data.append(row)

            # 获取列信息
            columns = get_columns_info(model)

        else:
            # 使用SQL查询动态表
            # 构建WHERE子句
            where_clauses = []
            if start_date:
                where_clauses.append(f"{date_field} >= '{start_date}'")
            if end_date:
                where_clauses.append(f"{date_field} <= '{end_date}'")

            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # 获取总记录数
            count_query = f"SELECT COUNT(*) FROM {actual_table_name}{where_sql}"
            total_count = db.execute(text(count_query)).scalar() or 0

            # 构建排序子句
            order_sql = ""
            if sort_by:
                order_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
                order_sql = f" ORDER BY {sort_by} {order_direction}"
            else:
                # 默认按 ID 倒序
                order_sql = " ORDER BY id DESC"

            # 构建分页子句
            offset = (page - 1) * page_size
            limit_sql = f" LIMIT {page_size} OFFSET {offset}"

            # 查询数据
            data_query = f"SELECT * FROM {actual_table_name}{where_sql}{order_sql}{limit_sql}"
            result = db.execute(text(data_query)).fetchall()

            # 转换为字典列表
            data = []
            if result:
                for row in result:
                    # 使用 _mapping 将 Row 转换为字典
                    row_dict = dict(row._mapping)
                    # 处理日期/时间类型
                    for col_name, value in row_dict.items():
                        if isinstance(value, (datetime, date)):
                            row_dict[col_name] = value.isoformat() if value else None
                    data.append(row_dict)

            # 获取列信息
            columns = get_columns_info_from_table(db, actual_table_name)

        return RawDataResponse(
            table_name=table_name,
            total_count=total_count,
            page=page,
            page_size=page_size,
            data=data,
            columns=columns
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/{table_name}/columns", response_model=List[ColumnInfo])
async def get_table_columns(
    table_name: str,
    db: Session = Depends(get_db)
) -> List[ColumnInfo]:
    """
    获取指定表的列信息

    参数：
    - table_name: 表名

    返回：
    - 列信息列表（名称、类型、是否可为空）
    """
    if table_name not in RAW_TABLES:
        raise HTTPException(
            status_code=404,
            detail=f"表不存在: {table_name}"
        )

    table_config = RAW_TABLES[table_name]

    if table_config['type'] == 'static':
        return get_columns_info(table_config['model'])
    else:
        return get_columns_info_from_table(db, table_config['table_name'])


@router.get("/{table_name}/stats")
async def get_table_stats(
    table_name: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取原始数据表的统计信息

    参数：
    - table_name: 表名

    返回：
    - total_count: 总记录数
    - first_record_date: 最早记录日期
    - last_record_date: 最新记录日期
    - distinct_stocks: 不同股票数量（如果适用）
    """
    if table_name not in RAW_TABLES:
        raise HTTPException(
            status_code=404,
            detail=f"表不存在: {table_name}"
        )

    table_config = RAW_TABLES[table_name]
    actual_table_name = table_config['table_name']
    date_field = table_config['date_field']

    try:
        stats = {
            "table_name": table_name,
        }

        if table_config['type'] == 'static':
            # 静态表统计
            model = table_config['model']
            stats['total_count'] = db.query(model).count()

            if hasattr(model, date_field):
                date_column = getattr(model, date_field)
                first = db.query(date_column).order_by(date_column.asc()).first()
                last = db.query(date_column).order_by(date_column.desc()).first()
                stats['first_record_date'] = first[0].isoformat() if first and first[0] else None
                stats['last_record_date'] = last[0].isoformat() if last and last[0] else None

            if hasattr(model, 'stock_code'):
                stats['distinct_stocks'] = db.query(model.stock_code).distinct().count()

        else:
            # 动态表统计
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {actual_table_name}")).scalar()
            stats['total_count'] = count_result if count_result else 0

            # 获取日期范围
            try:
                first_result = db.execute(
                    text(f"SELECT {date_field} FROM {actual_table_name} ORDER BY {date_field} ASC LIMIT 1")
                ).scalar()
                last_result = db.execute(
                    text(f"SELECT {date_field} FROM {actual_table_name} ORDER BY {date_field} DESC LIMIT 1")
                ).scalar()

                if first_result:
                    if isinstance(first_result, date):
                        stats['first_record_date'] = first_result.isoformat()
                    else:
                        stats['first_record_date'] = str(first_result)

                if last_result:
                    if isinstance(last_result, date):
                        stats['last_record_date'] = last_result.isoformat()
                    else:
                        stats['last_record_date'] = str(last_result)
            except Exception:
                pass

            # 获取不同股票数量
            try:
                stock_result = db.execute(
                    text(f"SELECT COUNT(DISTINCT stock_code) FROM {actual_table_name}")
                ).scalar()
                if stock_result:
                    stats['distinct_stocks'] = stock_result
            except Exception:
                pass

        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )
