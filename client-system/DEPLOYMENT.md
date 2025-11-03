# 客户端系统部署指南

## 部署概览

客户端系统已完全编译，位于 `dist/` 目录，大小约 1.1MB。

### 编译输出文件
- `index.html` - HTML入口文件 (883B)
- `assets/` - JavaScript和CSS资源文件
- 总大小: 1.1MB（未压缩）
- 压缩后约 340KB（Gzip）

## 快速部署

### 方式1: 自动部署脚本（推荐）

在项目根目录运行：

```bash
bash deploy.sh root qwquant.com
```

脚本会自动：
1. 上传编译后的应用到服务器 `/app/client-system/dist/`
2. 配置Nginx以提供应用服务
3. 重加载Nginx配置

### 方式2: 手动部署步骤

#### 步骤1: 上传文件到服务器

```bash
# 创建远程目录
ssh root@qwquant.com "mkdir -p /app/client-system"

# 上传编译后的文件
scp -r dist/ root@qwquant.com:/app/client-system/
```

#### 步骤2: 配置Nginx

方案A - 在 `/client/` 路径下提供服务：

```bash
# 复制Nginx配置到服务器
scp nginx.conf root@qwquant.com:/etc/nginx/conf.d/client-system.conf

# 连接到服务器，测试并重加载Nginx
ssh root@qwquant.com "nginx -t && systemctl reload nginx"
```

方案B - 在根路径提供服务（编辑nginx.conf后）：

```bash
# 编辑nginx.conf，取消注释根路径location块
# 然后复制配置文件
scp nginx.conf root@qwquant.com:/etc/nginx/conf.d/client-system.conf
ssh root@qwquant.com "nginx -t && systemctl reload nginx"
```

#### 步骤3: 验证部署

```bash
# 检查文件是否上传成功
ssh root@qwquant.com "ls -la /app/client-system/dist/"

# 检查Nginx配置
ssh root@qwquant.com "nginx -T | grep client-system"

# 查看Nginx状态
ssh root@qwquant.com "systemctl status nginx"
```

## 访问应用

部署完成后，可以通过以下URL访问应用：

- **本地开发**: http://localhost:5173
- **服务器部署**: https://qwquant.com/client/

## 更新部署

当需要更新应用时：

### 1. 重新构建

```bash
npm run build
```

### 2. 上传新文件

```bash
scp -r dist/ root@qwquant.com:/app/client-system/
```

或使用一行命令：

```bash
npm run build && scp -r dist/ root@qwquant.com:/app/client-system/
```

## 故障排除

### 应用无法访问

1. **检查文件是否上传**

```bash
ssh root@qwquant.com "test -f /app/client-system/dist/index.html && echo '文件存在' || echo '文件不存在'"
```

2. **检查Nginx配置**

```bash
ssh root@qwquant.com "nginx -t"
```

3. **查看Nginx错误日志**

```bash
ssh root@qwquant.com "tail -f /var/log/nginx/client-system-error.log"
```

### 页面加载失败（404 Not Found）

- 确保Nginx配置中的 `alias` 或 `root` 路径正确
- 确保 `try_files` 规则正确配置以支持SPA路由
- 检查文件权限：`chmod -R 755 /app/client-system/dist/`

### API调用失败

- 检查后端API是否运行在 `https://qwquant.com/api/v1`
- 确认后端API CORS配置允许来自前端的请求
- 查看浏览器控制台Network标签检查请求细节

### 页面样式加载失败

- 清空浏览器缓存
- 硬刷新页面 (Ctrl+Shift+R 或 Cmd+Shift+R)
- 检查静态资源是否正确上传
- 查看浏览器开发者工具查看CSS加载状态

## 性能优化建议

### 1. 启用Gzip压缩

在Nginx配置中添加：

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_vary on;
gzip_comp_level 6;
```

### 2. 启用HTTP/2

```nginx
listen 443 ssl http2;
```

### 3. 设置适当的缓存头

已在 `nginx.conf` 中配置：
- HTML文件：无缓存
- 静态资源：1年缓存

### 4. 启用HTTPS

```bash
# 使用Let's Encrypt获取免费证书
certbot certonly --webroot -w /var/www/letsencrypt -d qwquant.com -d www.qwquant.com
```

## 监控和维护

### 实时监控日志

```bash
# 查看访问日志
ssh root@qwquant.com "tail -f /var/log/nginx/client-system-access.log"

# 查看错误日志
ssh root@qwquant.com "tail -f /var/log/nginx/client-system-error.log"
```

### 定期备份

```bash
# 备份编译后的应用
ssh root@qwquant.com "tar -czf /backup/client-system-$(date +%Y%m%d).tar.gz /app/client-system/dist"
```

## 环境变量配置

如需使用自定义API地址，可在构建前设置环境变量：

```bash
# 构建时使用自定义API地址
VITE_API_URL=https://api.example.com npm run build
```

## 回滚部署

如果需要回滚到之前的版本：

```bash
# 恢复之前备份的版本
ssh root@qwquant.com "tar -xzf /backup/client-system-20241027.tar.gz -C /app/client-system/"

# 重加载Nginx
ssh root@qwquant.com "systemctl reload nginx"
```

## 安全建议

1. **使用HTTPS** - 确保所有连接都使用HTTPS
2. **安全头部** - 添加以下Nginx配置：

```nginx
add_header X-Content-Type-Options "nosniff";
add_header X-Frame-Options "SAMEORIGIN";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

3. **定期更新** - 定期更新依赖和系统包
4. **监控日志** - 定期检查访问和错误日志
5. **备份配置** - 备份Nginx配置和应用文件

## 支持和帮助

如遇到问题：

1. 检查Nginx配置: `nginx -t`
2. 查看Nginx日志: `tail -f /var/log/nginx/error.log`
3. 检查浏览器控制台错误
4. 确保后端API服务运行正常

---

**部署完成日期**: 2024-10-27
**应用版本**: 1.0.0
**构建大小**: 1.1MB
