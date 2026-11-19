"""
database/connection.py
Single database connection function used by every module.
Tries MySQL via .env credentials; automatically falls back to SQLite
if MySQL access is denied or database is unconfigured.
"""
import os
import sqlite3
import bcrypt
from dotenv import load_dotenv

load_dotenv()

_SQLITE_PATH = os.path.join(os.path.dirname(__file__), "rprms.db")

class SQLiteCursorAdapter:
    def __init__(self, conn, dictionary=False):
        self.conn = conn
        self.cur = conn.cursor()
        self.dictionary = dictionary
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql_clean = (
            sql.replace("%s", "?")
               .replace("NOW()", "CURRENT_TIMESTAMP")
               .replace("ON UPDATE NOW()", "")
               .replace("ENGINE=InnoDB", "")
               .replace("AUTO_INCREMENT PRIMARY KEY", "PRIMARY KEY AUTOINCREMENT")
               .replace("TINYINT(1)", "INTEGER")
               .replace("BIGINT UNSIGNED", "INTEGER")
               .replace("INT UNSIGNED", "INTEGER")
        )
        if sql_clean.strip().upper() == "SHOW TABLES":
            sql_clean = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"

        if "ENUM(" in sql_clean:
            import re
            sql_clean = re.sub(r"ENUM\([^)]+\)", "TEXT", sql_clean)

        self.cur.execute(sql_clean, params)
        self.lastrowid = self.cur.lastrowid
        return self

    def fetchone(self):
        row = self.cur.fetchone()
        if row is None:
            return None
        if self.dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = self.cur.fetchall()
        if self.dictionary:
            return [dict(r) for r in rows]
        return rows

    def close(self):
        self.cur.close()

class SQLiteConnAdapter:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        return SQLiteCursorAdapter(self.conn, dictionary=dictionary)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

