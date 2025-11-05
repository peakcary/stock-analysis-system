# 立即部署 API 路径重复修复

## 修复内容总结

API路径重复问题已完全修复。相关提交:
- **66153fd2**: 前端 - 为所有API调用添加 `/api` 前缀
- **96d0624d**: Nginx - 添加路径重写规则 `/api/*` → `/api/v1/*`
- **bf17f459**: 文档 - 更新部署指南

## 修复原理

**问题**: 接口路径变成 `/api/v1/api/v1/stocks/simple`

**修复方式**:

1. **前端改变**: 所有API调用现在使用 `/api/stocks` 而不是 `/stocks`
2. **Nginx改变**: 使用rewrite规则在proxy_pass之前转换路径
   ```
   rewrite ^/api/(.*)$ /api/v1/$1 break;
   ```

**请求流程** (修复后):
```
前端: GET /api/stocks
  ↓
Nginx rewrite: /api/stocks → /api/v1/stocks
  ↓
后端收到: GET /api/v1/stocks (正确！)
  ↓
FastAPI 路由: app.include_router(api_router, prefix="/api/v1")
  ↓
最终路由: /api/v1/stocks → /stocks处理器 ✅
```

## 部署步骤

### 步骤 1: 在服务器上拉取最新代码

```bash
# SSH 到服务器
ssh ubuntu@82.157.28.35

# 进入项目目录
cd /opt/stock-analysis-system

# 拉取最新更改
git pull origin main

# 验证Nginx配置语法
sudo nginx -t
```

### 步骤 2: 重新加载Nginx配置

```bash
# 重新加载Nginx（不停服务）
sudo systemctl reload nginx

# 或者如果使用nginx命令
sudo nginx -s reload
```

### 步骤 3: 重新构建前端应用

```bash
# 构建前端（管理后台）
cd frontend
npm run build
cd ..

# 构建客户端应用
cd client
npm run build
cd ..
```

### 步骤 4: 验证部署

```bash
# 检查后端健康状态
curl https://qwquant.com/api/health

# 或
curl https://qwquant.com/api/v1/auth/login -X POST
```

## 验证修复是否成功

在浏览器中验证:

1. **打开管理后台**
   ```
   https://qwquant.com/admin
   ```

2. **打开浏览器DevTools（F12）**
   - 切换到 "Network" 标签
   - 登录或加载数据

3. **检查API请求**
   - 查看网络请求中的API调用
   - 应该看到路径如: `/api/stocks`, `/api/admin/auth/login` 等
   - **不应该**看到 `/api/v1/api/v1/...` 的重复

4. **预期结果**
   ```
   ✅ 请求: GET /api/stocks
   ✅ 请求: GET /api/admin/client-users/users
   ✅ 请求: POST /api/admin/auth/login

   ❌ 不应该出现: /api/v1/api/v1/...
   ```

## 常见问题排查

### 如果API仍然返回404

```bash
# 检查Nginx配置是否正确
sudo nginx -t

# 查看Nginx错误日志
sudo tail -f /var/log/nginx/error.log

# 检查后端是否运行
ps aux | grep gunicorn
```

### 如果Nginx配置有错误

```bash
# 查看当前使用的Nginx配置
sudo cat /etc/nginx/sites-enabled/qwquant.com
# 或
sudo cat /etc/nginx/conf.d/qwquant.conf

# 备份当前配置
sudo cp /etc/nginx/sites-enabled/qwquant.com /etc/nginx/sites-enabled/qwquant.com.bak

# 更新配置（使用 nginx/nginx.prod.conf 或 nginx/nginx.prod.complete.conf）
```

### 如果需要回滚

```bash
# 回滚到之前的提交
git revert 96d0624d  # Nginx配置回滚
git revert 66153fd2  # 前端代码回滚

git push origin main

# 重新部署
npm run build
sudo systemctl reload nginx
```

## 部署清单

- [ ] SSH 连接到服务器
- [ ] 执行 `git pull origin main`
- [ ] 验证 Nginx 配置: `sudo nginx -t`
- [ ] 重新加载 Nginx: `sudo systemctl reload nginx`
- [ ] 重新构建前端: `cd frontend && npm run build`
- [ ] 重新构建客户端: `cd client && npm run build`
- [ ] 测试后端健康检查
- [ ] 在浏览器中验证API请求路径
- [ ] 确认没有 `/api/v1/api/v1/...` 的重复路径

## 后续

所有修复都已准备好部署。一旦服务器更新完成，API应该正常工作，没有路径重复的问题。

如有任何问题，请检查:
1. Nginx 日志: `/var/log/nginx/error.log`
2. 后端日志: 通常在 `/opt/stock-analysis-system/logs/`
3. 浏览器 DevTools Network 标签中的API请求详情
