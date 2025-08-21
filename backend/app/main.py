"""
股票概念分析系统 - FastAPI 主应用
Stock Concept Analysis System - FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# TODO: 导入路由和配置
# from app.api.api_v1.api import api_router
# from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("🚀 股票分析系统启动中...")
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

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React 开发服务器
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # 备用端口
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# TODO: 添加 API 路由
# app.include_router(api_router, prefix="/api/v1")


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
        host="0.0.0.0", 
        port=8000, 
        reload=True,  # 开发模式热重载
        log_level="info"
    )