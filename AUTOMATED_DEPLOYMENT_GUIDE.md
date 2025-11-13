# 自动化部署指南

## 📋 目录

1. [概述](#概述)
2. [部署架构](#部署架构)
3. [快速开始](#快速开始)
4. [详细流程](#详细流程)
5. [回滚机制](#回滚机制)
6. [常见问题](#常见问题)
7. [故障排查](#故障排查)

---

## 概述

本指南介绍了股票分析系统的三阶段自动化部署框架，支持从本地打包到生产环境部署的完整工作流。

### 核心特性

- ✅ **本地打包**: 清理、编译、打包为可部署的 tar.gz 包
- ✅ **完整性验证**: MD5 校验和防止包损坏
- ✅ **零停机部署**: 智能备份和恢复机制
- ✅ **一键回滚**: 快速恢复到任何之前的版本
- ✅ **自动化验证**: 部署后自动检查服务状态

---

## 部署架构

### 三阶段部署流程

```
┌─────────────────┐
│  本地开发机器   │
├─────────────────┤
│ 1-local-package │ ─┐
│      .sh        │  │ 生成 tar.gz + MD5
└─────────────────┘  │
                     │
                 [SCP上传]
                     │
                     ▼
    ┌─────────────────────────────────┐
    │     生产服务器 (82.157.28.35)   │
    ├─────────────────────────────────┤
    │  2-remote-deploy.sh             │
    │  ├─ 验证包完整性                │
    │  ├─ 备份当前版本                │
    │  ├─ 解包新版本                  │
    │  ├─ 更新配置                    │
    │  ├─ 安装依赖                    │
    │  ├─ 启动服务                    │
    │  └─ 验证部署                    │
    └─────────────────────────────────┘
         │
         │ (如需回滚)
         ▼
    ┌─────────────────────────────────┐
    │  3-rollback.sh                  │
    │  ├─ 停止服务                    │
    │  ├─ 备份失败版本                │
    │  ├─ 恢复备份版本                │
    │  ├─ 启动服务                    │
    │  └─ 验证恢复                    │
    └─────────────────────────────────┘
```

### 文件结构

```
scripts/deploy/
├── 1-local-package.sh          # 本地打包脚本
├── 2-remote-deploy.sh          # 远程部署脚本
└── 3-rollback.sh               # 回滚脚本

deploy-packages/                 # 部署包输出目录
├── stock-analysis-system_YYYYMMDD_HHMMSS.tar.gz
└── stock-analysis-system_YYYYMMDD_HHMMSS.md5
```

---

## 快速开始

### 前置要求

#### 本地机器

```bash
# macOS
brew install sshpass

# Ubuntu/Debian
sudo apt-get install sshpass
```

#### 服务器配置 (已预设)

- 服务器IP: 82.157.28.35
- SSH 用户: ubuntu
- 项目路径: /opt/stock-analysis-system
- 备份路径: /opt/backups
- 数据库: PostgreSQL (localhost:5432)
- 应用服务器: Gunicorn (127.0.0.1:3007)
- Web 服务器: Nginx (0.0.0.0:80)

### 一键部署 (3 步)

#### 步骤 1: 本地打包

```bash
cd /Users/peakom/work/stock-analysis-system
bash scripts/deploy/1-local-package.sh
```

预期输出:
```
📦 部署包信息：
  文件名: stock-analysis-system_YYYYMMDD_HHMMSS.tar.gz
  大小: X.XXM
  位置: /Users/peakom/work/stock-analysis-system/deploy-packages
  MD5: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 步骤 2: 上传部署包

```bash
# 替换 YYYYMMDD_HHMMSS 为实际的包名称
PACKAGE_NAME="stock-analysis-system_20251113_160003"

sshpass -p "chen_188_8_8" scp -o StrictHostKeyChecking=no \
  deploy-packages/${PACKAGE_NAME}.tar.gz \
  deploy-packages/${PACKAGE_NAME}.md5 \
  ubuntu@82.157.28.35:/tmp/
```

#### 步骤 3: 远程部署

```bash
sshpass -p "chen_188_8_8" scp -o StrictHostKeyChecking=no \
  scripts/deploy/2-remote-deploy.sh \
  ubuntu@82.157.28.35:/tmp/

sshpass -p "chen_188_8_8" ssh -o StrictHostKeyChecking=no \
  ubuntu@82.157.28.35 \
  "bash /tmp/2-remote-deploy.sh ${PACKAGE_NAME}"
```

预期输出:
```
✅ 生产环境部署完成！
📋 服务访问地址：
  🔗 后端 API:     http://82.157.28.35:3007
  📖 API 文档:     http://82.157.28.35:3007/docs
  🌐 前端应用:     http://82.157.28.35
```

---

## 详细流程

### 1. 本地打包 (1-local-package.sh)

#### 功能

- 清理临时文件
- 复制后端源码
- 构建前端应用 (npm run build)
- 打包配置文件
- 生成 tar.gz 压缩包
- 计算 MD5 校验和

#### 执行流程

```bash
# 创建临时目录
TEMP_DIR=$(mktemp -d)
PACKAGE_TEMP="$TEMP_DIR/$PACKAGE_NAME"

# 复制后端代码
cp -r backend/*.py backend/app backend/requirements.txt

# 构建前端
cd frontend && npm run build && cp -r dist ../

# 生成压缩包
cd $TEMP_DIR
tar -czf $PACKAGE_DIR/${PACKAGE_NAME}.tar.gz $PACKAGE_NAME
md5sum $(pwd)/${PACKAGE_NAME}.tar.gz > ${PACKAGE_NAME}.md5

# 清理临时目录
rm -rf $TEMP_DIR
```

#### 输出文件

| 文件 | 用途 | 示例 |
|------|------|------|
| `.tar.gz` | 部署包 | stock-analysis-system_20251113_160003.tar.gz (1.0M) |
| `.md5` | 完整性验证 | bb7240b3500524eb0b912da2db6357f4  stock-analysis-system_20251113_160003.tar.gz |

### 2. 远程部署 (2-remote-deploy.sh)

#### 执行步骤 (8 步)

##### 步骤 1: 验证部署包
- 检查包是否存在
- 验证 MD5 校验和
- 确保包完整无损

##### 步骤 2: 备份当前版本
- 创建备份目录: `/opt/backups/stock-analysis-system_YYYYMMDD_HHMMSS`
- 保存当前完整项目
- 记录备份时间

##### 步骤 3: 停止服务
- 强制停止 Gunicorn 进程: `pkill -9 gunicorn`
- 等待 2 秒确保进程结束

##### 步骤 4: 解包新版本
- 提取 tar.gz 到 /tmp
- 删除旧项目目录
- 复制新版本到 `/opt/stock-analysis-system`
- 修复文件权限: `chown -R ubuntu:ubuntu`

##### 步骤 5: 更新配置文件
- 检查 `config/.env.prod` 文件
- 复制为 `backend/.env`
- 保持环境变量一致

##### 步骤 6: 安装依赖
- 创建 Python 虚拟环境 (venv)
- 升级 pip
- 安装 requirements.txt 所有依赖

##### 步骤 7: 启动服务
- 启动 Gunicorn (4 workers, UvicornWorker)
- 绑定到 127.0.0.1:3007
- 启用日志记录

##### 步骤 8: 验证部署
- 检查进程数量
- 验证端口监听
- 测试 API 健康检查
- 保存版本信息

#### 关键参数

```bash
# Gunicorn 配置
--workers 4                                  # 4 个工作进程
--worker-class uvicorn.workers.UvicornWorker # FastAPI 支持
--bind 127.0.0.1:3007                       # 本地绑定
--timeout 120                                # 请求超时 120 秒
```

#### 日志位置

| 日志 | 路径 |
|------|------|
| Gunicorn 访问日志 | `/var/log/gunicorn-access.log` |
| Gunicorn 错误日志 | `/var/log/gunicorn-error.log` |
| Nginx 访问日志 | `/var/log/nginx/stock-analysis-access.log` |
| Nginx 错误日志 | `/var/log/nginx/stock-analysis-error.log` |

### 3. 回滚机制 (3-rollback.sh)

#### 使用场景

- 部署后发现问题需要快速恢复
- 需要测试多个版本
- 灾难恢复和应急响应

#### 回滚到特定版本

```bash
# 查看可用备份
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "ls -ldt /opt/backups/stock-analysis-system_* | head -5"

# 回滚到特定版本
sshpass -p "chen_188_8_8" scp -o StrictHostKeyChecking=no \
  scripts/deploy/3-rollback.sh \
  ubuntu@82.157.28.35:/tmp/

sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "bash /tmp/3-rollback.sh 20251113_160054"
```

#### 回滚到最新备份 (自动)

```bash
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "bash /tmp/3-rollback.sh"
```

#### 回滚流程 (5 步)

1. **列出可用备份**: 显示最近的 5 个备份
2. **停止服务**: 优雅地停止 Gunicorn 和 Nginx
3. **备份失败版本**: 保存故障版本便于调查
4. **恢复备份**: 复制备份版本到生产路径
5. **验证恢复**: 启动服务并检查状态

---

## 常见问题

### Q1: 如何查看部署日志?

```bash
# 查看部署时的输出
cat /var/log/gunicorn-error.log
tail -f /var/log/gunicorn-error.log

# 查看最后 50 行错误
tail -50 /var/log/gunicorn-error.log
```

### Q2: 如何验证部署成功?

```bash
# API 健康检查
curl http://82.157.28.35/health

# 查看 API 文档
curl -I http://82.157.28.35/docs

# 检查进程
ps aux | grep gunicorn

# 检查端口
netstat -tlnp | grep 3007
```

### Q3: 部署包如何保存历史版本?

```bash
# 部署包默认保存在本地
ls -lh /Users/peakom/work/stock-analysis-system/deploy-packages/

# 整理历史包 (保留最近 10 个)
cd deploy-packages && ls -1t | tail -n +11 | xargs rm -f
```

### Q4: 如何快速重启后端服务?

```bash
# 在服务器上执行
pkill -9 gunicorn
cd /opt/stock-analysis-system/backend
source venv/bin/activate
nohup gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:3007 --daemon app.main:app
```

### Q5: 如何更新环境变量?

```bash
# 编辑服务器上的 .env 文件
ssh ubuntu@82.157.28.35
vim /opt/stock-analysis-system/backend/.env

# 重启后端生效
pkill -9 gunicorn
# (见 Q4 重启命令)
```

---

## 故障排查

### 问题 1: 部署包上传失败

**症状**: `scp: Connection closed`

**解决方案**:
```bash
# 1. 检查网络连接
ping 82.157.28.35

# 2. 检查 SSH 配置
ssh -v ubuntu@82.157.28.35

# 3. 检查服务器 SSH 服务
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 "echo OK"

# 4. 检查磁盘空间
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 "df -h"
```

### 问题 2: 部署后 API 无响应

**症状**: `curl http://82.157.28.35:3007/health` 返回 Failed to connect

**排查步骤**:
```bash
# 1. 检查 Gunicorn 进程
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "ps aux | grep gunicorn"

# 2. 检查错误日志
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "tail -20 /var/log/gunicorn-error.log"

# 3. 检查端口占用
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "netstat -tlnp | grep 3007"

# 4. 检查 Nginx 状态
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo systemctl status nginx"
```

### 问题 3: 备份恢复失败

**症状**: 回滚脚本执行失败或恢复后服务无法启动

**解决方案**:
```bash
# 1. 检查备份目录
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "ls -l /opt/backups/"

# 2. 手动恢复备份
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 << 'EOF'
  cd /opt
  rm -rf stock-analysis-system
  cp -r /opt/backups/stock-analysis-system_YYYYMMDD_HHMMSS stock-analysis-system
  sudo chown -R ubuntu:ubuntu stock-analysis-system
EOF

# 3. 手动启动服务
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "cd /opt/stock-analysis-system/backend && source venv/bin/activate && \
   nohup gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
   --bind 127.0.0.1:3007 --daemon app.main:app"
```

### 问题 4: 数据库连接失败

**症状**: 应用启动后数据库错误

**排查步骤**:
```bash
# 1. 检查 .env 配置
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "cat /opt/stock-analysis-system/backend/.env | grep DATABASE"

# 2. 测试数据库连接
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "PGPASSWORD=Pp123456 psql -U postgres -h localhost -d stockdb -c 'SELECT 1;'"

# 3. 检查 PostgreSQL 服务
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo systemctl status postgresql"
```

---

## 部署检查清单

### 部署前

- [ ] 代码已提交到 main 分支
- [ ] 本地构建测试成功
- [ ] 前端应用可正常构建 (`npm run build`)
- [ ] 通知了团队关于部署计划
- [ ] 备份了重要数据
- [ ] 确认服务器磁盘空间充足

### 部署中

- [ ] 本地打包脚本执行成功
- [ ] 部署包上传完成
- [ ] MD5 校验和验证通过
- [ ] 远程部署脚本执行完成
- [ ] 所有 8 个部署步骤都显示成功

### 部署后

- [ ] API 健康检查通过 (HTTP 200)
- [ ] 前端应用可加载
- [ ] 用户登录功能正常
- [ ] 数据库表数据完整
- [ ] 错误日志无异常警告
- [ ] 性能指标在预期范围内

---

## 性能监控

### 实时监控 Gunicorn

```bash
# 监控 Gunicorn 进程资源占用
watch -n 1 'ps aux | grep gunicorn | grep -v grep'

# 查看活动连接数
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "netstat -an | grep :3007 | grep ESTABLISHED | wc -l"
```

### 查看应用日志

```bash
# 实时查看错误日志
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "tail -f /var/log/gunicorn-error.log" | grep ERROR

# 统计错误频率
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "grep ERROR /var/log/gunicorn-error.log | wc -l"
```

---

## 版本

- **版本**: 1.0
- **最后更新**: 2025-11-13
- **适用系统**: Ubuntu 20.04 LTS
- **Python 版本**: 3.8+
- **Node.js 版本**: 16+

---

## 支持

遇到问题?

1. 查看本文档的 [常见问题](#常见问题) 部分
2. 查看 [故障排查](#故障排查) 部分
3. 检查服务器日志文件
4. 查看脚本内的详细输出

---

**祝部署顺利! 🚀**
