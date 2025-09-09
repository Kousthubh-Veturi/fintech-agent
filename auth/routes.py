"""
Authentication routes and OAuth integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from typing import Optional
import re
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .database import (
    get_db, User, LoginAttempt, Session as UserSession,
    verify_password, get_password_hash, create_access_token, verify_token,
    generate_totp_secret, generate_totp_qr, verify_totp, generate_backup_codes,
    generate_reset_token, generate_verification_token
)
from .email_service import email_service
from .schemas import (
    UserCreate, UserLogin, UserResponse, Token, PasswordReset,
    TwoFactorSetup, TwoFactorVerify, PasswordResetRequest
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    return request.client.host

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_strong_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

def log_login_attempt(db: Session, email: str, ip_address: str, success: bool, user_agent: str = None):
    """Log login attempt for security tracking"""
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        success=success,
        user_agent=user_agent
    )
    db.add(attempt)
    db.commit()

def check_rate_limit(db: Session, email: str, ip_address: str) -> bool:
    """Check if user/IP is rate limited"""
    # Check failed attempts in last 15 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    failed_attempts = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,
        LoginAttempt.attempted_at > cutoff
    ).count()
    
    return failed_attempts < 5

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    email = verify_token(token)
    
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        logger.info(f"Registration attempt for email: {user_data.email}")
        
        # Validate input
        if not is_valid_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        if not is_strong_password(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
            )
        
        # Check if user already exists (with retry for database connection issues)
        try:
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()
        except Exception as db_error:
            logger.error(f"Database connection error during user lookup: {db_error}")
            # Try to refresh the connection
            db.close()
            db = next(get_db())
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already registered"
            )
        
        # Create user
        verification_token = generate_verification_token()
        hashed_password = get_password_hash(user_data.password)
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            verification_token=verification_token,
            verification_token_expires=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send verification email (don't fail registration if email fails)
        try:
            email_service.send_verification_email(user.email, verification_token)
        except Exception as e:
            logger.warning(f"Failed to send verification email: {e}")
        
        logger.info(f"User registered successfully: {user.email}")
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_verified=user.is_verified,
            is_2fa_enabled=user.is_2fa_enabled
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login user"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    
    # Check rate limiting
    if not check_rate_limit(db, user_data.email, ip_address):
        log_login_attempt(db, user_data.email, ip_address, False, user_agent)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later."
        )
    
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        log_login_attempt(db, user_data.email, ip_address, False, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        log_login_attempt(db, user_data.email, ip_address, False, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Check email verification - REQUIRED!
    if not user.is_verified:
        log_login_attempt(db, user_data.email, ip_address, False, user_agent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email address before logging in. Check your inbox for the verification link."
        )
    
    # Check 2FA if enabled
    if user.is_2fa_enabled:
        if not user_data.totp_code:
            log_login_attempt(db, user_data.email, ip_address, False, user_agent)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required"
            )
        
        if not verify_totp(user.totp_secret, user_data.totp_code):
            # Check backup codes
            backup_codes = json.loads(user.backup_codes) if user.backup_codes else []
            if user_data.totp_code.upper() not in backup_codes:
                log_login_attempt(db, user_data.email, ip_address, False, user_agent)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code"
                )
            else:
                # Remove used backup code
                backup_codes.remove(user_data.totp_code.upper())
                user.backup_codes = json.dumps(backup_codes)
                db.commit()
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Create session
    session = UserSession(
        user_id=user.id,
        session_token=access_token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(session)
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    log_login_attempt(db, user_data.email, ip_address, True, user_agent)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_verified=user.is_verified,
            is_2fa_enabled=user.is_2fa_enabled
        )
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user"""
    # Deactivate all user sessions
    db.query(UserSession).filter(UserSession.user_id == current_user.id).update({"is_active": False})
    db.commit()
    
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_verified=current_user.is_verified,
        is_2fa_enabled=current_user.is_2fa_enabled
    )

@router.post("/verify-email")
async def verify_email(request_data: dict, db: Session = Depends(get_db)):
    """Verify email address"""
    token = request_data.get("token")
    user = db.query(User).filter(
        User.verification_token == token,
        User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification_email(request_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Resend verification email"""
    email = request_data.email
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists and is unverified, a new verification email has been sent"}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified"
        )
    
    # Generate new verification token
    verification_token = generate_verification_token()
    user.verification_token = verification_token
    user.verification_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    
    # Send verification email
    try:
        email_service.send_verification_email(user.email, verification_token)
    except Exception as e:
        logger.warning(f"Failed to send verification email: {e}")
    
    return {"message": "If the email exists and is unverified, a new verification email has been sent"}

@router.post("/request-account-deletion")
async def request_account_deletion(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Request account deletion with email verification"""
    if current_user.is_verified:
        # Generate deletion token
        deletion_token = generate_verification_token()
        current_user.reset_token = deletion_token  # Reuse reset_token field for deletion
        current_user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # Send deletion confirmation email
        try:
            email_service.send_account_deletion_email(current_user.email, deletion_token)
        except Exception as e:
            logger.warning(f"Failed to send account deletion email: {e}")
        
        return {"message": "Account deletion confirmation email sent. Check your inbox."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify your email first"
        )

@router.post("/delete-account-with-password")
async def delete_account_with_password(
    password: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Delete account with password verification"""
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )
    
    # Delete user account
    db.delete(current_user)
    db.commit()
    
    return {"message": "Account deleted successfully"}

@router.post("/delete-account-with-token")
async def delete_account_with_token(token: str, db: Session = Depends(get_db)):
    """Delete account with email token verification"""
    user = db.query(User).filter(
        User.reset_token == token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired deletion token"
        )
    
    # Delete user account
    db.delete(user)
    db.commit()
    
    return {"message": "Account deleted successfully"}

@router.post("/forgot-password")
async def forgot_password(request_data: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset"""
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    reset_token = generate_reset_token()
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    email_service.send_password_reset(user.email, reset_token)
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """Reset password with token"""
    user = db.query(User).filter(
        User.reset_token == reset_data.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if not is_strong_password(reset_data.new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
        )
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/setup-2fa", response_model=TwoFactorSetup)
async def setup_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Setup 2FA for user"""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    secret = generate_totp_secret()
    qr_code = generate_totp_qr(current_user.email, secret)
    backup_codes = generate_backup_codes()
    
    # Store secret (not yet enabled)
    current_user.totp_secret = secret
    current_user.backup_codes = json.dumps(backup_codes)
    db.commit()
    
    return TwoFactorSetup(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@router.post("/verify-2fa")
async def verify_2fa_setup(verify_data: TwoFactorVerify, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify and enable 2FA"""
    if current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    if not verify_totp(current_user.totp_secret, verify_data.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )
    
    current_user.is_2fa_enabled = True
    db.commit()
    
    # Send backup codes via email
    backup_codes = json.loads(current_user.backup_codes) if current_user.backup_codes else []
    email_service.send_2fa_backup_codes(current_user.email, backup_codes)
    
    return {"message": "2FA enabled successfully"}

@router.post("/disable-2fa")
async def disable_2fa(totp_code: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Disable 2FA"""
    if not current_user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    if not verify_totp(current_user.totp_secret, totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid 2FA code"
        )
    
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    current_user.backup_codes = None
    db.commit()
    
    return {"message": "2FA disabled successfully"}
