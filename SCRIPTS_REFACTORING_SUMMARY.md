# 脚本整理汇总 - Scripts Refactoring Summary

整理日期: 2025-01-13
整理版本: v1.0

## 📋 整理概述

本次整理旨在规范和优化项目中散落的 Shell 脚本，提高脚本的可维护性和易用性。

### 问题分析

**整理前的问题：**
- ❌ 脚本位置分散（根目录、scripts/deployment/、scripts/database/）
- ❌ 重复脚本多（start.sh、stop.sh、status.sh 在多个地方）
- ❌ 命名不规范（quick-deploy.sh、migrate_to_plan1.sh 等含义不清）
- ❌ 缺少统一的使用文档
- ❌ 过时脚本未清理（upgrade_v2.7.sh 等）

### 整理目标

✅ 建立统一的脚本目录结构  
✅ 消除脚本重复  
✅ 规范脚本命名和功能  
✅ 创建详细的使用文档  
✅ 简化日常操作流程

## 🏗️ 新的目录结构

```
stock-analysis-system/
├── scripts/                          # 统一脚本目录
│   ├── bin/                          # ⭐ 日常开发和运维脚本（最常用）
│   │   ├── start.sh                  # 启动所有服务
│   │   ├── stop.sh                   # 停止所有服务
│   │   ├── restart.sh                # 重启所有服务
│   │   ├── status.sh                 # 检查服务状态
│   │   └── check-env.sh              # 环境检查
│   │
│   ├── database/                     # 数据库管理脚本
│   │   ├── init.sh                   # 初始化数据库
│   │   ├── verify.sh                 # 验证数据库
│   │   ├── migrate.sh                # 数据库迁移
│   │   └── optimize.sh               # 数据库优化
│   │   └── ... (SQL files & Python scripts)
│   │
│   ├── deploy/                       # 部署脚本
│   │   ├── deploy-local.sh           # 本地部署
│   │   ├── deploy-staging.sh         # 预发布部署
│   │   └── deploy-production.sh      # 生产部署
│   │
│   ├── utils/                        # 工具脚本
│   │   ├── setup-database.sh         # PostgreSQL 设置
│   │   ├── generate-token.sh         # 生成 JWT token
│   │   └── cleanup.sh                # 清理临时文件
│   │
│   └── README.md                     # ⭐ 脚本使用文档
│
├── start.sh                          # 根目录快捷脚本（指向 scripts/bin/start.sh）
├── stop.sh                           # 根目录快捷脚本（指向 scripts/bin/stop.sh）
├── restart.sh                        # 根目录快捷脚本（指向 scripts/bin/restart.sh）
├── status.sh                         # 根目录快捷脚本（指向 scripts/bin/status.sh）
└── ...
```

## 📝 主要改动

### 1. 新增脚本

#### scripts/bin/ 目录（核心脚本）
- `start.sh` - 启动所有服务（后端 + 前端 + 客户端）
- `stop.sh` - 优雅地停止所有服务
- `restart.sh` - 重启所有服务（stop + start）
- `status.sh` - 详细的服务状态检查和日志预览
- `check-env.sh` - 环境检查（已复制）

#### scripts/deploy/ 目录
- `deploy-local.sh` - 本地部署脚本
- `deploy-staging.sh` - 预发布环境部署
- `deploy-production.sh` - 生产环境部署

#### scripts/utils/ 目录
- `setup-database.sh` - PostgreSQL 初始化和数据库创建
- `generate-token.sh` - 生成 JWT tokens
- `cleanup.sh` - 清理日志和临时文件

### 2. 改进的脚本

#### 根目录脚本
- `start.sh` → 现在指向 `scripts/bin/start.sh`
- `stop.sh` → 现在指向 `scripts/bin/stop.sh`
- `restart.sh` → 现在指向 `scripts/bin/restart.sh`
- `status.sh` → 现在指向 `scripts/bin/status.sh`

这样用户可以在根目录直接运行 `./start.sh`，也可以运行 `./scripts/bin/start.sh`。

### 3. 新增文档

