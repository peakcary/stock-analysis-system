#!/usr/bin/env python3
"""
启用数据库优化功能脚本
支持渐进式切换和回滚
v2.6.4 - 2025-09-13
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def update_env_file(env_file_path: str, optimizations: dict) -> bool:
    """更新 .env 文件中的优化配置"""
    try:
        # 读取现有内容
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # 更新配置项
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key = line.split('=')[0]
                if key in optimizations:
                    updated_lines.append(f"{key}={optimizations[key]}\n")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line + '\n')
            else:
                updated_lines.append(line + '\n')
        
        # 添加新的配置项
        for key, value in optimizations.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\n")
        
        # 写回文件
        with open(env_file_path, 'w') as f:
            f.writelines(updated_lines)
        
        logger.info(f"已更新环境配置文件: {env_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"更新环境文件失败: {e}")
        return False


def enable_optimization_mode(mode: str = "testing") -> bool:
    """启用优化模式"""
    
    # 定义不同模式的配置
    configurations = {
        "testing": {
            "USE_OPTIMIZED_TABLES": "false",
            "ENABLE_PERFORMANCE_LOG": "true", 
            "ENABLE_QUERY_CACHE": "true",
            "API_PERFORMANCE_MONITORING": "true"
        },
        "dual_write": {
            "USE_OPTIMIZED_TABLES": "false",
            "ENABLE_PERFORMANCE_LOG": "true",
            "ENABLE_QUERY_CACHE": "true", 
            "API_PERFORMANCE_MONITORING": "true",
            "ENABLE_DUAL_WRITE": "true"
        },
        "optimized": {
            "USE_OPTIMIZED_TABLES": "true",
            "ENABLE_PERFORMANCE_LOG": "true",
            "ENABLE_QUERY_CACHE": "true",
            "API_PERFORMANCE_MONITORING": "true",
            "ENABLE_DUAL_WRITE": "false"
        },
        "production": {
            "USE_OPTIMIZED_TABLES": "true",
            "ENABLE_PERFORMANCE_LOG": "false",  # 生产环境关闭详细日志
            "ENABLE_QUERY_CACHE": "true",
            "API_PERFORMANCE_MONITORING": "true"
        }
    }
    
    if mode not in configurations:
        logger.error(f"未知模式: {mode}. 可用模式: {list(configurations.keys())}")
        return False
    
    config = configurations[mode]
    
    logger.info(f"启用优化模式: {mode}")
    logger.info(f"配置详情: {config}")
    
    # 查找 .env 文件
    project_root = Path(__file__).parent.parent.parent
    backend_env = project_root / "backend" / ".env"
    
    # 更新后端配置
    if backend_env.exists():
        success = update_env_file(str(backend_env), config)
        if success:
            logger.info("✓ 后端环境配置已更新")
        else:
            logger.error("✗ 更新后端环境配置失败")
            return False
    else:
        logger.warning(f"后端 .env 文件不存在: {backend_env}")
        logger.info("请手动复制 .env.example 到 .env 并配置")
    
    # 生成切换报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = project_root / f"optimization_switch_{mode}_{timestamp}.log"
    
    with open(report_file, 'w') as f:
        f.write(f"数据库优化切换报告\n")
        f.write(f"切换时间: {datetime.now()}\n")
        f.write(f"切换模式: {mode}\n")
        f.write(f"配置项:\n")
        for key, value in config.items():
            f.write(f"  {key}={value}\n")
        f.write(f"\n注意事项:\n")
        f.write(f"1. 重启后端服务以应用新配置\n")
        f.write(f"2. 监控系统性能和错误日志\n")
        f.write(f"3. 如有问题可回滚到之前配置\n")
    
    logger.info(f"切换报告已保存: {report_file}")
    
    return True


def rollback_optimization() -> bool:
    """回滚到原始配置"""
    
    rollback_config = {
        "USE_OPTIMIZED_TABLES": "false",
        "ENABLE_PERFORMANCE_LOG": "false",
        "ENABLE_QUERY_CACHE": "false",
        "API_PERFORMANCE_MONITORING": "false",
        "ENABLE_DUAL_WRITE": "false"
    }
    
    logger.info("回滚数据库优化配置...")
    
    project_root = Path(__file__).parent.parent.parent
    backend_env = project_root / "backend" / ".env"
    
    if backend_env.exists():
        success = update_env_file(str(backend_env), rollback_config)
        if success:
            logger.info("✓ 已回滚到原始配置")
            return True
    
    logger.error("✗ 回滚失败")
    return False


def check_optimization_status() -> dict:
    """检查当前优化状态"""
    
    project_root = Path(__file__).parent.parent.parent
    backend_env = project_root / "backend" / ".env"
    
    status = {
        "env_file_exists": backend_env.exists(),
        "configurations": {},
        "optimization_enabled": False
    }
    
    if backend_env.exists():
        try:
            with open(backend_env, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        if key.startswith(('USE_OPTIMIZED', 'ENABLE_PERFORMANCE', 'ENABLE_QUERY', 'API_PERFORMANCE')):
                            status["configurations"][key] = value
            
            # 判断是否启用优化
            status["optimization_enabled"] = status["configurations"].get("USE_OPTIMIZED_TABLES", "false").lower() == "true"
            
        except Exception as e:
            logger.error(f"读取环境配置失败: {e}")
    
    return status


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库优化功能管理工具")
    parser.add_argument("action", choices=["enable", "disable", "status", "rollback"], 
                       help="操作类型")
    parser.add_argument("--mode", choices=["testing", "dual_write", "optimized", "production"],
                       default="testing", help="启用模式")
    
    args = parser.parse_args()
    
    if args.action == "enable":
        success = enable_optimization_mode(args.mode)
        if success:
            print(f"✓ 已启用优化模式: {args.mode}")
            print("请重启后端服务以应用新配置")
        else:
            print("✗ 启用优化模式失败")
            sys.exit(1)
    
    elif args.action == "disable" or args.action == "rollback":
        success = rollback_optimization()
        if success:
            print("✓ 已回滚到原始配置")
            print("请重启后端服务以应用新配置")
        else:
            print("✗ 回滚失败")
            sys.exit(1)
    
    elif args.action == "status":
        status = check_optimization_status()
        print("\n当前优化状态:")
        print(f"环境文件存在: {status['env_file_exists']}")
        print(f"优化已启用: {status['optimization_enabled']}")
        print("\n配置详情:")
        for key, value in status['configurations'].items():
            print(f"  {key}={value}")
        
        if status['optimization_enabled']:
            print("\n🚀 数据库优化已启用")
        else:
            print("\n⚠️  数据库优化未启用")


if __name__ == "__main__":
    main()