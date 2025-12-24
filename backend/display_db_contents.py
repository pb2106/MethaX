#!/usr/bin/env python3
"""
Display contents of methax.db SQLite database.
Shows all tables and their data.
"""
import sqlite3
from pathlib import Path
from tabulate import tabulate


def display_db_contents():
    """Display all tables and their contents from methax.db."""
    
    db_path = Path(__file__).parent / "methax.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("📊 Database is empty - no tables found\n")
            return
        
        print("\n" + "="*80)
        print("  MethaX Database Contents (methax.db)")
        print("="*80 + "\n")
        
        for table_name, in tables:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"📋 Table: {table_name.upper()}")
            print(f"   Rows: {len(rows)}")
            
            if rows:
                print(f"\n{tabulate(rows, headers=columns, tablefmt='grid')}\n")
            else:
                print("   (Empty table)\n")
            
            print("-" * 80 + "\n")
        
        conn.close()
        print("✅ Database display complete\n")
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")


if __name__ == "__main__":
    display_db_contents()
