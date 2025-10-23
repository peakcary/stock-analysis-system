# 🚀 快速开始指南

## 当前状态 ✅

| 组件 | 状态 | 说明 |
|------|------|------|
| **Nginx反向代理** | ✅ | HTTPS/HTTP已配置，所有路由正常 |
| **后端API服务** | ✅ | Gunicorn + Uvicorn运行中 |
| **健康检查** | ✅ | `/api/v1/health` 返回200 |
| **API文档** | ✅ | `/api/docs` (Swagger) 可访问 |
| **部署脚本** | ✅ | 一键部署系统就绪 |
| **数据库** | ⚠️ | 需要配置MySQL |

---

## 📋 部署清单

### 第一步: 配置数据库 (5-10分钟)

```bash
# 进入部署工具目录
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 查看数据库配置指南
cat DATABASE_SETUP.md

# 选择一个方案进行配置（推荐Docker MySQL或重新安装）
```

### 第二步: 部署代码到服务器 (1-2分钟)

```bash
# 进入部署工具目录
cd /Users/peakom/work/stock-analysis-system/deploy-tools

# 一键部署
./deploy.sh
```

**自动执行的步骤：**
- ✅ 清理本地虚拟环境和缓存
- ✅ 打包后端代码
- ✅ 上传到服务器
- ✅ 自动备份
- ✅ 部署并重启服务
- ✅ 验证服务健康

### 第三步: 初始化数据库 (1分钟)

```bash
# SSH连接到服务器
sshpass -p "chen_188_8_8" ssh ubuntu@82.157.28.35

# 进入后端目录
cd /opt/stock-analysis-system/backend

# 初始化数据库表
python3 init_database.py

# 退出SSH
exit
```

### 第四步: 验证一切正常 (1分钟)

```bash
# 查看服务状态
cd /Users/peakom/work/stock-analysis-system/deploy-tools
./check-status.sh

# 或手动测试API
curl https://qwquant.com/api/v1/health

# 访问API文档
# 浏览器打开: https://qwquant.com/api/docs
```

---

## 📁 文件夹位置

你的所有部署工具都在这里：

```
/Users/peakom/work/stock-analysis-system/deploy-tools/
├── deploy.sh              ← 每次更新时运行这个
├── rollback.sh            ← 如果部署失败运行这个
├── check-status.sh        ← 检查服务状态
├── README.md              ← 详细说明
└── DATABASE_SETUP.md      ← 数据库配置步骤
```

---

## 🔄 日常工作流程

### 更新代码和部署

```bash
# 1. 修改代码（在 /Users/peakom/work/stock-analysis-system/backend/ 中）
# 例如修改某个API端点...

# 2. 部署到服务器（一条命令）
/Users/peakom/work/stock-analysis-system/deploy-tools/deploy.sh

# 3. 验证部署成功
curl https://qwquant.com/api/v1/health

# 完成！
```

### 紧急回滚（如果部署失败）

```bash
# 立即回滚到上一个版本
/Users/peakom/work/stock-analysis-system/deploy-tools/rollback.sh

# 验证回滚成功
curl https://qwquant.com/api/v1/health
```

### 检查服务状态

```bash
# 查看运行状态、日志、备份文件
/Users/peakom/work/stock-analysis-system/deploy-tools/check-status.sh
```

---

## 🔗 关键网址

- **API健康检查**: https://qwquant.com/api/v1/health
- **Swagger UI**: https://qwquant.com/api/docs
- **ReDoc**: https://qwquant.com/api/redoc
- **OpenAPI规范**: https://qwquant.com/api/openapi.json

---

## ⚙️ 服务器信息

| 项目 | 值 |
|------|-----|
| **IP地址** | 82.157.28.35 |
| **用户** | ubuntu |
| **密码** | chen_188_8_8 |
| **后端目录** | /opt/stock-analysis-system/backend |
| **备份目录** | /opt/stock-analysis-system/backend_backup |
| **服务名** | stock-api |
| **监听端口** | 127.0.0.1:3007 |
| **域名** | qwquant.com |

---

## 💡 常见问题

**Q: 部署多久？**
A: 通常1-2分钟，取决于代码大小和网络速度

**Q: 部署会停机吗？**
A: 不会。Gunicorn会优雅处理，影响极小

**Q: 部署失败了怎么办？**
A: 运行 `rollback.sh` 自动回滚到上个版本

**Q: 如何查看部署日志？**
A: 运行 `check-status.sh` 查看最近20条日志

**Q: 我想改某个API端点？**
A: 修改代码后运行 `deploy.sh` 即可

---

## 📞 需要帮助?

查看对应的文档文件：
- 部署问题 → `README.md`
- 数据库问题 → `DATABASE_SETUP.md`
- 代码问题 → 后端源代码 `/Users/peakom/work/stock-analysis-system/backend/`

---

**你现在已经拥有一个生产级的部署系统！** 🎉

下一步：配置数据库，然后就可以开始使用了！
