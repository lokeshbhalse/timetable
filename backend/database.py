# backend/database.py
import mysql.connector
from mysql.connector import Error
from backend.config import config
from typing import Optional, Dict, Any, List

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_connection(self):
        """Get database connection"""
        try:
            connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Dict]]:
        """Execute SELECT query and return results"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Query error: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Execute INSERT query and return last inserted ID"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.lastrowid
        except Error as e:
            print(f"Insert error: {e}")
            connection.rollback()
            return None
        finally:
            cursor.close()
            connection.close()
    
    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Execute UPDATE/DELETE query and return success status"""
        connection = self.get_connection()
        if not connection:
            return False
        
        cursor = connection.cursor()
        try:
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount > 0
        except Error as e:
            print(f"Update error: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()

db = Database()