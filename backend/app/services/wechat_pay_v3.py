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

            # 验证时间戳（防重放攻击）
            current_timestamp = int(time.time())
            request_timestamp = int(timestamp)
            if abs(current_timestamp - request_timestamp) > 300:  # 5分钟内有效
                logger.error(f"Timestamp too old: {timestamp}")
                return False

            # 构造验证字符串
            sign_str = f"{timestamp}\n{nonce}\n{body}\n"

            # 使用微信支付平台公钥验证签名
            return self._verify_signature_with_platform_cert(signature, sign_str, cert_serial)

        except Exception as e:
            logger.error(f"Verify notify signature error: {e}")
            return False

    def _verify_signature_with_platform_cert(self, signature: str, sign_str: str, cert_serial: str) -> bool:
        """使用微信支付平台证书验证签名"""
        try:
            # 获取平台证书
            platform_cert = self._get_platform_certificate(cert_serial)
            if not platform_cert:
                logger.error(f"Platform certificate not found for serial: {cert_serial}")
                return False

            # 解码签名
            signature_bytes = base64.b64decode(signature)

            # 验证签名
            hash_obj = SHA256.new(sign_str.encode('utf-8'))

            try:
                pkcs1_15.new(platform_cert).verify(hash_obj, signature_bytes)
                logger.info("Platform signature verification passed")
                return True
            except (ValueError, TypeError) as e:
                logger.error(f"Platform signature verification failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Verify signature with platform cert error: {e}")
            return False

    def _get_platform_certificate(self, cert_serial: str) -> Optional[RSA.RsaKey]:
        """获取微信支付平台证书"""
        try:
            # 检查本地缓存的平台证书
            platform_cert_path = f"backend/certs/wechatpay_platform_{cert_serial}.pem"

            import os
            if os.path.exists(platform_cert_path):
                with open(platform_cert_path, 'r') as f:
                    cert_content = f.read()
                return RSA.import_key(cert_content)

            # 如果本地没有，尝试从微信支付API获取
            logger.warning(f"Platform certificate not found locally: {platform_cert_path}")
            return self._fetch_platform_certificate(cert_serial)

        except Exception as e:
            logger.error(f"Get platform certificate error: {e}")
            return None

    def _fetch_platform_certificate(self, cert_serial: str) -> Optional[RSA.RsaKey]:
        """从微信支付API获取平台证书"""
        try:
            if settings.PAYMENT_MOCK_MODE:
                logger.info("Mock mode: skipping platform certificate fetch")
                return None

            # 调用微信支付获取证书API
            url_path = "/v3/certificates"

            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': self._generate_authorization('GET', url_path),
                'User-Agent': 'Stock-Analysis-System/1.0'
            }

            cert_url = f"{self.base_url}{url_path}"
            response = requests.get(cert_url, headers=headers, timeout=30)

            if response.status_code == 200:
                cert_data = response.json()
                certificates = cert_data.get('data', [])

                for cert_info in certificates:
                    if cert_info.get('serial_no') == cert_serial:
                        # 解密证书内容
                        encrypted_cert = cert_info.get('encrypt_certificate', {})
                        cert_content = self._decrypt_certificate(encrypted_cert)

                        if cert_content:
                            # 保存到本地缓存
                            platform_cert_path = f"backend/certs/wechatpay_platform_{cert_serial}.pem"
                            os.makedirs(os.path.dirname(platform_cert_path), exist_ok=True)

                            with open(platform_cert_path, 'w') as f:
                                f.write(cert_content)

                            logger.info(f"Platform certificate cached: {platform_cert_path}")
                            return RSA.import_key(cert_content)

                logger.error(f"Certificate with serial {cert_serial} not found in API response")
                return None
            else:
                logger.error(f"Fetch platform certificate failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Fetch platform certificate error: {e}")
            return None

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

            decrypted_transaction_data = None
            if ciphertext:
                # 解密resource数据
                decrypted_data = self._decrypt_resource(resource)
                if decrypted_data:
                    # 验证解密数据的完整性
                    expected_fields = ['out_trade_no', 'transaction_id', 'trade_state', 'amount']
                    if self._validate_decrypted_data(decrypted_data, expected_fields):
                        decrypted_transaction_data = decrypted_data
                        logger.info("Transaction data decryption and validation successful")
                    else:
                        logger.error("Decrypted transaction data validation failed")
                        return {
                            'success': False,
                            'message': '解密数据验证失败',
                            'data': {}
                        }
                else:
                    logger.error("Failed to decrypt resource data")
                    return {
                        'success': False,
                        'message': '解密支付通知数据失败',
                        'data': {}
                    }

            # 检查事件类型和支付状态
            event_type = notify_data.get('event_type')
            if event_type == 'TRANSACTION.SUCCESS':
                # 使用解密后的交易数据（如果有的话）
                transaction_data = decrypted_transaction_data or notify_data

                return {
                    'success': True,
                    'message': '支付成功',
                    'data': {
                        'out_trade_no': transaction_data.get('out_trade_no'),
                        'transaction_id': transaction_data.get('transaction_id'),
                        'total_fee': transaction_data.get('amount', {}).get('total', 0),
                        'success_time': transaction_data.get('success_time'),
                        'payer_openid': transaction_data.get('payer', {}).get('openid', ''),
                        'trade_state': transaction_data.get('trade_state'),
                        'bank_type': transaction_data.get('bank_type', ''),
                        'currency': transaction_data.get('amount', {}).get('currency', 'CNY'),
                        'raw_data': notify_data,
                        'decrypted_data': decrypted_transaction_data
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
            algorithm = resource.get('algorithm', 'AEAD_AES_256_GCM')

            if not all([ciphertext, nonce]):
                logger.error("Missing required decryption parameters")
                return None

            # 验证加密算法
            if algorithm != 'AEAD_AES_256_GCM':
                logger.error(f"Unsupported encryption algorithm: {algorithm}")
                return None

            # 验证API v3密钥长度
            if not self.api_v3_key or len(self.api_v3_key) != 32:
                logger.error("Invalid API v3 key length, must be 32 characters")
                return None

            # 准备解密参数
            key = self.api_v3_key.encode('utf-8')
            nonce_bytes = nonce.encode('utf-8')
            ciphertext_bytes = base64.b64decode(ciphertext)

            # 分离密文和认证标签（GCM模式下标签长度为16字节）
            if len(ciphertext_bytes) < 16:
                logger.error("Ciphertext too short")
                return None

            encrypted_data = ciphertext_bytes[:-16]
            auth_tag = ciphertext_bytes[-16:]

            # 创建AES-GCM解密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce_bytes)

            # 添加附加认证数据
            if associated_data:
                cipher.update(associated_data.encode('utf-8'))

            try:
                # 解密并验证
                decrypted_bytes = cipher.decrypt_and_verify(encrypted_data, auth_tag)
                decrypted_text = decrypted_bytes.decode('utf-8')

                logger.info("Resource decryption successful")
                return json.loads(decrypted_text)

            except ValueError as e:
                logger.error(f"Decryption verification failed: {e}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"Decrypted data is not valid JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Decrypt resource error: {e}")
            return None

    def _decrypt_certificate(self, encrypted_certificate: dict) -> Optional[str]:
        """解密微信支付平台证书"""
        try:
            # 证书解密逻辑与resource解密类似，但返回证书内容字符串
            decrypted_data = self._decrypt_resource(encrypted_certificate)

            if decrypted_data and isinstance(decrypted_data, dict):
                # 假设解密后的数据包含证书内容
                return decrypted_data.get('certificate', '')
            elif isinstance(decrypted_data, str):
                # 直接返回证书字符串
                return decrypted_data

            return None

        except Exception as e:
            logger.error(f"Decrypt certificate error: {e}")
            return None

    def _validate_decrypted_data(self, data: dict, expected_fields: list = None) -> bool:
        """验证解密后的数据完整性"""
        try:
            if not isinstance(data, dict):
                logger.error("Decrypted data is not a dictionary")
                return False

            # 检查必需字段
            if expected_fields:
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    logger.error(f"Missing required fields: {missing_fields}")
                    return False

            # 检查交易相关字段的有效性
            if 'out_trade_no' in data:
                out_trade_no = data.get('out_trade_no', '')
                if not out_trade_no or not isinstance(out_trade_no, str):
                    logger.error("Invalid out_trade_no")
                    return False

            if 'amount' in data:
                amount = data.get('amount', {})
                if not isinstance(amount, dict):
                    logger.error("Invalid amount structure")
                    return False

                total = amount.get('total')
                if total is not None and (not isinstance(total, int) or total <= 0):
                    logger.error("Invalid total amount")
                    return False

            logger.info("Decrypted data validation passed")
            return True

        except Exception as e:
            logger.error(f"Validate decrypted data error: {e}")
            return False

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

    async def handle_order_timeout(self, out_trade_no: str, timeout_minutes: int = 30) -> Dict[str, Any]:
        """处理订单超时"""
        try:
            logger.info(f"Handling timeout for order: {out_trade_no}")

            # 先查询订单状态
            order_status = await self.query_order(out_trade_no)

            if order_status.get('mock_mode'):
                return {
                    'success': True,
                    'action': 'mock_timeout',
                    'message': '模拟模式：订单超时处理',
                    'data': order_status
                }

            trade_state = order_status.get('trade_state')

            if trade_state == 'SUCCESS':
                # 订单已支付成功，无需处理
                return {
                    'success': True,
                    'action': 'already_paid',
                    'message': '订单已支付成功',
                    'data': order_status
                }
            elif trade_state == 'CLOSED':
                # 订单已关闭
                return {
                    'success': True,
                    'action': 'already_closed',
                    'message': '订单已关闭',
                    'data': order_status
                }
            elif trade_state in ['NOTPAY', 'USERPAYING']:
                # 订单未支付或用户支付中，关闭订单
                close_result = await self.close_order(out_trade_no)
                if close_result:
                    logger.info(f"Order {out_trade_no} closed due to timeout")
                    return {
                        'success': True,
                        'action': 'closed',
                        'message': f'订单超时已关闭（{timeout_minutes}分钟）',
                        'data': {
                            'out_trade_no': out_trade_no,
                            'original_state': trade_state,
                            'timeout_minutes': timeout_minutes
                        }
                    }
                else:
                    logger.error(f"Failed to close timeout order: {out_trade_no}")
                    return {
                        'success': False,
                        'action': 'close_failed',
                        'message': '关闭超时订单失败',
                        'data': order_status
                    }
            elif trade_state == 'NOTFOUND':
                # 订单不存在
                return {
                    'success': True,
                    'action': 'not_found',
                    'message': '订单不存在',
                    'data': {'out_trade_no': out_trade_no}
                }
            else:
                # 其他状态
                logger.warning(f"Unknown trade state for timeout handling: {trade_state}")
                return {
                    'success': False,
                    'action': 'unknown_state',
                    'message': f'未知订单状态: {trade_state}',
                    'data': order_status
                }

        except Exception as e:
            logger.error(f"Handle order timeout error: {e}")
            return {
                'success': False,
                'action': 'error',
                'message': f'处理订单超时异常: {e}',
                'data': {'out_trade_no': out_trade_no}
            }

    def calculate_order_timeout(self, created_time: datetime, timeout_minutes: int = 30) -> bool:
        """计算订单是否超时"""
        try:
            current_time = datetime.now()
            timeout_threshold = created_time + timedelta(minutes=timeout_minutes)

            is_timeout = current_time > timeout_threshold
            logger.info(f"Order timeout check - Created: {created_time}, Current: {current_time}, "
                       f"Timeout: {timeout_threshold}, IsTimeout: {is_timeout}")

            return is_timeout

        except Exception as e:
            logger.error(f"Calculate order timeout error: {e}")
            return True  # 出错时默认认为超时

    async def batch_handle_timeout_orders(self, order_list: list, timeout_minutes: int = 30) -> Dict[str, Any]:
        """批量处理超时订单"""
        try:
            results = {
                'total': len(order_list),
                'processed': 0,
                'success': 0,
                'failed': 0,
                'details': []
            }

            for order_info in order_list:
                out_trade_no = order_info.get('out_trade_no')
                created_time = order_info.get('created_time')

                if not out_trade_no or not created_time:
                    results['failed'] += 1
                    results['details'].append({
                        'out_trade_no': out_trade_no,
                        'success': False,
                        'message': '订单信息不完整'
                    })
                    continue

                # 检查是否超时
                if isinstance(created_time, str):
                    try:
                        created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                    except ValueError:
                        created_time = datetime.strptime(created_time, '%Y-%m-%d %H:%M:%S')

                if not self.calculate_order_timeout(created_time, timeout_minutes):
                    # 未超时，跳过
                    results['details'].append({
                        'out_trade_no': out_trade_no,
                        'success': True,
                        'message': '订单未超时'
                    })
                    continue

                # 处理超时订单
                timeout_result = await self.handle_order_timeout(out_trade_no, timeout_minutes)
                results['processed'] += 1

                if timeout_result.get('success'):
                    results['success'] += 1
                else:
                    results['failed'] += 1

                results['details'].append({
                    'out_trade_no': out_trade_no,
                    'success': timeout_result.get('success', False),
                    'action': timeout_result.get('action'),
                    'message': timeout_result.get('message')
                })

            logger.info(f"Batch timeout processing completed: {results['success']}/{results['total']} successful")
            return results

        except Exception as e:
            logger.error(f"Batch handle timeout orders error: {e}")
            return {
                'total': len(order_list),
                'processed': 0,
                'success': 0,
                'failed': len(order_list),
                'error': str(e),
                'details': []
            }

    def get_timeout_policy(self) -> Dict[str, Any]:
        """获取超时策略配置"""
        return {
            'default_timeout_minutes': 30,  # 默认30分钟超时
            'max_timeout_minutes': 120,     # 最大2小时超时
            'min_timeout_minutes': 5,       # 最小5分钟超时
            'batch_process_limit': 100,     # 批量处理限制
            'retry_interval_seconds': 60,   # 重试间隔60秒
            'supported_timeout_actions': [
                'close_order',      # 关闭订单
                'query_status',     # 查询状态
                'send_notification' # 发送通知
            ]
        }


# 创建全局实例
wechat_pay_v3_service = WechatPayV3Service()