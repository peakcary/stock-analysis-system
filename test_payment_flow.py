#!/usr/bin/env python3
"""
完整支付流程测试脚本
Complete Payment Flow Test
"""

import requests
import json
import time

BASE_URL = "http://localhost:3007/api/v1"

def test_login():
    """登录获取token"""
    login_data = {"username": "admin", "password": "admin123"}
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登录成功: {result['user']['username']}")
        return result['access_token']
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_create_payment_order(token, package_type):
    """创建支付订单"""
    headers = {"Authorization": f"Bearer {token}"}
    order_data = {
        "package_type": package_type,
        "payment_method": "wechat_native",
        "client_ip": "127.0.0.1"
    }
    
    print(f"🛒 创建支付订单: {package_type}")
    response = requests.post(f"{BASE_URL}/payment/orders", json=order_data, headers=headers)
    
    if response.status_code == 200:
        order = response.json()
        print(f"✅ 订单创建成功:")
        print(f"   订单号: {order['out_trade_no']}")
        print(f"   套餐: {order['package_name']}")
        print(f"   金额: ¥{order['amount']}")
        print(f"   状态: {order['status']}")
        print(f"   二维码: {order['code_url'][:50]}...")
        return order
    else:
        print(f"❌ 创建订单失败: {response.text}")
        return None

def test_simulate_payment_success(token, out_trade_no):
    """模拟支付成功"""
    headers = {"Authorization": f"Bearer {token}"}
    print(f"💰 模拟支付成功: {out_trade_no}")
    
    response = requests.post(f"{BASE_URL}/payment/test/simulate-success/{out_trade_no}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        return True
    else:
        print(f"❌ 模拟支付失败: {response.text}")
        return False

def test_check_order_status(token, out_trade_no):
    """查询订单状态"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/payment/orders/{out_trade_no}/status", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"📋 订单状态: {result['status']}")
        if result.get('paid_at'):
            print(f"   支付时间: {result['paid_at']}")
        if result.get('transaction_id'):
            print(f"   交易号: {result['transaction_id']}")
        return result
    else:
        print(f"❌ 查询状态失败: {response.text}")
        return None

def main():
    print("🚀 完整支付流程测试")
    print("=" * 50)
    
    # 1. 登录
    print("\n1️⃣ 用户登录...")
    token = test_login()
    if not token:
        return
    
    # 2. 创建支付订单（使用10次查询包，价格0.01元测试）
    print("\n2️⃣ 创建支付订单...")
    order = test_create_payment_order(token, "10_queries")
    if not order:
        return
    
    # 3. 查询初始状态
    print("\n3️⃣ 查询订单状态（支付前）...")
    test_check_order_status(token, order['out_trade_no'])
    
    # 4. 模拟支付成功
    print("\n4️⃣ 模拟支付成功...")
    if test_simulate_payment_success(token, order['out_trade_no']):
        # 5. 查询支付后状态
        print("\n5️⃣ 查询订单状态（支付后）...")
        final_status = test_check_order_status(token, order['out_trade_no'])
        
        if final_status and final_status['status'] == 'paid':
            print("\n🎉 支付流程测试成功！")
            print("✅ 订单状态已更新为已支付")
            print("✅ 会员权益应该已经生效")
        else:
            print("\n⚠️ 支付状态未更新，请检查后端逻辑")
    
    print("\n" + "=" * 50)
    print("测试完成")

if __name__ == "__main__":
    main()