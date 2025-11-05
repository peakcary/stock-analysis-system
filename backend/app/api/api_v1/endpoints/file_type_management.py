from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db, get_engine
from app.services.schema import FileTypeRegistry, FileTypeConfig, FileTypeConfigManager
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ========================= 请求/响应模型 =========================

class FileTypeConfigRequest(BaseModel):
    """文件类型配置请求模型"""
    file_type: str = Field(..., description="文件类型标识", pattern="^[a-zA-Z0-9_-]+$")
    display_name: str = Field(..., description="显示名称", min_length=1, max_length=100)
    description: str = Field("", description="描述信息", max_length=500)
    enabled: bool = Field(True, description="是否启用")
    file_extensions: List[str] = Field(default_factory=lambda: [".txt"], description="支持的文件扩展名")
    max_file_size: int = Field(100 * 1024 * 1024, description="最大文件大小（字节）", gt=0)
    table_prefix: str = Field("", description="表名前缀")
    stock_code_column: str = Field("股票代码", description="股票代码列名")
    volume_column: str = Field("成交量", description="交易量列名")
    date_format: str = Field("%Y%m%d", description="日期格式")
    concept_mapping_file: Optional[str] = Field(None, description="概念映射文件路径")
    use_default_concept_mapping: bool = Field(True, description="是否使用默认概念映射")
    required_columns: List[str] = Field(default_factory=lambda: ["股票代码", "成交量"], description="必需列")
    enable_concept_summary: bool = Field(True, description="是否启用概念汇总计算")
    enable_ranking: bool = Field(True, description="是否启用排名计算")
    enable_high_record: bool = Field(True, description="是否启用创新高记录计算")
    batch_size: int = Field(1000, description="批量处理大小", gt=0, le=10000)
    calculation_timeout: int = Field(300, description="计算超时时间（秒）", gt=0, le=3600)

class FileTypeConfigUpdateRequest(BaseModel):
    """文件类型配置更新请求模型"""
    display_name: Optional[str] = Field(None, description="显示名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="描述信息", max_length=500)
    enabled: Optional[bool] = Field(None, description="是否启用")
    file_extensions: Optional[List[str]] = Field(None, description="支持的文件扩展名")
    max_file_size: Optional[int] = Field(None, description="最大文件大小（字节）", gt=0)
    stock_code_column: Optional[str] = Field(None, description="股票代码列名")
    volume_column: Optional[str] = Field(None, description="交易量列名")
    date_format: Optional[str] = Field(None, description="日期格式")
    concept_mapping_file: Optional[str] = Field(None, description="概念映射文件路径")
    use_default_concept_mapping: Optional[bool] = Field(None, description="是否使用默认概念映射")
    required_columns: Optional[List[str]] = Field(None, description="必需列")
    enable_concept_summary: Optional[bool] = Field(None, description="是否启用概念汇总计算")
    enable_ranking: Optional[bool] = Field(None, description="是否启用排名计算")
    enable_high_record: Optional[bool] = Field(None, description="是否启用创新高记录计算")
    batch_size: Optional[int] = Field(None, description="批量处理大小", gt=0, le=10000)
    calculation_timeout: Optional[int] = Field(None, description="计算超时时间（秒）", gt=0, le=3600)

class TemplateCreateRequest(BaseModel):
    """从模板创建文件类型请求模型"""
    file_type: str = Field(..., description="新文件类型标识", pattern="^[a-zA-Z0-9_-]+$")
    display_name: str = Field(..., description="显示名称", min_length=1, max_length=100)
    template: str = Field("ttv", description="模板类型")
    overrides: Dict[str, Any] = Field(default_factory=dict, description="覆盖的配置项")

class RepairRequest(BaseModel):
    """修复请求模型"""
    rebuild_tables: bool = Field(False, description="是否重建数据库表")
    rebuild_models: bool = Field(True, description="是否重建模型")
    force: bool = Field(False, description="是否强制执行（忽略数据丢失警告）")

# ========================= 依赖注入 =========================

def get_registry(db: Session = Depends(get_db)) -> FileTypeRegistry:
    """获取文件类型注册管理器"""
    engine = get_engine()
    return FileTypeRegistry(engine, db)

# ========================= API 端点 =========================

@router.get("/system/summary", response_model=Dict[str, Any], summary="获取系统概览")
async def get_system_summary(registry: FileTypeRegistry = Depends(get_registry)):
    """获取文件类型系统概览"""
    try:
        result = registry.get_system_summary()
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['message']
            )
        return result
    except Exception as e:
        logger.error(f"获取系统概览失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取系统概览失败: {str(e)}"
        )

