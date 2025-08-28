#!/usr/bin/env python3
"""
模拟支付测试脚本
Test Mock Payment Flow
"""

import requests
import json
import time

BASE_URL = "http://localhost:3007/api/v1"

def test_login():
    """测试登录获取token"""
    login_data = {
        "username": "admin", 
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登录成功: {result['user']['username']}")
        return result['access_token']
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_get_packages():
    """测试获取支付套餐"""
    response = requests.get(f"{BASE_URL}/payment/packages")
    if response.status_code == 200:
        packages = response.json()
        print(f"✅ 获取支付套餐成功，共 {len(packages)} 个套餐")
        for pkg in packages:
            print(f"   - {pkg['name']}: ¥{pkg['price']}")
        return packages[0] if packages else None
    else:
        print(f"❌ 获取支付套餐失败: {response.text}")
        return None

def test_create_order(token, package_type):
    """测试创建支付订单"""
    headers = {"Authorization": f"Bearer {token}"}
    order_data = {
        "package_type": package_type,
        "payment_method": "wechat_native",
        "client_ip": "127.0.0.1",
        "user_agent": "TestScript/1.0"
    }
    
    response = requests.post(f"{BASE_URL}/payment/orders", json=order_data, headers=headers)
    if response.status_code == 200:
        order = response.json()
        print(f"✅ 创建订单成功")
        print(f"   订单号: {order['out_trade_no']}")
        print(f"   金额: ¥{order['amount']}")
        print(f"   状态: {order['status']}")
        print(f"   二维码URL: {order['code_url'][:50]}..." if order.get('code_url') else "   无二维码URL")
        return order['out_trade_no']
    else:
        print(f"❌ 创建订单失败: {response.text}")
        return None

def test_check_order_status(token, out_trade_no):
    """测试查询订单状态"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/payment/orders/{out_trade_no}/status", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"📋 订单状态: {result['status']}")
        if result['status'] == 'paid':
            print(f"   支付时间: {result.get('paid_at', 'N/A')}")
            print(f"   交易号: {result.get('transaction_id', 'N/A')}")
        return result['status']
    else:
        print(f"❌ 查询订单状态失败: {response.text}")
        return None

def test_simulate_payment(token, out_trade_no):
    """测试模拟支付成功"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/payment/test/simulate-success/{out_trade_no}", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 模拟支付成功: {result['message']}")
        return True
    else:
        print(f"❌ 模拟支付失败: {response.text}")
        return False

def test_payment_stats(token):
    """测试获取支付统计"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/payment/stats", headers=headers)
    
    if response.status_code == 200:
        stats = response.json()
        print(f"📊 支付统计:")
        print(f"   总订单数: {stats['total_orders']}")
        print(f"   已支付订单: {stats['paid_orders']}")
        print(f"   总金额: ¥{stats['total_amount']}")
        print(f"   会员类型: {stats['membership_type']}")
        print(f"   剩余查询次数: {stats['queries_remaining']}")
        return stats
    else:
        print(f"❌ 获取支付统计失败: {response.text}")
        return None

def main():
    """主测试流程"""
    print("🚀 开始模拟支付流程测试")
    print("=" * 50)
    
    # 1. 登录
    print("\n1️⃣  测试登录...")
    token = test_login()
    if not token:
        return
    
    # 2. 获取支付套餐
    print("\n2️⃣  获取支付套餐...")
    packages = test_get_packages()
    if not packages:
        return
    
    # 3. 创建支付订单
    print("\n3️⃣  创建支付订单...")
    out_trade_no = test_create_order(token, packages[0]['package_type'])
    if not out_trade_no:
        return
    
    # 4. 查询初始订单状态
    print("\n4️⃣  查询订单状态（支付前）...")
    status = test_check_order_status(token, out_trade_no)
    
    # 5. 模拟支付成功
    print("\n5️⃣  模拟支付成功...")
    if test_simulate_payment(token, out_trade_no):
        # 6. 再次查询订单状态
        print("\n6️⃣  查询订单状态（支付后）...")
        status = test_check_order_status(token, out_trade_no)
        
        # 7. 查看支付统计
        print("\n7️⃣  查看支付统计...")
        test_payment_stats(token)
    
    print("\n" + "=" * 50)
    print("✅ 模拟支付流程测试完成！")

if __name__ == "__main__":
    main()