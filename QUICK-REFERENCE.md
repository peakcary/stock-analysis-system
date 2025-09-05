# 🚀 快速参考卡片

## 📋 四个核心命令

```bash
./deploy.sh        # 🔧 一键部署（首次使用）
./start.sh         # ▶️  启动系统
./stop.sh          # 🛑 停止系统  
./init-database.sh # 🗄️ 数据库管理
```

## 🌐 访问地址

| 服务 | 地址 | 标题 | 用途 |
|-----|------|-----|-----|
| 用户端 | http://localhost:8005 | 股票分析系统 | 股票查询、会员购买 |
| 管理端 | http://localhost:8006 | 股票分析系统 - 管理端 | 系统管理、数据导入 |
| API文档 | http://localhost:3007/docs | Stock Analysis API | 接口文档 |

## 👤 默认账户

```
管理员: admin / admin123
```

## 🔧 常用操作

```bash
# 首次使用
./deploy.sh && ./start.sh

# 日常开发
./start.sh    # 开始工作
./stop.sh     # 结束工作

# 解决问题
./stop.sh && ./start.sh        # 重启服务
./init-database.sh             # 重置数据库
./deploy.sh                    # 重新部署

# 查看日志
tail -f logs/backend.log       # API日志
tail -f logs/client.log        # 用户端日志
tail -f logs/frontend.log      # 管理端日志
```

## 🏗️ 系统架构

```
端口配置:
┌─────────────────┐
│ API服务: 3007   │ ← FastAPI后端
├─────────────────┤
│ 用户端: 8005    │ ← React前端(用户)
├─────────────────┤  
│ 管理端: 8006    │ ← React前端(管理)
└─────────────────┘
```

## 💡 解决问题的万能公式

```bash
# 遇到任何问题时
./stop.sh && ./deploy.sh && ./start.sh
```