@router.get("", response_model=Dict[str, Any], summary="列出所有文件类型")
async def list_file_types(
    enabled_only: bool = False,
    registry: FileTypeRegistry = Depends(get_registry)
):
    """列出所有文件类型配置"""
    try:
        if enabled_only:
            configs = registry.config_manager.get_enabled_configs()
        else:
            configs = registry.list_all_configs()

        return {
            "success": True,
            "file_types": {
                file_type: config.to_dict()
                for file_type, config in configs.items()
            },
            "total_count": len(configs)
        }
    except Exception as e:
        logger.error(f"获取文件类型列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件类型列表失败: {str(e)}"
        )

@router.get("/{file_type}", response_model=Dict[str, Any], summary="获取文件类型配置")
async def get_file_type_config(
    file_type: str,
    registry: FileTypeRegistry = Depends(get_registry)
):
    """获取指定文件类型的配置"""
    try:
        config = registry.get_file_type_config(file_type)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件类型 {file_type} 不存在"
            )

        return {
            "success": True,
            "config": config.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件类型配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件类型配置失败: {str(e)}"
        )

@router.post("", response_model=Dict[str, Any], summary="注册新文件类型")
async def create_file_type(
    request: FileTypeConfigRequest,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """注册新的文件类型"""
    try:
        # 转换为配置对象
        config_dict = request.dict()
        config_dict['created_by'] = current_user
        config = FileTypeConfig.from_dict(config_dict)

        result = registry.register_new_file_type(config)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册文件类型失败: {str(e)}"
        )

@router.put("/{file_type}", response_model=Dict[str, Any], summary="更新文件类型配置")
async def update_file_type_config(
    file_type: str,
    request: FileTypeConfigUpdateRequest,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """更新文件类型配置"""
    try:
        # 只包含非空的字段
        updates = {k: v for k, v in request.dict().items() if v is not None}
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供任何更新字段"
            )

        result = registry.update_file_type_config(file_type, updates)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件类型配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文件类型配置失败: {str(e)}"
        )

@router.delete("/{file_type}", response_model=Dict[str, Any], summary="注销文件类型")
async def unregister_file_type(
    file_type: str,
    force: bool = False,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """注销文件类型"""
    try:
        if file_type == "txt":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除TXT默认文件类型"
            )

        result = registry.unregister_file_type(file_type, force=force)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注销文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注销文件类型失败: {str(e)}"
        )

@router.post("/{file_type}/enable", response_model=Dict[str, Any], summary="启用文件类型")
async def enable_file_type(
    file_type: str,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """启用文件类型"""
    try:
        result = registry.enable_file_type(file_type)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启用文件类型失败: {str(e)}"
        )

@router.post("/{file_type}/disable", response_model=Dict[str, Any], summary="禁用文件类型")
async def disable_file_type(
    file_type: str,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """禁用文件类型"""
    try:
        result = registry.disable_file_type(file_type)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"禁用文件类型失败: {str(e)}"
        )

@router.post("/from-template", response_model=Dict[str, Any], summary="从模板创建文件类型")
async def create_from_template(
    request: TemplateCreateRequest,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """从模板创建新的文件类型"""
    try:
        overrides = request.overrides.copy()
        overrides['created_by'] = current_user

        result = registry.create_file_type_from_template(
            file_type=request.file_type,
            display_name=request.display_name,
            template=request.template,
            **overrides
        )
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"从模板创建文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从模板创建文件类型失败: {str(e)}"
        )

@router.get("/{file_type}/health", response_model=Dict[str, Any], summary="检查文件类型健康状态")
async def check_file_type_health(
    file_type: str,
    registry: FileTypeRegistry = Depends(get_registry)
):
    """检查文件类型健康状态"""
    try:
        result = registry.validate_file_type_health(file_type)
        return result
    except Exception as e:
        logger.error(f"检查文件类型健康状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查健康状态失败: {str(e)}"
        )