#### `scripts/README.md`
详细的脚本使用文档，包括：
- 快速开始指南
- 每个脚本的功能说明
- 常见任务的命令示例
- 故障排除指南
- 安全建议

## 🚀 使用方式

### 日常开发

```bash
# 启动所有服务
./start.sh

# 或使用完整路径
./scripts/bin/start.sh

# 查看状态
./status.sh

# 停止服务
./stop.sh

# 重启服务
./restart.sh
```

### 数据库管理

```bash
# 初始化数据库
./scripts/database/init.sh

# 验证数据库
./scripts/database/verify.sh
```

### 部署

```bash
# 本地部署
./scripts/deploy/deploy-local.sh

# 生产部署
./scripts/deploy/deploy-production.sh 82.157.28.35
```

## ✨ 改进优势

1. **易用性提升**
   - ✅ 统一的脚本位置
   - ✅ 清晰的功能分类
   - ✅ 详细的使用文档

2. **可维护性提升**
   - ✅ 消除脚本重复
   - ✅ 规范的命名方式
   - ✅ 统一的脚本格式

3. **用户友好**
   - ✅ 根目录的快捷脚本
   - ✅ 彩色输出和清晰的提示
   - ✅ 错误信息提示

4. **向后兼容**
   - ✅ 根目录脚本仍可使用
   - ✅ 原有脚本保留（可逐步迁移）
   - ✅ 无需改变现有工作流

## 🔄 迁移计划

### 第 1 阶段（已完成）
- ✅ 创建新的脚本目录结构
- ✅ 开发核心脚本 (start, stop, restart, status)
- ✅ 创建文档
- ✅ 创建根目录的链接脚本

### 第 2 阶段（待进行）
- ⏳ 编写完整的部署脚本
- ⏳ 编写完整的数据库脚本
- ⏳ 删除过时的脚本
- ⏳ 团队培训和文档更新

### 第 3 阶段（后续优化）
- ⏳ 添加更多工具脚本
- ⏳ 支持多环境配置
- ⏳ 添加脚本版本管理
- ⏳ 集成 CI/CD 流程

## 📚 文档位置

- **脚本使用指南**: `scripts/README.md`
- **本汇总文档**: `SCRIPTS_REFACTORING_SUMMARY.md`

## ⚠️ 注意事项

1. **权限问题**
   如果脚本无执行权限，运行：
   ```bash
   chmod +x scripts/bin/*.sh
   chmod +x scripts/database/*.sh
   chmod +x scripts/deploy/*.sh
   chmod +x scripts/utils/*.sh
   ```

2. **日志位置**
   - 后端日志: `logs/backend.log`
   - 前端日志: `logs/frontend.log`
   - 客户端日志: `logs/client.log`

3. **数据库配置**
   配置文件：`backend/.env`
   DATABASE_URL 的格式：
   ```
   postgresql+psycopg2://user:password@localhost/dbname
   ```

## 🎯 下一步建议

1. **验证脚本**
   ```bash
   ./scripts/bin/check-env.sh
   ```

2. **测试启动**
   ```bash
   ./start.sh
   ```

3. **查看文档**
   ```bash
   cat scripts/README.md
   ```

4. **定期维护**
   - 清理过时的脚本
   - 更新文档
   - 收集用户反馈

## 💡 常见问题

### Q: 根目录的脚本还能用吗？
A: 可以的！根目录的脚本现在是链接脚本，会自动调用 `scripts/bin/` 目录下的脚本。

### Q: 如何集成到 CI/CD？
A: 部署脚本在 `scripts/deploy/` 目录，可以在 CI/CD 流程中调用。

### Q: 如何添加新脚本？
A: 根据功能类型，将新脚本放在相应的目录（bin/、database/、deploy/ 或 utils/），并更新 README.md。

## 📞 支持

如有任何问题或建议，请参考：
- `scripts/README.md` - 使用文档
- `logs/backend.log` 等 - 服务日志
- `.env` 文件 - 配置说明

---

**版本**: 1.0  
**更新日期**: 2025-01-13  
**维护者**: Development Team
