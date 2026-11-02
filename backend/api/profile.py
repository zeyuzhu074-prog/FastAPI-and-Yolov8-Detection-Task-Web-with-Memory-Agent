from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.user import User
from backend.services.profile_service import ProfileService


router = APIRouter(
    prefix="/api/profile",
    tags=["个人中心"]
)


class ProfileUpdateRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "success": True,
        "message": "获取个人资料成功",
        "data": ProfileService.get_profile(current_user),
    }


@router.put("/me")
def update_my_profile(
    request: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:

        data = ProfileService.update_profile(
            db=db,
            user=current_user,
            username=request.username,
            email=request.email,
        )

        return {
            "success": True,
            "message": "个人资料修改成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"个人资料修改失败：{str(e)}",
        )


@router.post("/avatar")
async def upload_my_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:

        data = await ProfileService.upload_avatar(
            db=db,
            user=current_user,
            upload_file=file,
        )

        return {
            "success": True,
            "message": "头像上传成功",
            "data": data,
        }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"头像上传失败：{str(e)}",
        )


@router.delete("/avatar")
def delete_my_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:

        data = ProfileService.delete_avatar(
            db=db,
            user=current_user,
        )

        return {
            "success": True,
            "message": "头像已删除",
            "data": data,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"头像删除失败：{str(e)}",
        )
