#!/usr/bin/env python3
"""
API端点测试脚本 - 用于验证两个关键API是否正常工作
Test script for verifying API endpoints functionality
"""

import requests
import json
import sys
from datetime import date

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def print_header(text):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def test_market_overview():
    """测试市场总览API"""
    print_header("测试1: GET /chart-data/market-overview")
    
    try:
        url = f"{BASE_URL}/chart-data/market-overview"
        print(f"请求URL: {url}")
        print(f"请求方法: GET")
        
        response = requests.get(url, timeout=10)
        
        print(f"响应状态: {response.status_code}")
        print(f"响应头: Content-Type = {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ API返回成功 (200)")
            print(f"\n返回数据结构:")
            print(f"  - trade_date: {data.get('trade_date', 'N/A')}")
            
            market_stats = data.get('market_stats', {})
            print(f"\n市场统计数据:")
            print(f"  - total_stocks (总股票数): {market_stats.get('total_stocks', 'N/A')}")
            print(f"  - total_concepts (总概念数): {market_stats.get('total_concepts', 'N/A')}")
            print(f"  - innovation_concepts (创新高概念数): {market_stats.get('innovation_concepts', 'N/A')}")
            print(f"  - avg_heat_value (平均热度): {market_stats.get('avg_heat_value', 'N/A')}")
            print(f"  - total_heat_value (总热度值): {market_stats.get('total_heat_value', 'N/A')}")
            print(f"  - max_heat_value (最大热度值): {market_stats.get('max_heat_value', 'N/A')}")
            
            heat_dist = data.get('heat_distribution_chart', {})
            print(f"\n热度分布数据:")
            categories = heat_dist.get('categories', [])
            dist_data = heat_dist.get('data', [])
            for cat, val in zip(categories, dist_data):
                print(f"  - {cat}: {val}只股票")
            
            # 判断是否有真实数据
            if market_stats.get('total_stocks', 0) > 0:
                print("\n✓ 数据库中存在股票数据")
                return True
            else:
                print("\n⚠️ 警告: 数据库中无股票数据或未正确连接")
                return False
                
        elif response.status_code == 404:
            print("\n✗ API返回404: 没有股票数据")
            print(response.json())
            return False
        else:
            print(f"\n✗ API返回异常状态: {response.status_code}")
            print(response.json())
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ 连接失败: 无法连接到 http://localhost:8000")
        print("请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")
        return False

def test_innovation_concepts():
    """测试创新高概念API"""
    print_header("测试2: GET /concept-analysis/concepts/innovation")
    
    try:
        url = f"{BASE_URL}/concept-analysis/concepts/innovation"
        print(f"请求URL: {url}")
        print(f"请求方法: GET")
        print(f"参数: page=1, page_size=10")
        
        response = requests.get(url, params={"page": 1, "page_size": 10}, timeout=10)
        
        print(f"响应状态: {response.status_code}")
        print(f"响应头: Content-Type = {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ API返回成功 (200)")
            print(f"\n返回数据结构:")
            print(f"  - trade_date: {data.get('trade_date', 'N/A')}")
            print(f"  - days_back: {data.get('days_back', 'N/A')}")
            
            concepts = data.get('innovation_concepts', [])
            print(f"\n创新高概念数量: {len(concepts)}")
            
            if concepts:
                print(f"\n第一个概念详情:")
                first = concepts[0]
                print(f"  - concept_id: {first.get('concept_id', 'N/A')}")
                print(f"  - concept_name: {first.get('concept_name', 'N/A')}")
                print(f"  - total_heat_value: {first.get('total_heat_value', 'N/A')}")
                print(f"  - stock_count: {first.get('stock_count', 'N/A')}")
                print(f"  - avg_heat_value: {first.get('avg_heat_value', 'N/A')}")
                print(f"  - new_high_days: {first.get('new_high_days', 'N/A')}")
                
                top_stocks = first.get('top_stocks', [])
                if top_stocks:
                    print(f"  - top_stocks (前3只股票):")
                    for stock in top_stocks:
                        print(f"      • {stock.get('stock_code')} {stock.get('stock_name')}: {stock.get('heat_value')}")
                else:
                    print(f"  - top_stocks: 无")
            
            pagination = data.get('pagination', {})
            print(f"\n分页信息:")
            print(f"  - page: {pagination.get('page', 'N/A')}")
            print(f"  - page_size: {pagination.get('page_size', 'N/A')}")
            print(f"  - total: {pagination.get('total', 'N/A')}")
            print(f"  - total_pages: {pagination.get('total_pages', 'N/A')}")
            
            # 判断是否为Mock数据
            if len(concepts) == 3 and concepts[0].get('concept_name') == '人工智能':
                print("\n⚠️ 警告: 返回的是Mock数据")
                print("这表示数据库中没有真实的创新高概念数据")
                return False
            else:
                print("\n✓ 返回的是真实数据")
                return True
                
        else:
            print(f"\n✗ API返回异常状态: {response.status_code}")
            print(response.json())
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n✗ 连接失败: 无法连接到 http://localhost:8000")
        print("请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")
        return False

