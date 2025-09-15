#!/usr/bin/env python3
"""
模型定义同步脚本
用于在数据库优化部署后自动同步SQLAlchemy模型定义

当数据库表结构通过SQL脚本修改后，这个脚本会自动检测差异并更新模型文件
"""

import os
import sys
import re
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
import argparse

# 添加项目根目录到路径
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.append(str(project_root / "backend"))

def get_database_url():
    """获取数据库连接URL"""
    try:
        from app.core.config import settings
        return settings.SQLALCHEMY_DATABASE_URI
    except ImportError:
        # 如果配置文件不可用，使用默认配置
        return "mysql+pymysql://root:123456@localhost:3306/stock_analysis_dev"

def analyze_table_structure(engine, table_name):
    """分析数据库表结构"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text(f"DESCRIBE {table_name}"))
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES',
                    'key': row[3],
                    'default': row[4],
                    'extra': row[5] if len(row) > 5 else ''
                })
            return columns
        except Exception as e:
            print(f"❌ 分析表 {table_name} 失败: {e}")
            return []

def generate_sqlalchemy_field(column):
    """将数据库字段转换为SQLAlchemy字段定义"""
    field_type = column['type'].lower()

    # 映射数据库类型到SQLAlchemy类型
    type_mapping = {
        'int': 'Integer',
        'varchar': 'String',
        'date': 'Date',
        'datetime': 'DateTime',
        'timestamp': 'DateTime',
        'bigint': 'BigInteger',
        'text': 'Text',
        'decimal': 'DECIMAL',
        'float': 'Float',
        'boolean': 'Boolean',
        'tinyint(1)': 'Boolean'
    }

    # 提取类型名称（去掉长度信息）
    type_name = re.match(r'([a-z]+)', field_type).group(1)
    sqlalchemy_type = type_mapping.get(type_name, 'String')

    # 处理字符串长度
    if 'varchar' in field_type:
        length_match = re.search(r'varchar\((\d+)\)', field_type)
        if length_match:
            length = length_match.group(1)
            sqlalchemy_type = f'String({length})'

    # 构建字段定义
    field_definition = f"Column({sqlalchemy_type}"

    # 添加约束
    if column['key'] == 'PRI':
        field_definition += ", primary_key=True"
    if not column['nullable']:
        field_definition += ", nullable=False"
    if column['key'] == 'MUL':
        field_definition += ", index=True"
    if column['extra'] == 'auto_increment':
        field_definition += ", autoincrement=True"
    if column['default'] and column['default'] != 'NULL':
        if 'timestamp' in field_type.lower() or 'datetime' in field_type.lower():
            if 'current_timestamp' in str(column['default']).lower():
                field_definition += ", default=datetime.datetime.utcnow"
        else:
            field_definition += f", default={repr(column['default'])}"

    # 添加注释
    field_definition += f', comment="{column["name"]}"'

    field_definition += ")"

    return f"    {column['name']} = {field_definition}"

def update_model_file(model_file_path, table_name, columns):
    """更新模型文件"""
    if not os.path.exists(model_file_path):
        print(f"❌ 模型文件不存在: {model_file_path}")
        return False

    # 读取现有文件
    with open(model_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 查找类定义
    class_pattern = rf'class\s+\w+.*?__tablename__\s*=\s*["\']({table_name})["\'].*?(?=class|\Z)'
    match = re.search(class_pattern, content, re.DOTALL)

    if not match:
        print(f"❌ 在 {model_file_path} 中未找到表 {table_name} 的模型定义")
        return False

    # 生成新的字段定义
    new_fields = []
    for column in columns:
        if column['name'] != 'id':  # id字段通常已经存在
            new_fields.append(generate_sqlalchemy_field(column))

    # 提取现有的字段部分
    class_content = match.group(0)

    # 查找字段定义区域
    field_pattern = r'(\s+)(\w+)\s*=\s*Column\([^)]+\)'
    existing_fields = re.findall(field_pattern, class_content)

    if existing_fields:
        # 更新字段定义
        updated_class = class_content
        for field in new_fields:
            field_name = field.split(' = ')[0].strip()
            field_pattern = rf'(\s+){field_name}\s*=\s*Column\([^)]+\)'
            if re.search(field_pattern, updated_class):
                # 替换现有字段
                updated_class = re.sub(field_pattern, field, updated_class)
            else:
                # 添加新字段（在第一个字段后）
                first_field_match = re.search(r'(\s+\w+\s*=\s*Column\([^)]+\))', updated_class)
                if first_field_match:
                    insertion_point = first_field_match.end()
                    updated_class = updated_class[:insertion_point] + '\n' + field + updated_class[insertion_point:]

        # 替换原内容
        new_content = content.replace(class_content, updated_class)

        # 写回文件
        with open(model_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ 已更新模型文件: {model_file_path}")
        return True
    else:
        print(f"❌ 无法解析 {model_file_path} 中的字段定义")
        return False

def sync_models(database_url, dry_run=False):
    """同步所有模型定义"""
    print("🔄 开始同步模型定义...")

    # 连接数据库
    engine = create_engine(database_url)

    # 需要同步的表和对应的模型文件
    tables_to_sync = {
        'daily_trading': 'backend/app/models/daily_trading.py',
        'concept_daily_summary': 'backend/app/models/daily_trading.py',
        'stock_concept_ranking': 'backend/app/models/daily_trading.py',
        'concept_high_record': 'backend/app/models/daily_trading.py',
        'txt_import_record': 'backend/app/models/daily_trading.py'
    }

    success_count = 0
    total_count = len(tables_to_sync)

    for table_name, model_file in tables_to_sync.items():
        print(f"\n📊 同步表: {table_name}")

        # 分析表结构
        columns = analyze_table_structure(engine, table_name)
        if not columns:
            continue

        print(f"  发现 {len(columns)} 个字段")

        if dry_run:
            print("  [DRY RUN] 模拟同步，不修改文件")
            for column in columns:
                print(f"    - {column['name']}: {column['type']}")
        else:
            # 更新模型文件
            model_path = project_root / model_file
            if update_model_file(str(model_path), table_name, columns):
                success_count += 1

    print(f"\n🎉 同步完成: {success_count}/{total_count} 个表成功同步")

    if success_count == total_count:
        print("✅ 所有模型定义已同步")
        return True
    else:
        print(f"⚠️  {total_count - success_count} 个表同步失败，请手动检查")
        return False

def main():
    parser = argparse.ArgumentParser(description='同步SQLAlchemy模型定义')
    parser.add_argument('--database-url', help='数据库连接URL')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际修改文件')
    parser.add_argument('--table', help='只同步指定表')

    args = parser.parse_args()

    # 获取数据库URL
    database_url = args.database_url or get_database_url()
    print(f"🔗 数据库连接: {database_url.split('@')[1] if '@' in database_url else database_url}")

    try:
        success = sync_models(database_url, args.dry_run)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()