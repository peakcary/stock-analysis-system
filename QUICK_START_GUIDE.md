# 快速启动指南

## 🚀 立即启动系统

### 1. 一键启动
```bash
cd /Users/peakom/work/stock-analysis-system
./scripts/deployment/start.sh
```

### 2. 访问地址
- **管理端**: http://localhost:8006
- **客户端**: http://localhost:8005
- **API文档**: http://localhost:3007/docs

### 3. 登录信息
```
用户名: admin
密码: admin123
```

## 🔧 新功能使用说明

### 通用文件导入功能
1. 登录管理端后点击"数据导入"
2. 选择"通用文件导入"标签页
3. 选择文件类型（txt/ttv/eee）
4. 设置交易日期和导入模式
5. 拖拽或点击上传文件

### 文件类型管理功能
1. 在"数据导入"页面选择"文件类型管理"标签页
2. 查看系统概览和健康状态
3. 创建、编辑或删除文件类型
4. 监控各文件类型的导入统计

## 🛑 停止系统
```bash
./scripts/deployment/stop.sh
```

## 📊 当前支持的文件类型
- **txt**: 原始TXT格式股票交易数据
- **ttv**: TTV格式股票交易数据
- **eee**: EEE格式股票交易数据

每种文件类型都有独立的数据表和处理逻辑，完全隔离存储。

## ⚠️ 注意事项
- 确保数据库 MySQL 正在运行
- 系统启动需要约10-15秒
- 如遇端口占用，脚本会自动清理

---
**快速联系**: 查看 DEVELOPMENT_PROGRESS.md 了解详细开发进度