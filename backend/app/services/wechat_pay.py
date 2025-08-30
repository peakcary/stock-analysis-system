"""
微信支付服务类
WeChat Pay Service
"""

import hashlib
import hmac
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import requests
import json
import uuid
from urllib.parse import urlencode

from app.core.config import settings
from app.core.logging import logger


class WechatPayException(Exception):
    """微信支付异常"""
    pass


class WechatPayService:
    """微信支付服务"""
    
    def __init__(self):
        self.appid = settings.WECHAT_APPID or "mock_appid"
        self.mch_id = settings.WECHAT_MCH_ID or "mock_mch_id"
        self.api_key = settings.WECHAT_API_KEY or "mock_api_key"
        self.notify_url = f"{settings.BASE_URL}/api/v1/payment/notify"
        self.mock_mode = settings.PAYMENT_MOCK_MODE
        
        # API URLs
        self.unified_order_url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
        self.order_query_url = "https://api.mch.weixin.qq.com/pay/orderquery"
        self.close_order_url = "https://api.mch.weixin.qq.com/pay/closeorder"
        self.refund_url = "https://api.mch.weixin.qq.com/secapi/pay/refund"
        self.refund_query_url = "https://api.mch.weixin.qq.com/pay/refundquery"

    def generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        return uuid.uuid4().hex[:length]

    def generate_out_trade_no(self, user_id: int) -> str:
        """生成商户订单号"""
        timestamp = int(datetime.now().timestamp())
        return f"SA_{user_id}_{timestamp}"

    def generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 过滤空值并排序
        filtered_params = {k: v for k, v in params.items() if v is not None and v != ""}
        sorted_params = sorted(filtered_params.items())
        
        # 拼接字符串
        string_a = "&".join([f"{k}={v}" for k, v in sorted_params])
        string_sign_temp = f"{string_a}&key={self.api_key}"
        
        # MD5加密并转大写
        sign = hashlib.md5(string_sign_temp.encode('utf-8')).hexdigest().upper()
        logger.info(f"Generate sign: {string_a} -> {sign}")
        return sign

    def verify_sign(self, params: Dict[str, Any]) -> bool:
        """验证签名"""
        if 'sign' not in params:
            return False
        
        received_sign = params.pop('sign')
        calculated_sign = self.generate_sign(params)
        
        # 恢复sign参数
        params['sign'] = received_sign
        
        is_valid = received_sign == calculated_sign
        logger.info(f"Verify sign: received={received_sign}, calculated={calculated_sign}, valid={is_valid}")
        return is_valid

    def dict_to_xml(self, data: Dict[str, Any]) -> str:
        """字典转XML"""
        xml_items = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                xml_items.append(f"<{key}>{value}</{key}>")
            else:
                xml_items.append(f"<{key}><![CDATA[{value}]]></{key}>")
        
        xml_content = "".join(xml_items)
        return f"<xml>{xml_content}</xml>"

    def xml_to_dict(self, xml_data: str) -> Dict[str, Any]:
        """XML转字典"""
        try:
            root = ET.fromstring(xml_data)
            result = {}
            
            for child in root:
                if child.text:
                    # 尝试转换为数字
                    try:
                        if '.' in child.text:
                            result[child.tag] = float(child.text)
                        else:
                            result[child.tag] = int(child.text)
                    except ValueError:
                        result[child.tag] = child.text
                else:
                    result[child.tag] = ""
            
            return result
        except ET.ParseError as e:
            logger.error(f"XML parse error: {e}, xml_data: {xml_data}")
            raise WechatPayException(f"XML解析失败: {e}")

    async def unified_order(
        self, 
        user_id: int, 
        package_type: str,
        package_name: str,
        total_fee: int,  # 单位：分
        trade_type: str = "NATIVE",
        client_ip: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """统一下单"""
        out_trade_no = self.generate_out_trade_no(user_id)
        
        # 模拟支付模式
        if self.mock_mode:
            logger.info(f"[MOCK MODE] Creating payment order for user {user_id}, package {package_type}, amount {total_fee}")
            
            # 生成模拟的支付链接
            mock_code_url = f"weixin://wxpay/bizpayurl?pr=mock_{out_trade_no}"
            mock_h5_url = f"{settings.BASE_URL}/mock/payment/{out_trade_no}"
            
            return {
                'out_trade_no': out_trade_no,
                'prepay_id': f'mock_prepay_{uuid.uuid4().hex[:16]}',
                'code_url': mock_code_url if trade_type == "NATIVE" else None,
                'mweb_url': mock_h5_url if trade_type == "MWEB" else None,
                'mock_mode': True
            }
        
        params = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
            'body': f'股票分析系统-{package_name}',
            'detail': f'用户ID: {user_id}, 套餐: {package_type}',
            'out_trade_no': out_trade_no,
            'total_fee': total_fee,
            'spbill_create_ip': client_ip,
            'notify_url': self.notify_url,
            'trade_type': trade_type,
        }
        
        # H5支付需要额外参数
        if trade_type == "MWEB":
            params['scene_info'] = json.dumps({
                "h5_info": {
                    "type": "Wap",
                    "wap_url": settings.BASE_URL,
                    "wap_name": "股票分析系统"
                }
            })
        
        # 生成签名
        params['sign'] = self.generate_sign(params)
        
        # 转换为XML并发送请求
        xml_data = self.dict_to_xml(params)
        logger.info(f"Unified order request: {xml_data}")
        
        try:
            response = requests.post(
                self.unified_order_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            response.raise_for_status()
            
            # 解析响应
            result = self.xml_to_dict(response.text)
            logger.info(f"Unified order response: {result}")
            
            if result.get('return_code') != 'SUCCESS':
                raise WechatPayException(f"微信支付请求失败: {result.get('return_msg', '未知错误')}")
            
            if result.get('result_code') != 'SUCCESS':
                error_msg = result.get('err_code_des') or result.get('err_code', '业务失败')
                raise WechatPayException(f"微信支付业务失败: {error_msg}")
            
            # 验证签名
            if not self.verify_sign(result):
                raise WechatPayException("微信支付响应签名验证失败")
            
            return {
                'out_trade_no': out_trade_no,
                'prepay_id': result.get('prepay_id'),
                'code_url': result.get('code_url'),  # NATIVE支付
                'mweb_url': result.get('mweb_url'),  # H5支付
            }
            
        except requests.RequestException as e:
            logger.error(f"Wechat pay request error: {e}")
            raise WechatPayException(f"微信支付请求异常: {e}")

    async def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """查询订单"""
        # 模拟支付模式
        if self.mock_mode:
            logger.info(f"[MOCK MODE] Querying order: {out_trade_no}")
            
            # 模拟订单状态（可以在实际应用中根据需要设置）
            return {
                'return_code': 'SUCCESS',
                'result_code': 'SUCCESS',
                'out_trade_no': out_trade_no,
                'trade_state': 'NOTPAY',  # 默认未支付状态
                'trade_state_desc': '订单未支付',
                'total_fee': 0,
                'mock_mode': True
            }
            
        params = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'out_trade_no': out_trade_no,
            'nonce_str': self.generate_nonce_str(),
        }
        
        params['sign'] = self.generate_sign(params)
        xml_data = self.dict_to_xml(params)
        
        try:
            response = requests.post(
                self.order_query_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            response.raise_for_status()
            
            result = self.xml_to_dict(response.text)
            logger.info(f"Query order response: {result}")
            
            if result.get('return_code') != 'SUCCESS':
                raise WechatPayException(f"查询订单失败: {result.get('return_msg', '未知错误')}")
            
            if not self.verify_sign(result):
                raise WechatPayException("查询订单响应签名验证失败")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Query order error: {e}")
            raise WechatPayException(f"查询订单异常: {e}")

    async def mock_payment_success(self, out_trade_no: str, total_fee: int) -> Dict[str, Any]:
        """模拟支付成功（用于开发测试）"""
        if not self.mock_mode:
            raise WechatPayException("非模拟模式不能调用此方法")
            
        logger.info(f"[MOCK MODE] Simulating payment success for order: {out_trade_no}")
        
        # 模拟微信支付成功通知数据
        mock_notify_data = {
            'return_code': 'SUCCESS',
            'result_code': 'SUCCESS',
            'out_trade_no': out_trade_no,
            'transaction_id': f'mock_wx_{uuid.uuid4().hex[:16]}',
            'total_fee': total_fee,
            'time_end': datetime.now().strftime('%Y%m%d%H%M%S'),
            'openid': f'mock_openid_{uuid.uuid4().hex[:16]}',
            'mock_mode': True
        }
        
        return {
            'success': True,
            'message': '模拟支付成功',
            'data': mock_notify_data
        }

    async def close_order(self, out_trade_no: str) -> bool:
        """关闭订单"""
        params = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'out_trade_no': out_trade_no,
            'nonce_str': self.generate_nonce_str(),
        }
        
        params['sign'] = self.generate_sign(params)
        xml_data = self.dict_to_xml(params)
        
        try:
            response = requests.post(
                self.close_order_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            response.raise_for_status()
            
            result = self.xml_to_dict(response.text)
            logger.info(f"Close order response: {result}")
            
            return (
                result.get('return_code') == 'SUCCESS' and 
                result.get('result_code') == 'SUCCESS'
            )
            
        except requests.RequestException as e:
            logger.error(f"Close order error: {e}")
            return False

    def process_notify(self, xml_data: str) -> Dict[str, Any]:
        """处理支付通知"""
        try:
            data = self.xml_to_dict(xml_data)
            logger.info(f"Payment notify data: {data}")
            
            # 验证签名
            if not self.verify_sign(data):
                logger.error("Payment notify signature verification failed")
                return {
                    'success': False,
                    'message': '签名验证失败',
                    'data': data
                }
            
            # 检查支付结果
            if (data.get('return_code') == 'SUCCESS' and 
                data.get('result_code') == 'SUCCESS'):
                
                return {
                    'success': True,
                    'message': '支付成功',
                    'data': {
                        'out_trade_no': data.get('out_trade_no'),
                        'transaction_id': data.get('transaction_id'),
                        'total_fee': data.get('total_fee'),
                        'time_end': data.get('time_end'),
                        'openid': data.get('openid', ''),
                        'raw_data': data
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f"支付失败: {data.get('err_code_des', data.get('return_msg', '未知错误'))}",
                    'data': data
                }
                
        except Exception as e:
            logger.error(f"Process notify error: {e}")
            return {
                'success': False,
                'message': f'处理支付通知异常: {e}',
                'data': {}
            }

    def create_success_response(self) -> str:
        """创建成功响应XML"""
        return '<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>'

    def create_fail_response(self, msg: str = 'FAIL') -> str:
        """创建失败响应XML"""
        return f'<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[{msg}]]></return_msg></xml>'

    def generate_out_refund_no(self, order_id: int) -> str:
        """生成退款订单号"""
        timestamp = int(datetime.now().timestamp())
        return f"RF_SA_{order_id}_{timestamp}"

    async def apply_refund(self, out_trade_no: str, total_fee: int, refund_fee: int, 
                          refund_reason: str = "用户申请退款") -> Dict[str, Any]:
        """申请退款"""
        try:
            import ssl
            import os
            
            # 检查证书文件是否存在
            cert_path = settings.WECHAT_CERT_PATH
            key_path = settings.WECHAT_KEY_PATH
            
            if not cert_path or not os.path.exists(cert_path):
                raise WechatPayException("微信商户证书文件未找到，请配置WECHAT_CERT_PATH")
            if not key_path or not os.path.exists(key_path):
                raise WechatPayException("微信商户私钥文件未找到，请配置WECHAT_KEY_PATH")
            
            out_refund_no = self.generate_out_refund_no(out_trade_no)
            
            params = {
                'appid': self.appid,
                'mch_id': self.mch_id,
                'nonce_str': self.generate_nonce_str(),
                'out_trade_no': out_trade_no,
                'out_refund_no': out_refund_no,
                'total_fee': total_fee,
                'refund_fee': refund_fee,
                'refund_desc': refund_reason,
                'notify_url': f"{settings.BASE_URL}/api/v1/payment/refund/notify"
            }
            
            params['sign'] = self.generate_sign(params)
            xml_data = self.dict_to_xml(params)
            
            logger.info(f"Apply refund params: {params}")
            
            # 使用证书进行请求
            response = requests.post(
                self.refund_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                cert=(cert_path, key_path),
                timeout=30
            )
            response.raise_for_status()
            
            result = self.xml_to_dict(response.text)
            logger.info(f"Refund response: {result}")
            
            if result.get('return_code') != 'SUCCESS':
                raise WechatPayException(f"退款申请失败: {result.get('return_msg', '未知错误')}")
            
            if result.get('result_code') != 'SUCCESS':
                error_code = result.get('err_code', '')
                error_msg = result.get('err_code_des', '未知错误')
                raise WechatPayException(f"退款失败[{error_code}]: {error_msg}")
            
            # 验证签名
            if not self.verify_sign(result):
                raise WechatPayException("退款响应签名验证失败")
            
            return {
                'out_refund_no': result.get('out_refund_no'),
                'refund_id': result.get('refund_id'),
                'refund_fee': result.get('refund_fee'),
                'settlement_refund_fee': result.get('settlement_refund_fee'),
                'total_fee': result.get('total_fee'),
                'settlement_total_fee': result.get('settlement_total_fee'),
                'refund_channel': result.get('refund_channel'),
                'refund_status': 'PROCESSING'  # 退款处理中
            }
            
        except requests.RequestException as e:
            logger.error(f"Refund request error: {e}")
            raise WechatPayException(f"退款请求异常: {e}")

    async def query_refund(self, out_trade_no: str = None, out_refund_no: str = None) -> Dict[str, Any]:
        """查询退款"""
        if not out_trade_no and not out_refund_no:
            raise WechatPayException("商户订单号和退款订单号至少提供一个")
        
        params = {
            'appid': self.appid,
            'mch_id': self.mch_id,
            'nonce_str': self.generate_nonce_str(),
        }
        
        if out_trade_no:
            params['out_trade_no'] = out_trade_no
        if out_refund_no:
            params['out_refund_no'] = out_refund_no
        
        params['sign'] = self.generate_sign(params)
        xml_data = self.dict_to_xml(params)
        
        try:
            response = requests.post(
                self.refund_query_url,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            response.raise_for_status()
            
            result = self.xml_to_dict(response.text)
            logger.info(f"Query refund response: {result}")
            
            if result.get('return_code') != 'SUCCESS':
                raise WechatPayException(f"查询退款失败: {result.get('return_msg', '未知错误')}")
            
            if not self.verify_sign(result):
                raise WechatPayException("查询退款响应签名验证失败")
            
            return result
            
        except requests.RequestException as e:
            logger.error(f"Query refund error: {e}")
            raise WechatPayException(f"查询退款异常: {e}")

    async def process_refund_notify(self, xml_data: str) -> Dict[str, Any]:
        """处理退款通知"""
        try:
            # 解析XML数据
            data = self.xml_to_dict(xml_data)
            logger.info(f"Received refund notify: {data}")
            
            # 验证签名
            if not self.verify_sign(data):
                logger.error("Refund notify signature verification failed")
                return {
                    'success': False,
                    'message': '签名验证失败',
                    'data': {}
                }
            
            # 检查通知状态
            if data.get('return_code') != 'SUCCESS':
                logger.error(f"Refund notify return_code error: {data.get('return_msg')}")
                return {
                    'success': False,
                    'message': data.get('return_msg', '退款通知失败'),
                    'data': {}
                }
            
            # 解析退款结果
            req_info = data.get('req_info', '')
            if req_info:
                # 解密req_info（需要使用MD5(API密钥)作为密钥）
                import base64
                from Crypto.Cipher import AES
                
                key = hashlib.md5(self.api_key.encode()).digest()
                cipher = AES.new(key, AES.MODE_ECB)
                decrypted_data = cipher.decrypt(base64.b64decode(req_info))
                
                # 去除填充
                decrypted_data = decrypted_data.rstrip(b'\x00')
                refund_info = self.xml_to_dict(decrypted_data.decode('utf-8'))
                
                return {
                    'success': True,
                    'message': '退款通知处理成功',
                    'data': {
                        'out_trade_no': refund_info.get('out_trade_no'),
                        'out_refund_no': refund_info.get('out_refund_no'),
                        'refund_id': refund_info.get('refund_id'),
                        'refund_fee': refund_info.get('refund_fee'),
                        'settlement_refund_fee': refund_info.get('settlement_refund_fee'),
                        'refund_status': refund_info.get('refund_status'),
                        'success_time': refund_info.get('success_time'),
                        'refund_recv_accout': refund_info.get('refund_recv_accout'),
                        'refund_account': refund_info.get('refund_account'),
                        'refund_request_source': refund_info.get('refund_request_source')
                    }
                }
            else:
                return {
                    'success': False,
                    'message': '退款通知数据不完整',
                    'data': {}
                }
                
        except Exception as e:
            logger.error(f"Process refund notify error: {e}")
            return {
                'success': False,
                'message': f'处理退款通知异常: {e}',
                'data': {}
            }


# 创建全局实例
wechat_pay_service = WechatPayService()