from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

@dataclass
class FileTypeConfig:
    """文件类型配置类"""

    # 基本信息
    file_type: str  # 文件类型标识 (如: ttv, eee, aaa)
    display_name: str  # 显示名称 (如: TTV数据, EEE数据)
    description: str = ""  # 描述信息

    # 数据处理配置
    enabled: bool = True  # 是否启用
    file_extensions: List[str] = field(default_factory=lambda: [".txt"])  # 支持的文件扩展名
    max_file_size: int = 100 * 1024 * 1024  # 最大文件大小（字节）

    # 数据库配置
    table_prefix: str = ""  # 表名前缀，如果为空则使用 file_type + "_"
    use_separate_schema: bool = False  # 是否使用独立的数据库schema

    # 业务配置
    stock_code_column: str = "股票代码"  # 股票代码列名
    volume_column: str = "成交量"  # 交易量列名
    date_format: str = "%Y%m%d"  # 日期格式

    # 概念匹配配置
    concept_mapping_file: Optional[str] = None  # 概念映射文件路径
    use_default_concept_mapping: bool = True  # 是否使用默认概念映射

    # 数据验证配置
    required_columns: List[str] = field(default_factory=lambda: ["股票代码", "成交量"])
    validation_rules: Dict[str, Any] = field(default_factory=dict)

    # 计算配置
    enable_concept_summary: bool = True  # 是否启用概念汇总计算
    enable_ranking: bool = True  # 是否启用排名计算
    enable_high_record: bool = True  # 是否启用创新高记录计算

    # 高级配置
    batch_size: int = 1000  # 批量处理大小
    calculation_timeout: int = 300  # 计算超时时间（秒）

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    version: str = "1.0.0"

    def __post_init__(self):
        """初始化后处理"""
        # 如果没有设置表前缀，使用文件类型作为前缀
        if not self.table_prefix:
            self.table_prefix = f"{self.file_type}_" if self.file_type != 'txt' else ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, (list, dict)):
                result[key] = value.copy()
            else:
                result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileTypeConfig':
        """从字典创建配置对象"""
        # 处理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])

        return cls(**data)

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'FileTypeConfig':
        """从JSON字符串创建配置对象"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> Dict[str, Any]:
        """验证配置的有效性"""
        errors = []
        warnings = []

        # 验证必需字段
        if not self.file_type or not isinstance(self.file_type, str):
            errors.append("file_type 必须是非空字符串")
        elif not self.file_type.replace('_', '').replace('-', '').isalnum():
            errors.append("file_type 只能包含字母、数字、下划线和短横线")

        if not self.display_name:
            errors.append("display_name 不能为空")

        # 验证文件大小
        if self.max_file_size <= 0:
            errors.append("max_file_size 必须大于0")
        elif self.max_file_size > 500 * 1024 * 1024:  # 500MB
            warnings.append("文件大小超过500MB可能影响性能")

        # 验证文件扩展名
        if not self.file_extensions:
            errors.append("file_extensions 不能为空")
        else:
            for ext in self.file_extensions:
                if not ext.startswith('.'):
                    errors.append(f"文件扩展名 {ext} 必须以.开头")

        # 验证必需列
        if not self.required_columns:
            errors.append("required_columns 不能为空")

        if self.stock_code_column not in self.required_columns:
            warnings.append(f"股票代码列 {self.stock_code_column} 不在必需列中")

        if self.volume_column not in self.required_columns:
            warnings.append(f"交易量列 {self.volume_column} 不在必需列中")

        # 验证批量大小
        if self.batch_size <= 0:
            errors.append("batch_size 必须大于0")
        elif self.batch_size > 10000:
            warnings.append("batch_size 过大可能影响内存使用")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


class FileTypeConfigManager:
    """文件类型配置管理器"""

    def __init__(self, config_storage_path: Optional[str] = None):
        self.config_storage_path = config_storage_path
        self._configs: Dict[str, FileTypeConfig] = {}
        self._load_default_configs()

    def _load_default_configs(self):
        """加载默认配置"""
        # TXT默认配置
        txt_config = FileTypeConfig(
            file_type="txt",
            display_name="TXT数据",
            description="原始TXT格式股票交易数据",
            table_prefix="",  # TXT不使用前缀
            stock_code_column="股票代码",
            volume_column="成交量",
            concept_mapping_file="/Users/peakom/Desktop/概念匹配表/概念匹配表.xlsx",
            created_by="system"
        )

        # TTV默认配置
        ttv_config = FileTypeConfig(
            file_type="ttv",
            display_name="TTV数据",
            description="TTV格式股票交易数据",
            table_prefix="ttv_",
            stock_code_column="股票代码",
            volume_column="成交量",
            use_default_concept_mapping=True,
            created_by="system"
        )

        # EEE默认配置
        eee_config = FileTypeConfig(
            file_type="eee",
            display_name="EEE数据",
            description="EEE格式股票交易数据",
            table_prefix="eee_",
            stock_code_column="股票代码",
            volume_column="成交量",
            use_default_concept_mapping=True,
            created_by="system"
        )

        self._configs = {
            "txt": txt_config,
            "ttv": ttv_config,
            "eee": eee_config
        }

    def get_config(self, file_type: str) -> Optional[FileTypeConfig]:
        """获取指定文件类型的配置"""
        return self._configs.get(file_type)

    def add_config(self, config: FileTypeConfig) -> bool:
        """添加新的文件类型配置"""
        validation_result = config.validate()
        if not validation_result['valid']:
            raise ValueError(f"配置验证失败: {validation_result['errors']}")

        self._configs[config.file_type] = config
        return True

    def update_config(self, file_type: str, config: FileTypeConfig) -> bool:
        """更新文件类型配置"""
        if file_type not in self._configs:
            raise KeyError(f"文件类型 {file_type} 不存在")

        validation_result = config.validate()
        if not validation_result['valid']:
            raise ValueError(f"配置验证失败: {validation_result['errors']}")

        self._configs[file_type] = config
        return True

    def remove_config(self, file_type: str) -> bool:
        """移除文件类型配置"""
        if file_type == "txt":
            raise ValueError("不能删除TXT默认配置")

        if file_type in self._configs:
            del self._configs[file_type]
            return True
        return False

    def list_configs(self) -> Dict[str, FileTypeConfig]:
        """列出所有配置"""
        return self._configs.copy()

    def get_enabled_configs(self) -> Dict[str, FileTypeConfig]:
        """获取所有启用的配置"""
        return {
            file_type: config
            for file_type, config in self._configs.items()
            if config.enabled
        }

    def validate_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """验证所有配置"""
        results = {}
        for file_type, config in self._configs.items():
            results[file_type] = config.validate()
        return results

    def export_configs(self) -> Dict[str, Any]:
        """导出所有配置"""
        return {
            'export_time': datetime.now().isoformat(),
            'configs': {
                file_type: config.to_dict()
                for file_type, config in self._configs.items()
            }
        }

    def import_configs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """导入配置"""
        results = {
            'success': [],
            'errors': [],
            'warnings': []
        }

        if 'configs' not in data:
            results['errors'].append("导入数据格式错误: 缺少configs字段")
            return results

        for file_type, config_data in data['configs'].items():
            try:
                config = FileTypeConfig.from_dict(config_data)
                validation_result = config.validate()

                if validation_result['valid']:
                    self._configs[file_type] = config
                    results['success'].append(f"成功导入 {file_type} 配置")

                    if validation_result['warnings']:
                        results['warnings'].extend([
                            f"{file_type}: {warning}"
                            for warning in validation_result['warnings']
                        ])
                else:
                    results['errors'].append(
                        f"{file_type}: {', '.join(validation_result['errors'])}"
                    )

            except Exception as e:
                results['errors'].append(f"{file_type}: 导入失败 - {str(e)}")

        return results