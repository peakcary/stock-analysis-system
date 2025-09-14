#!/usr/bin/env python3
"""
数据库优化管理工具 v2.6.4
集成所有数据库优化功能的统一管理脚本
"""

import argparse
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Colors:
    """颜色输出类"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color


class DatabaseOptimizationManager:
    """数据库优化管理器"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent.parent
        
        # 解析数据库连接信息
        self._parse_database_url()
        
        # 初始化数据库连接
        self._init_database()
    
    def _parse_database_url(self):
        """解析数据库URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.database_url)
            
            self.db_type = parsed.scheme.split('+')[0]  # mysql
            self.db_host = parsed.hostname
            self.db_port = parsed.port or 3306
            self.db_user = parsed.username
            self.db_password = parsed.password
            self.db_name = parsed.path.lstrip('/')
            
            logger.info(f"数据库配置: {self.db_type}://{self.db_host}:{self.db_port}/{self.db_name}")
            
        except Exception as e:
            logger.error(f"解析数据库URL失败: {e}")
            raise
    
    def _init_database(self):
        """初始化数据库连接"""
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            
            self.engine = create_engine(self.database_url, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            
            logger.info("数据库连接成功")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def print_status(self, message: str, status: str = "info"):
        """打印带颜色的状态信息"""
        colors = {
            "info": Colors.BLUE,
            "success": Colors.GREEN,
            "warning": Colors.YELLOW,
            "error": Colors.RED,
            "cyan": Colors.CYAN
        }
        
        color = colors.get(status, Colors.WHITE)
        print(f"{color}{message}{Colors.NC}")
    
    def check_optimization_status(self) -> Dict[str, Any]:
        """检查优化状态"""
        self.print_status("🔍 检查数据库优化状态...", "info")
        
        status = {
            "environment": {},
            "tables": {},
            "views": {},
            "data_counts": {},
            "performance": {}
        }
        
        try:
            with self.SessionLocal() as db:
                # 检查环境变量
                env_vars = [
                    'USE_OPTIMIZED_TABLES',
                    'ENABLE_PERFORMANCE_LOG',
                    'ENABLE_QUERY_CACHE',
                    'API_PERFORMANCE_MONITORING'
                ]
                
                for var in env_vars:
                    status["environment"][var] = os.getenv(var, 'false')
                
                # 检查优化表
                optimized_tables = [
                    'daily_trading_unified',
                    'concept_daily_metrics',
                    'stock_concept_daily_snapshot',
                    'today_trading_cache'
                ]
                
                for table in optimized_tables:
                    try:
                        result = db.execute(f"SHOW TABLES LIKE '{table}'").fetchone()
                        exists = result is not None
                        status["tables"][table] = exists
                        
                        if exists:
                            count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                            status["data_counts"][table] = count
                        
                    except Exception as e:
                        status["tables"][table] = False
                        logger.error(f"检查表 {table} 失败: {e}")
                
                # 检查优化视图
                optimized_views = [
                    'v_stock_daily_summary',
                    'v_concept_daily_ranking',
                    'v_stock_concept_performance'
                ]
                
                for view in optimized_views:
                    try:
                        db.execute(f"SELECT 1 FROM {view} LIMIT 1")
                        status["views"][view] = True
                    except Exception:
                        status["views"][view] = False
                
                # 检查原始表数据量
                original_tables = [
                    'daily_trading',
                    'concept_daily_summary',
                    'stock_concept_ranking'
                ]
                
                for table in original_tables:
                    try:
                        count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                        status["data_counts"][f"{table}_original"] = count
                    except Exception:
                        status["data_counts"][f"{table}_original"] = 0
                
        except Exception as e:
            logger.error(f"检查优化状态失败: {e}")
            status["error"] = str(e)
        
        return status
    
    def create_optimized_tables(self) -> bool:
        """创建优化表结构"""
        self.print_status("🏗️ 创建优化表结构...", "info")
        
        try:
            # 执行建表脚本
            tables_script = self.script_dir / "create_optimized_tables.sql"
            views_script = self.script_dir / "create_views_and_indexes.sql"
            
            if not tables_script.exists():
                self.print_status(f"建表脚本不存在: {tables_script}", "error")
                return False
            
            # 使用mysql命令执行脚本
            import subprocess
            
            cmd = [
                "mysql",
                f"-h{self.db_host}",
                f"-P{self.db_port}",
                f"-u{self.db_user}",
                f"-p{self.db_password}",
                self.db_name
            ]
            
            # 执行建表脚本
            with open(tables_script, 'r') as f:
                result = subprocess.run(cmd, input=f.read(), text=True, 
                                      capture_output=True)
            
            if result.returncode != 0:
                self.print_status(f"建表脚本执行失败: {result.stderr}", "error")
                return False
            
            self.print_status("✓ 优化表创建完成", "success")
            
            # 创建视图和索引
            if views_script.exists():
                with open(views_script, 'r') as f:
                    result = subprocess.run(cmd, input=f.read(), text=True,
                                          capture_output=True)
                
                if result.returncode != 0:
                    self.print_status(f"视图创建失败: {result.stderr}", "warning")
                else:
                    self.print_status("✓ 优化视图创建完成", "success")
            
            return True
            
        except Exception as e:
            logger.error(f"创建优化表失败: {e}")
            self.print_status(f"创建优化表失败: {e}", "error")
            return False
    
    def migrate_data(self, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> bool:
        """迁移数据到优化表"""
        self.print_status("📦 执行数据迁移...", "info")
        
        try:
            import subprocess
            
            migration_script = self.script_dir / "smooth_migration_service.py"
            
            if not migration_script.exists():
                self.print_status(f"迁移脚本不存在: {migration_script}", "error")
                return False
            
            cmd = [
                "python3", str(migration_script),
                "--database-url", self.database_url
            ]
            
            if start_date:
                cmd.extend(["--start-date", start_date])
            if end_date:
                cmd.extend(["--end-date", end_date])
            
            # 执行迁移脚本
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_status("✓ 数据迁移完成", "success")
                return True
            else:
                self.print_status(f"数据迁移失败: {result.stderr}", "error")
                return False
                
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            self.print_status(f"数据迁移失败: {e}", "error")
            return False
    
    def enable_optimization(self, mode: str = "optimized") -> bool:
        """启用优化功能"""
        self.print_status(f"⚙️ 启用优化功能 (模式: {mode})...", "info")
        
        try:
            import subprocess
            
            enable_script = self.script_dir / "enable_optimization.py"
            
            if not enable_script.exists():
                self.print_status(f"启用脚本不存在: {enable_script}", "error")
                return False
            
            cmd = [
                "python3", str(enable_script),
                "enable", "--mode", mode
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_status("✓ 优化功能已启用", "success")
                return True
            else:
                self.print_status(f"启用优化功能失败: {result.stderr}", "error")
                return False
                
        except Exception as e:
            logger.error(f"启用优化功能失败: {e}")
            self.print_status(f"启用优化功能失败: {e}", "error")
            return False
    
    def performance_test(self, trading_date: Optional[str] = None) -> Dict[str, Any]:
        """性能测试"""
        if not trading_date:
            trading_date = "2025-09-02"  # 默认测试日期
        
        self.print_status(f"🚀 执行性能测试 (日期: {trading_date})...", "info")
        
        results = {
            "testing_date": trading_date,
            "original_query": {},
            "optimized_query": {},
            "improvement": {}
        }
        
        try:
            with self.SessionLocal() as db:
                parsed_date = datetime.strptime(trading_date, '%Y-%m-%d').date()
                
                # 测试原始查询
                self.print_status("测试原始查询性能...", "cyan")
                start_time = time.time()
                
                try:
                    original_count = db.execute(
                        "SELECT COUNT(*) FROM daily_trading WHERE trading_date = %s",
                        (parsed_date,)
                    ).scalar()
                    original_time = (time.time() - start_time) * 1000
                    
                    results["original_query"] = {
                        "record_count": original_count,
                        "execution_time_ms": round(original_time, 2),
                        "status": "success"
                    }
                    
                except Exception as e:
                    results["original_query"] = {
                        "record_count": 0,
                        "execution_time_ms": -1,
                        "status": f"failed: {e}"
                    }
                
                # 测试优化查询
                self.print_status("测试优化查询性能...", "cyan")
                start_time = time.time()
                
                try:
                    # 检查优化表是否存在
                    table_check = db.execute(
                        "SHOW TABLES LIKE 'daily_trading_unified'"
                    ).fetchone()
                    
                    if table_check:
                        optimized_count = db.execute(
                            "SELECT COUNT(*) FROM daily_trading_unified WHERE trading_date = %s",
                            (parsed_date,)
                        ).scalar()
                        optimized_time = (time.time() - start_time) * 1000
                        
                        results["optimized_query"] = {
                            "record_count": optimized_count,
                            "execution_time_ms": round(optimized_time, 2),
                            "status": "success"
                        }
                        
                        # 计算性能提升
                        if original_time > 0 and optimized_time > 0:
                            improvement_factor = original_time / optimized_time
                            results["improvement"] = {
                                "factor": round(improvement_factor, 2),
                                "description": f"{improvement_factor:.1f}倍提升",
                                "time_saved_ms": round(original_time - optimized_time, 2)
                            }
                    else:
                        results["optimized_query"] = {
                            "record_count": 0,
                            "execution_time_ms": -1,
                            "status": "table not exists"
                        }
                        
                except Exception as e:
                    results["optimized_query"] = {
                        "record_count": 0,
                        "execution_time_ms": -1,
                        "status": f"failed: {e}"
                    }
        
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            results["error"] = str(e)
        
        return results
    
    def backup_database(self) -> str:
        """备份数据库"""
        self.print_status("💾 备份数据库...", "info")
        
        try:
            import subprocess
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.project_root / f"database_backup_{timestamp}.sql"
            
            cmd = [
                "mysqldump",
                f"-h{self.db_host}",
                f"-P{self.db_port}",
                f"-u{self.db_user}",
                f"-p{self.db_password}",
                "--single-transaction",
                "--routines",
                "--triggers",
                self.db_name
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                self.print_status(f"✓ 数据库备份完成: {backup_file}", "success")
                return str(backup_file)
            else:
                self.print_status(f"数据库备份失败: {result.stderr}", "error")
                return ""
                
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            self.print_status(f"数据库备份失败: {e}", "error")
            return ""
    
    def full_deployment(self) -> bool:
        """完整部署流程"""
        self.print_status("🚀 开始完整优化部署...", "info")
        
        steps = [
            ("备份数据库", self.backup_database),
            ("创建优化表", self.create_optimized_tables),
            ("迁移数据", self.migrate_data),
            ("启用优化", lambda: self.enable_optimization("optimized"))
        ]
        
        for step_name, step_func in steps:
            self.print_status(f"执行: {step_name}", "cyan")
            
            try:
                if step_name == "备份数据库":
                    result = step_func()
                    success = bool(result)
                else:
                    success = step_func()
                
                if success:
                    self.print_status(f"✓ {step_name} 完成", "success")
                else:
                    self.print_status(f"✗ {step_name} 失败", "error")
                    return False
                    
            except Exception as e:
                self.print_status(f"✗ {step_name} 异常: {e}", "error")
                return False
        
        self.print_status("🎉 完整优化部署成功！", "success")
        return True
    
    def print_report(self):
        """打印状态报告"""
        print("\n" + "="*60)
        print(f"{Colors.BOLD}{Colors.GREEN}数据库优化状态报告{Colors.NC}")
        print("="*60)
        
        status = self.check_optimization_status()
        
        # 环境配置
        print(f"\n{Colors.CYAN}📊 环境配置:{Colors.NC}")
        for key, value in status.get("environment", {}).items():
            color = Colors.GREEN if value.lower() == 'true' else Colors.YELLOW
            print(f"  • {key}: {color}{value}{Colors.NC}")
        
        # 表状态
        print(f"\n{Colors.CYAN}🗃️ 优化表状态:{Colors.NC}")
        for table, exists in status.get("tables", {}).items():
            color = Colors.GREEN if exists else Colors.RED
            count = status.get("data_counts", {}).get(table, 0)
            status_text = f"存在 ({count} 条记录)" if exists else "不存在"
            print(f"  • {table}: {color}{status_text}{Colors.NC}")
        
        # 视图状态
        print(f"\n{Colors.CYAN}👁️ 优化视图状态:{Colors.NC}")
        for view, exists in status.get("views", {}).items():
            color = Colors.GREEN if exists else Colors.RED
            status_text = "可用" if exists else "不可用"
            print(f"  • {view}: {color}{status_text}{Colors.NC}")
        
        # 数据对比
        print(f"\n{Colors.CYAN}📈 数据量对比:{Colors.NC}")
        original_daily = status.get("data_counts", {}).get("daily_trading_original", 0)
        optimized_daily = status.get("data_counts", {}).get("daily_trading_unified", 0)
        print(f"  • 每日交易数据: {original_daily} → {optimized_daily}")
        
        # 整体状态
        tables_ready = sum(1 for x in status.get("tables", {}).values() if x)
        total_tables = len(status.get("tables", {}))
        overall_ready = tables_ready == total_tables and tables_ready > 0
        
        print(f"\n{Colors.CYAN}🎯 整体状态:{Colors.NC}")
        color = Colors.GREEN if overall_ready else Colors.YELLOW
        status_text = "已就绪" if overall_ready else "未完成"
        print(f"  • 优化状态: {color}{status_text}{Colors.NC}")
        print(f"  • 表完成度: {tables_ready}/{total_tables}")
        
        print("\n" + "="*60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据库优化管理工具 v2.6.4")
    parser.add_argument("--db-url", required=True, help="数据库连接URL")
    
    subparsers = parser.add_subparsers(dest="action", help="操作命令")
    
    # 状态检查
    subparsers.add_parser("status", help="检查优化状态")
    
    # 创建表结构
    subparsers.add_parser("create-tables", help="创建优化表结构")
    
    # 数据迁移
    migrate_parser = subparsers.add_parser("migrate", help="迁移数据")
    migrate_parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD)")
    migrate_parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    
    # 启用优化
    enable_parser = subparsers.add_parser("enable", help="启用优化功能")
    enable_parser.add_argument("--mode", default="optimized", 
                             choices=["testing", "optimized", "production"],
                             help="启用模式")
    
    # 性能测试
    test_parser = subparsers.add_parser("test", help="性能测试")
    test_parser.add_argument("--date", help="测试日期 (YYYY-MM-DD)")
    
    # 数据库备份
    subparsers.add_parser("backup", help="备份数据库")
    
    # 完整部署
    subparsers.add_parser("deploy", help="完整优化部署")
    
    # 状态报告
    subparsers.add_parser("report", help="生成状态报告")
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        return
    
    # 初始化管理器
    try:
        manager = DatabaseOptimizationManager(args.db_url)
    except Exception as e:
        print(f"{Colors.RED}初始化失败: {e}{Colors.NC}")
        return
    
    # 执行相应操作
    try:
        if args.action == "status":
            status = manager.check_optimization_status()
            print(json.dumps(status, indent=2, ensure_ascii=False))
        
        elif args.action == "create-tables":
            success = manager.create_optimized_tables()
            sys.exit(0 if success else 1)
        
        elif args.action == "migrate":
            success = manager.migrate_data(args.start_date, args.end_date)
            sys.exit(0 if success else 1)
        
        elif args.action == "enable":
            success = manager.enable_optimization(args.mode)
            sys.exit(0 if success else 1)
        
        elif args.action == "test":
            results = manager.performance_test(args.date)
            print(json.dumps(results, indent=2, ensure_ascii=False))
        
        elif args.action == "backup":
            backup_file = manager.backup_database()
            sys.exit(0 if backup_file else 1)
        
        elif args.action == "deploy":
            success = manager.full_deployment()
            sys.exit(0 if success else 1)
        
        elif args.action == "report":
            manager.print_report()
    
    except Exception as e:
        print(f"{Colors.RED}操作执行失败: {e}{Colors.NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()