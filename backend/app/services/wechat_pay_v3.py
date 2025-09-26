"""
微信支付API V3服务
WeChat Pay API V3 Service

支持微信支付API V3版本，包括NATIVE支付、H5支付等
"""

import hashlib
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import requests
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64

from app.core.config import settings
from app.core.logging import logger


class WechatPayV3Exception(Exception):
    """微信支付V3异常"""
    pass


class WechatPayV3Service:
    """微信支付API V3服务"""

    def __init__(self):
        self.appid = settings.WECHAT_APPID
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_v3_key = settings.WECHAT_API_V3_KEY or settings.WECHAT_API_KEY
        self.cert_serial = settings.WECHAT_CERT_SERIAL
        self.cert_path = settings.WECHAT_CERT_PATH
        self.key_path = settings.WECHAT_KEY_PATH
        self.notify_url = settings.WECHAT_NOTIFY_URL or f"{settings.BASE_URL}/api/v1/payment/notify"

        # API URLs (V3)
        self.base_url = "https://api.mch.weixin.qq.com"
        self.native_pay_url = f"{self.base_url}/v3/pay/transactions/native"
        self.h5_pay_url = f"{self.base_url}/v3/pay/transactions/h5"
        self.query_order_url = f"{self.base_url}/v3/pay/transactions/out-trade-no"
        self.close_order_url = f"{self.base_url}/v3/pay/transactions/out-trade-no"
        self.refund_url = f"{self.base_url}/v3/refund/domestic/refunds"

        # 验证配置
        self._validate_config()

    def _validate_config(self):
        """验证配置"""
        if settings.PAYMENT_MOCK_MODE:
            logger.info("微信支付运行在模拟模式")
            return

        required_configs = {
            'WECHAT_APPID': self.appid,
            'WECHAT_MCH_ID': self.mch_id,
            'WECHAT_API_V3_KEY': self.api_v3_key,
            'WECHAT_CERT_SERIAL': self.cert_serial
        }

        missing_configs = [key for key, value in required_configs.items() if not value]

        if missing_configs:
            raise WechatPayV3Exception(f"缺少必需配置: {', '.join(missing_configs)}")

        # 验证证书文件
        import os
        cert_issues = []

        if not self.cert_path:
            cert_issues.append("未配置证书路径 (WECHAT_CERT_PATH)")
        elif not os.path.exists(self.cert_path):
            cert_issues.append(f"证书文件不存在: {self.cert_path}")
        elif not os.path.isfile(self.cert_path):
            cert_issues.append(f"证书路径不是文件: {self.cert_path}")

        if not self.key_path:
            cert_issues.append("未配置私钥路径 (WECHAT_KEY_PATH)")
        elif not os.path.exists(self.key_path):
            cert_issues.append(f"私钥文件不存在: {self.key_path}")
        elif not os.path.isfile(self.key_path):
            cert_issues.append(f"私钥路径不是文件: {self.key_path}")

        if cert_issues:
            error_msg = "\n".join([
                "微信支付V3证书配置错误:",
                *[f"  - {issue}" for issue in cert_issues],
                "",
                "解决方案:",
                "  1. 从微信商户平台下载API证书",
                "  2. 将证书文件放在 backend/certs/ 目录下",
                "  3. 配置环境变量 WECHAT_CERT_PATH 和 WECHAT_KEY_PATH",
                "  4. 参考 backend/certs/README.md 获取详细说明"
            ])
            raise WechatPayV3Exception(error_msg)

        # 尝试读取证书验证格式
        try:
            with open(self.cert_path, 'r') as f:
                cert_content = f.read()
            if not cert_content.strip().startswith('-----BEGIN CERTIFICATE-----'):
                cert_issues.append("证书文件格式错误，需要PEM格式")
        except Exception as e:
            cert_issues.append(f"无法读取证书文件: {e}")

        try:
            with open(self.key_path, 'r') as f:
                key_content = f.read()
            if not key_content.strip().startswith('-----BEGIN'):
                cert_issues.append("私钥文件格式错误，需要PEM格式")
        except Exception as e:
            cert_issues.append(f"无法读取私钥文件: {e}")

        if cert_issues:
            logger.error(f"证书验证失败: {'; '.join(cert_issues)}")
            raise WechatPayV3Exception(f"证书验证失败: {'; '.join(cert_issues)}")

        logger.info("微信支付V3证书配置验证通过")

    def get_config_status(self) -> dict:
        """获取配置状态"""
        import os
        status = {
            'api_version': 'v3',
            'mock_mode': settings.PAYMENT_MOCK_MODE,
            'appid_configured': bool(self.appid),
            'mch_id_configured': bool(self.mch_id),
            'api_key_configured': bool(self.api_v3_key),
            'cert_serial_configured': bool(self.cert_serial),
            'cert_file_exists': bool(self.cert_path and os.path.exists(self.cert_path)),
            'key_file_exists': bool(self.key_path and os.path.exists(self.key_path)),
            'cert_path': self.cert_path or '未配置',
            'key_path': self.key_path or '未配置'
        }

        # 计算整体状态
        if settings.PAYMENT_MOCK_MODE:
            status['overall_status'] = 'mock_mode'
        elif all([
            status['appid_configured'],
            status['mch_id_configured'],
            status['api_key_configured'],
            status['cert_serial_configured'],
            status['cert_file_exists'],
            status['key_file_exists']
        ]):
            status['overall_status'] = 'ready'
        else:
            status['overall_status'] = 'incomplete'

        return status

    def _generate_authorization(self, method: str, url_path: str, request_body: str = "") -> str:
        """生成Authorization头"""
        try:
            import os
            if not os.path.exists(self.key_path):
                raise WechatPayV3Exception(f"商户私钥文件不存在: {self.key_path}")

            # 读取私钥
            with open(self.key_path, 'r') as f:
                private_key_content = f.read()

            private_key = RSA.import_key(private_key_content)

            # 构造签名字符串
            timestamp = str(int(time.time()))
            nonce_str = uuid.uuid4().hex[:32]

            sign_str = f"{method}\n{url_path}\n{timestamp}\n{nonce_str}\n{request_body}\n"

            # 生成签名
            hash_obj = SHA256.new(sign_str.encode('utf-8'))
            signature = pkcs1_15.new(private_key).sign(hash_obj)
            sign_b64 = base64.b64encode(signature).decode('utf-8')

            # 构造Authorization
            authorization = (
                f'WECHATPAY2-SHA256-RSA2048 '
                f'mchid="{self.mch_id}",'
                f'nonce_str="{nonce_str}",'
                f'signature="{sign_b64}",'
                f'timestamp="{timestamp}",'
                f'serial_no="{self.cert_serial}"'
            )

            return authorization

        except Exception as e:
            logger.error(f"Generate authorization error: {e}")
            raise WechatPayV3Exception(f"生成签名失败: {e}")

    def generate_out_trade_no(self, user_id: int) -> str:
        """生成商户订单号"""
        timestamp = int(datetime.now().timestamp())
        return f"SA_{user_id}_{timestamp}_{uuid.uuid4().hex[:6]}"

    async def create_native_payment(
        self,
        user_id: int,
        package_type: str,
        package_name: str,
        total_amount: int,  # 单位：分
        description: str = None
    ) -> Dict[str, Any]:
        """创建NATIVE支付订单"""
        try:
            out_trade_no = self.generate_out_trade_no(user_id)

            # 模拟模式
            if settings.PAYMENT_MOCK_MODE:
                return {
                    'out_trade_no': out_trade_no,
                    'code_url': f"weixin://wxpay/bizpayurl?pr=mock_{out_trade_no}",
                    'mock_mode': True
                }

            # 构造请求数据
            request_data = {
                "appid": self.appid,
                "mchid": self.mch_id,
                "description": description or f"股票分析系统-{package_name}",
                "out_trade_no": out_trade_no,
                "notify_url": self.notify_url,
                "amount": {
                    "total": total_amount,
                    "currency": "CNY"
                }
            }

            request_body = json.dumps(request_data, separators=(',', ':'))
            url_path = "/v3/pay/transactions/native"

            # 生成请求头
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': self._generate_authorization('POST', url_path, request_body),
                'User-Agent': 'Stock-Analysis-System/1.0'
            }

            logger.info(f"Native payment request: {request_data}")

            # 发送请求
            response = requests.post(
                self.native_pay_url,
                headers=headers,
                data=request_body,
                timeout=30
            )

            response_data = response.json()
            logger.info(f"Native payment response: {response_data}")

            if response.status_code == 200:
                return {
                    'out_trade_no': out_trade_no,
                    'code_url': response_data.get('code_url'),
                    'mock_mode': False
                }
            else:
                error_code = response_data.get('code', 'UNKNOWN')
                error_msg = response_data.get('message', '未知错误')
                raise WechatPayV3Exception(f"创建支付订单失败[{error_code}]: {error_msg}")

        except requests.RequestException as e:
            logger.error(f"Native payment request error: {e}")
            raise WechatPayV3Exception(f"网络请求异常: {e}")

    async def create_h5_payment(
        self,
        user_id: int,
        package_type: str,
        package_name: str,
        total_amount: int,  # 单位：分
        client_ip: str,
        description: str = None
    ) -> Dict[str, Any]:
        """创建H5支付订单"""
        try:
            out_trade_no = self.generate_out_trade_no(user_id)

            # 模拟模式
            if settings.PAYMENT_MOCK_MODE:
                return {
                    'out_trade_no': out_trade_no,
                    'h5_url': f"{settings.BASE_URL}/mock/payment/{out_trade_no}",
                    'mock_mode': True
                }

            # 构造请求数据
            request_data = {
                "appid": self.appid,
                "mchid": self.mch_id,
                "description": description or f"股票分析系统-{package_name}",
                "out_trade_no": out_trade_no,
                "notify_url": self.notify_url,
                "amount": {
                    "total": total_amount,
                    "currency": "CNY"
                },
                "scene_info": {
                    "payer_client_ip": client_ip,
                    "h5_info": {
                        "type": "Wap",
                        "app_name": "股票分析系统",
                        "app_url": settings.BASE_URL
                    }
                }
            }

            request_body = json.dumps(request_data, separators=(',', ':'))
            url_path = "/v3/pay/transactions/h5"

            # 生成请求头
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': self._generate_authorization('POST', url_path, request_body),
                'User-Agent': 'Stock-Analysis-System/1.0'
            }

            logger.info(f"H5 payment request: {request_data}")

            # 发送请求
            response = requests.post(
                self.h5_pay_url,
                headers=headers,
                data=request_body,
                timeout=30
            )

            response_data = response.json()
            logger.info(f"H5 payment response: {response_data}")

            if response.status_code == 200:
                return {
                    'out_trade_no': out_trade_no,
                    'h5_url': response_data.get('h5_url'),
                    'mock_mode': False
                }
            else:
                error_code = response_data.get('code', 'UNKNOWN')
                error_msg = response_data.get('message', '未知错误')
                raise WechatPayV3Exception(f"创建H5支付订单失败[{error_code}]: {error_msg}")

        except requests.RequestException as e:
            logger.error(f"H5 payment request error: {e}")
            raise WechatPayV3Exception(f"网络请求异常: {e}")

    async def query_order(self, out_trade_no: str) -> Dict[str, Any]:
        """查询订单状态"""
        try:
            # 模拟模式
            if settings.PAYMENT_MOCK_MODE:
                return {
                    'out_trade_no': out_trade_no,
                    'trade_state': 'NOTPAY',
                    'trade_state_desc': '订单未支付',
                    'mock_mode': True
                }

            url_path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}"
            query_url = f"{self.query_order_url}/{out_trade_no}?mchid={self.mch_id}"

            # 生成请求头
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': self._generate_authorization('GET', url_path + f"?mchid={self.mch_id}"),
                'User-Agent': 'Stock-Analysis-System/1.0'
            }

            # 发送请求
            response = requests.get(query_url, headers=headers, timeout=30)
            response_data = response.json()

            logger.info(f"Query order response: {response_data}")

            if response.status_code == 200:
                return {
                    'out_trade_no': response_data.get('out_trade_no'),
                    'transaction_id': response_data.get('transaction_id'),
                    'trade_state': response_data.get('trade_state'),
                    'trade_state_desc': response_data.get('trade_state_desc'),
                    'amount': response_data.get('amount', {}),
                    'payer': response_data.get('payer', {}),
                    'success_time': response_data.get('success_time'),
                    'mock_mode': False
                }
            elif response.status_code == 404:
                return {
                    'out_trade_no': out_trade_no,
                    'trade_state': 'NOTFOUND',
                    'trade_state_desc': '订单不存在',
                    'mock_mode': False
                }
            else:
                error_code = response_data.get('code', 'UNKNOWN')
                error_msg = response_data.get('message', '未知错误')
                raise WechatPayV3Exception(f"查询订单失败[{error_code}]: {error_msg}")

        except requests.RequestException as e:
            logger.error(f"Query order request error: {e}")
            raise WechatPayV3Exception(f"查询订单网络异常: {e}")

    async def close_order(self, out_trade_no: str) -> bool:
        """关闭订单"""
        try:
            if settings.PAYMENT_MOCK_MODE:
                return True

            request_data = {"mchid": self.mch_id}
            request_body = json.dumps(request_data, separators=(',', ':'))
            url_path = f"/v3/pay/transactions/out-trade-no/{out_trade_no}/close"

            # 生成请求头
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': self._generate_authorization('POST', url_path, request_body),
                'User-Agent': 'Stock-Analysis-System/1.0'
            }

            close_url = f"{self.close_order_url}/{out_trade_no}/close"

            response = requests.post(
                close_url,
                headers=headers,
                data=request_body,
                timeout=30
            )

            logger.info(f"Close order response: {response.status_code}")

            return response.status_code == 204

        except requests.RequestException as e:
            logger.error(f"Close order request error: {e}")
            return False

    def verify_notify_signature(self, headers: dict, body: str) -> bool:
        """验证回调签名"""
        try:
            # 获取签名相关信息
            signature = headers.get('Wechatpay-Signature')
            timestamp = headers.get('Wechatpay-Timestamp')
            nonce = headers.get('Wechatpay-Nonce')
            cert_serial = headers.get('Wechatpay-Serial')

            if not all([signature, timestamp, nonce, cert_serial]):
                logger.error("Missing signature headers")
                return False

            # 构造验证字符串
            sign_str = f"{timestamp}\n{nonce}\n{body}\n"

            # TODO: 这里需要使用微信支付平台公钥验证签名
            # 实际应用中需要先获取微信支付平台证书来验证签名
            # 现在先简单验证一下基本格式
            if len(signature) > 10 and timestamp.isdigit() and len(nonce) > 10:
                logger.info("Signature format validation passed")
                return True
            else:
                logger.error("Signature format validation failed")
                return False

        except Exception as e:
            logger.error(f"Verify notify signature error: {e}")
            return False

    def process_notify(self, headers: dict, body: str) -> Dict[str, Any]:
        """处理支付通知"""
        try:
            # 验证签名
            if not settings.PAYMENT_MOCK_MODE and not self.verify_notify_signature(headers, body):
                return {
                    'success': False,
                    'message': '签名验证失败',
                    'data': {}
                }

            # 解析通知数据
            notify_data = json.loads(body)
            logger.info(f"Payment notify data: {notify_data}")

            # 解密resource数据（如果需要）
            resource = notify_data.get('resource', {})
            ciphertext = resource.get('ciphertext')

            if ciphertext:
                # TODO: 解密resource数据
                # 实际应用中需要使用API v3密钥解密
                decrypted_data = self._decrypt_resource(resource)
                if decrypted_data:
                    notify_data.update(decrypted_data)

            # 检查事件类型和支付状态
            event_type = notify_data.get('event_type')
            if event_type == 'TRANSACTION.SUCCESS':
                return {
                    'success': True,
                    'message': '支付成功',
                    'data': {
                        'out_trade_no': notify_data.get('out_trade_no'),
                        'transaction_id': notify_data.get('transaction_id'),
                        'total_fee': notify_data.get('amount', {}).get('total', 0),
                        'success_time': notify_data.get('success_time'),
                        'payer_openid': notify_data.get('payer', {}).get('openid', ''),
                        'raw_data': notify_data
                    }
                }
            else:
                return {
                    'success': False,
                    'message': f'不支持的事件类型: {event_type}',
                    'data': notify_data
                }

        except json.JSONDecodeError as e:
            logger.error(f"Parse notify data error: {e}")
            return {
                'success': False,
                'message': '通知数据格式错误',
                'data': {}
            }
        except Exception as e:
            logger.error(f"Process notify error: {e}")
            return {
                'success': False,
                'message': f'处理支付通知异常: {e}',
                'data': {}
            }

    def _decrypt_resource(self, resource: dict) -> Optional[dict]:
        """解密resource数据"""
        try:
            from Crypto.Cipher import AES
            import base64

            # 获取加密数据
            ciphertext = resource.get('ciphertext', '')
            associated_data = resource.get('associated_data', '')
            nonce = resource.get('nonce', '')

            if not all([ciphertext, nonce]):
                return None

            # 解密（使用API v3密钥）
            key = self.api_v3_key.encode('utf-8')
            cipher = AES.new(key, AES.MODE_GCM, nonce.encode('utf-8'))

            if associated_data:
                cipher.update(associated_data.encode('utf-8'))

            decrypted_data = cipher.decrypt(base64.b64decode(ciphertext))

            return json.loads(decrypted_data.decode('utf-8'))

        except Exception as e:
            logger.error(f"Decrypt resource error: {e}")
            return None

    def create_notify_response(self, success: bool = True) -> dict:
        """创建通知响应"""
        if success:
            return {"code": "SUCCESS", "message": "成功"}
        else:
            return {"code": "FAIL", "message": "失败"}

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        import os

        return {
            'api_version': 'v3',
            'mock_mode': settings.PAYMENT_MOCK_MODE,
            'appid_configured': bool(self.appid),
            'mch_id_configured': bool(self.mch_id),
            'api_v3_key_configured': bool(self.api_v3_key),
            'cert_serial_configured': bool(self.cert_serial),
            'cert_file_exists': bool(self.cert_path and os.path.exists(self.cert_path)),
            'key_file_exists': bool(self.key_path and os.path.exists(self.key_path)),
            'notify_url': self.notify_url,
            'production_ready': self._is_production_ready()
        }

    def _is_production_ready(self) -> bool:
        """检查是否准备好生产环境"""
        try:
            if settings.PAYMENT_MOCK_MODE:
                return True
            self._validate_config()
            return True
        except WechatPayV3Exception:
            return False


# 创建全局实例
wechat_pay_v3_service = WechatPayV3Service()