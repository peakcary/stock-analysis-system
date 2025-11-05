# 股票分析系统 v2.7.0 - 快速开始指南

## 🚀 一键启动

```bash
# 克隆项目 (如果还没有)
git clone <repository-url>
cd stock-analysis-system

# 启动所有服务
./start-dev.sh

# 停止所有服务
./stop-dev.sh
```

## 📊 访问地址

启动后，可以通过以下地址访问各个服务：

- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **管理端**: http://localhost:8007
- **客户端**: http://localhost:8008

## 👤 登录信息

### 管理员账户
- **用户名**: `admin`
- **密码**: `admin123`
- **权限**: 系统管理、用户管理、数据导入

### 客户端测试账户
- **用户名**: `fullaccess_user`
- **密码**: `fullaccess123`
- **权限**: Premium会员，100000+查询次数

## 🔍 核心功能测试

### 1. 个股查询功能
1. 访问客户端：http://localhost:8008
2. 使用测试账户登录
3. 点击"个股查询"标签页
4. 输入股票代码（如：000001）进行测试
5. 点击概念查看相关股票

### 2. 用户管理功能
1. 访问管理端：http://localhost:8007
2. 使用管理员账户登录
3. 查看"用户管理"功能
4. 创建、编辑用户信息
5. 管理用户权限和查询次数

### 3. 数据导入功能
1. 在管理端登录后
2. 访问"数据导入"页面
3. 测试TXT、TTV、EEE文件导入
4. 查看导入记录和统计信息

## 🛠️ 开发调试

### 查看日志
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log

# 查看客户端日志
tail -f logs/client.log
```

### 端口占用检查
```bash
# 检查端口占用
lsof -i:8000  # 后端
lsof -i:8007  # 管理端
lsof -i:8008  # 客户端
```

### 服务状态检查
```bash
# 检查所有端口状态
for port in 8000 8007 8008; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "端口 $port: ✅ 运行中"
    else
        echo "端口 $port: ❌ 未运行"
    fi
done
```

## 📁 项目结构

```
stock-analysis-system/
├── backend/              # FastAPI后端服务
├── frontend/             # React管理端应用
├── client/               # React客户端应用
├── shared/               # 共享配置和工具
├── logs/                 # 运行日志目录
├── start-dev.sh          # 开发环境启动脚本
├── stop-dev.sh           # 开发环境停止脚本
└── README.md             # 项目文档
```

## ⚡ 核心技术栈

- **后端**: FastAPI + SQLAlchemy + MySQL
- **前端**: React + TypeScript + Ant Design
- **认证**: JWT Token
- **数据库**: MySQL 8.0+
- **缓存**: Redis (可选) + 内存缓存

## 🔧 环境要求

- **Node.js**: 16+
- **Python**: 3.8+
- **MySQL**: 8.0+
- **Redis**: 可选

## 🆘 常见问题

### 启动失败
1. 检查端口是否被占用
2. 确认数据库连接正常
3. 查看日志文件定位错误

### 登录问题
1. 确认使用正确的登录信息
2. 检查JWT token配置
3. 清除浏览器缓存

### API访问问题
1. 确认后端服务正常运行
2. 检查跨域配置
3. 验证API路径和参数

## 📞 技术支持

如遇到问题，可以：
1. 查看日志文件：`logs/*.log`
2. 检查服务状态：端口8000/8007/8008
3. 重启服务：`./stop-dev.sh && ./start-dev.sh`

---

**版本**: v2.7.0
**更新时间**: 2025-09-22
**状态**: ✅ 生产就绪