# 股票分析系统 - 部署工具

这个文件夹包含了所有用于部署和管理后端服务的脚本。

## 📁 文件说明

### 1. `deploy.sh` - 部署脚本 ⭐ 最常用
**功能**: 本地打包代码 → 上传到服务器 → 自动部署

**使用方法**:
```bash
cd /Users/peakom/work/stock-analysis-system/deploy-tools
./deploy.sh
```

**执行过程**:
1. 清理本地虚拟环境和Python缓存
2. 压缩后端代码为 tar.gz
3. 上传到服务器 /tmp/ 目录
4. 服务器自动：
   - 停止当前服务
   - 备份旧版本到 `backend_backup`
   - 解压新代码
   - 安装依赖
   - 重启服务
   - 验证健康状态

**预计耗时**: 1-2 分钟

---

### 2. `rollback.sh` - 回滚脚本 🔄
**功能**: 紧急回滚到上一个版本

**使用方法**:
```bash
./rollback.sh
```

**何时使用**:
- 部署后发现服务异常
- 需要恢复到上个稳定版本

**执行过程**:
1. 停止当前服务
2. 删除有问题的版本
3. 恢复备份的旧版本
4. 重启服务
5. 验证是否成功

**预计耗时**: 30 秒

---

### 3. `check-status.sh` - 状态检查脚本 📊
**功能**: 查看服务运行状态、健康检查、最近日志

**使用方法**:
```bash
./check-status.sh
```

**显示内容**:
- 服务 systemd 运行状态
- API 健康检查结果 (200 OK)
- 最近10条服务日志
- 备份文件是否存在

**预计耗时**: 10 秒

---

## 🚀 工作流程示例

### 场景 1: 正常更新部署

```bash
# 1. 在项目根目录修改代码
cd /Users/peakom/work/stock-analysis-system

# 修改 backend/ 中的代码...

# 2. 部署到服务器
cd deploy-tools
./deploy.sh

# 3. 检查部署是否成功
./check-status.sh

# 4. 测试API
curl https://qwquant.com/api/v1/health
```

### 场景 2: 部署失败需要回滚

```bash
# 1. 发现部署后服务异常
./check-status.sh

# 2. 立即回滚到上个版本
./rollback.sh

# 3. 验证服务恢复正常
./check-status.sh
```

### 场景 3: 定期检查服务健康

```bash
# 随时检查服务状态
./check-status.sh
```

---

## ⚙️ 服务器配置信息

| 配置项 | 值 |
|--------|-----|
| **服务器地址** | 82.157.28.35 |
| **用户名** | ubuntu |
| **后端目录** | /opt/stock-analysis-system/backend |
| **备份目录** | /opt/stock-analysis-system/backend_backup |
| **服务名称** | stock-api |
| **监听端口** | 127.0.0.1:3007 |
| **域名** | https://qwquant.com |
| **API前缀** | /api/v1/ |

---

## 📝 重要提示

### ✅ 部署前检查清单

- [ ] 修改代码已在本地测试
- [ ] 确保网络连接正常
- [ ] 确保有足够的磁盘空间 (建议 > 500MB)

### ⚠️ 常见问题

**Q: 部署失败了怎么办？**
A: 运行 `./rollback.sh` 立即回滚到上个版本

**Q: 如何查看部署日志？**
A: 运行 `./check-status.sh` 查看最近日志

**Q: 部署需要多长时间？**
A: 一般 1-2 分钟，取决于代码大小和网络速度

**Q: 能否跳过某个步骤？**
A: 不建议，每个步骤都很重要。如有特殊需求，请手动SSH到服务器

---

## 🔧 高级用法

### 手动SSH连接服务器

```bash
sshpass -p "chen_188_8_8" ssh -o StrictHostKeyChecking=no ubuntu@82.157.28.35
```

### 查看服务日志 (实时)

```bash
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo journalctl -u stock-api -f"
```

### 手动重启服务

```bash
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "sudo systemctl restart stock-api"
```

### 查看服务工作进程

```bash
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35 \
  "ps aux | grep gunicorn"
```

---

## 📦 脚本自动完成的任务

每次运行 `deploy.sh` 时，系统会自动：

✅ 清理虚拟环境 (venv)
✅ 删除Python缓存文件 (__pycache__)
✅ 删除编译文件 (*.pyc)
✅ 打包代码为压缩文件 (backend_YYYYMMDD_HHMMSS.tar.gz)
✅ 上传到服务器 /tmp/ 目录
✅ 备份当前版本
✅ 解压新代码
✅ 设置正确的文件权限
✅ 安装Python依赖
✅ 重启Gunicorn服务
✅ 验证服务健康状态

---

## 🎯 数据库配置 (重要！)

API健康检查已通过，但数据库还未配置。请参考 `DATABASE_SETUP.md` 进行配置。

**三个选项：**
1. **Docker MySQL** (推荐) - 最简单，隔离环境
2. **重新安装 MySQL** - 标准方案
3. **临时 SQLite** - 快速测试

完成数据库配置后，所有API功能都会100%正常工作！

---

## 📂 部署工具文件夹结构

```
deploy-tools/
├── deploy.sh              # 一键部署脚本 ⭐
├── rollback.sh            # 紧急回滚脚本
├── check-status.sh        # 状态检查脚本
├── README.md              # 这个文件
└── DATABASE_SETUP.md      # 数据库配置指南
```

---

**最后更新**: 2025-10-23
**版本**: 1.0
**作者**: Claude Code
