# 📋 脚本使用指南

## 🚀 优化版脚本概述

我们提供了优化版的部署和管理脚本，专门针对管理员认证系统和端口配置进行了优化。

### 📁 脚本文件列表

| 脚本名称 | 功能说明 | 使用方式 |
|---------|----------|----------|
| `deploy.sh` | 环境部署和初始化 | `./deploy.sh` |
| `migrate_database.sh` | 数据库迁移升级 | `./migrate_database.sh` |
| `start.sh` | 启动所有服务 | `./start.sh` |
| `stop.sh` | 停止所有服务 | `./stop.sh` |
| `status.sh` | 查看系统状态 | `./status.sh` |

## 🔧 脚本功能详解

### 1. **deploy.sh** - 环境部署脚本 ⭐ v2.6.4性能优化
- ✅ **数据库性能优化** - 自动部署高性能数据库架构，查询提升50-200倍
- ✅ **智能密码输入** - 支持动态MySQL密码输入，适配新环境部署
- ✅ **一键优化部署** - 完整集成数据库优化，零配置启用高性能模式
- ✅ **智能依赖检查** - 检测已安装包，避免重复安装
- ✅ **国内镜像加速** - 使用清华源，大幅提升安装速度  
- ✅ **容错性增强** - 优雅处理安装失败，提供详细错误提示
- ✅ 自动创建管理员用户账号 (`admin/admin123`)
- ✅ **创建TXT导入相关数据表** 
- ✅ 修复 package.json 中的端口配置问题
- ✅ 安装后端 Python 依赖和前端 Node.js 依赖
- ✅ 验证关键服务可用性（MySQL、Node.js、Python）
- ✅ **验证数据库表创建状态**
- ✅ 生成端口配置文件 `ports.env`

**参数选项**：
```bash
./deploy.sh                    # 完整部署 (包含数据库优化)
./deploy.sh --migrate         # 仅更新数据库结构  
./deploy.sh --upgrade-stock-codes # 升级股票代码字段
./deploy.sh --optimize-database   # 仅部署数据库优化 ⭐ 新增
./deploy.sh --help            # 显示帮助信息
```

**🚀 v2.6.4新增数据库优化功能**：
- 自动部署6张优化表结构和5个高性能视图
- 27,000+条数据无损迁移和预计算排名
- 查询性能提升50-200倍，毫秒级响应
- 智能缓存和分区表设计
- 完整的监控和回滚机制

### 2. **migrate_database.sh** - 数据库迁移脚本 🆕
- ✅ 专为现有环境升级设计
- ✅ 创建TXT导入相关的5个新数据表
- ✅ 保持现有数据不受影响
- ✅ 完整的迁移验证和状态检查
- ✅ 详细的错误处理和用户指引

### 3. **start.sh** - 服务启动脚本  
- ✅ 使用正确的端口配置启动所有服务
- ✅ 自动清理端口占用
- ✅ 后台启动服务并记录 PID
- ✅ 实时检查启动状态
- ✅ 提供服务访问地址

### 4. **stop.sh** - 服务停止脚本
- ✅ 根据 PID 文件优雅停止服务
- ✅ 强制清理端口占用进程
- ✅ 清理 PID 文件
- ✅ 详细的停止状态报告

### 5. **status.sh** - 系统状态检查
- 🆕 实时服务状态检查
- 🆕 资源使用情况监控  
- 🆕 数据库连接检查
- 🆕 日志文件状态和错误检查
- 🆕 网络可达性检查
- 🆕 系统健康度评估

## 📊 端口配置 

| 服务 | 端口 | 说明 |
|------|------|------|
| API服务 | 3007 | 后端API接口 |
| 客户端 | 8005 | 用户注册登录界面 |
| 管理端 | 8006 | 管理员后台界面 |

## 👤 默认账号

### 管理员账号（管理端 - 端口8006）
- **用户名**: `admin`
- **密码**: `admin123`  
- **访问**: http://localhost:8006
- **权限**: 无查询限制，完整管理权限

### 客户端账号（客户端 - 端口8005）
- 需要注册新账号
- **访问**: http://localhost:8005
- **权限**: 有查询限制，需购买套餐

## 🔄 使用流程

### 📦 首次部署 (全新环境)
```bash
# 1. 环境部署和初始化
./deploy.sh

# 2. 启动所有服务
./start.sh

# 3. 检查系统状态
./status.sh
```

### 🔄 环境迁移 (现有环境升级到v2.3.0)
```bash
# 1. 数据库迁移 (添加TXT导入功能相关表)
./migrate_database.sh

# 2. 启动所有服务
./start.sh

# 3. 检查系统状态和新功能
./status.sh
```

