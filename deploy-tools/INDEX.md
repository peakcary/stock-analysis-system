# 📚 部署工具文件夹 - 完整索引

## 📂 文件夹位置

```
/Users/peakom/work/stock-analysis-system/deploy-tools/
```

---

## 📄 文件清单

### 1. **QUICKSTART.md** ⭐ 新手必读
- **用途**: 快速开始指南，5分钟了解整个部署流程
- **内容**: 
  - 当前部署状态
  - 4个步骤完整指南
  - 日常工作流程
  - 常见问题解答
- **何时查看**: 第一次使用或需要快速参考

---

### 2. **deploy.sh** 🚀 核心脚本
- **用途**: 一键自动部署脚本
- **执行方式**: `./deploy.sh`
- **功能**:
  - 清理本地虚拟环境和缓存
  - 打包后端代码为 tar.gz
  - 上传到服务器
  - 自动备份当前版本
  - 解压新代码
  - 安装依赖
  - 重启服务
  - 验证健康状态
- **预计耗时**: 1-2 分钟
- **何时使用**: 每次更新代码后
- **配置参数**:
  ```bash
  PROJECT_PATH="/Users/peakom/work/stock-analysis-system/backend"
  SERVER_IP="82.157.28.35"
  SERVER_USER="ubuntu"
  SERVER_PASSWORD="chen_188_8_8"
  ```

---

### 3. **rollback.sh** 🔄 应急回滚
- **用途**: 紧急回滚到上一个版本
- **执行方式**: `./rollback.sh`
- **功能**:
  - 停止当前服务
  - 删除有问题的版本
  - 恢复备份的旧版本
  - 重启服务
  - 验证恢复成功
- **预计耗时**: 30 秒
- **何时使用**: 部署后发现服务异常
- **回滚位置**: `/opt/stock-analysis-system/backend_backup`

---

### 4. **check-status.sh** 📊 状态检查
- **用途**: 查看服务运行状态和诊断信息
- **执行方式**: `./check-status.sh`
- **显示内容**:
  - 服务 systemd 运行状态
  - API 健康检查结果 (200 OK)
  - 最近 10 条服务日志
  - 备份文件是否存在
  - 内存使用情况
- **预计耗时**: 10 秒
- **何时使用**: 
  - 部署后验证
  - 定期健康检查
  - 排查问题时

---

### 5. **README.md** 📖 详细文档
- **用途**: 完整的部署系统说明文档
- **内容**:
  - 文件说明详解
  - 工作流程示例
  - 服务器配置信息
  - 高级用法
  - 常见问题
  - 自动完成的任务清单
- **何时查看**: 
  - 需要了解细节
  - 遇到问题需要排查
  - 学习高级用法

---

### 6. **DATABASE_SETUP.md** 🗄️ 数据库配置
- **用途**: MySQL 数据库一次性配置指南
- **内容**:
  - 当前问题说明
  - 三种解决方案:
    - 方案 A: 重新安装 MySQL
    - 方案 B: 使用 Docker MySQL (推荐)
    - 方案 C: 临时使用 SQLite
  - 完成后验证步骤
  - 自动数据库初始化
- **何时查看**: 
  - 第一次配置数据库
  - API数据操作出错
  - 需要重置数据库

---

### 7. **INDEX.md** (本文件) 📑
- **用途**: 完整索引和文件导航
- **内容**: 
  - 所有文件的说明
  - 快速查找指南
  - 工作流程决策树
  - 问题排查表

---

## 🎯 快速查找指南

### 我想做什么？

#### 📤 部署新代码
1. 修改代码
2. 运行 `./deploy.sh`
3. 完成！

#### 🔧 检查服务状态
```bash
./check-status.sh
```

#### 🔄 紧急回滚
```bash
./rollback.sh
```

#### ❓ 我不知道从哪里开始
```bash
cat QUICKSTART.md
```

#### 🗄️ 数据库有问题
```bash
cat DATABASE_SETUP.md
```

#### 📚 需要详细说明
```bash
cat README.md
```

#### 🔍 查找特定文件
```bash
cat INDEX.md  # 你正在读这个！
```

---

## 🚀 常用命令速查

```bash
# 进入部署工具目录
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 部署代码
./deploy.sh

# 回滚版本
./rollback.sh

# 检查状态
./check-status.sh

# 查看快速开始
cat QUICKSTART.md

# 查看数据库配置
cat DATABASE_SETUP.md

# 查看详细文档
cat README.md

# 给脚本执行权限（如果需要）
chmod +x *.sh
```

---

## ⚙️ 配置快速参考

### 服务器信息
- **IP**: 82.157.28.35
- **用户**: ubuntu
- **密码**: chen_188_8_8
- **后端目录**: /opt/stock-analysis-system/backend

### 部署路径
- **本地项目**: /Users/peakom/work/stock-analysis-system/
- **服务器项目**: /opt/stock-analysis-system/
- **备份位置**: /opt/stock-analysis-system/backend_backup

### API信息
- **域名**: https://qwquant.com
- **健康检查**: https://qwquant.com/api/v1/health
- **文档**: https://qwquant.com/api/docs
- **OpenAPI**: https://qwquant.com/api/openapi.json

---

## 📋 工作流程决策树

```
你需要：
│
├─ 部署代码? → ./deploy.sh
│
├─ 服务异常? → ./rollback.sh
│
├─ 检查状态? → ./check-status.sh
│
├─ 不知道从哪开始? → cat QUICKSTART.md
│
├─ 数据库问题? → cat DATABASE_SETUP.md
│
├─ 需要详细说明? → cat README.md
│
└─ 找文件? → cat INDEX.md (你在这里)
```

---

## 🆘 问题排查表

| 问题 | 第一步 | 第二步 | 第三步 |
|------|--------|--------|--------|
| 不知道如何开始 | 读 QUICKSTART.md | | |
| 服务无法连接 | `./check-status.sh` | 检查日志 | 联系支持 |
| 部署失败 | `./rollback.sh` | 检查错误日志 | 修复代码重试 |
| API返回500错误 | `./check-status.sh` | 查看后端日志 | 检查数据库 |
| 数据库连接失败 | 读 DATABASE_SETUP.md | 配置MySQL | 重启服务 |
| 性能变慢 | `./check-status.sh` | 监控日志 | 优化代码 |

---

## 📞 支持资源

- **部署文档**: README.md
- **快速开始**: QUICKSTART.md
- **数据库帮助**: DATABASE_SETUP.md
- **服务器日志**: 运行 `./check-status.sh`
- **代码位置**: /Users/peakom/work/stock-analysis-system/backend/

---

**版本**: 1.0
**最后更新**: 2025-10-23
**所有文件状态**: ✅ 就绪使用

🎉 你现在拥有完整的部署系统了！祝你使用愉快！
