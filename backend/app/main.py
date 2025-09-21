"""
股票概念分析系统 - FastAPI 主应用
Stock Concept Analysis System - FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 导入路由和配置
from app.api.api_v1.api import api_router
from app.api.simple_import import router as simple_import_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exception_handlers import setup_exception_handlers
from app.middleware.request_middleware import (
    RequestLoggingMiddleware,
    RateLimitMiddleware
)
from app.core.database import SessionLocal, get_engine
from app.services.schema import FileTypeRegistry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logging(
        log_level="INFO",
        log_file="logs/app.log",
        use_json_format=False
    )
    print("🚀 股票分析系统启动中...")
    print("📊 日志系统已初始化")
    # 确保默认文件类型(eee/ttv)的动态表与模型可用
    try:
      engine = get_engine()
      db = SessionLocal()
      registry = FileTypeRegistry(engine, db)
      for ft in ["ttv", "eee"]:
          try:
              # 如果表不存在则创建，并确保模型生成
              if not registry.table_manager._tables_exist(ft):
                  registry.table_manager.create_file_type_tables(ft)
              registry.model_generator.generate_models_for_file_type(ft)
          except Exception as se:
              print(f"⚠️ 初始化文件类型 {ft} 失败: {se}")
      db.close()
      print("✅ 默认文件类型(eee/ttv)已初始化")
    except Exception as e:
      print(f"⚠️ 启动初始化文件类型失败: {e}")
    yield
    # 关闭时执行
    print("🛑 股票分析系统已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="股票概念分析系统",
    description="Stock Concept Analysis System API - 提供股票概念数据分析和查询服务",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc
    lifespan=lifespan
)

# 设置异常处理器
setup_exception_handlers(app)

# 添加中间件
app.add_middleware(RequestLoggingMiddleware, log_requests=True, log_responses=False)
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8005",  # Client 应用
        "http://127.0.0.1:8005",
        "http://localhost:8006",  # Frontend 管理应用  
        "http://127.0.0.1:8006",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# 添加 API 路由 - 统一在 /api/v1 下
app.include_router(api_router, prefix="/api/v1")
app.include_router(simple_import_router, prefix="/api/v1/import")


@app.get("/")
async def root():
    """根路径 - 系统健康检查"""
    return {
        "message": "股票概念分析系统 API",
        "version": "1.0.0",
        "status": "运行中",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "系统正常运行"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True,  # 开发模式热重载
        log_level="info"
    )
