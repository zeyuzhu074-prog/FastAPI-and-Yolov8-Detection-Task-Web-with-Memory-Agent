from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.dependencies.auth import require_admin
from backend.models.user import User
from backend.services.admin_service import AdminService
from backend.services.audit_service import AuditService


router = APIRouter(
    prefix="/api/admin",
    tags=["管理员后台"]
)


class AdminUserCreateRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "user"


class AdminUserUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    status: Optional[int] = None


class AdminStatusRequest(BaseModel):
    status: int


class AdminResetPasswordRequest(BaseModel):
    new_password: str


@router.get("/users")
def list_users(
    page: int = 1,
    page_size: int = 10,
    keyword: Optional[str] = None,
    status: Optional[int] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.list_users(
            db=db,
            page=page,
            page_size=page_size,
            keyword=keyword,
            status=status,
            role=role,
        )

        return {
            "success": True,
            "message": "用户列表查询成功",
            "data": data,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"用户列表查询失败：{str(e)}",
        )


@router.get("/logs")
def list_operation_logs(
    page: int = 1,
    page_size: int = 20,
    operation_type: Optional[str] = None,
    target_type: Optional[str] = None,
    admin_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    查询管理员操作审计日志。
    """

    try:

        data = AuditService.list_logs(
            db=db,
            page=page,
            page_size=page_size,
            operation_type=operation_type,
            target_type=target_type,
            admin_id=admin_id,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
        )

        return {
            "success": True,
            "message": "操作日志查询成功",
            "data": data,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"操作日志查询失败：{str(e)}",
        )


@router.post("/users")
def create_user(
    request: AdminUserCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.create_user(
            db=db,
            admin_id=admin.id,
            username=request.username,
            password=request.password,
            email=request.email,
            role=request.role,
        )

        return {
            "success": True,
            "message": "用户创建成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"用户创建失败：{str(e)}",
        )


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        return {
            "success": True,
            "message": "用户详情查询成功",
            "data": AdminService.get_user(db, user_id),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.update_user(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            username=request.username,
            email=request.email,
            role=request.role,
            status=request.status,
        )

        return {
            "success": True,
            "message": "用户资料修改成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"用户资料修改失败：{str(e)}",
        )


@router.patch("/users/{user_id}/status")
def set_user_status(
    user_id: int,
    request: AdminStatusRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.set_status(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            status=request.status,
        )

        return {
            "success": True,
            "message": "用户状态修改成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"用户状态修改失败：{str(e)}",
        )


@router.post("/users/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    request: AdminResetPasswordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.reset_password(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
            new_password=request.new_password,
        )

        return {
            "success": True,
            "message": "用户密码重置成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"用户密码重置失败：{str(e)}",
        )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:

        data = AdminService.delete_user(
            db=db,
            admin_id=admin.id,
            user_id=user_id,
        )

        return {
            "success": True,
            "message": "用户已删除",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"用户删除失败：{str(e)}",
        )
