from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.statistics_service import StatisticsService


router = APIRouter(
    prefix="/api/statistics",
    tags=["统计分析"]
)


# ==============================
# 1. 获取当前用户总体统计
# ==============================

@router.get("/overview")
def get_overview(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取用户总体统计信息
    """

    try:
        result = StatisticsService.get_user_overview(
            db=db,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "获取总体统计成功",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取总体统计失败：{str(e)}"
        )


# ==============================
# 2. 获取目标类别统计
# ==============================

@router.get("/classes")
def get_class_statistics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取当前用户的目标类别统计
    """

    try:
        result = StatisticsService.get_user_class_statistics(
            db=db,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "获取类别统计成功",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取类别统计失败：{str(e)}"
        )


# ==============================
# 3. 获取单次检测统计
# ==============================

@router.get("/record/{record_id}")
def get_record_statistics(
    record_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取某一次检测任务的详细统计
    """

    try:
        result = StatisticsService.get_record_statistics(
            db=db,
            user_id=user_id,
            record_id=record_id
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="检测记录不存在或无权访问"
            )

        return {
            "success": True,
            "message": "获取检测结果统计成功",
            "data": result
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取检测结果统计失败：{str(e)}"
        )


# ==============================
# 4. 获取检测趋势
# ==============================

@router.get("/trend")
def get_detection_trend(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取当前用户检测任务趋势
    """

    try:
        result = StatisticsService.get_detection_trend(
            db=db,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "获取检测趋势成功",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取检测趋势失败：{str(e)}"
        )

# ==============================
# 5. 获取每日类别趋势
# ==============================

@router.get("/class-trend")
def get_class_trend(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    获取当前用户各目标类别的每日检测趋势
    """

    try:
        result = StatisticsService.get_class_trend(
            db=db,
            user_id=user_id
        )

        return {
            "success": True,
            "message": "获取类别趋势成功",
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取类别趋势失败：{str(e)}"
        )