# test.py - Place in C:\Users\Prince\Desktop\time-table\
import sys
import os

print("Current directory:", os.getcwd())
print("Python executable:", sys.executable)
print()

# Check if backend folder exists
if os.path.exists('backend'):
    print("✓ backend folder found")
else:
    print("✗ backend folder NOT found")
    sys.exit(1)

# Check required files
required_files = [
    'backend/__init__.py',
    'backend/config.py',
    'backend/main.py',
    'backend/database.py',
    'backend/models.py',
    'backend/auth.py',
]

for file in required_files:
    if os.path.exists(file):
        print(f"✓ {file} found")
    else:
        print(f"✗ {file} NOT found")

# Test import
print("\nTesting imports...")
try:
    sys.path.insert(0, os.getcwd())
    from backend.config import config
    print(f"✓ Config imported successfully")
    print(f"  API_HOST: {config.API_HOST}")
    print(f"  API_PORT: {config.API_PORT}")
except Exception as e:
    print(f"✗ Import error: {e}")

print("\n✅ Setup looks good! Run: python run.py")