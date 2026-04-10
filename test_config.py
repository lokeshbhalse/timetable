# test_config.py
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing config.py...")
print("=" * 50)

try:
    from backend.config import config
    
    print("\n✅ Config imported successfully!")
    print("\nCurrent Configuration:")
    print(f"  DB_HOST: {config.DB_HOST}")
    print(f"  DB_USER: {config.DB_USER}")
    print(f"  DB_PASSWORD: {'*' * len(config.DB_PASSWORD) if config.DB_PASSWORD else '(empty)'}")
    print(f"  DB_NAME: {config.DB_NAME}")
    print(f"  API_HOST: {config.API_HOST}")
    print(f"  API_PORT: {config.API_PORT}")
    print(f"  CORS_ORIGINS: {config.CORS_ORIGINS}")
    print(f"  BASE_DIR: {config.BASE_DIR}")
    print(f"  DATA_DIR: {config.DATA_DIR}")
    
    # Test database connection
    print("\n" + "=" * 50)
    print("Testing database connection...")
    
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        print("✅ Database connection successful!")
        conn.close()
    except Exception as e:
        print(f"⚠ Database connection failed: {e}")
        print("   Make sure MySQL is running and database exists")
    
except Exception as e:
    print(f"❌ Failed to import config: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)