"""
API v1 主路由配置
"""

from fastapi import APIRouter
from app.api.api_v1.endpoints import stocks, concepts, data_import, auth, client_user_management, admin_management, payment, admin_packages, system, mock_payment, admin_order_management, stock_data, daily_analysis, concept_analysis, chart_data, admin_auth, txt_import, stock_analysis, optimization_status, historical_txt_import
# from app.api.api_v1.endpoints import large_file_upload
from app.api import simple_import

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(admin_auth.router, prefix="/admin/auth", tags=["admin-authentication"])
api_router.include_router(client_user_management.router, prefix="/admin/client-users", tags=["client-user-management"])
api_router.include_router(admin_management.router, prefix="/admin", tags=["admin-management"])
api_router.include_router(admin_packages.router, prefix="/admin", tags=["admin-packages"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(concepts.router, prefix="/concepts", tags=["concepts"])
api_router.include_router(data_import.router, prefix="/data", tags=["data-import"])
api_router.include_router(payment.router, prefix="/payment", tags=["payment"])
api_router.include_router(mock_payment.router, prefix="/mock", tags=["mock-payment"])
api_router.include_router(admin_order_management.router, prefix="/admin/orders", tags=["admin-order-management"])
# 新增股票概念数据接口
api_router.include_router(stock_data.router, prefix="/stock-data", tags=["stock-data"])
# 新增简化导入接口
api_router.include_router(simple_import.router, prefix="/simple-import", tags=["simple-import"])
# 新增每日分析接口
api_router.include_router(daily_analysis.router, prefix="/daily-analysis", tags=["daily-analysis"])
# 新增概念分析接口
api_router.include_router(concept_analysis.router, prefix="/concept-analysis", tags=["concept-analysis"])
# 新增图表数据接口
api_router.include_router(chart_data.router, prefix="/chart-data", tags=["chart-data"])
# 新增TXT文件导入接口
api_router.include_router(txt_import.router, prefix="/txt-import", tags=["txt-import"])
# 新增股票分析接口
api_router.include_router(stock_analysis.router, prefix="/stock-analysis", tags=["stock-analysis"])
# 新增数据库优化状态检查接口
api_router.include_router(optimization_status.router, prefix="/optimization", tags=["database-optimization"])
# 新增历史TXT文件导入接口
api_router.include_router(historical_txt_import.router, prefix="/historical-txt-import", tags=["historical-txt-import"])
# 新增大文件上传接口 (暂时注释，修复后启用)
# api_router.include_router(large_file_upload.router, prefix="/large-file-upload", tags=["large-file-upload"])