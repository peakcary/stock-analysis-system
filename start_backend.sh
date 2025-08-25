#!/bin/bash
echo "🚀 启动后端服务..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 3007 --reload
