#!/usr/bin/env python3
"""
DB Debug Check - Verify universal import write/read paths for a given file type.

Usage:
  python scripts/database/debug_check.py --file-type eee --date 2025-08-29

This script uses the project's configured database connection (app.core.database)
to query dynamic tables for the specified file type and prints row counts and
recent import records to help diagnose issues like "import success but list empty".
"""

import argparse
import os
import sys
from datetime import date as date_cls


def add_backend_to_path():
    # Allow running from repo root; add backend to sys.path
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    backend_path = os.path.join(repo_root, 'backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)


def main():
    add_backend_to_path()

    from sqlalchemy import text
    from app.core.database import get_engine

    parser = argparse.ArgumentParser(description='DB debug check for universal import tables')
    parser.add_argument('--file-type', '-t', required=True, help='File type, e.g., eee or ttv')
    parser.add_argument('--date', '-d', help='Trading date YYYY-MM-DD')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Recent records limit')
    args = parser.parse_args()

    ft = args.file_type.strip().lower()
    prefix = f"{ft}_" if ft != 'txt' else ''

    tables = {
        'import_record': f"{prefix}import_record" if prefix else 'txt_import_record',
        'daily_trading': f"{prefix}daily_trading",
        'concept_summary': f"{prefix}concept_daily_summary",
        'ranking': f"{prefix}stock_concept_ranking",
        'high_record': f"{prefix}concept_high_record",
    }

    engine = get_engine()
    with engine.connect() as conn:
        print(f"\n== Debug check for file_type={ft} ==")
        # Show table existence
        exists = {}
        for key, table in tables.items():
            try:
                res = conn.execute(text(f"SHOW TABLES LIKE :t"), {'t': table}).fetchone()
                exists[key] = bool(res)
            except Exception:
                exists[key] = False
        print("Table exists:")
        for k, v in exists.items():
            print(f"  - {tables[k]}: {'YES' if v else 'NO'}")

        # Recent import records
        if exists['import_record']:
            try:
                rows = conn.execute(text(
                    f"SELECT id, filename, trading_date, import_status, total_records, success_records, error_records, import_started_at, import_completed_at "
                    f"FROM {tables['import_record']} ORDER BY import_started_at DESC LIMIT :lim"
                ), {'lim': args.limit}).fetchall()
                print(f"\nRecent import records (limit {args.limit}):")
                for r in rows:
                    print(f"  - id={r.id}, date={r.trading_date}, status={r.import_status}, success={r.success_records}, errors={r.error_records}, file={r.filename}")
            except Exception as e:
                print(f"  [ERR] query recent import records failed: {e}")

        # Date-specific counts
        if args.date:
            print(f"\nCounts for trading_date={args.date}:")
            for key in ['import_record', 'daily_trading', 'concept_summary', 'ranking', 'high_record']:
                table = tables[key]
                if not exists.get(key):
                    print(f"  - {table}: table not found")
                    continue
                try:
                    cnt = conn.execute(text(
                        f"SELECT COUNT(*) AS c FROM {table} WHERE trading_date = :d"
                    ), {'d': args.date}).scalar()
                    print(f"  - {table}: {cnt}")
                except Exception as e:
                    print(f"  - {table}: [ERR] {e}")

        # Dates list (from import_record)
        if exists['import_record']:
            try:
                dates = conn.execute(text(
                    f"SELECT DISTINCT trading_date FROM {tables['import_record']} ORDER BY trading_date DESC LIMIT 20"
                )).fetchall()
                dates_str = ", ".join([str(r.trading_date) for r in dates])
                print(f"\nRecent dates (from {tables['import_record']}): {dates_str}")
            except Exception as e:
                print(f"  [ERR] query dates failed: {e}")

    print("\nDone.")


if __name__ == '__main__':
    main()

