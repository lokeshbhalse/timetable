# backend/database.py - SQLite Version
import sqlite3
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sgsits_timetable.db")

@contextmanager
def get_db():
    """Get database connection with context manager"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(DB_PATH)
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Execute SELECT query and return results"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            result = [dict(row) for row in cursor.fetchall()]
            return result
        except Exception as e:
            print(f"Query error: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Execute INSERT query and return last inserted ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Insert error: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute UPDATE/DELETE query and return success status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Update error: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

db = Database()

def init_db():
    """Initialize database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'teacher', 'student')) DEFAULT 'student',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Teachers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT NOT NULL,
            year INTEGER NOT NULL,
            semester INTEGER NOT NULL,
            teacher_id INTEGER,
            teacher2_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (teacher2_id) REFERENCES teachers(id)
        )
    ''')

    # Ensure existing subjects table has semester column
    cursor.execute("PRAGMA table_info(subjects)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    if 'semester' not in existing_columns:
        cursor.execute("ALTER TABLE subjects ADD COLUMN semester INTEGER NOT NULL DEFAULT 1")
    
    # Insert default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        import hashlib
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', 'admin@sgsits.com', admin_hash, 'System Administrator', 'admin'))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")