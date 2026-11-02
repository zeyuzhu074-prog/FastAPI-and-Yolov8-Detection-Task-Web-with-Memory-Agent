import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.detection_record import (
    DetectionRecord
)

from backend.services.image_service import (
    ImageService
)


router = APIRouter(
    prefix="/api/history",
    tags=["检测历史"]
)


@router.get("/")
def get_history(
    db: Session = Depends(get_db)
):
    """
    获取检测历史记录。
    """

    records = (
        db.query(DetectionRecord)
        .order_by(
            DetectionRecord.created_at.desc()
        )
        .all()
    )

    data = []

    for record in records:

        data.append(
            {
                "id": record.id,

                "image_name": (
                    record.image_name
                ),

                "model_name": (
                    record.model_name
                ),

                "object_count": (
                    record.object_count
                ),

                "inference_time": (
                    record.inference_time
                ),

                "status": (
                    record.status
                ),

                "created_at": (
                    record.created_at.isoformat()
                    if record.created_at
                    else None
                )
            }
        )

    return {
        "success": True,
        "data": data
    }


@router.get("/{record_id}")
def get_history_detail(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定检测任务的详细结果。
    """

    record = (
        db.query(DetectionRecord)
        .filter(
            DetectionRecord.id == record_id
        )
        .first()
    )

    if record is None:

        raise HTTPException(
            status_code=404,
            detail="检测记录不存在"
        )

    detections = []

    if record.detection_result:

        try:

            detections = json.loads(
                record.detection_result
            )

        except Exception:

            detections = []

    return {
        "success": True,

        "data": {
            "id": record.id,

            "image_name": (
                record.image_name
            ),

            "original_path": (
                record.original_path
            ),

            "result_path": (
                record.result_path
            ),

            "model_name": (
                record.model_name
            ),

            "object_count": (
                record.object_count
            ),

            "inference_time": (
                record.inference_time
            ),

            "status": (
                record.status
            ),

            "detections": detections,

            "created_at": (
                record.created_at.isoformat()
                if record.created_at
                else None
            )
        }
    }


@router.delete("/{record_id}")
def delete_history(
    record_id: int,
    db: Session = Depends(get_db)
):
    """
    删除检测历史记录。
    """

    record = (
        db.query(DetectionRecord)
        .filter(
            DetectionRecord.id == record_id
        )
        .first()
    )

    if record is None:

        raise HTTPException(
            status_code=404,
            detail="检测记录不存在"
        )

    # 删除原始图片
    ImageService.delete_file(
        record.original_path
    )

    # 删除结果图片
    if record.result_path:

        ImageService.delete_file(
            record.result_path
        )

    # 删除数据库记录
    db.delete(record)
    db.commit()

    return {
        "success": True,
        "message": "删除成功"
    }