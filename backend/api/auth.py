from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend.database.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.user import User
from backend.services.auth_service import AuthService
from backend.services.profile_service import user_to_dict
from backend.config.settings import JWT_EXPIRE_MINUTES
from backend.utils.security import create_access_token


router = APIRouter(
    prefix="/api/auth",
    tags=["用户认证"]
)


# ==========================================
# 请求数据模型
# ==========================================

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    user_id: Optional[int] = None
    old_password: str
    new_password: str
    two_new_password: str


# ==========================================
# 用户注册
# ==========================================

@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册接口
    """

    try:

        user = AuthService.register_user(
            db=db,
            username=request.username,
            password=request.password,
            email=request.email
        )

        return {
            "success": True,
            "message": "注册成功",
            "data": user_to_dict(user)
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"注册失败：{str(e)}"
        )


# ==========================================
# 用户登录
# ==========================================

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录接口
    """

    try:

        user = AuthService.login_user(
            db=db,
            username=request.username,
            password=request.password
        )

        return {
            "success": True,
            "message": "登录成功",
            "data": {
                **user_to_dict(user),
                "access_token": create_access_token(
                    user_id=user.id,
                    username=user.username,
                    role=user.role
                ),
                "token_type": "bearer",
                "expires_in": JWT_EXPIRE_MINUTES * 60,
            }
        }

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"登录失败：{str(e)}"
        )


# ==========================================
# 修改密码
# ==========================================

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    修改用户密码
    """

    try:

        user = AuthService.change_password(
            db=db,
            user_id=current_user.id,
            old_password=request.old_password,
            new_password=request.new_password,
            two_new_password=request.two_new_password
        )

        return {
            "success": True,
            "message": "密码修改成功",
            "data": {
                "user_id": user.id,
                "username": user.username
            }
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"修改密码失败：{str(e)}"
        )
