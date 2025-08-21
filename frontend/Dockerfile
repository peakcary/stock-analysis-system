# 多阶段构建 Dockerfile for React + Vite

# 开发阶段
FROM node:20-alpine as development

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3000

# 开发环境启动命令
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# 生产构建阶段
FROM node:20-alpine as build

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产阶段 - 使用 nginx 提供静态文件
FROM nginx:alpine as production

# 复制构建结果到 nginx
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]