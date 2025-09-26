#!/usr/bin/env python3
"""
安全审计工具
Security Audit Tool

用法:
    python scripts/security_audit.py

功能:
    - 检查环境文件中的敏感信息
    - 验证配置文件的安全性
    - 扫描潜在的安全风险
"""

import os
import re
import glob
import json
from pathlib import Path
from typing import List, Dict, Tuple


class SecurityAuditor:
    """安全审计器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []

    def add_issue(self, level: str, file_path: str, line: int, message: str, suggestion: str = ""):
        """添加安全问题"""
        self.issues.append({
            'level': level,
            'file': str(file_path),
            'line': line,
            'message': message,
            'suggestion': suggestion
        })

    def check_env_files(self):
        """检查环境变量文件"""
        print("🔍 检查环境变量文件...")

        env_files = list(self.project_root.glob('.env*'))
        env_files.extend(list(self.project_root.glob('**/.env*')))

        weak_passwords = [
            'password', 'admin', 'root', '123456', 'admin123',
            'password123', 'root123', 'test', 'demo', '111111',
            'qwerty', 'abc123', 'your_password_here', 'change_me'
        ]

        for env_file in env_files:
            if env_file.name.endswith('.example'):
                continue

            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    # 检查弱密码
                    for weak_pwd in weak_passwords:
                        if weak_pwd.lower() in line.lower():
                            self.add_issue(
                                'HIGH',
                                env_file,
                                line_num,
                                f'可能包含弱密码: {weak_pwd}',
                                '请使用强密码，至少8位包含大小写字母、数字和特殊字符'
                            )

                    # 检查空密码
                    if re.match(r'.*PASSWORD.*=\s*$', line, re.IGNORECASE):
                        self.add_issue(
                            'HIGH',
                            env_file,
                            line_num,
                            '密码为空',
                            '请设置强密码'
                        )

                    # 检查默认密钥
                    if re.match(r'.*SECRET.*=.*your.*secret.*here', line, re.IGNORECASE):
                        self.add_issue(
                            'CRITICAL',
                            env_file,
                            line_num,
                            '使用默认密钥',
                            '请生成随机密钥'
                        )

                    # 检查短密钥
                    secret_match = re.match(r'.*SECRET.*=(.+)', line, re.IGNORECASE)
                    if secret_match:
                        secret_value = secret_match.group(1).strip()
                        if len(secret_value) < 32:
                            self.add_issue(
                                'MEDIUM',
                                env_file,
                                line_num,
                                f'密钥长度不足: {len(secret_value)}字符',
                                '建议使用至少32字符的随机密钥'
                            )

            except Exception as e:
                self.add_issue(
                    'LOW',
                    env_file,
                    0,
                    f'无法读取文件: {e}',
                    '检查文件权限'
                )

    def check_hardcoded_secrets(self):
        """检查硬编码的密钥和密码"""
        print("🔍 检查硬编码密钥...")

        # 需要检查的文件模式
        code_files = []
        code_files.extend(self.project_root.glob('**/*.py'))
        code_files.extend(self.project_root.glob('**/*.js'))
        code_files.extend(self.project_root.glob('**/*.ts'))
        code_files.extend(self.project_root.glob('**/*.jsx'))
        code_files.extend(self.project_root.glob('**/*.tsx'))

        # 敏感模式
        sensitive_patterns = [
            (r'password\s*=\s*["\']([^"\']{1,50})["\']', 'password'),
            (r'secret\s*=\s*["\']([^"\']{1,100})["\']', 'secret'),
            (r'api_key\s*=\s*["\']([^"\']{1,100})["\']', 'api_key'),
            (r'token\s*=\s*["\']([^"\']{1,100})["\']', 'token'),
        ]

        for file_path in code_files:
            # 跳过某些目录
            if any(part in str(file_path) for part in ['node_modules', '__pycache__', '.git', 'dist', 'build']):
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for line_num, line in enumerate(lines, 1):
                    for pattern, secret_type in sensitive_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            secret_value = match.group(1)
                            # 跳过明显的示例和占位符
                            if any(placeholder in secret_value.lower() for placeholder in [
                                'your_', 'example', 'test', 'demo', 'change', 'here', 'xxx'
                            ]):
                                continue

                            self.add_issue(
                                'HIGH',
                                file_path,
                                line_num,
                                f'发现硬编码{secret_type}: {secret_value[:20]}...',
                                '使用环境变量存储敏感信息'
                            )

            except Exception:
                continue  # 跳过无法读取的文件

    def check_file_permissions(self):
        """检查文件权限"""
        print("🔍 检查文件权限...")

        sensitive_files = [
            '.env', '.env.local', '.env.prod', '.env.production',
            'id_rsa', 'id_dsa', '*.pem', '*.key', '*.p12'
        ]

        for pattern in sensitive_files:
            files = list(self.project_root.glob(f'**/{pattern}'))
            for file_path in files:
                if file_path.is_file():
                    try:
                        # 获取文件权限
                        permissions = oct(file_path.stat().st_mode)[-3:]
                        if permissions != '600':
                            self.add_issue(
                                'MEDIUM',
                                file_path,
                                0,
                                f'文件权限不安全: {permissions}',
                                '建议设置为600 (仅所有者可读写)'
                            )
                    except Exception:
                        continue

    def check_gitignore(self):
        """检查.gitignore配置"""
        print("🔍 检查.gitignore配置...")

        gitignore_path = self.project_root / '.gitignore'
        if not gitignore_path.exists():
            self.add_issue(
                'MEDIUM',
                gitignore_path,
                0,
                '缺少.gitignore文件',
                '创建.gitignore文件以防止敏感文件被提交'
            )
            return

        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()

            required_patterns = [
                '.env', '*.key', '*.pem', '*.p12', 'secrets/',
                '*.log', '*.pid', 'certs/'
            ]

            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    self.add_issue(
                        'MEDIUM',
                        gitignore_path,
                        0,
                        f'缺少忽略模式: {pattern}',
                        f'添加 {pattern} 到.gitignore'
                    )

        except Exception as e:
            self.add_issue(
                'LOW',
                gitignore_path,
                0,
                f'无法读取.gitignore: {e}',
                '检查文件权限'
            )

    def check_committed_secrets(self):
        """检查已提交的敏感文件"""
        print("🔍 检查已提交的敏感文件...")

        if not (self.project_root / '.git').exists():
            return

        # 检查git中跟踪的敏感文件
        sensitive_patterns = ['.env', '*.key', '*.pem', '*.p12']

        for pattern in sensitive_patterns:
            files = list(self.project_root.glob(f'**/{pattern}'))
            for file_path in files:
                if file_path.is_file():
                    # 检查文件是否在git中
                    try:
                        relative_path = file_path.relative_to(self.project_root)
                        result = os.system(f'cd "{self.project_root}" && git ls-files --error-unmatch "{relative_path}" > /dev/null 2>&1')
                        if result == 0:  # 文件在git中
                            self.add_issue(
                                'CRITICAL',
                                file_path,
                                0,
                                '敏感文件已被git跟踪',
                                '使用git rm --cached移除，并添加到.gitignore'
                            )
                    except Exception:
                        continue

    def generate_report(self):
        """生成审计报告"""
        print("\n" + "=" * 60)
        print("🛡️  安全审计报告")
        print("=" * 60)

        if not self.issues:
            print("✅ 未发现安全问题!")
            return

        # 按严重程度分组
        critical_issues = [i for i in self.issues if i['level'] == 'CRITICAL']
        high_issues = [i for i in self.issues if i['level'] == 'HIGH']
        medium_issues = [i for i in self.issues if i['level'] == 'MEDIUM']
        low_issues = [i for i in self.issues if i['level'] == 'LOW']

        total_issues = len(self.issues)
        print(f"📊 总共发现 {total_issues} 个问题:")
        print(f"   🚨 严重: {len(critical_issues)}")
        print(f"   ⚠️  高危: {len(high_issues)}")
        print(f"   ⚡ 中等: {len(medium_issues)}")
        print(f"   ℹ️  低危: {len(low_issues)}")
        print()

        # 详细报告
        for level, issues, emoji in [
            ('CRITICAL', critical_issues, '🚨'),
            ('HIGH', high_issues, '⚠️'),
            ('MEDIUM', medium_issues, '⚡'),
            ('LOW', low_issues, 'ℹ️')
        ]:
            if issues:
                print(f"{emoji} {level} 级别问题:")
                print("-" * 40)
                for i, issue in enumerate(issues, 1):
                    print(f"{i}. 文件: {issue['file']}")
                    if issue['line'] > 0:
                        print(f"   行号: {issue['line']}")
                    print(f"   问题: {issue['message']}")
                    if issue['suggestion']:
                        print(f"   建议: {issue['suggestion']}")
                    print()

    def run_audit(self):
        """运行完整的安全审计"""
        print("🛡️  开始安全审计...")
        print()

        self.check_env_files()
        self.check_hardcoded_secrets()
        self.check_file_permissions()
        self.check_gitignore()
        self.check_committed_secrets()

        self.generate_report()

        # 返回是否有严重问题
        critical_count = len([i for i in self.issues if i['level'] in ['CRITICAL', 'HIGH']])
        return critical_count == 0


def main():
    """主函数"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auditor = SecurityAuditor(project_root)

    success = auditor.run_audit()

    if success:
        print("🎉 安全审计通过!")
        return 0
    else:
        print("❌ 发现严重安全问题，请立即修复!")
        return 1


if __name__ == "__main__":
    exit(main())