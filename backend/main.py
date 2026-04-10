# Add these imports at the top if not present
import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed

@app.post("/api/auth/signup")
async def signup(request: dict):
    try:
        username = request.get('username')
        email = request.get('email')
        password = request.get('password')
        full_name = request.get('full_name')
        role = request.get('role', 'student')
        
        # Validation
        if not username or not email or not password:
            raise HTTPException(status_code=400, detail="All fields are required")
        
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            existing = cursor.fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Username or email already exists")
            
            # Create user
            hashed_pw = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            ''', (username, email, hashed_pw, full_name, role, datetime.now()))
            
            user_id = cursor.lastrowid
            
            return {
                "success": True,
                "message": "Account created successfully",
                "user": {
                    "id": user_id,
                    "username": username,
                    "email": email,
                    "name": full_name,
                    "role": role
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login")
async def login(request: dict):
    try:
        username = request.get('username')
        password = request.get('password')
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('''
                SELECT id, username, email, password_hash, full_name, role, is_active 
                FROM users 
                WHERE username = ? OR email = ?
            ''', (username, username))
            
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            if not user['is_active']:
                raise HTTPException(status_code=401, detail="Account is deactivated")
            
            if not verify_password(password, user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', (datetime.now(), user['id']))
            
            return {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "email": user['email'],
                    "name": user['full_name'],
                    "role": user['role']
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))