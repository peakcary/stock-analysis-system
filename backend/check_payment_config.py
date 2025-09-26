#!/usr/bin/env python3
"""
微信支付配置检查工具
WeChat Pay Configuration Checker

用法:
    python check_payment_config.py

功能:
    检查微信支付V3 API配置是否完整
    验证证书文件是否存在且格式正确
    提供配置建议和错误解决方案
"""

import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from app.core.config import settings
    from app.services.wechat_pay_v3 import wechat_pay_v3_service
    from app.services.payment_manager import payment_manager
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)


def check_environment_variables():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置...")

    required_vars = [
        ('WECHAT_APPID', '微信AppID'),
        ('WECHAT_MCH_ID', '商户号'),
        ('WECHAT_API_V3_KEY', 'API v3密钥'),
        ('WECHAT_CERT_SERIAL', '证书序列号'),
        ('WECHAT_CERT_PATH', '证书文件路径'),
        ('WECHAT_KEY_PATH', '私钥文件路径'),
    ]

    missing_vars = []
    configured_vars = []

    for var_name, var_desc in required_vars:
        value = os.getenv(var_name)
        if value:
            configured_vars.append(f"  ✅ {var_desc} ({var_name}): 已配置")
        else:
            missing_vars.append(f"  ❌ {var_desc} ({var_name}): 未配置")

    print("\n配置状态:")
    for msg in configured_vars:
        print(msg)
    for msg in missing_vars:
        print(msg)

    return len(missing_vars) == 0


def check_certificate_files():
    """检查证书文件"""
    print("\n🔐 检查证书文件...")

    cert_path = settings.WECHAT_CERT_PATH
    key_path = settings.WECHAT_KEY_PATH

    issues = []
    success = []

    # 检查证书文件
    if not cert_path:
        issues.append("  ❌ 未配置证书文件路径 (WECHAT_CERT_PATH)")
    elif not os.path.exists(cert_path):
        issues.append(f"  ❌ 证书文件不存在: {cert_path}")
    elif not os.path.isfile(cert_path):
        issues.append(f"  ❌ 证书路径不是文件: {cert_path}")
    else:
        try:
            with open(cert_path, 'r') as f:
                content = f.read().strip()
            if content.startswith('-----BEGIN CERTIFICATE-----'):
                success.append(f"  ✅ 证书文件格式正确: {cert_path}")
            else:
                issues.append(f"  ❌ 证书文件格式错误: {cert_path} (需要PEM格式)")
        except Exception as e:
            issues.append(f"  ❌ 无法读取证书文件 {cert_path}: {e}")

    # 检查私钥文件
    if not key_path:
        issues.append("  ❌ 未配置私钥文件路径 (WECHAT_KEY_PATH)")
    elif not os.path.exists(key_path):
        issues.append(f"  ❌ 私钥文件不存在: {key_path}")
    elif not os.path.isfile(key_path):
        issues.append(f"  ❌ 私钥路径不是文件: {key_path}")
    else:
        try:
            with open(key_path, 'r') as f:
                content = f.read().strip()
            if content.startswith('-----BEGIN'):
                success.append(f"  ✅ 私钥文件格式正确: {key_path}")
            else:
                issues.append(f"  ❌ 私钥文件格式错误: {key_path} (需要PEM格式)")
        except Exception as e:
            issues.append(f"  ❌ 无法读取私钥文件 {key_path}: {e}")

    print("证书文件状态:")
    for msg in success:
        print(msg)
    for msg in issues:
        print(msg)

    return len(issues) == 0


def check_payment_service():
    """检查支付服务状态"""
    print("\n⚙️  检查支付服务状态...")

    try:
        # 获取配置状态
        config_status = payment_manager.get_payment_config_status()

        print("支付服务配置:")
        print(f"  支付功能: {'启用' if config_status['payment_enabled'] else '禁用'}")
        print(f"  运行模式: {'模拟模式' if config_status['mock_mode'] else '生产模式'}")
        print(f"  订单超时: {config_status['order_timeout_hours']} 小时")
        print(f"  推荐API: {config_status['recommended_api']}")

        # V3 API状态
        v3_config = config_status.get('wechat_v3_config', {})
        print(f"\n微信支付V3配置:")

        if v3_config:
            print(f"  整体状态: {v3_config.get('overall_status', '未知')}")
            print(f"  API版本: {v3_config.get('api_version', '未知')}")
            print(f"  模拟模式: {v3_config.get('mock_mode', False)}")
            print(f"  AppID配置: {'✅' if v3_config.get('appid_configured') else '❌'}")
            print(f"  商户号配置: {'✅' if v3_config.get('mch_id_configured') else '❌'}")
            print(f"  API密钥配置: {'✅' if v3_config.get('api_key_configured') else '❌'}")
            print(f"  证书序列号配置: {'✅' if v3_config.get('cert_serial_configured') else '❌'}")
            print(f"  证书文件存在: {'✅' if v3_config.get('cert_file_exists') else '❌'}")
            print(f"  私钥文件存在: {'✅' if v3_config.get('key_file_exists') else '❌'}")

            return v3_config.get('overall_status') in ['ready', 'mock_mode']
        else:
            print("  ❌ 无法获取V3配置状态")
            return False

    except Exception as e:
        print(f"  ❌ 检查支付服务时出错: {e}")
        return False


def provide_suggestions():
    """提供配置建议"""
    print("\n💡 配置建议:")
    print("1. 证书获取:")
    print("   - 登录微信商户平台: https://pay.weixin.qq.com")
    print("   - 进入【账户中心】-【API安全】")
    print("   - 下载API证书")

    print("\n2. 证书配置:")
    print("   - 将证书文件放在 backend/certs/ 目录")
    print("   - 确保文件名为 apiclient_cert.pem 和 apiclient_key.pem")
    print("   - 设置正确的文件权限: chmod 600 certs/*.pem")

    print("\n3. 环境变量:")
    print("   - 复制 .env.security.example 为 .env")
    print("   - 填写真实的微信支付配置信息")
    print("   - 获取证书序列号: openssl x509 -in apiclient_cert.pem -noout -serial")

    print("\n4. 测试验证:")
    print("   - 开发阶段可启用模拟模式: PAYMENT_MOCK_MODE=true")
    print("   - 生产环境设置: PAYMENT_MOCK_MODE=false")
    print("   - 使用HTTPS域名配置 WECHAT_NOTIFY_URL")


def main():
    """主函数"""
    print("🚀 微信支付配置检查工具")
    print("=" * 50)

    # 检查各个组件
    env_ok = check_environment_variables()
    cert_ok = check_certificate_files()
    service_ok = check_payment_service()

    # 总结
    print("\n" + "=" * 50)
    print("📊 配置检查总结:")

    if env_ok and cert_ok and service_ok:
        print("✅ 所有配置检查通过！微信支付系统可以正常使用。")
        if settings.PAYMENT_MOCK_MODE:
            print("🧪 当前运行在模拟模式，适合开发测试。")
        else:
            print("🎯 当前运行在生产模式，可以处理真实支付。")
    else:
        print("❌ 配置存在问题，请根据上述检查结果进行修复。")
        provide_suggestions()

    print("\n详细配置说明请参考: backend/certs/README.md")


if __name__ == "__main__":
    main()