"""
TXT文件处理器相关的API路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.services.txt_processors.processor_factory import get_processor_factory

router = APIRouter(prefix="/api/v1/txt-processors", tags=["txt-processors"])


@router.get("/list")
async def list_processors() -> List[Dict[str, str]]:
    """
    获取所有可用的TXT文件处理器列表

    Returns:
        List[Dict]: 处理器信息列表
    """
    try:
        factory = get_processor_factory()
        processors = factory.list_processors()

        return processors

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理器列表失败: {str(e)}")


@router.get("/processors/{processor_type}/info")
async def get_processor_info(processor_type: str) -> Dict[str, Any]:
    """
    获取指定处理器的详细信息

    Args:
        processor_type: 处理器类型

    Returns:
        Dict: 处理器详细信息
    """
    try:
        factory = get_processor_factory()
        processor = factory.get_processor_by_type(processor_type)

        if not processor:
            raise HTTPException(status_code=404, detail=f"未找到处理器类型: {processor_type}")

        return processor.get_processor_info()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取处理器信息失败: {str(e)}")


@router.post("/test")
async def test_processor_selection(
    content: str,
    filename: str = None
) -> Dict[str, Any]:
    """
    测试处理器选择逻辑

    Args:
        content: 文件内容
        filename: 文件名（可选）

    Returns:
        Dict: 选择结果和所有处理器的评分
    """
    try:
        factory = get_processor_factory()

        # 获取最佳处理器
        best_processor = factory.get_best_processor(content, filename)

        # 测试所有处理器的评分
        all_scores = []
        for processor in factory._processors:
            try:
                can_process, confidence = processor.can_process(content, filename)
                all_scores.append({
                    'processor_type': processor.processor_type,
                    'description': processor.description,
                    'can_process': can_process,
                    'confidence': confidence
                })
            except Exception as e:
                all_scores.append({
                    'processor_type': processor.processor_type,
                    'description': processor.description,
                    'can_process': False,
                    'confidence': 0.0,
                    'error': str(e)
                })

        # 按置信度排序
        all_scores.sort(key=lambda x: x['confidence'], reverse=True)

        result = {
            'selected_processor': best_processor.processor_type if best_processor else None,
            'selected_confidence': 0.0,
            'all_scores': all_scores
        }

        if best_processor:
            can_process, confidence = best_processor.can_process(content, filename)
            result['selected_confidence'] = confidence

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试处理器选择失败: {str(e)}")