"""
API v1 主路由配置
"""

from fastapi import APIRouter
from app.api.api_v1.endpoints import stocks, concepts, data_import, auth, admin_users, payment, admin_packages, system
from app.api import simple_import

api_router = APIRouter()

# 包含各个模块的路由
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(admin_users.router, prefix="/admin", tags=["admin-users"])
api_router.include_router(admin_packages.router, prefix="/admin", tags=["admin-packages"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(concepts.router, prefix="/concepts", tags=["concepts"])
api_router.include_router(data_import.router, prefix="/data", tags=["data-import"])
api_router.include_router(payment.router, prefix="/payment", tags=["payment"])
# 新增简化导入接口
api_router.include_router(simple_import.router, prefix="/simple-import", tags=["simple-import"])