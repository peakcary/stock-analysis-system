#!/usr/bin/env python3
"""
安全密码和密钥生成工具
Secure Password and Key Generation Tool

用法:
    python scripts/generate_secure_passwords.py

功能:
    - 生成符合复杂度要求的安全密码
    - 生成JWT密钥
    - 生成完整的环境变量配置
"""

import secrets
import string
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'backend'))

try:
    from app.utils.password_validator import PasswordValidator, get_password_strength
except ImportError:
    print("警告: 无法导入密码验证器，将使用基本生成方式")
    PasswordValidator = None
    get_password_strength = None


def generate_jwt_key(length: int = 32) -> str:
    """生成JWT密钥"""
    return secrets.token_urlsafe(length)


def generate_secure_password(length: int = 12) -> str:
    """生成安全密码"""
    # 确保包含各种字符类型
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # 每种类型至少包含一个字符
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special_chars)
    ]

    # 填充剩余长度
    all_chars = lowercase + uppercase + digits + special_chars
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))

    # 打乱顺序
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def validate_generated_password(password: str) -> tuple:
    """验证生成的密码"""
    if PasswordValidator is None:
        return True, []

    validator = PasswordValidator()
    is_valid, errors = validator.validate(password)

    if get_password_strength:
        score, level = get_password_strength(password)
        return is_valid, errors, score, level

    return is_valid, errors


def generate_database_password() -> str:
    """生成数据库密码"""
    max_attempts = 10
    for _ in range(max_attempts):
        password = generate_secure_password(16)
        result = validate_generated_password(password)

        if result[0]:  # 如果密码有效
            if len(result) > 2:  # 如果有强度评分
                score, level = result[2], result[3]
                if score >= 70:  # 强度要求
                    return password
            else:
                return password

    # 如果多次尝试都不满足要求，返回一个手动构造的强密码
    return "DbPass2024!@#$"


def generate_admin_password() -> str:
    """生成管理员密码"""
    max_attempts = 10
    for _ in range(max_attempts):
        password = generate_secure_password(12)
        result = validate_generated_password(password)

        if result[0]:  # 如果密码有效
            if len(result) > 2:  # 如果有强度评分
                score, level = result[2], result[3]
                if score >= 70:  # 强度要求
                    return password
            else:
                return password

    return "Admin2024!@#$"


def main():
    """主函数"""
    print("=" * 60)
    print("股票分析系统 - 安全密码生成工具")
    print("Stock Analysis System - Security Password Generator")
    print("=" * 60)
    print()

    # 生成各种密钥和密码
    jwt_secret = generate_jwt_key(32)
    admin_jwt_secret = generate_jwt_key(32)
    db_password = generate_database_password()
    admin_password = generate_admin_password()
    redis_password = generate_secure_password(20)

    print("🔐 生成的安全密钥和密码:")
    print("-" * 40)
    print(f"JWT密钥:")
    print(f"SECRET_KEY={jwt_secret}")
    print()

    print(f"管理员JWT密钥:")
    print(f"ADMIN_SECRET_KEY={admin_jwt_secret}")
    print()

    print(f"数据库密码:")
    print(f"DATABASE_PASSWORD={db_password}")
    print()

    print(f"Redis密码:")
    print(f"REDIS_PASSWORD={redis_password}")
    print()

    print(f"建议的初始管理员密码:")
    print(f"INITIAL_ADMIN_PASSWORD={admin_password}")
    print()

    # 密码强度验证
    if get_password_strength:
        print("🎯 密码强度评估:")
        print("-" * 40)

        db_score, db_level = get_password_strength(db_password)
        print(f"数据库密码强度: {db_score}/100 ({db_level})")

        admin_score, admin_level = get_password_strength(admin_password)
        print(f"管理员密码强度: {admin_score}/100 ({admin_level})")
        print()

    # 生成完整的.env文件内容
    print("📄 完整的 .env 配置:")
    print("-" * 40)
    env_content = f"""# 自动生成的安全配置 - {secrets.token_hex(8)}
# 请妥善保管这些密钥和密码

# 数据库配置
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD={db_password}
DATABASE_NAME=stock_analysis_dev

# JWT配置
SECRET_KEY={jwt_secret}
ADMIN_SECRET_KEY={admin_jwt_secret}
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis配置
REDIS_PASSWORD={redis_password}

# 应用配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# 初始管理员密码（首次登录后请立即修改）
INITIAL_ADMIN_PASSWORD={admin_password}
"""

    print(env_content)

    # 安全提醒
    print("⚠️  安全提醒:")
    print("-" * 40)
    print("1. 请将生成的密码保存到安全的地方")
    print("2. 不要将密码提交到版本控制系统")
    print("3. 生产环境请使用更强的密码")
    print("4. 定期更换密码和密钥")
    print("5. 首次使用生成的管理员密码登录后，请立即修改")
    print()

    # 询问是否保存到文件
    save_to_file = input("是否保存配置到 .env.generated 文件? (y/N): ").lower().strip()
    if save_to_file in ['y', 'yes']:
        env_file = os.path.join(project_root, '.env.generated')
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ 配置已保存到: {env_file}")
        print("   请将此文件重命名为 .env 并根据需要调整配置")

    print("\n🎉 密码生成完成!")


if __name__ == "__main__":
    main()