from fastapi import APIRouter, Depends, HTTPException, status
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), full_name=user.full_name, email=user.email,
        role=user.role, phone=user.phone, is_verified=user.is_verified
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest):
    if payload.role not in {"student", "owner"}:
        raise HTTPException(status_code=400, detail="Role must be student or owner")
    if await User.find_one(User.email == payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(
        full_name=payload.full_name.strip(), email=payload.email,
        phone=payload.phone, password_hash=hash_password(payload.password),
        role=payload.role,
    )
    await user.insert()
    return TokenResponse(access_token=create_access_token(str(user.id), user.role), user=user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await User.find_one(User.email == payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled")
    return TokenResponse(access_token=create_access_token(str(user.id), user.role), user=user_response(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user_response(user)
