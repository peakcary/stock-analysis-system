"""
股票概念分析系统 - FastAPI 主应用
Stock Concept Analysis System - FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
import os

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
      print("✅ 默认文件类型(eee/ttv)已初始化")

      # 初始化支付套餐
      try:
          from app.models.payment import PaymentPackage
          from decimal import Decimal

          # 检查是否已有套餐
          existing_packages = db.query(PaymentPackage).count()
          if existing_packages == 0:
              packages = [
                  PaymentPackage(
                      package_type='free_trial',
                      name='免费试用',
                      description='免费试用套餐，测试专用',
                      price=Decimal('0.01'),
                      queries_count=10,
                      validity_days=7,
                      membership_type='free',
                      is_active=True,
                      sort_order=1
                  ),
                  PaymentPackage(
                      package_type='monthly_pro',
                      name='专业版月卡',
                      description='专业版月度套餐',
                      price=Decimal('99.00'),
                      queries_count=500,
                      validity_days=30,
                      membership_type='pro',
                      is_active=True,
                      sort_order=2
                  ),
              ]
              for pkg in packages:
                  db.add(pkg)
              db.commit()
              print("✅ 支付套餐已初始化")
      except Exception as e:
          print(f"⚠️ 初始化支付套餐失败: {e}")

      db.close()
    except Exception as e:
      print(f"⚠️ 启动初始化失败: {e}")
    yield
    # 关闭时执行
    print("🛑 股票分析系统已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="股票概念分析系统",
    description="Stock Concept Analysis System API - 提供股票概念数据分析和查询服务",
    version="1.0.0",
    docs_url=None,  # 禁用默认的 Swagger UI（使用 CDN）
    redoc_url=None,  # 禁用默认的 ReDoc（使用 CDN）
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
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json"
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "系统正常运行"}


@app.get("/docs", response_class=HTMLResponse)
async def get_swagger_docs():
    """API 文档页面 - 显示 OpenAPI JSON 和访问说明"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>API 文档 - 股票概念分析系统</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
            }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            header { background: #2c3e50; color: white; padding: 40px 0; margin-bottom: 40px; }
            header h1 { margin-bottom: 10px; }
            header p { opacity: 0.9; }
            .section { background: white; padding: 30px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h2 { color: #2c3e50; margin-bottom: 20px; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h3 { color: #34495e; margin-top: 20px; margin-bottom: 10px; }
            .info-box { background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; border-radius: 4px; }
            .success { color: #27ae60; }
            .warning { color: #f39c12; }
            .code {
                background: #2c3e50;
                color: #ecf0f1;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                margin: 10px 0;
                font-family: 'Courier New', monospace;
                font-size: 13px;
            }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #3498db; }
            .method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-weight: bold; font-size: 12px; margin-right: 10px; }
            .get { background: #61affe; color: white; }
            .post { background: #49cc90; color: white; }
            .put { background: #fca130; color: white; }
            .delete { background: #f93e3e; color: white; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th { background: #34495e; color: white; padding: 12px; text-align: left; }
            td { padding: 12px; border-bottom: 1px solid #ecf0f1; }
            tr:hover { background: #f8f9fa; }
            a { color: #3498db; text-decoration: none; }
            a:hover { text-decoration: underline; }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background: #3498db;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                margin: 5px 5px 5px 0;
                border: none;
                cursor: pointer;
            }
            .button:hover { background: #2980b9; }
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <h1>📚 API 文档</h1>
                <p>股票概念分析系统</p>
            </div>
        </header>

        <div class="container">
            <div class="section">
                <h2>✅ 服务状态</h2>
                <div class="info-box">
                    <span class="success">✓ 服务运行中</span><br>
                    <span class="success">✓ 数据库已连接</span><br>
                    <span class="success">✓ API 端点正常</span>
                </div>
            </div>

            <div class="section">
                <h2>🔗 API 访问方式</h2>
                <h3>1. OpenAPI JSON (推荐用于 API 集成)</h3>
                <button class="button" onclick="fetch('/openapi.json').then(r=>r.json()).then(d=>console.log(d))">获取 OpenAPI 规范</button>
                <div class="code">GET /openapi.json</div>

                <h3>2. 使用 curl 测试 API</h3>
                <div class="code">curl http://localhost:3007/openapi.json | python -m json.tool</div>

                <h3>3. 使用 Postman 或其他工具</h3>
                <p>导入 OpenAPI JSON: <code>http://localhost:3007/openapi.json</code></p>

                <h3>4. 查看完整 API 规范</h3>
                <a href="/openapi.json" target="_blank" class="button">查看 OpenAPI JSON</a>
            </div>

            <div class="section">
                <h2>🧪 快速测试</h2>
                <div class="endpoint">
                    <span class="method get">GET</span>
                    <code>/</code><br>
                    <small>系统信息</small>
                </div>
                <div class="code">curl http://localhost:3007/</div>

                <div class="endpoint">
                    <span class="method get">GET</span>
                    <code>/health</code><br>
                    <small>健康检查</small>
                </div>
                <div class="code">curl http://localhost:3007/health</div>

                <div class="endpoint">
                    <span class="method post">POST</span>
                    <code>/api/v1/auth/register</code><br>
                    <small>用户注册</small>
                </div>
                <div class="code">curl -X POST http://localhost:3007/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"username":"test","email":"test@example.com","password":"password123"}'</div>
            </div>

            <div class="section">
                <h2>📋 主要 API 端点</h2>
                <h3>认证 (/api/v1/auth)</h3>
                <table>
                    <tr>
                        <th>方法</th>
                        <th>端点</th>
                        <th>描述</th>
                    </tr>
                    <tr>
                        <td><span class="method post">POST</span></td>
                        <td>/api/v1/auth/register</td>
                        <td>用户注册</td>
                    </tr>
                    <tr>
                        <td><span class="method post">POST</span></td>
                        <td>/api/v1/auth/login</td>
                        <td>用户登录</td>
                    </tr>
                    <tr>
                        <td><span class="method get">GET</span></td>
                        <td>/api/v1/auth/me</td>
                        <td>获取当前用户信息</td>
                    </tr>
                </table>

                <h3>股票 (/api/v1/stocks)</h3>
                <table>
                    <tr>
                        <th>方法</th>
                        <th>端点</th>
                        <th>描述</th>
                    </tr>
                    <tr>
                        <td><span class="method get">GET</span></td>
                        <td>/api/v1/stocks/</td>
                        <td>获取股票列表</td>
                    </tr>
                    <tr>
                        <td><span class="method get">GET</span></td>
                        <td>/api/v1/stocks/{stock_code}</td>
                        <td>获取股票详情</td>
                    </tr>
                </table>

                <h3>更多端点</h3>
                <p>请查看完整的 <a href="/openapi.json" target="_blank">OpenAPI JSON 规范</a> 了解所有可用端点。</p>
            </div>

            <div class="section">
                <h2>💡 常见问题</h2>
                <h3>Q: 如何查看完整的 API 文档？</h3>
                <p>A: 访问 <a href="/openapi.json" target="_blank">/openapi.json</a> 获取完整的 OpenAPI 规范。</p>

                <h3>Q: 如何测试 API？</h3>
                <p>A: 使用 curl、Postman 或其他 HTTP 客户端工具。导入 OpenAPI JSON 规范即可。</p>

                <h3>Q: 有其他文档格式吗？</h3>
                <p>A: 访问 <a href="/redoc">/redoc</a> 获取 ReDoc 格式的文档（如果可用）。</p>
            </div>

            <div class="section">
                <h2>📞 其他资源</h2>
                <ul>
                    <li><a href="/health">健康检查端点</a></li>
                    <li><a href="/openapi.json">OpenAPI JSON 规范</a></li>
                    <li><a href="/redoc">ReDoc 文档</a></li>
                    <li><a href="/">系统信息</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/redoc", response_class=HTMLResponse)
async def get_redoc_docs():
    """ReDoc 文档 - 显示 OpenAPI JSON"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ReDoc - API 文档</title>
        <style>
            body { margin: 0; padding: 0; }
        </style>
    </head>
    <body>
        <div id="redoc-container"></div>
        <script>
            // 简单的 API 文档浏览器
            document.addEventListener('DOMContentLoaded', function() {
                fetch('/openapi.json')
                    .then(r => r.json())
                    .then(spec => {
                        const container = document.getElementById('redoc-container');
                        const html = '<h1>API 文档</h1><pre>' + JSON.stringify(spec, null, 2) + '</pre>';
                        container.innerHTML = html;
                    })
                    .catch(e => {
                        const container = document.getElementById('redoc-container');
                        container.innerHTML = '<h1>错误：无法加载 API 规范</h1><p>' + e.message + '</p>';
                    });
            });
        </script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; }
            pre { background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }
        </style>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=True,  # 开发模式热重载
        log_level="info"
    )
