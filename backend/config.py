# backend/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Get the root directory (where backend folder is located)
ROOT_DIR = Path(__file__).parent.parent
ENV_PATH = ROOT_DIR / '.env'

# Load .env file from root directory
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    print(f"✓ Loaded .env from {ENV_PATH}")
else:
    load_dotenv()  # Try default location
    print(f"⚠ No .env file found at {ENV_PATH}, using defaults")

class Config:
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "timetable")
    
    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # CORS - Handle multiple origins properly
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
    
    # Server
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    
    # File paths
    BASE_DIR = str(ROOT_DIR)
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    def __repr__(self):
        return f"""
Config:
  DB: {self.DB_USER}@{self.DB_HOST}/{self.DB_NAME}
  API: http://{self.API_HOST}:{self.API_PORT}
  CORS: {self.CORS_ORIGINS}
  BASE_DIR: {self.BASE_DIR}
        """

config = Config()

# Print config on startup (for debugging)
print("✅ Configuration loaded successfully!")
print(f"   API Server: http://{config.API_HOST}:{config.API_PORT}")
print(f"   Database: {config.DB_NAME} on {config.DB_HOST}")
print(f"   CORS Origins: {config.CORS_ORIGINS}")