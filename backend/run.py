# backend/run.py
import sys
import os

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Change working directory to parent
os.chdir(parent_dir)

import uvicorn
import backend.config

if __name__ == "__main__":
    print("=" * 60)
    print("Timetable Generator API Server")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")
    print(f"Starting server on http://{backend.config.config.API_HOST}:{backend.config.config.API_PORT}")
    print(f"API Documentation: http://{backend.config.config.API_HOST}:{backend.config.config.API_PORT}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host=backend.config.config.API_HOST,
        port=backend.config.config.API_PORT,
        reload=True
    )