def _init_sqlite_db(path):
    conn = SQLiteConnAdapter(path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL UNIQUE,
        dept_code TEXT NOT NULL UNIQUE,
        hod_name TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        phone TEXT DEFAULT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        dept_id INTEGER DEFAULT NULL,
        created_by INTEGER DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME DEFAULT NULL
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notif_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        link TEXT DEFAULT NULL,
        is_read INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT NULL,
        action TEXT NOT NULL,
        entity TEXT DEFAULT NULL,
        entity_id INTEGER DEFAULT NULL,
        ip_address TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS papers (
        paper_id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        abstract TEXT DEFAULT NULL,
        keywords TEXT DEFAULT NULL,
        research_area TEXT DEFAULT NULL,
        guide_name TEXT DEFAULT NULL,
        dept_id INTEGER DEFAULT NULL,
        pub_year INTEGER DEFAULT NULL,
        paper_type TEXT NOT NULL DEFAULT 'journal',
        uploaded_by INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        qr_code_path TEXT DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS paper_status_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        old_status TEXT DEFAULT NULL,
        new_status TEXT NOT NULL,
        changed_by INTEGER NOT NULL,
        comments TEXT DEFAULT NULL,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS paper_versions (
        version_id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        version_no INTEGER NOT NULL DEFAULT 1,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT NULL,
        uploaded_by INTEGER NOT NULL,
        change_notes TEXT DEFAULT NULL,
        uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS downloads (
        download_id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        bookmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(paper_id, user_id)
    )""")

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        def hash_pw(plain: str) -> str:
            return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

        depts = [
            ("Master of Computer Applications", "MCA", "Dr. A. Sharma"),
            ("Bachelor of Technology - CSE", "BTECH-CSE", "Dr. B. Verma"),
            ("Master of Business Administration", "MBA", "Dr. C. Gupta"),
        ]
        for name, code, hod in depts:
            cur.execute("INSERT OR IGNORE INTO departments (dept_name, dept_code, hod_name) VALUES (?, ?, ?)", (name, code, hod))
        conn.commit()

        cur.execute("SELECT dept_id FROM departments WHERE dept_code='MCA'")
        mca_row = cur.fetchone()
        mca_id = mca_row[0] if mca_row else 1

        cur.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, is_active) VALUES (?, ?, ?, 'admin', 1)",
                    ("System Admin", "admin@rprms.edu", hash_pw("Admin@123")))
        cur.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, dept_id, is_active) VALUES (?, ?, ?, 'faculty', ?, 1)",
                    ("Dr. Priya Mehta", "faculty@rprms.edu", hash_pw("Faculty@123"), mca_id))
        cur.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, dept_id, is_active) VALUES (?, ?, ?, 'student', ?, 1)",
                    ("Anjali Sharma", "student@rprms.edu", hash_pw("Student@123"), mca_id))
        cur.execute("INSERT OR IGNORE INTO users (full_name, email, password_hash, role, is_active) VALUES (?, ?, ?, 'student', 0)",
                    ("Inactive User", "inactive@rprms.edu", hash_pw("Test@123")))
        conn.commit()

        cur.execute("""
        INSERT OR IGNORE INTO papers (paper_code, title, abstract, keywords, research_area, guide_name, dept_id, pub_year, paper_type, uploaded_by, file_name, file_path, file_size, status)
        VALUES 
        ('PAP-2025-001', 'Deep Learning Architectures for Quantum Computing Simulation', 'An in-depth analysis of neural network algorithms optimized for quantum gate synthesis and noise mitigation.', 'AI, Quantum, Deep Learning', 'Artificial Intelligence', 'Dr. A. Sharma', ?, 2025, 'journal', 2, 'quantum_ai.pdf', 'uploads/papers/quantum_ai.pdf', 2450000, 'approved'),
        ('PAP-2025-002', 'Blockchain Based Decentralized Identity Management', 'Exploring cryptographic zero-knowledge proofs for secure digital identity assertion in web3 ecosystems.', 'Blockchain, ZKP, Security', 'Cyber Security', 'Dr. B. Verma', ?, 2025, 'conference', 2, 'blockchain_id.pdf', 'uploads/papers/blockchain_id.pdf', 1890000, 'pending'),
        ('PAP-2025-003', 'Optimization of High-Throughput Edge Computing Frameworks', 'Evaluating micro-frontend architectures and edge worker latency in distributed IoT networks.', 'Edge Computing, IoT, Web Performance', 'Computer Networks', 'Dr. A. Sharma', ?, 2024, 'thesis', 2, 'edge_computing.pdf', 'uploads/papers/edge_computing.pdf', 3120000, 'approved')
        """, (mca_id, mca_id, mca_id))
        conn.commit()

    conn.close()

_MYSQL_POOL = None
_MYSQL_POOL_FAILED = False
_MYSQL_DIRECT_FAILED = False

def _init_mysql_pool():
    global _MYSQL_POOL, _MYSQL_POOL_FAILED
    if _MYSQL_POOL_FAILED:
        return None
    if _MYSQL_POOL is not None:
        return _MYSQL_POOL
    try:
        from mysql.connector import pooling
        host = os.getenv("DB_HOST", "127.0.0.1")
        # On Windows, 127.0.0.1 connects instantly without IPv6 DNS delay
        if host.lower() in ("localhost", "127.0.0.1"):
            host = "127.0.0.1"

        _MYSQL_POOL = pooling.MySQLConnectionPool(
            pool_name="rprms_app_pool",
            pool_size=3,
            pool_reset_session=True,
            host=host,
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Mysql@123"),
            database=os.getenv("DB_NAME", "rprms_db"),
            autocommit=False
        )
        return _MYSQL_POOL
    except Exception:
        _MYSQL_POOL_FAILED = True
        return None

def get_connection():
    """
    High-performance database connection.
    Uses connection pooling for instant sub-millisecond query responses.
    Falls back to SQLite if MySQL is unavailable.
    """
    pool = _init_mysql_pool()
    if pool is not None:
        try:
            return pool.get_connection()
        except Exception:
            pass

    # Direct connection attempt if pool is exhausted or failed
    global _MYSQL_DIRECT_FAILED
    if not _MYSQL_DIRECT_FAILED:
        try:
            import mysql.connector
            host = os.getenv("DB_HOST", "127.0.0.1")
            if host.lower() in ("localhost", "127.0.0.1"):
                host = "127.0.0.1"
            return mysql.connector.connect(
                host=host,
                port=int(os.getenv("DB_PORT", 3306)),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", "Mysql@123"),
                database=os.getenv("DB_NAME", "rprms_db"),
                connection_timeout=1,
                autocommit=False
            )
        except Exception:
            _MYSQL_DIRECT_FAILED = True

    # Seamless fallback to SQLite
    if not os.path.exists(_SQLITE_PATH):
        _init_sqlite_db(_SQLITE_PATH)
    return SQLiteConnAdapter(_SQLITE_PATH)
