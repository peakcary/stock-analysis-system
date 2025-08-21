# 🚀 快速开始指南

## 📱 支持跨电脑开发的完整方案

### 🎯 第一次在新电脑上开发

#### 1. 一键环境安装
```bash
# 下载项目代码
git clone <your-repo-url>
cd stock-analysis-system

# 一键安装所有环境 (Python + Node.js + MySQL)
./setup_environment.sh

# 初始化数据库
./setup_database.sh

# 一键启动开发环境
./start_dev.sh
```

#### 2. 验证环境
- 🌐 前端: http://localhost:3000
- 🔗 后端: http://localhost:8000  
- 📚 API文档: http://localhost:8000/docs

### 🔄 换电脑开发

#### 在当前电脑备份
```bash
# 备份完整环境 (代码+数据库+配置)
./backup_environment.sh

# 将生成的 backup_YYYYMMDD_HHMMSS 目录复制到新电脑
```

#### 在新电脑恢复
```bash
# 进入备份目录
cd backup_YYYYMMDD_HHMMSS

# 一键恢复环境
./restore_environment.sh

# 进入恢复的项目
cd ../stock-analysis-system-restored

# 启动开发
./start_dev.sh
```

## 🛠️ 日常开发命令

### 开发启动
```bash
./start_dev.sh          # 一键启动前后端 (推荐)
# 或分别启动
./start_backend.sh      # 仅启动后端
./start_frontend.sh     # 仅启动前端
```

### 开发停止
```bash
./stop_dev.sh           # 停止所有服务
```

### 数据库操作
```bash
# 连接数据库
mysql -u root -proot123 stock_analysis

# 重置数据库
./setup_database.sh

# 备份数据库
mysqldump -u root -proot123 stock_analysis > backup.sql
```

### 查看日志
```bash
tail -f logs/backend.log   # 后端日志
tail -f logs/frontend.log  # 前端日志
```

## 📁 重要文件说明

### 环境脚本
- `setup_environment.sh` - 安装基础环境 (Python + Node.js + MySQL)
- `setup_database.sh` - 初始化数据库和配置
- `backup_environment.sh` - 备份完整环境
- `start_dev.sh` - 一键启动开发环境
- `stop_dev.sh` - 停止开发环境

### 项目文档
- `docs/PROJECT_DEVELOPMENT_GUIDE.md` - 完整开发指南
- `docs/CURRENT_STATUS.md` - 当前开发状态 (最重要!)
- `docs/ENVIRONMENT_MIGRATION.md` - 环境迁移详细说明
- `QUICK_START.md` - 快速开始 (本文件)

### 配置文件
- `backend/.env` - 后端环境变量
- `frontend/.env` - 前端环境变量
- `database/init.sql` - 数据库初始化脚本

## 🔍 故障排除

### 常见问题
1. **MySQL 连接失败**: 检查密码是否为 root123
2. **端口被占用**: 运行 `./stop_dev.sh` 释放端口
3. **Python 环境问题**: 删除 `backend/venv` 重新运行设置
4. **前端依赖问题**: 删除 `frontend/node_modules` 重新安装

### 环境重置
```bash
# 完全重置环境
rm -rf backend/venv frontend/node_modules
./setup_environment.sh
./setup_database.sh
```

## 🎯 开发继续流程

### 每次开始开发时
1. 查看 `docs/CURRENT_STATUS.md` - 了解当前进度
2. 运行 `./start_dev.sh` - 启动开发环境
3. 继续未完成的开发任务

### 开发完成时
1. 运行 `./stop_dev.sh` - 停止服务
2. 更新 `docs/CURRENT_STATUS.md` - 记录进度
3. 提交代码到 Git
4. 需要时运行 `./backup_environment.sh` 备份

### 重要节点备份
- 完成重要功能后
- 准备换电脑前
- 每周定期备份
- 部署前备份

## 💡 最佳实践

1. **始终使用脚本启动** - 避免手动配置错误
2. **定期备份环境** - 保证数据安全
3. **及时更新状态文档** - 保持开发连续性
4. **使用 Git 管理代码** - 版本控制和协作
5. **保持环境一致性** - 所有电脑使用相同配置

这套方案支持您在任意数量的电脑间无缝切换开发！