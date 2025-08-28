"""
模拟支付服务 - 用于本地开发测试
Mock Payment Service for Local Development
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from app.core.logging import logger


class MockPaymentService:
    """模拟支付服务"""
    
    def __init__(self):
        self.mock_orders = {}  # 存储模拟订单
    
    def generate_out_trade_no(self, user_id: int) -> str:
        """生成模拟订单号"""
        timestamp = int(datetime.now().timestamp())
        return f"MOCK_{user_id}_{timestamp}"
    
    async def unified_order(
        self, 
        user_id: int, 
        package_type: str,
        package_name: str,
        total_fee: int,  # 单位：分
        trade_type: str = "NATIVE",
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """模拟统一下单"""
        out_trade_no = self.generate_out_trade_no(user_id)
        
        # 模拟微信支付返回
        mock_result = {
            'out_trade_no': out_trade_no,
            'prepay_id': f'wx_prepay_{uuid.uuid4().hex[:16]}',
            'code_url': f'weixin://wxpay/bizpayurl?pr={uuid.uuid4().hex}',  # 模拟二维码URL
            'mweb_url': f'https://wx.tenpay.com/cgi-bin/mmpayweb-bin/checkmweb?prepay_id=wx_prepay_{uuid.uuid4().hex[:16]}'
        }
        
        # 存储模拟订单信息
        self.mock_orders[out_trade_no] = {
            'user_id': user_id,
            'package_type': package_type,
            'package_name': package_name,
            'total_fee': total_fee,
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        logger.info(f"Mock unified order created: {out_trade_no} for user {user_id}")
        return mock_result
    
    async def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """模拟查询订单"""
        if out_trade_no not in self.mock_orders:
            return {
                'return_code': 'SUCCESS',
                'result_code': 'FAIL',
                'err_code': 'ORDERNOTEXIST',
                'err_code_des': '此交易订单号不存在'
            }
        
        order = self.mock_orders[out_trade_no]
        
        # 模拟支付状态变化（创建5分钟后自动"支付成功"）
        if order['status'] == 'pending':
            time_diff = datetime.now() - order['created_at']
            if time_diff.total_seconds() > 300:  # 5分钟后自动成功
                order['status'] = 'SUCCESS'
                order['transaction_id'] = f'4200001234567890{uuid.uuid4().hex[:8]}'
                order['time_end'] = datetime.now().strftime('%Y%m%d%H%M%S')
        
        return {
            'return_code': 'SUCCESS',
            'result_code': 'SUCCESS',
            'trade_state': order['status'],
            'transaction_id': order.get('transaction_id', ''),
            'out_trade_no': out_trade_no,
            'total_fee': order['total_fee'],
            'time_end': order.get('time_end', '')
        }
    
    async def close_order(self, out_trade_no: str) -> bool:
        """模拟关闭订单"""
        if out_trade_no in self.mock_orders:
            self.mock_orders[out_trade_no]['status'] = 'CLOSED'
            logger.info(f"Mock order closed: {out_trade_no}")
            return True
        return False
    
    def process_notify(self, xml_data: str) -> Dict[str, Any]:
        """模拟处理支付通知（本地测试不会收到真实通知）"""
        return {
            'success': True,
            'message': '模拟支付通知',
            'data': {
                'out_trade_no': 'mock_order_123',
                'transaction_id': '4200001234567890',
                'total_fee': 1000,
                'time_end': datetime.now().strftime('%Y%m%d%H%M%S'),
                'openid': 'mock_openid',
                'raw_data': xml_data
            }
        }
    
    def create_success_response(self) -> str:
        """创建成功响应"""
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'
    
    def create_fail_response(self, msg: str = 'FAIL') -> str:
        """创建失败响应"""
        return f'<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[{msg}]]></return_msg></xml>'
    
    def simulate_payment_success(self, out_trade_no: str) -> bool:
        """手动模拟支付成功（测试用）"""
        if out_trade_no in self.mock_orders:
            order = self.mock_orders[out_trade_no]
            order['status'] = 'SUCCESS'
            order['transaction_id'] = f'4200001234567890{uuid.uuid4().hex[:8]}'
            order['time_end'] = datetime.now().strftime('%Y%m%d%H%M%S')
            logger.info(f"Mock payment success simulated: {out_trade_no}")
            return True
        return False


# 创建模拟支付服务实例
mock_payment_service = MockPaymentService()