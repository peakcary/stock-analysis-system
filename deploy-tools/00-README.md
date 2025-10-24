# 📦 部署工具完整指南

## 🎯 您现在拥有的完整部署系统

这个文件夹包含了一个**完整的生产级部署和维护系统**，支持：

✅ 自动化代码部署
✅ 数据库版本管理和迁移
✅ 自动备份和恢复
✅ 快速回滚
✅ 完整的文档和指南

---

## 📁 文件夹结构

```
deploy-tools/
├── 📄 00-README.md                    ← 这个文件（概览）
├── 📄 QUICK_UPDATE_GUIDE.md           ← ⭐ 快速参考（常用操作）
├── 📄 DEPLOYMENT_UPDATES.md           ← 详细的更新和版本管理指南
├── 📄 DB-QUICKSTART.md                ← 数据库快速开始
├── 📄 DATABASE_OPS.md                 ← 完整的数据库操作手册
├── 📄 VERSION                         ← 当前版本信息（自动更新）
│
├── 🔧 deploy.sh                       ← 部署脚本（已改进）
│   └─ 功能: 打包 → 上传 → 启动
│   └─ 用时: 2-3 分钟
│   └─ 命令: ./deploy.sh
│
├── 🔧 db-migrate.sh                   ← 数据库迁移脚本（新增）
│   └─ 功能: 执行数据库版本迁移
│   └─ 用时: 1-2 分钟
│   └─ 命令: ./db-migrate.sh <版本号> upgrade
│
├── 🔧 db-backup.sh                    ← 数据库备份脚本
│   └─ 功能: 备份数据库到本地
│   └─ 用时: 1-2 分钟
│   └─ 命令: ./db-backup.sh
│
├── 🔧 db-restore.sh                   ← 数据库恢复脚本
│   └─ 功能: 从备份恢复数据库
│   └─ 用时: 2-5 分钟
│   └─ 命令: ./db-restore.sh <备份文件>
│
├── 🔧 rollback.sh                     ← 代码回滚脚本
│   └─ 功能: 快速回滚到上一个版本
│   └─ 用时: 1-2 分钟
│   └─ 命令: ./rollback.sh
│
├── 🔧 check-status.sh                 ← 状态检查脚本
│   └─ 功能: 检查服务运行状态和日志
│   └─ 命令: ./check-status.sh
│
├── 📁 migrations/                     ← 数据库迁移脚本文件夹（新增）
│   ├── 001_initial_schema.py          ← 初始化迁移（自动运行）
│   ├── TEMPLATE.py                    ← 迁移模板（复制后修改）
│   ├── 002_*.py                       ← 您以后创建的迁移
│   └── 003_*.py                       ← 更多迁移...
│
└── 📁 db-backups/                     ← 数据库备份文件夹
    ├── stock_analysis_prod_20251023_120000.sql
    ├── stock_analysis_prod_20251024_143022.sql
    └── ... 更多备份文件
```

---

## 🚀 快速开始（5 分钟）

### 1. 查看快速参考

```bash
cat QUICK_UPDATE_GUIDE.md
```

### 2. 执行第一次部署

```bash
# 部署代码
./deploy.sh

# 验证服务
curl https://qwquant.com/api/v1/health
```

### 3. 查看当前版本

```bash
cat VERSION
```

---

## 📚 文档导航

### 👶 初学者

1. 先读这个: `QUICK_UPDATE_GUIDE.md` (3 分钟)
2. 然后读: `DEPLOYMENT_UPDATES.md` 前半部分 (10 分钟)

### 👨‍💼 定期维护

1. `QUICK_UPDATE_GUIDE.md` - 查看命令
2. `DB-QUICKSTART.md` - 数据库操作
3. `DEPLOYMENT_UPDATES.md` - 问题排查

### 🔧 高级用户

- `DEPLOYMENT_UPDATES.md` - 完整指南
- `DATABASE_OPS.md` - 数据库详解
- `migrations/TEMPLATE.py` - 创建新的迁移

### 🚨 有问题时

1. `QUICK_UPDATE_GUIDE.md` - 故障排查小节
2. `DEPLOYMENT_UPDATES.md` - 常见情况处理
3. `DATABASE_OPS.md` - 常见问题

---

## 🎯 常见操作

### 部署新代码

```bash
./deploy.sh
```

数据库结构不变的情况下，这是**最常用的命令**。

### 部署 + 数据库迁移

```bash
./db-backup.sh              # 1. 先备份
./deploy.sh                 # 2. 部署代码
./db-migrate.sh 002 upgrade # 3. 迁移数据库
```

数据库结构有变化时使用这个流程。

### 紧急回滚

```bash
./rollback.sh               # 回滚代码
./db-restore.sh ./db-backups/stock_analysis_prod_20251024_*.sql
```

出问题时使用。会从备份恢复数据。

### 备份数据库

```bash
./db-backup.sh
```

定期运行，建议每周一次。

---

## 📊 工作流程图

```
日常工作:
┌─────────────────┐
│ 修改代码        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ ./deploy.sh     │  ← 部署代码
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ 验证 API        │  ← curl https://qwquant.com/api/v1/health
└─────────────────┘

版本更新流程:
┌──────────────────┐
│ 代码改变         │
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ ./db-backup.sh   │  ← 1. 备份
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ ./deploy.sh      │  ← 2. 部署
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ 需要迁移数据库？  │
└────────┬─────────┘
    是 / \否
      /   \
     ↓     ↓
  迁移   完成
```

---

## 🔐 安全提醒

### 危险操作

⚠️ **这些操作会删除或覆盖数据，请小心：**