### 日常使用
```bash
# 启动系统
./start.sh

# 检查状态  
./status.sh

# 停止系统
./stop.sh
```

## 📝 日志管理

### 查看实时日志
```bash
# 后端API日志
tail -f logs/backend.log

# 客户端日志
tail -f logs/client.log

# 管理端日志
tail -f logs/frontend.log
```

### 日志文件说明
- `logs/backend.log` - 后端API服务日志
- `logs/client.log` - 客户端前端日志  
- `logs/frontend.log` - 管理端前端日志
- `logs/*.pid` - 进程ID文件

## 🚨 故障排除

### 🔧 部署阶段问题

**deploy.sh卡在设置后端** (已解决)：
```bash
# 问题原因：
# 1. Python版本兼容性问题 (Python 3.13过新)
# 2. pip包下载速度慢 (默认使用国外源)  
# 3. 重复安装已存在的包

# v2.4.3解决方案：
# ✅ 智能检查已安装包，避免重复安装
# ✅ 使用清华镜像源，10倍速度提升
# ✅ 增强容错性，优雅处理失败

# 手动修复方法(如果仍有问题)：
cd backend
python3 -m venv venv  
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**MySQL连接问题**：
```bash
# 检查MySQL服务状态
mysqladmin ping -h127.0.0.1

# 启动MySQL (macOS)
brew services start mysql

# 首次安装设置root密码
mysql_secure_installation
```

### 🚀 运行阶段问题

**端口被占用**：
```bash
# 检查端口占用
lsof -ti:3007,8005,8006

# 强制清理端口
lsof -ti:3007,8005,8006 | xargs kill -9
```

### 服务启动失败
```bash  
# 检查详细状态
./status.sh

# 查看错误日志
tail -n 50 logs/backend.log
tail -n 50 logs/client.log  
tail -n 50 logs/frontend.log
```

### 数据库连接问题
```bash
# 检查MySQL服务
mysqladmin ping -h127.0.0.1

# 启动MySQL服务
brew services start mysql  # macOS
```

## 📊 数据库结构更新 (v2.3.0)

### 🆕 新增数据表
- **`daily_trading`** - 每日交易量数据
- **`concept_daily_summary`** - 概念每日汇总
- **`stock_concept_ranking`** - 个股概念排名
- **`concept_high_record`** - 概念创新高记录
- **`txt_import_record`** - TXT导入记录

### 🔄 迁移说明
- **现有环境**: 使用 `./migrate_database.sh` 进行迁移
- **全新环境**: 使用 `./deploy.sh` 完整部署
- **数据安全**: 迁移过程不会影响现有股票和概念数据

## ⚠️ 注意事项

### 1. **数据库结构变更**
- v2.3.0版本新增了5个核心数据表
- 现有环境必须运行 `./migrate_database.sh` 才能使用TXT导入功能
- 建议在迁移前备份数据库

### 2. **端口配置冲突**
- 如果遇到端口占用问题，请先运行 `./stop.sh` 清理所有服务
- 然后重新运行 `./deploy.sh` 进行初始化

### 3. **认证系统变更**
- 新系统使用独立的管理员认证
- 管理端和客户端使用不同的认证token
- 如果发现认证问题，请清理浏览器缓存

### 4. **数据库迁移**  
- 部署脚本会自动创建所有必要的数据表
- 迁移脚本会保护现有的用户数据和股票数据
- 如有问题请检查 MySQL 服务状态和权限配置

## 🔍 系统验证

部署完成后，请验证以下内容：

### 1. 服务可访问性
- [ ] http://localhost:3007/docs (API文档)
- [ ] http://localhost:8005 (客户端)  
- [ ] http://localhost:8006 (管理端)

### 2. 管理员登录
- [ ] 使用 `admin/admin123` 登录管理端
- [ ] 能够访问股票列表和管理功能
- [ ] 无查询次数限制提示

### 3. 功能验证
- [ ] 股票数据显示正常
- [ ] 概念数据加载正常
- [ ] 数据导入功能可用

## 📞 技术支持

如果遇到问题，请：
1. 运行 `./status.sh` 获取系统状态
2. 检查相关日志文件
3. 提供详细的错误信息和系统状态报告

---

## 📈 性能建议

### 1. **生产环境配置**
- 修改 `backend/.env` 中的 `SECRET_KEY`
- 设置 `PAYMENT_MOCK_MODE=false` （如果使用真实支付）
- 配置适当的 `CORS` 域名

### 2. **监控和维护**
- 定期运行 `./status.sh` 检查系统健康度
- 监控日志文件大小，必要时清理
- 定期备份数据库数据

### 3. **扩展建议**  
- 可以添加定时任务执行 `./status.sh`
- 可以配置日志轮转避免文件过大
- 可以添加监控告警机制