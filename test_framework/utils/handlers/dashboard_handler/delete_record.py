#!/usr/bin/env python3
"""
Simple command-line tool to delete performance database records.

Usage:
    python delete_record.py                    # Delete last record
    python delete_record.py --test login       # Delete last record for specific test
    python delete_record.py --show 5           # Show last 5 records first
"""

import sys
import argparse
from test_framework.utils.handlers.dashboard_handler.dashboard_manager import PerformanceDashboardManager

def main():
    parser = argparse.ArgumentParser(description='Delete performance database records')
    parser.add_argument('--test', help='Delete last record for specific test name')
    parser.add_argument('--show', type=int, help='Show last N records before deleting')
    parser.add_argument('--db', default=r"C:\performance-data\performance.db", help='Database path')
    
    args = parser.parse_args()
    
    try:
        dashboard = PerformanceDashboardManager(
            use_sqlite=True,
            db_path=args.db
        )
        
        # Show records first if requested
        if args.show:
            print(f"\nLast {args.show} records:")
            history = dashboard.get_filtered_history(limit=args.show)
            for i, record in enumerate(reversed(history)):
                print(f"{i+1}: {record['test_run_timestamp']} - {record['duration']:.3f}s - {record['test_name']}")
            print()
            
        # Delete record
        if args.test:
            success = dashboard.delete_last_record(test_name=args.test)
            if success:
                print(f"✅ Deleted last record for test: {args.test}")
            else:
                print(f"❌ No records found for test: {args.test}")
        else:
            success = dashboard.delete_last_record()
            if success:
                print("✅ Deleted last record")
            else:
                print("❌ No records found to delete")
                
        dashboard.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()