| 操作 | 风险 | 防护措施 |
|------|------|---------|
| `db-restore.sh` | 🔴 很高 | 执行前手动确认 |
| `db-migrate.sh downgrade` | 🔴 很高 | 二次确认 |
| 编辑迁移脚本 | 🟡 中等 | 先在本地测试 |

### 安全最佳实践

✅ **必做：**
- 部署前备份数据库: `./db-backup.sh`
- 重要更新前制作备份副本
- 定期自动备份（可加到 cron）

⚠️ **注意：**
- 不要直接修改生产数据库
- 迁移脚本要经过测试
- 保存多个备份版本

---

## 🔄 完整的更新周期

### 第一周：初始部署

```bash
# 1. 初始化数据库（第一次部署时）
cd /Users/peakom/work/stock-analysis-system/deploy-tools
./db-init-simple.sh      # 创建表和默认用户

# 2. 创建初始备份
./db-backup.sh

# 3. 验证
./check-status.sh
```

### 定期维护

```bash
# 每周
./db-backup.sh           # 定期备份

# 代码有改动时
./deploy.sh              # 部署新代码

# 数据库有改动时
./db-migrate.sh X upgrade # 执行迁移
```

### 出现问题时

```bash
# 立即执行
./rollback.sh            # 回滚代码

# 如果数据库有问题
./db-restore.sh ./db-backups/good_backup.sql
```

---

## 📋 版本跟踪

### 查看当前版本

```bash
cat VERSION
```

输出：
```
APP_VERSION=20251024_143022      # 应用部署时间
DB_VERSION=001_initial_schema    # 数据库版本
LAST_UPDATE=2025-10-24           # 最后更新日期
DESCRIPTION=...                  # 描述
```

### 版本号含义

- **APP_VERSION**: 应用代码的版本（时间戳）
- **DB_VERSION**: 数据库结构的版本（迁移版本号）
- 两者**独立管理**，可以不同步

### 更新版本

版本信息在执行 `./deploy.sh` 时**自动更新**，无需手动修改。

---

## 🎓 学习路径

### 路径 1: 快速上手（15 分钟）

1. 阅读: `QUICK_UPDATE_GUIDE.md` (5 分钟)
2. 尝试: `./deploy.sh` (3 分钟)
3. 尝试: `./db-backup.sh` (2 分钟)
4. 验证: `curl https://qwquant.com/api/v1/health` (1 分钟)
5. 查看: `cat VERSION` (1 分钟)

### 路径 2: 完整理解（45 分钟）

1. 阅读: `QUICK_UPDATE_GUIDE.md` (10 分钟)
2. 阅读: `DEPLOYMENT_UPDATES.md` (20 分钟)
3. 实践: 执行一次完整的部署流程 (10 分钟)
4. 阅读: 了解迁移系统 (5 分钟)

### 路径 3: 深入精通（2 小时）

1. 完成路径 2 (45 分钟)
2. 阅读: `DATABASE_OPS.md` (30 分钟)
3. 创建一个测试迁移脚本 (20 分钟)
4. 研究 `migrations/TEMPLATE.py` (15 分钟)
5. 实践回滚和恢复 (10 分钟)

---

## 💬 常见问题

### Q: 部署多久需要一次？

A: 根据需要。有代码改动时就部署一次，通常 2-3 分钟完成。

### Q: 数据库迁移是必须的吗？

A: 只有当数据库结构改变时才需要。代码改动但表结构不变时，不需要迁移。

### Q: 如何知道需不需要创建新的迁移？

A: 如果修改了 ORM 模型（添加/删除/修改字段），就需要创建新的迁移。

### Q: 备份要保留多久？

A: 建议保留最近 10 个备份，每周创建一个。可以用命令清理：
```bash
ls -t ./db-backups/*.sql | tail -n +11 | xargs rm -f
```

### Q: 可以同时备份和部署吗？

A: 不推荐。应该先备份 → 等待完成 → 再部署。

---

## 🆘 获取帮助

### 问题排查步骤

1. 查看快速参考: `QUICK_UPDATE_GUIDE.md` - 故障排查
2. 查看详细文档: `DEPLOYMENT_UPDATES.md` - 常见情况处理
3. 检查日志: `./check-status.sh`
4. 如果不确定，先回滚: `./rollback.sh`

### 重要文件位置

```
项目根目录
└── deploy-tools/           ← 您现在这里
    ├── deploy.sh
    ├── db-migrate.sh
    ├── migrations/
    └── [各种文档]

生产服务器
└── /opt/stock-analysis-system/
    ├── backend/            ← 当前应用代码
    └── backend_backup/     ← 备份代码
```

---

## 📞 快速命令速查

```bash
# 最常用的 5 个命令
./deploy.sh                    # 部署代码
./db-backup.sh                 # 备份数据库
./db-restore.sh ./db-backups/[文件]  # 恢复数据库
./rollback.sh                  # 回滚代码
./check-status.sh              # 查看状态

# 数据库迁移
./db-migrate.sh 002 upgrade    # 升级到版本 002
./db-migrate.sh 002 downgrade  # 回滚版本 002

# 查看信息
cat VERSION                     # 查看版本
ls -lh ./db-backups/           # 查看备份
ls ./migrations/               # 查看迁移
```

---

## 🎉 您现在拥有

✅ 完整的自动化部署系统
✅ 数据库版本管理
✅ 自动备份和恢复
✅ 快速回滚能力
✅ 详细的文档和指南

**一切已准备好用于生产环境！**

---

## 📝 下一步

1. 👉 **立即阅读**: `QUICK_UPDATE_GUIDE.md`
2. 👉 **理解流程**: `DEPLOYMENT_UPDATES.md`
3. 👉 **开始使用**: `./deploy.sh`

---

**版本**: 1.0
**最后更新**: 2025-10-24
**维护者**: Claude Code
