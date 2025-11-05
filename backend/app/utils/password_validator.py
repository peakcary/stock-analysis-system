"""
密码复杂度验证工具
Password Complexity Validator
"""

import re
from typing import List, Tuple


class PasswordValidator:
    """密码复杂度验证器"""

    def __init__(self,
                 min_length: int = 8,
                 max_length: int = 128,
                 require_uppercase: bool = True,
                 require_lowercase: bool = True,
                 require_digits: bool = True,
                 require_special_chars: bool = True,
                 forbidden_patterns: List[str] = None):
        """
        初始化密码验证器

        Args:
            min_length: 最小长度
            max_length: 最大长度
            require_uppercase: 需要大写字母
            require_lowercase: 需要小写字母
            require_digits: 需要数字
            require_special_chars: 需要特殊字符
            forbidden_patterns: 禁用的模式（如常见密码）
        """
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special_chars = require_special_chars
        self.forbidden_patterns = forbidden_patterns or [
            "password", "123456", "admin", "root", "qwerty",
            "password123", "admin123", "123456789", "111111"
        ]

        # 特殊字符集合
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def validate(self, password: str) -> Tuple[bool, List[str]]:
        """
        验证密码复杂度

        Args:
            password: 要验证的密码

        Returns:
            (is_valid, error_messages): 验证结果和错误信息列表
        """
        errors = []

        # 长度检查
        if len(password) < self.min_length:
            errors.append(f"密码长度至少需要{self.min_length}个字符")
        elif len(password) > self.max_length:
            errors.append(f"密码长度不能超过{self.max_length}个字符")

        # 大写字母检查
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("密码必须包含至少一个大写字母")

        # 小写字母检查
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("密码必须包含至少一个小写字母")

        # 数字检查
        if self.require_digits and not re.search(r'\d', password):
            errors.append("密码必须包含至少一个数字")

        # 特殊字符检查
        if self.require_special_chars:
            special_char_pattern = f"[{re.escape(self.special_chars)}]"
            if not re.search(special_char_pattern, password):
                errors.append("密码必须包含至少一个特殊字符 (!@#$%^&*等)")

        # 禁用模式检查
        password_lower = password.lower()
        for pattern in self.forbidden_patterns:
            if pattern.lower() in password_lower:
                errors.append(f"密码不能包含常见密码模式: {pattern}")

        # 连续字符检查
        if self._has_consecutive_chars(password):
            errors.append("密码不能包含连续的相同字符（如aaa、111）")

        # 简单序列检查
        if self._has_simple_sequence(password):
            errors.append("密码不能包含简单序列（如abc、123）")

        return len(errors) == 0, errors

    def _has_consecutive_chars(self, password: str, max_consecutive: int = 3) -> bool:
        """检查是否有连续相同字符"""
        for i in range(len(password) - max_consecutive + 1):
            if len(set(password[i:i + max_consecutive])) == 1:
                return True
        return False

    def _has_simple_sequence(self, password: str, min_sequence_length: int = 3) -> bool:
        """检查是否有简单序列"""
        password_lower = password.lower()

        # 检查字母序列
        for i in range(len(password_lower) - min_sequence_length + 1):
            substring = password_lower[i:i + min_sequence_length]
            if self._is_alphabetical_sequence(substring):
                return True

        # 检查数字序列
        for i in range(len(password) - min_sequence_length + 1):
            substring = password[i:i + min_sequence_length]
            if substring.isdigit() and self._is_numerical_sequence(substring):
                return True

        return False

    def _is_alphabetical_sequence(self, s: str) -> bool:
        """检查是否为字母序列"""
        if len(s) < 3:
            return False

        # 升序检查
        ascending = all(ord(s[i]) + 1 == ord(s[i + 1]) for i in range(len(s) - 1))
        # 降序检查
        descending = all(ord(s[i]) - 1 == ord(s[i + 1]) for i in range(len(s) - 1))

        return ascending or descending

    def _is_numerical_sequence(self, s: str) -> bool:
        """检查是否为数字序列"""
        if len(s) < 3 or not s.isdigit():
            return False

        nums = [int(c) for c in s]

        # 升序检查
        ascending = all(nums[i] + 1 == nums[i + 1] for i in range(len(nums) - 1))
        # 降序检查
        descending = all(nums[i] - 1 == nums[i + 1] for i in range(len(nums) - 1))

        return ascending or descending

    def get_strength_score(self, password: str) -> Tuple[int, str]:
        """
        计算密码强度评分

        Args:
            password: 密码

        Returns:
            (score, level): 分数(0-100)和等级描述
        """
        score = 0

        # 长度评分 (0-25分)
        length_score = min(25, (len(password) - 8) * 2 + 10) if len(password) >= 8 else 0
        score += max(0, length_score)

        # 字符种类评分 (0-40分)
        char_types = 0
        if re.search(r'[a-z]', password):
            char_types += 1
        if re.search(r'[A-Z]', password):
            char_types += 1
        if re.search(r'\d', password):
            char_types += 1
        if re.search(f"[{re.escape(self.special_chars)}]", password):
            char_types += 1

        score += char_types * 10

        # 唯一字符比例评分 (0-20分)
        unique_ratio = len(set(password)) / len(password) if password else 0
        score += int(unique_ratio * 20)

        # 复杂度评分 (0-15分)
        if not self._has_consecutive_chars(password, 2):
            score += 5
        if not self._has_simple_sequence(password):
            score += 5
        if not any(pattern.lower() in password.lower() for pattern in self.forbidden_patterns):
            score += 5

        # 确定等级
        if score >= 90:
            level = "极强"
        elif score >= 70:
            level = "强"
        elif score >= 50:
            level = "中等"
        elif score >= 30:
            level = "弱"
        else:
            level = "极弱"

        return min(100, score), level


# 默认验证器实例
default_password_validator = PasswordValidator()


def validate_password(password: str) -> Tuple[bool, List[str]]:
    """
    使用默认配置验证密码

    Args:
        password: 要验证的密码

    Returns:
        (is_valid, error_messages): 验证结果和错误信息列表
    """
    return default_password_validator.validate(password)


def get_password_strength(password: str) -> Tuple[int, str]:
    """
    获取密码强度评分

    Args:
        password: 要评估的密码

    Returns:
        (score, level): 分数和等级
    """
    return default_password_validator.get_strength_score(password)