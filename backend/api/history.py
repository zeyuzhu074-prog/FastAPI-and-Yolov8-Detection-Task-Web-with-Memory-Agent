from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.history_service import HistoryService


router = APIRouter(
    prefix="/api/history",
    tags=["历史记录"]
)


# ==========================================
# 1. 查询历史记录列表
# ==========================================

@router.get("")
async def get_history_list(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    task_type: str = None,
    db: Session = Depends(get_db)
):
    """
    查询用户历史检测记录
    """

    try:

        result = HistoryService.get_history_list(
            db=db,
            user_id=user_id,
            page=page,
            page_size=page_size,
            task_type=task_type
        )

        return {
            "success": True,
            "message": "历史记录查询成功",
            "data": result
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"历史记录查询失败：{str(e)}"
        )


# ==========================================
# 2. 查询历史记录详情
# ==========================================

@router.get("/{record_id}")
async def get_history_detail(
    record_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    查询指定历史检测记录的详细信息
    """

    try:

        result = HistoryService.get_history_detail(
            db=db,
            user_id=user_id,
            record_id=record_id
        )

        return {
            "success": True,
            "message": "历史记录详情查询成功",
            "data": result
        }

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"历史记录详情查询失败：{str(e)}"
        )