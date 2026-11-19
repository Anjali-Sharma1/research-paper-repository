"""
test_connection.py
Quick check that MySQL connection works before running the app.
Run: python test_connection.py
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from database.connection import get_connection
try:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]
    print("✅ Connected to database!")
    print(f"   Tables found: {tables if tables else 'None — run schema.sql first'}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("   → Check your .env file and confirm MySQL is running.")
