# 📚 股票分析系统 - 文档中心

## 📖 文档索引

### 🏗️ 架构设计
- [📋 系统设计文档](./architecture/SYSTEM_DESIGN.md) - 完整的系统架构、数据库设计、API接口设计
- [🗄️ 数据库架构](./architecture/database-schema.md) - 数据库表结构和关系设计

### 🚀 部署运维
- [⚙️ 部署配置指南](./deployment/setup.md) - 系统部署和配置说明
- [💳 微信支付配置](./deployment/WECHAT_PAYMENT_SETUP.md) - 微信支付系统配置指南
- [🔧 脚本使用指南](./SCRIPTS_GUIDE.md) - 部署和管理脚本详细说明
- [📥 TXT导入指南](./TXT_IMPORT_GUIDE.md) - 数据导入功能使用指南
- [💳 支付系统配置](./PAYMENT_CONFIG.md) - 支付系统配置和使用说明

### 💻 开发文档
- [🔧 构建优化文档](./development/BUILD_OPTIMIZATION.md) - 项目构建和性能优化
- [✨ v2.4.1增强功能](./development/ENHANCED_FEATURES_v2.4.1.md) - 功能增强详细说明
- [📊 股票代码升级](./development/STOCK_CODE_UPGRADE.md) - 股票代码标准化升级
- [📊 数据导入功能开发](./development/2025-09-05-数据导入功能开发文档.md) - 数据导入功能设计
- [🎯 概念分析系统设计](./development/2025-09-05-概念分析系统需求设计文档.md) - 概念分析需求设计

### 🔗 API文档
- [📡 API接口文档](http://localhost:3007/docs) - FastAPI自动生成的交互式API文档

## 📁 文档目录结构

```
docs/
├── README.md                    # 文档索引（本文件）
├── SCRIPTS_GUIDE.md             # 脚本使用指南
├── TXT_IMPORT_GUIDE.md          # 数据导入指南
├── PAYMENT_CONFIG.md            # 支付配置指南
├── architecture/                # 架构设计文档
│   ├── SYSTEM_DESIGN.md         # 系统设计文档
│   └── database-schema.md       # 数据库架构文档
├── deployment/                  # 部署运维文档
│   ├── setup.md                 # 部署配置指南
│   └── WECHAT_PAYMENT_SETUP.md  # 微信支付配置
├── development/                 # 开发相关文档
│   ├── BUILD_OPTIMIZATION.md    # 构建优化
│   ├── ENHANCED_FEATURES_v2.4.1.md
│   ├── STOCK_CODE_UPGRADE.md
│   ├── 2025-09-05-数据导入功能开发文档.md
│   └── 2025-09-05-概念分析系统需求设计文档.md
└── api/                         # API文档（计划中）
    └── API_DESIGN.md            # API设计规范
```

## 🚀 快速导航

### 新用户指南
1. 📖 先阅读主 [README](../README.md) 了解系统概述
2. 🏗️ 查看 [系统设计文档](./architecture/SYSTEM_DESIGN.md) 了解架构
3. 🔧 参考 [脚本使用指南](./SCRIPTS_GUIDE.md) 进行部署
4. 📊 根据需要查看具体功能文档

### 开发者指南
1. 🏗️ 研读 [系统设计文档](./architecture/SYSTEM_DESIGN.md) 了解整体架构
2. 🗄️ 查看 [数据库架构](./architecture/database-schema.md) 了解数据结构
3. 💻 参考开发文档了解具体功能实现
4. 🔗 使用 [API文档](http://localhost:3007/docs) 进行接口开发

### 运维人员指南
1. ⚙️ 参考 [部署配置指南](./deployment/setup.md) 进行系统部署
2. 💳 配置 [微信支付系统](./deployment/WECHAT_PAYMENT_SETUP.md)
3. 🔧 使用 [脚本使用指南](./SCRIPTS_GUIDE.md) 进行日常维护
4. 📥 了解 [数据导入流程](./TXT_IMPORT_GUIDE.md)

## 🔄 文档维护规范

### 更新频率
- **系统设计文档**: 每个版本发布时更新
- **API文档**: 接口变更时实时更新
- **部署文档**: 部署流程变更时更新
- **开发文档**: 功能开发完成时更新

### 文档规范
- 使用Markdown格式编写
- 遵循统一的文档模板
- 包含版本号和更新日期
- 提供清晰的目录结构
- 使用emoji增强可读性

### 维护责任
- **技术负责人**: 架构设计文档
- **开发团队**: 开发和API文档
- **运维团队**: 部署运维文档
- **产品团队**: 功能需求文档

## 📞 获取帮助

如果您在使用文档过程中遇到问题或有改进建议，请通过以下方式反馈：

1. **GitHub Issues**: 提交文档相关问题
2. **技术团队**: 直接联系相关负责人
3. **系统状态检查**: 运行 `./scripts/deployment/status.sh` 检查系统状态
4. **故障排除**: 查看主 README 中的故障排除部分

---

**文档维护**: 技术团队 | **最后更新**: 2025-09-13 | **版本**: v2.6.0