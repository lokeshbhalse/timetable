# backend/routes/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.models import LoginRequest, SignupRequest, TokenResponse, ChangePasswordRequest, ApiResponse
from backend.auth import authenticate_user, create_access_token, get_password_hash, decode_token
from backend.database import db
from datetime import timedelta
from backend.config import config

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    user = authenticate_user(request.email, request.password, request.role)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["email"], "role": user["role"], "id": user["id"]}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "name": user.get("name", "")
        }
    )

@router.post("/signup", response_model=ApiResponse)
async def signup(request: SignupRequest):
    """Create new user account"""
    
    # Check if user already exists
    check_query = "SELECT UserName FROM user_master WHERE UserName = %s"
    existing = db.execute_query(check_query, (request.email,))
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(request.password)
    
    # Insert into user_master
    insert_query = "INSERT INTO user_master (UserName, Password) VALUES (%s, %s)"
    user_id = db.execute_insert(insert_query, (request.email, hashed_password))
    
    if not user_id:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Role-specific inserts
    if request.role == "teacher":
        teacher_query = """
            INSERT INTO facultyreg (name, email, department) 
            VALUES (%s, %s, %s)
        """
        db.execute_insert(teacher_query, (request.full_name, request.email, request.department))
    
    elif request.role == "student":
        # Create students table if needed
        # student_query = "INSERT INTO students (name, email, student_id, department) VALUES (%s, %s, %s, %s)"
        # db.execute_insert(student_query, (request.full_name, request.email, request.student_id, request.department))
        pass
    
    return ApiResponse(
        success=True,
        message="Account created successfully",
        data={"email": request.email, "role": request.role}
    )

@router.post("/change-password", response_model=ApiResponse)
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Change user password"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = payload.get("sub")
    
    # Get current password hash
    query = "SELECT Password FROM user_master WHERE UserName = %s"
    result = db.execute_query(query, (email,))
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    from backend.auth import verify_password
    if not verify_password(request.old_password, result[0]['Password']):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    new_hashed = get_password_hash(request.new_password)
    update_query = "UPDATE user_master SET Password = %s WHERE UserName = %s"
    success = db.execute_update(update_query, (new_hashed, email))
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return ApiResponse(success=True, message="Password changed successfully")

@router.post("/logout")
async def logout():
    """Logout user (client-side token removal)"""
    return {"message": "Logged out successfully"}