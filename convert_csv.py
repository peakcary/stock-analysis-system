#!/usr/bin/env python3
"""
CSV格式转换脚本
将实际的CSV文件格式转换为系统期望的格式
"""

import pandas as pd
from datetime import date
import sys

def convert_csv(input_file, output_file):
    """
    转换CSV文件格式
    
    输入格式: 股票代码,股票名称,全部页数,热帖首页页阅读总数,价格,行业,概念,换手,净流入
    输出格式: stock_code,stock_name,concept,industry,date,price,turnover_rate,net_inflow
    """
    try:
        # 读取原始文件
        df = pd.read_csv(input_file, encoding='utf-8')
        
        print(f"原始文件列名: {list(df.columns)}")
        print(f"原始数据行数: {len(df)}")
        
        # 创建字段映射
        column_mapping = {
            '股票代码': 'stock_code',
            '股票名称': 'stock_name', 
            '概念': 'concept',
            '行业': 'industry',
            '价格': 'price',
            '换手': 'turnover_rate',
            '净流入': 'net_inflow'
        }
        
        # 选择并重命名列
        converted_df = df[list(column_mapping.keys())].rename(columns=column_mapping)
        
        # 添加日期列（使用今天的日期）
        converted_df['date'] = date.today().strftime('%Y-%m-%d')
        
        # 处理None值和数据清理
        converted_df['industry'] = converted_df['industry'].replace('None', '')
        converted_df['price'] = pd.to_numeric(converted_df['price'], errors='coerce').fillna(0)
        converted_df['turnover_rate'] = pd.to_numeric(converted_df['turnover_rate'], errors='coerce').fillna(0)
        converted_df['net_inflow'] = pd.to_numeric(converted_df['net_inflow'], errors='coerce').fillna(0)
        
        # 重新排列列的顺序
        converted_df = converted_df[['stock_code', 'stock_name', 'concept', 'industry', 'date', 'price', 'turnover_rate', 'net_inflow']]
        
        # 保存转换后的文件
        converted_df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"转换完成！")
        print(f"转换后数据行数: {len(converted_df)}")
        print(f"转换后文件保存到: {output_file}")
        print(f"转换后列名: {list(converted_df.columns)}")
        
        # 显示前几行数据
        print("\n前5行数据预览:")
        print(converted_df.head())
        
        return True
        
    except Exception as e:
        print(f"转换失败: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "/Users/cary/Downloads/数据分析/数据文件/2025-08-12-09-38.csv"
    output_file = "/Users/cary/Desktop/AAA.csv"
    
    print("开始转换CSV文件格式...")
    print(f"输入文件: {input_file}")
    print(f"输出文件: {output_file}")
    
    success = convert_csv(input_file, output_file)
    
    if success:
        print("\n✅ 转换成功！现在可以使用 AAA.csv 文件进行导入了。")
    else:
        print("\n❌ 转换失败！请检查文件格式。")