def test_database_connection():
    """测试数据库连接"""
    print_header("测试0: 数据库连接检查")
    
    try:
        from app.core.database import engine
        from sqlalchemy import text
        
        # 测试连接
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✓ 数据库连接成功")
            
        # 检查表
        tables_to_check = [
            'daily_stock_data',
            'daily_concept_summaries',
            'daily_concept_rankings',
            'concepts',
            'stocks'
        ]
        
        with engine.connect() as connection:
            for table in tables_to_check:
                result = connection.execute(
                    text(f"SELECT COUNT(*) as count FROM {table}")
                )
                count = result.fetchone()[0]
                print(f"  - {table}: {count} 行")
        
        return True
        
    except ImportError:
        print("✗ 无法导入数据库模块")
        print("请在后端项目目录运行此脚本")
        return False
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  股票概念分析系统 - API端点测试")
    print("  Stock Concept Analysis - API Endpoint Test")
    print("="*60)
    
    print(f"\n测试时间: {date.today().isoformat()}")
    print(f"目标服务器: {BASE_URL}")
    
    # 运行测试
    results = {}
    
    # 测试0: 数据库连接（如果在后端目录运行）
    print("\n提示: 如果在后端项目目录运行，会自动检查数据库连接")
    try:
        results['database'] = test_database_connection()
    except:
        print("(跳过数据库连接测试，因为不在后端目录)")
    
    # 测试1: 市场总览
    results['market_overview'] = test_market_overview()
    
    # 测试2: 创新高概念
    results['innovation_concepts'] = test_innovation_concepts()
    
    # 总结
    print_header("测试总结")
    
    summary = {
        'market_overview': '✓ PASS' if results.get('market_overview') else '✗ FAIL',
        'innovation_concepts': '✓ PASS' if results.get('innovation_concepts') else '✗ FAIL',
    }
    
    if 'database' in results:
        summary['database'] = '✓ PASS' if results.get('database') else '✗ FAIL'
    
    for test_name, status in summary.items():
        print(f"{test_name}: {status}")
    
    # 建议
    print("\n建议:")
    if not results.get('market_overview'):
        print("1. 确保后端服务运行在 http://localhost:8000")
        print("2. 检查数据库连接是否正常")
        print("3. 检查daily_stock_data表中是否有数据")
    
    if not results.get('innovation_concepts'):
        print("1. 如果返回Mock数据，表示daily_concept_summaries表中无创新高概念")
        print("2. 运行数据分析任务来生成概念统计数据")
        print("3. 访问 /api/v1/concept-analysis/analysis/trigger 触发分析")
    
    print("\n详细分析报告请查看: BACKEND_API_ANALYSIS.md")
    print("代码实现细节请查看: BACKEND_API_CODE_SNIPPETS.md")

if __name__ == '__main__':
    main()
