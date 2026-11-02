from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.dependencies.auth import get_current_user, require_admin
from backend.models.user import User
from backend.services.history_service import HistoryService


router = APIRouter(
    prefix="/api/history",
    tags=["历史记录"]
)


class HistoryUpdateRequest(BaseModel):
    original_name: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[str] = None


@router.get("")
async def get_history_list(
    page: int = 1,
    page_size: int = 10,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filename: Optional[str] = None,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询历史检测记录。

    普通用户只能查询自己的记录；管理员可查询全部，
    并可按 user_id / username 过滤。
    """

    try:

        result = HistoryService.get_history_list(
            db=db,
            user_id=current_user.id,
            is_admin=current_user.role == "admin",
            page=page,
            page_size=page_size,
            task_type=task_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            filename=filename,
            target_user_id=user_id,
            username=username,
        )

        return {
            "success": True,
            "message": "历史记录查询成功",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"历史记录查询失败：{str(e)}",
        )


@router.get("/{record_id}")
async def get_history_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询指定历史检测记录的详细信息。
    """

    try:

        result = HistoryService.get_history_detail(
            db=db,
            record_id=record_id,
            user_id=current_user.id,
            is_admin=current_user.role == "admin",
        )

        return {
            "success": True,
            "message": "历史记录详情查询成功",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"历史记录详情查询失败：{str(e)}",
        )


@router.put("/{record_id}")
async def update_history_record(
    record_id: int,
    request: HistoryUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    管理员修改检测记录（仅允许展示字段）。
    """

    try:

        result = HistoryService.update_record(
            db=db,
            record_id=record_id,
            admin_id=admin.id,
            original_name=request.original_name,
            remark=request.remark,
            status=request.status,
        )

        return {
            "success": True,
            "message": "检测记录修改成功",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检测记录修改失败：{str(e)}",
        )


@router.delete("/{record_id}")
async def delete_history_record(
    record_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    管理员物理删除检测记录及其结果文件。
    """

    try:

        result = HistoryService.delete_record(
            db=db,
            record_id=record_id,
            admin_id=admin.id,
        )

        return {
            "success": True,
            "message": "检测记录已删除",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"检测记录删除失败：{str(e)}",
        )