@router.post("/{file_type}/repair", response_model=Dict[str, Any], summary="修复文件类型")
async def repair_file_type(
    file_type: str,
    request: RepairRequest,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """修复文件类型"""
    try:
        repair_options = request.dict()
        result = registry.repair_file_type(file_type, repair_options)
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result['message']
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修复文件类型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修复文件类型失败: {str(e)}"
        )

@router.get("/{file_type}/info", response_model=Dict[str, Any], summary="获取文件类型详细信息")
async def get_file_type_info(
    file_type: str,
    include_tables: bool = True,
    include_models: bool = True,
    registry: FileTypeRegistry = Depends(get_registry)
):
    """获取文件类型的详细信息"""
    try:
        result = {
            "success": True,
            "file_type": file_type
        }

        # 获取配置信息
        config = registry.get_file_type_config(file_type)
        if config:
            result["config"] = config.to_dict()
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件类型 {file_type} 不存在"
            )

        # 获取表信息
        if include_tables:
            table_info = registry.table_manager.get_table_info(file_type)
            result["tables"] = table_info

        # 获取模型信息
        if include_models:
            model_info = registry.model_generator.get_model_info(file_type)
            result["models"] = model_info

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件类型信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件类型信息失败: {str(e)}"
        )

@router.get("/configs/validate", response_model=Dict[str, Any], summary="验证所有配置")
async def validate_all_configs(registry: FileTypeRegistry = Depends(get_registry)):
    """验证所有文件类型配置"""
    try:
        results = registry.validate_all_configs()
        return {
            "success": True,
            "validation_results": results
        }
    except Exception as e:
        logger.error(f"验证配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证配置失败: {str(e)}"
        )

@router.get("/configs/export", response_model=Dict[str, Any], summary="导出配置")
async def export_configs(registry: FileTypeRegistry = Depends(get_registry)):
    """导出所有文件类型配置"""
    try:
        result = registry.export_configs()
        return result
    except Exception as e:
        logger.error(f"导出配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出配置失败: {str(e)}"
        )

@router.post("/configs/import", response_model=Dict[str, Any], summary="导入配置")
async def import_configs(
    config_data: Dict[str, Any],
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """导入文件类型配置"""
    try:
        result = registry.import_configs(config_data)
        return result
    except Exception as e:
        logger.error(f"导入配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入配置失败: {str(e)}"
        )

@router.get("/health/all", response_model=Dict[str, Any], summary="获取所有文件类型健康状态")
async def get_all_health_statuses(registry: FileTypeRegistry = Depends(get_registry)):
    """获取所有文件类型的健康状态"""
    try:
        file_types = registry.get_enabled_file_types()
        health_statuses = []

        for file_type in file_types:
            try:
                health_result = registry.validate_file_type_health(file_type)
                health_statuses.append({
                    "file_type": file_type,
                    "config_valid": health_result.get("config_valid", False),
                    "tables_exist": health_result.get("tables_exist", False),
                    "models_generated": health_result.get("models_generated", False),
                    "service_healthy": health_result.get("service_healthy", False),
                    "issues": health_result.get("issues", [])
                })
            except Exception as e:
                health_statuses.append({
                    "file_type": file_type,
                    "config_valid": False,
                    "tables_exist": False,
                    "models_generated": False,
                    "service_healthy": False,
                    "issues": [f"健康检查失败: {str(e)}"]
                })

        return {
            "success": True,
            "health_statuses": health_statuses,
            "total_count": len(health_statuses)
        }
    except Exception as e:
        logger.error(f"获取健康状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取健康状态失败: {str(e)}"
        )

@router.patch("/{file_type}/toggle", response_model=Dict[str, Any], summary="切换文件类型启用状态")
async def toggle_file_type(
    file_type: str,
    enabled: bool,
    registry: FileTypeRegistry = Depends(get_registry),
    current_user: str = Depends(get_current_user)
):
    """切换文件类型的启用状态"""
    try:
        if enabled:
            result = registry.enable_file_type(file_type)
        else:
            result = registry.disable_file_type(file_type)

        return result
    except Exception as e:
        logger.error(f"切换文件类型状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换文件类型状态失败: {str(e)}"
        )