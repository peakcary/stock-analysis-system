#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票分析系统 - 示例数据初始化脚本
Stock Analysis System - Sample Data Initialization Script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.models.payment import PaymentPackage
from app.models.user import User
from app.models.stock import Stock
from app.models.concept import Concept
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_sample_data():
    """初始化示例数据"""
    print("🚀 开始初始化示例数据...")
    
    # 创建会话
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. 初始化支付套餐
        print("📦 初始化支付套餐...")
        packages = [
            {
                "package_type": "queries_10",
                "name": "10次查询包", 
                "price": 9.90,
                "queries_count": 10,
                "validity_days": 30,
                "membership_type": "free",
                "description": "适合偶尔使用的用户，30天内有效",
                "sort_order": 1
            },
            {
                "package_type": "queries_100",
                "name": "100次查询包",
                "price": 39.90, 
                "queries_count": 100,
                "validity_days": 60,
                "membership_type": "free",
                "description": "高频使用推荐，60天内有效",
                "sort_order": 2
            },
            {
                "package_type": "queries_1000", 
                "name": "1000次查询包",
                "price": 99.90,
                "queries_count": 1000,
                "validity_days": 90,
                "membership_type": "pro",
                "description": "专业用户推荐，90天内有效",
                "sort_order": 3
            },
            {
                "package_type": "unlimited",
                "name": "无限查询包",
                "price": 299.90,
                "queries_count": 999999,
                "validity_days": 365, 
                "membership_type": "premium",
                "description": "一年内无限次查询，旗舰版体验",
                "sort_order": 4
            }
        ]
        
        for pkg_data in packages:
            existing = db.query(PaymentPackage).filter(
                PaymentPackage.package_type == pkg_data["package_type"]
            ).first()
            if not existing:
                package = PaymentPackage(**pkg_data)
                db.add(package)
                print(f"  ✅ 添加套餐: {pkg_data['name']}")
            else:
                print(f"  ⚠️  套餐已存在: {pkg_data['name']}")
        
        # 2. 初始化测试用户
        print("👥 初始化测试用户...")
        users = [
            {
                "username": "testuser",
                "email": "test@example.com", 
                "password_hash": pwd_context.hash("123456"),
                "membership_type": "free",
                "queries_remaining": 10
            },
            {
                "username": "prouser",
                "email": "pro@example.com",
                "password_hash": pwd_context.hash("123456"), 
                "membership_type": "pro",
                "queries_remaining": 1000
            },
            {
                "username": "premiumuser", 
                "email": "premium@example.com",
                "password_hash": pwd_context.hash("123456"),
                "membership_type": "premium", 
                "queries_remaining": 999999
            }
        ]
        
        for user_data in users:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(**user_data)
                db.add(user)
                print(f"  ✅ 添加用户: {user_data['username']}")
            else:
                print(f"  ⚠️  用户已存在: {user_data['username']}")
        
        # 3. 初始化股票数据
        print("📈 初始化股票数据...")
        stocks = [
            {"stock_code": "600000", "stock_name": "浦发银行", "industry": "银行业", "is_convertible_bond": False},
            {"stock_code": "000001", "stock_name": "平安银行", "industry": "银行业", "is_convertible_bond": False},
            {"stock_code": "000002", "stock_name": "万科A", "industry": "房地产业", "is_convertible_bond": False},
            {"stock_code": "000858", "stock_name": "五粮液", "industry": "食品饮料", "is_convertible_bond": False},
            {"stock_code": "600519", "stock_name": "贵州茅台", "industry": "食品饮料", "is_convertible_bond": False},
        ]
        
        for stock_data in stocks:
            existing = db.query(Stock).filter(Stock.stock_code == stock_data["stock_code"]).first()
            if not existing:
                stock = Stock(**stock_data)
                db.add(stock)
                print(f"  ✅ 添加股票: {stock_data['stock_code']} - {stock_data['stock_name']}")
            else:
                print(f"  ⚠️  股票已存在: {stock_data['stock_code']} - {stock_data['stock_name']}")
        
        # 4. 初始化概念数据 
        print("🏷️  初始化概念数据...")
        concepts = [
            {"concept_name": "银行股", "description": "银行业相关股票"},
            {"concept_name": "房地产", "description": "房地产行业相关股票"},
            {"concept_name": "白酒概念", "description": "白酒行业相关股票"},
            {"concept_name": "金融服务", "description": "金融服务行业相关股票"},
        ]
        
        for concept_data in concepts:
            existing = db.query(Concept).filter(Concept.concept_name == concept_data["concept_name"]).first()
            if not existing:
                concept = Concept(**concept_data)
                db.add(concept)
                print(f"  ✅ 添加概念: {concept_data['concept_name']}")
            else:
                print(f"  ⚠️  概念已存在: {concept_data['concept_name']}")
        
        # 提交所有更改
        db.commit()
        print("\n🎉 示例数据初始化完成!")
        
        # 显示统计信息
        print("\n📊 数据统计:")
        print(f"  💳 支付套餐: {db.query(PaymentPackage).count()} 个")
        print(f"  👥 用户数量: {db.query(User).count()} 个")
        print(f"  📈 股票数量: {db.query(Stock).count()} 个") 
        print(f"  🏷️  概念数量: {db.query(Concept).count()} 个")
        
        print("\n💡 测试账号:")
        print("  👤 testuser / 123456  (免费用户)")
        print("  👤 prouser / 123456   (专业版)")
        print("  👤 premiumuser / 123456 (旗舰版)")
        print("  👤 admin / admin123     (管理员)")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    success = init_sample_data()
    sys.exit(0 if success else 1)