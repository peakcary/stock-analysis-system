from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from app.services.schema.dynamic_table_manager import DynamicTableManager
from app.services.schema.dynamic_model_generator import DynamicModelGenerator
from app.services.schema.file_type_config import FileTypeConfig, FileTypeConfigManager
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class FileTypeRegistry:
    """文件类型注册管理器"""

    def __init__(self, engine: Engine, db: Session, config_manager: Optional[FileTypeConfigManager] = None):
        self.engine = engine
        self.db = db
        self.table_manager = DynamicTableManager(engine)
        self.model_generator = DynamicModelGenerator(engine)
        self.config_manager = config_manager or FileTypeConfigManager()

    def register_new_file_type(self, file_type_config: Dict) -> Dict:
        """注册新的文件类型

        Args:
            file_type_config: 文件类型配置字典或FileTypeConfig对象

        Returns:
            注册结果
        """
        try:
            # 支持传入字典或FileTypeConfig对象
            if isinstance(file_type_config, dict):
                config = FileTypeConfig.from_dict(file_type_config)
            elif isinstance(file_type_config, FileTypeConfig):
                config = file_type_config
            else:
                return {
                    'success': False,
                    'message': "配置格式错误，必须是字典或FileTypeConfig对象"
                }

            file_type = config.file_type

            # 1. 验证配置格式
            validation_result = config.validate()
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"配置验证失败: {', '.join(validation_result['errors'])}",
                    'warnings': validation_result.get('warnings', [])
                }

            # 2. 检查文件类型是否已存在（检查表是否存在）
            if self.table_manager._tables_exist(file_type):
                return {
                    'success': False,
                    'message': f"文件类型 {file_type} 已存在相关数据表"
                }

            # 3. 创建数据库表
            logger.info(f"开始为文件类型 {file_type} 创建数据库表...")
            table_creation_result = self.table_manager.create_file_type_tables(file_type)
            if not table_creation_result:
                return {
                    'success': False,
                    'message': f"创建数据库表失败"
                }

            # 4. 生成SQLAlchemy模型
            logger.info(f"开始为文件类型 {file_type} 生成SQLAlchemy模型...")
            models = self.model_generator.generate_models_for_file_type(file_type)
            if not models:
                # 如果模型生成失败，清理已创建的表
                self.table_manager.drop_file_type_tables(file_type)
                return {
                    'success': False,
                    'message': f"生成数据模型失败"
                }

            # 5. 验证创建的表和模型
            table_info = self.table_manager.get_table_info(file_type)
            model_validation = self.model_generator.validate_models(file_type)

            if not model_validation['valid']:
                # 如果验证失败，清理资源
                self.table_manager.drop_file_type_tables(file_type)
                self.model_generator.clear_model_cache(file_type)
                return {
                    'success': False,
                    'message': f"模型验证失败: {model_validation.get('error', '未知错误')}"
                }

            # 6. 保存配置到配置管理器
            self.config_manager.add_config(config)

            logger.info(f"成功注册文件类型: {file_type}")

            return {
                'success': True,
                'message': f"文件类型 {file_type} 注册成功",
                'file_type': file_type,
                'tables_created': list(table_info.keys()),
                'models_generated': len(models),
                'table_info': table_info,
                'config': config.to_dict(),
                'warnings': validation_result.get('warnings', [])
            }

        except Exception as e:
            logger.error(f"注册文件类型时出错: {e}")
            # 尝试清理可能已创建的资源
            try:
                if 'file_type' in locals():
                    self.table_manager.drop_file_type_tables(file_type)
                    self.model_generator.clear_model_cache(file_type)
            except:
                pass

            return {
                'success': False,
                'message': f"注册失败: {str(e)}"
            }

    def _validate_config(self, config: Dict) -> Dict:
        """验证文件类型配置"""
        errors = []

        # 必需字段检查
        required_fields = [
            'file_type', 'file_extension', 'display_name',
            'table_prefix', 'parse_config', 'api_prefix', 'ui_config'
        ]

        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # 字段格式检查
        if 'file_type' in config:
            file_type = config['file_type']
            if not file_type.replace('_', '').isalnum():
                errors.append("file_type只能包含字母、数字和下划线")
            if len(file_type) > 20:
                errors.append("file_type长度不能超过20个字符")
            if file_type.lower() in ['txt']:  # 保留关键字检查
                errors.append(f"file_type不能使用保留关键字: {file_type}")

        if 'file_extension' in config:
            if not config['file_extension'].startswith('.'):
                errors.append("file_extension必须以'.'开头")
            if len(config['file_extension']) > 10:
                errors.append("file_extension长度不能超过10个字符")

        if 'display_name' in config:
            if len(config['display_name']) > 100:
                errors.append("display_name长度不能超过100个字符")

        if 'table_prefix' in config:
            prefix = config['table_prefix']
            if prefix and not prefix.endswith('_'):
                errors.append("table_prefix如果不为空，必须以'_'结尾")

        if 'parse_config' in config:
            parse_config = config['parse_config']
            if not isinstance(parse_config, dict):
                errors.append("parse_config必须是字典格式")
            else:
                parse_required = ['delimiter', 'columns', 'date_format']
                for field in parse_required:
                    if field not in parse_config:
                        errors.append(f"parse_config中缺少{field}字段")

        if 'ui_config' in config:
            ui_config = config['ui_config']
            if not isinstance(ui_config, dict):
                errors.append("ui_config必须是字典格式")
            else:
                ui_required = ['color', 'icon', 'description']
                for field in ui_required:
                    if field not in ui_config:
                        errors.append(f"ui_config中缺少{field}字段")

        if 'api_prefix' in config:
            api_prefix = config['api_prefix']
            if not api_prefix.startswith('/api/v1/'):
                errors.append("api_prefix必须以'/api/v1/'开头")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _save_config_to_db(self, file_type: str, config: Dict):
        """保存配置到数据库（用于持久化和管理界面展示）"""
        try:
            # 这里可以创建一个专门的配置表来存储文件类型配置
            # 暂时使用日志记录，后续可以扩展为数据库存储
            logger.info(f"文件类型 {file_type} 的配置: {json.dumps(config, indent=2, ensure_ascii=False)}")
        except Exception as e:
            logger.warning(f"保存配置到数据库失败: {e}")

    def unregister_file_type(self, file_type: str, force: bool = False) -> Dict:
        """注销文件类型"""
        try:
            # 基本检查
            if not file_type or file_type == 'txt':
                return {
                    'success': False,
                    'message': "不能删除TXT类型或空类型名"
                }

            # 检查表是否存在
            if not self.table_manager._tables_exist(file_type):
                return {
                    'success': False,
                    'message': f"文件类型 {file_type} 不存在"
                }

            # 检查是否有数据
            table_info = self.table_manager.get_table_info(file_type)
            has_data = any(info.get('row_count', 0) > 0 for info in table_info.values())
            total_rows = sum(info.get('row_count', 0) for info in table_info.values())

            if has_data and not force:
                return {
                    'success': False,
                    'message': f"文件类型 {file_type} 包含 {total_rows} 条数据，请使用force=True强制删除",
                    'data_summary': table_info
                }

            # 删除数据库表
            logger.info(f"开始删除文件类型 {file_type} 的数据库表...")
            drop_result = self.table_manager.drop_file_type_tables(file_type)
            if not drop_result:
                return {
                    'success': False,
                    'message': f"删除数据库表失败"
                }

            # 清理模型缓存
            self.model_generator.clear_model_cache(file_type)

            logger.info(f"成功注销文件类型: {file_type}")

            return {
                'success': True,
                'message': f"文件类型 {file_type} 注销成功",
                'deleted_tables': list(table_info.keys()),
                'deleted_rows': total_rows if has_data else 0
            }

        except Exception as e:
            logger.error(f"注销文件类型时出错: {e}")
            return {
                'success': False,
                'message': f"注销失败: {str(e)}"
            }

    def get_registered_types(self) -> Dict:
        """获取已注册的文件类型列表"""
        try:
            # 通过检查数据库中的表来确定已注册的文件类型
            registered_types = {}

            # 检查所有可能的文件类型表
            from sqlalchemy import text
            with self.engine.connect() as conn:
                # 获取所有表名
                result = conn.execute(text("SHOW TABLES"))
                all_tables = [row[0] for row in result]

                # 分析表名，找出文件类型
                file_types = set()
                for table_name in all_tables:
                    if table_name.endswith('_daily_trading'):
                        prefix = table_name.replace('_daily_trading', '')
                        if prefix:  # 非空前缀
                            file_types.add(prefix)
                    elif table_name == 'daily_trading':
                        file_types.add('txt')  # TXT类型没有前缀

                # 为每个文件类型获取详细信息
                for file_type in file_types:
                    try:
                        table_info = self.table_manager.get_table_info(file_type)
                        model_info = self.model_generator.get_model_info(file_type)

                        registered_types[file_type] = {
                            'file_type': file_type,
                            'display_name': f"{file_type.upper()}数据" if file_type != 'txt' else "TXT数据",
                            'table_prefix': f"{file_type}_" if file_type != 'txt' else "",
                            'tables': table_info,
                            'models': model_info,
                            'total_rows': sum(info.get('row_count', 0) for info in table_info.values()),
                            'total_size_mb': round(sum(info.get('size_mb', 0) for info in table_info.values()), 2),
                            'models_cached': file_type in self.model_generator._model_cache
                        }
                    except Exception as e:
                        logger.warning(f"获取文件类型 {file_type} 的详细信息时出错: {e}")
                        registered_types[file_type] = {
                            'file_type': file_type,
                            'error': str(e)
                        }

            return {
                'success': True,
                'registered_types': registered_types,
                'total_count': len(registered_types)
            }

        except Exception as e:
            logger.error(f"获取注册类型列表时出错: {e}")
            return {
                'success': False,
                'message': f"获取失败: {str(e)}"
            }

    def validate_file_type_health(self, file_type: str) -> Dict:
        """验证文件类型的健康状态"""
        try:
            health_issues = []
            warnings = []

            # 1. 检查表是否存在
            if not self.table_manager._tables_exist(file_type):
                return {
                    'success': False,
                    'message': f"文件类型 {file_type} 未注册或表不存在"
                }

            # 2. 检查数据库表完整性
            table_info = self.table_manager.get_table_info(file_type)
            expected_tables = [
                f"{file_type}_daily_trading" if file_type != 'txt' else "daily_trading",
                f"{file_type}_concept_daily_summary" if file_type != 'txt' else "concept_daily_summary",
                f"{file_type}_stock_concept_ranking" if file_type != 'txt' else "stock_concept_ranking",
                f"{file_type}_concept_high_record" if file_type != 'txt' else "concept_high_record",
                f"{file_type}_import_record" if file_type != 'txt' else "txt_import_record"
            ]

            missing_tables = []
            for expected_table in expected_tables:
                if expected_table not in table_info or not table_info[expected_table].get('exists', False):
                    missing_tables.append(expected_table)

            if missing_tables:
                health_issues.append(f"缺少数据库表: {', '.join(missing_tables)}")

            # 3. 检查模型完整性
            try:
                model_validation = self.model_generator.validate_models(file_type)
                if not model_validation['valid']:
                    if model_validation.get('missing_models'):
                        health_issues.append(f"缺少SQLAlchemy模型: {', '.join(model_validation['missing_models'])}")
                    if model_validation.get('error'):
                        health_issues.append(f"模型验证错误: {model_validation['error']}")
            except Exception as e:
                health_issues.append(f"模型验证异常: {str(e)}")

            # 4. 数据完整性检查
            total_rows = sum(info.get('row_count', 0) for info in table_info.values())
            if total_rows > 0:
                # 检查数据分布是否合理
                daily_trading_rows = table_info.get(
                    f"{file_type}_daily_trading" if file_type != 'txt' else "daily_trading", {}
                ).get('row_count', 0)

                concept_summary_rows = table_info.get(
                    f"{file_type}_concept_daily_summary" if file_type != 'txt' else "concept_daily_summary", {}
                ).get('row_count', 0)

                if daily_trading_rows > 0 and concept_summary_rows == 0:
                    warnings.append("存在交易数据但缺少概念汇总数据，可能需要重新计算")

            # 5. 性能检查
            total_size_mb = sum(info.get('size_mb', 0) for info in table_info.values())
            if total_size_mb > 1000:  # 大于1GB
                warnings.append(f"数据量较大({total_size_mb:.1f}MB)，建议考虑分区优化")

            return {
                'success': True,
                'file_type': file_type,
                'healthy': len(health_issues) == 0,
                'issues': health_issues,
                'warnings': warnings,
                'statistics': {
                    'total_tables': len([t for t in table_info.values() if t.get('exists')]),
                    'total_rows': total_rows,
                    'total_size_mb': round(total_size_mb, 2),
                    'models_cached': file_type in self.model_generator._model_cache
                },
                'table_details': table_info
            }

        except Exception as e:
            logger.error(f"验证文件类型健康状态时出错: {e}")
            return {
                'success': False,
                'message': f"健康检查失败: {str(e)}"
            }

    def repair_file_type(self, file_type: str, repair_options: Dict = None) -> Dict:
        """修复文件类型（重建表或模型）"""
        try:
            if repair_options is None:
                repair_options = {
                    'rebuild_tables': False,
                    'rebuild_models': True,
                    'force': False
                }

            repair_results = []

            # 1. 重建模型缓存
            if repair_options.get('rebuild_models', True):
                self.model_generator.clear_model_cache(file_type)
                models = self.model_generator.generate_models_for_file_type(file_type)
                if models:
                    repair_results.append(f"重建了 {len(models)} 个SQLAlchemy模型")
                else:
                    repair_results.append("重建SQLAlchemy模型失败")

            # 2. 重建数据库表（慎用）
            if repair_options.get('rebuild_tables', False):
                if not repair_options.get('force', False):
                    # 检查是否有数据
                    table_info = self.table_manager.get_table_info(file_type)
                    has_data = any(info.get('row_count', 0) > 0 for info in table_info.values())
                    if has_data:
                        return {
                            'success': False,
                            'message': "检测到数据存在，重建表将丢失数据。请使用force=True强制执行。",
                            'repair_results': repair_results
                        }

                # 重建表
                rebuild_result = self.table_manager.recreate_file_type_tables(file_type)
                if rebuild_result:
                    repair_results.append("重建数据库表成功")
                else:
                    repair_results.append("重建数据库表失败")

            return {
                'success': True,
                'message': f"文件类型 {file_type} 修复完成",
                'repair_results': repair_results
            }

        except Exception as e:
            logger.error(f"修复文件类型时出错: {e}")
            return {
                'success': False,
                'message': f"修复失败: {str(e)}"
            }

    # ========================= 配置管理相关方法 =========================

    def get_file_type_config(self, file_type: str) -> Optional[FileTypeConfig]:
        """获取文件类型配置"""
        return self.config_manager.get_config(file_type)

    def update_file_type_config(self, file_type: str, config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新文件类型配置"""
        try:
            current_config = self.config_manager.get_config(file_type)
            if not current_config:
                return {
                    'success': False,
                    'message': f"文件类型 {file_type} 不存在"
                }

            # 创建更新后的配置
            config_dict = current_config.to_dict()
            config_dict.update(config_updates)
            updated_config = FileTypeConfig.from_dict(config_dict)

            # 验证配置
            validation_result = updated_config.validate()
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"配置验证失败: {', '.join(validation_result['errors'])}",
                    'warnings': validation_result.get('warnings', [])
                }

            # 更新配置
            self.config_manager.update_config(file_type, updated_config)

            return {
                'success': True,
                'message': f"文件类型 {file_type} 配置更新成功",
                'config': updated_config.to_dict(),
                'warnings': validation_result.get('warnings', [])
            }

        except Exception as e:
            logger.error(f"更新文件类型配置时出错: {e}")
            return {
                'success': False,
                'message': f"配置更新失败: {str(e)}"
            }

    def list_all_configs(self) -> Dict[str, FileTypeConfig]:
        """列出所有文件类型配置"""
        return self.config_manager.list_configs()

    def get_enabled_file_types(self) -> List[str]:
        """获取所有启用的文件类型"""
        enabled_configs = self.config_manager.get_enabled_configs()
        return list(enabled_configs.keys())

    def enable_file_type(self, file_type: str) -> Dict[str, Any]:
        """启用文件类型"""
        return self.update_file_type_config(file_type, {'enabled': True})

    def disable_file_type(self, file_type: str) -> Dict[str, Any]:
        """禁用文件类型"""
        return self.update_file_type_config(file_type, {'enabled': False})

    def validate_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """验证所有文件类型配置"""
        return self.config_manager.validate_all_configs()

    def export_configs(self) -> Dict[str, Any]:
        """导出所有配置"""
        return self.config_manager.export_configs()

    def import_configs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """导入配置"""
        return self.config_manager.import_configs(data)

    def create_file_type_from_template(self, file_type: str, display_name: str,
                                     template: str = "ttv", **overrides) -> Dict[str, Any]:
        """从模板创建新的文件类型配置"""
        try:
            # 获取模板配置
            template_config = self.config_manager.get_config(template)
            if not template_config:
                return {
                    'success': False,
                    'message': f"模板类型 {template} 不存在"
                }

            # 创建新配置
            config_dict = template_config.to_dict()
            config_dict.update({
                'file_type': file_type,
                'display_name': display_name,
                'table_prefix': f"{file_type}_" if file_type != 'txt' else "",
                'created_at': datetime.now(),
                'created_by': 'user'
            })
            config_dict.update(overrides)

            new_config = FileTypeConfig.from_dict(config_dict)

            # 注册新文件类型
            return self.register_new_file_type(new_config)

        except Exception as e:
            logger.error(f"从模板创建文件类型时出错: {e}")
            return {
                'success': False,
                'message': f"创建失败: {str(e)}"
            }

    def get_system_summary(self) -> Dict[str, Any]:
        """获取系统概览"""
        try:
            registered_types = self.get_registered_types()
            all_configs = self.list_all_configs()

            # 统计信息
            total_tables = 0
            total_rows = 0
            total_size_mb = 0
            healthy_types = 0

            for file_type, info in registered_types.get('file_types', {}).items():
                total_tables += info.get('table_count', 0)
                total_rows += info.get('total_rows', 0)
                total_size_mb += info.get('total_size_mb', 0)
                if info.get('healthy', False):
                    healthy_types += 1

            return {
                'success': True,
                'summary': {
                    'total_file_types': len(all_configs),
                    'enabled_file_types': len(self.get_enabled_file_types()),
                    'registered_file_types': len(registered_types.get('file_types', {})),
                    'healthy_file_types': healthy_types,
                    'total_tables': total_tables,
                    'total_rows': total_rows,
                    'total_size_mb': round(total_size_mb, 2)
                },
                'file_types': list(all_configs.keys()),
                'enabled_types': self.get_enabled_file_types(),
                'registered_types': list(registered_types.get('file_types', {}).keys()),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"获取系统概览时出错: {e}")
            return {
                'success': False,
                'message': f"获取概览失败: {str(e)}"
            }

