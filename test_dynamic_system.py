#!/usr/bin/env python3
"""
动态文件类型系统测试脚本
测试核心组件的功能：动态表管理器、模型生成器、文件类型注册管理器
"""

import sys
import os

# 添加项目路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.schema import (
    DynamicTableManager,
    DynamicModelGenerator,
    FileTypeRegistry,
    FileTypeConfig,
    FileTypeConfigManager
)

def test_dynamic_table_manager():
    """测试动态表管理器"""
    print("=== 测试动态表管理器 ===")

    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        table_manager = DynamicTableManager(engine)

        # 测试创建TTV文件类型的表
        print("1. 测试创建TTV文件类型的表...")
        result = table_manager.create_file_type_tables("ttv")
        print(f"创建结果: {result}")

        # 测试获取表信息
        print("2. 测试获取表信息...")
        table_info = table_manager.get_table_info("ttv")
        print(f"表信息: {table_info}")

        # 测试检查表是否存在
        print("3. 测试检查表是否存在...")
        exists = table_manager._tables_exist("ttv")
        print(f"TTV表是否存在: {exists}")

        print("✅ 动态表管理器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 动态表管理器测试失败: {e}\n")
        return False

def test_dynamic_model_generator():
    """测试动态模型生成器"""
    print("=== 测试动态模型生成器 ===")

    try:
        # 创建数据库引擎
        engine = create_engine(settings.DATABASE_URL)
        model_generator = DynamicModelGenerator(engine)

        # 测试为TTV生成模型
        print("1. 测试为TTV生成模型...")
        models = model_generator.generate_models_for_file_type("ttv")
        print(f"生成的模型数量: {len(models)}")
        print(f"模型名称: {list(models.keys())}")

        # 测试获取模型信息
        print("2. 测试获取模型信息...")
        model_info = model_generator.get_model_info("ttv")
        print(f"模型信息: {model_info}")

        # 测试模型验证
        print("3. 测试模型验证...")
        validation = model_generator.validate_models("ttv")
        print(f"验证结果: {validation}")

        print("✅ 动态模型生成器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 动态模型生成器测试失败: {e}\n")
        return False

def test_file_type_config_manager():
    """测试文件类型配置管理器"""
    print("=== 测试文件类型配置管理器 ===")

    try:
        config_manager = FileTypeConfigManager()

        # 测试获取默认配置
        print("1. 测试获取默认配置...")
        configs = config_manager.list_configs()
        print(f"默认配置数量: {len(configs)}")
        print(f"配置类型: {list(configs.keys())}")

        # 测试获取TTV配置
        print("2. 测试获取TTV配置...")
        ttv_config = config_manager.get_config("ttv")
        if ttv_config:
            print(f"TTV配置: {ttv_config.display_name} - {ttv_config.description}")

        # 测试创建新配置
        print("3. 测试创建新配置...")
        new_config = FileTypeConfig(
            file_type="test",
            display_name="测试类型",
            description="用于测试的文件类型",
            created_by="test_script"
        )

        validation = new_config.validate()
        print(f"新配置验证结果: {validation}")

        if validation['valid']:
            config_manager.add_config(new_config)
            print("新配置添加成功")

        print("✅ 文件类型配置管理器测试通过\n")
        return True

    except Exception as e:
        print(f"❌ 文件类型配置管理器测试失败: {e}\n")
        return False

def test_file_type_registry():
    """测试文件类型注册管理器"""
    print("=== 测试文件类型注册管理器 ===")

    try:
        # 创建数据库引擎和会话
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # 创建注册管理器
            registry = FileTypeRegistry(engine, db)

            # 测试获取系统概览
            print("1. 测试获取系统概览...")
            summary = registry.get_system_summary()
            print(f"系统概览: {summary}")

            # 测试获取已注册类型
            print("2. 测试获取已注册类型...")
            registered_types = registry.get_registered_types()
            print(f"已注册类型: {registered_types}")

            # 测试健康检查
            print("3. 测试健康检查...")
            if 'ttv' in [config.file_type for config in registry.config_manager.list_configs().values()]:
                health = registry.validate_file_type_health("ttv")
                print(f"TTV健康状态: {health}")

            print("✅ 文件类型注册管理器测试通过\n")
            return True

        finally:
            db.close()

    except Exception as e:
        print(f"❌ 文件类型注册管理器测试失败: {e}\n")
        return False

def test_end_to_end_registration():
    """测试端到端的文件类型注册流程"""
    print("=== 测试端到端文件类型注册 ===")

    try:
        # 创建数据库引擎和会话
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        try:
            # 创建注册管理器
            registry = FileTypeRegistry(engine, db)

            # 创建EEE文件类型配置
            print("1. 创建EEE文件类型配置...")
            eee_config = FileTypeConfig(
                file_type="eee",
                display_name="EEE数据",
                description="EEE格式股票交易数据",
                table_prefix="eee_",
                stock_code_column="股票代码",
                volume_column="成交量",
                use_default_concept_mapping=True,
                created_by="test_script"
            )

            # 注册新文件类型
            print("2. 注册EEE文件类型...")
            result = registry.register_new_file_type(eee_config)
            print(f"注册结果: {result}")

            if result['success']:
                print("3. 验证注册结果...")

                # 检查表是否创建
                table_info = registry.table_manager.get_table_info("eee")
                print(f"EEE表信息: {table_info}")

                # 检查模型是否生成
                model_info = registry.model_generator.get_model_info("eee")
                print(f"EEE模型信息: {model_info}")

                # 健康检查
                health = registry.validate_file_type_health("eee")
                print(f"EEE健康状态: {health}")

                print("✅ 端到端注册测试通过\n")
                return True
            else:
                print(f"注册失败: {result['message']}\n")
                return False

        finally:
            db.close()

    except Exception as e:
        print(f"❌ 端到端注册测试失败: {e}\n")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始动态文件类型系统测试\n")

    tests = [
        test_file_type_config_manager,
        test_dynamic_table_manager,
        test_dynamic_model_generator,
        test_file_type_registry,
        test_end_to_end_registration
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！动态文件类型系统运行正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)