# 客户端支付系统

一个完全独立的客户端支付系统，基于React 18 + TypeScript + Ant Design 5 + Vite构建。

## 功能特性

- ✅ **用户认证系统** - 完整的登录、注册、密码修改功能
- ✅ **支付管理** - 支付订单创建、QR码展示、模拟支付流程
- ✅ **订单管理** - 支付订单历史查询、订单详情查看
- ✅ **用户中心** - 个人信息编辑、账户设置、账户注销
- ✅ **仪表板** - 用户信息展示、会员级别、剩余查询次数统计
- ✅ **响应式设计** - 支持桌面端、平板、手机等多设备适配

## 系统需求

- Node.js 18+
- npm 9+ 或 yarn
- 后端API服务（推荐部署在 `https://qwquant.com/api/v1`）

## 项目结构

```
client-system/
├── src/
│   ├── pages/                 # 页面组件
│   │   ├── LoginPage.tsx     # 登录/注册页面
│   │   ├── DashboardPage.tsx # 仪表板
│   │   ├── PaymentPage.tsx   # 支付页面
│   │   ├── OrderHistoryPage.tsx # 订单历史
│   │   └── UserCenterPage.tsx # 用户中心
│   ├── styles/               # 样式文件
│   │   └── LoginPage.css     # 登录页面样式
│   ├── utils/               # 工具函数
│   │   └── api.ts           # API客户端（Axios）
│   ├── App.tsx              # 主应用组件
│   ├── App.css              # 全局样式
│   ├── main.tsx             # 入口文件
│   └── vite-env.d.ts        # Vite环境变量类型定义
├── index.html               # HTML模板
├── vite.config.ts           # Vite配置
├── tsconfig.json            # TypeScript配置
├── package.json             # 项目依赖
├── deploy.sh                # 部署脚本
└── README.md                # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 开发模式

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动

### 3. 生产构建

```bash
npm run build
```

编译后的文件位于 `dist/` 目录

### 4. 预览生产构建

```bash
npm run preview
```

## 部署指南

### 自动部署（推荐）

```bash
bash deploy.sh root qwquant.com
```

该命令将：
1. 上传编译后的应用到 `/app/client-system/dist`
2. 配置Nginx以提供应用服务
3. 自动重加载Nginx配置

### 手动部署

1. **上传文件**

```bash
scp -r dist/ root@qwquant.com:/app/client-system/
```

2. **配置Nginx**

复制 `deploy.sh` 中的Nginx配置到 `/etc/nginx/conf.d/client-system.conf`

3. **重加载Nginx**

```bash
ssh root@qwquant.com "nginx -t && systemctl reload nginx"
```

## 环境变量

在项目根目录创建 `.env` 或 `.env.local` 文件（可选）：

```env
# API基础URL（如果与默认不同）
VITE_API_URL=https://qwquant.com/api/v1
```

## API集成

应用使用Axios库与后端API通信。API基础URL默认为 `https://qwquant.com/api/v1`。

### 认证端点

- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/change-password` - 修改密码
- `PUT /auth/users/{id}` - 更新用户信息
- `DELETE /auth/users/{id}` - 删除账户

### 支付端点

- `GET /payment/packages` - 获取套餐列表
- `POST /payment/orders` - 创建支付订单
- `GET /payment/orders` - 获取用户订单列表
- `GET /payment/orders/{id}` - 获取订单详情
- `POST /payment/orders/{id}/notify` - 支付通知/模拟支付

## 页面说明

### 登录页面 (LoginPage)

- 支持用户登录和注册
- 使用localStorage存储认证令牌
- 自动显示/隐藏注册表单

### 仪表板 (DashboardPage)

- 欢迎信息
- 用户统计信息（会员级别、查询次数等）
- 快速操作按钮
- 最近订单列表

### 支付页面 (PaymentPage)

4步支付流程：
1. **选择套餐** - 从可用套餐列表中选择
2. **确认信息** - 显示订单详情（此步自动跳过）
3. **支付订单** - 显示QR码和模拟支付按钮
4. **支付成功** - 显示成功确认

### 订单历史页面 (OrderHistoryPage)

- 分页列表显示所有订单
- 支持查看订单详情
- 显示订单状态、金额、创建时间等

### 用户中心 (UserCenterPage)

- 编辑个人信息（邮箱）
- 修改密码
- 账户操作（退出登录、删除账户）

## 样式和主题

### 主色调

- 主色：`#667eea` - `#764ba2` （紫色渐变）
- 成功：`#52c41a` （绿色）
- 警告：`#faad14` （橙色）
- 错误：`#ff4d4f` （红色）
- 信息：`#1890ff` （蓝色）

### 响应式设计

应用使用Ant Design的Grid组件和CSS媒体查询实现响应式设计，支持：
- 桌面端（≥1024px）
- 平板（768px-1023px）
- 手机（<768px）

## 测试账户

开发时可使用以下测试账户：

- **用户名**: user1
- **密码**: 123456

## 常见问题

### Q: 登录失败显示"401 Unauthorized"

A: 检查后端API服务是否正在运行，确保 `VITE_API_URL` 环境变量正确指向后端API地址。

### Q: 支付订单创建失败

A: 确保后端数据库中存在支付套餐数据，检查后端日志获取更多错误信息。

### Q: CORS错误

A: 确保后端API服务正确配置了CORS（跨源资源共享），允许来自客户端的请求。

### Q: 页面不显示（Nginx部署）

A: 检查Nginx配置中的 `alias` 或 `root` 路径是否正确，确保 `try_files` 规则能正确处理SPA路由。

## 开发相关

### 依赖版本

- React: 18.2.0
- React-DOM: 18.2.0
- Ant Design: 5.x
- Ant Design Icons: 5.x
- Axios: 1.x
- TypeScript: 5.2.2
- Vite: 7.1.3

### 代码规范

项目使用TypeScript进行类型检查，确保类型安全。运行构建时会自动进行类型检查。

## 性能优化

- 使用Vite进行快速开发和生产构建
- Terser压缩JavaScript代码
- CSS内联和分离
- 静态资源使用长期缓存策略

## 浏览器支持

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## 许可证

MIT

## 技术支持

如有问题或建议，请联系开发团队。

---

**最后更新**: 2024-10-27
**版本**: 1.0.0
