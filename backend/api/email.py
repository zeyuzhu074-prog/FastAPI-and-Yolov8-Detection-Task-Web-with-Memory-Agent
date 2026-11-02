from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.dependencies.auth import get_current_user
from backend.models.detection_record import DetectionRecord
from backend.models.user import User
from backend.services.email_service import send_report


router = APIRouter(
    prefix="/api/email",
    tags=["邮件报告"]
)


class SendReportRequest(BaseModel):
    to_email: Optional[str] = None


@router.post("/send-report/{record_id}")
def send_detection_report(
    record_id: int,
    request: SendReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    将指定检测记录的报告发送到邮箱。

    普通用户只能发送自己的记录；管理员可以发送任意记录。
    未指定收件邮箱时，默认使用记录所属用户的邮箱。
    """

    record = (
        db.query(DetectionRecord)
        .filter(DetectionRecord.id == record_id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="检测记录不存在",
        )

    if (
        current_user.role != "admin"
        and record.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="检测记录不存在或无权访问",
        )

    owner = (
        db.query(User)
        .filter(User.id == record.user_id)
        .first()
    )

    recipient = (
        request.to_email
        or (owner.email if owner else None)
        or current_user.email
    )

    if not recipient:
        raise HTTPException(
            status_code=400,
            detail="当前用户未设置邮箱，请先填写收件邮箱",
        )

    try:

        result = send_report(
            db=db,
            record=record,
            recipient_email=recipient,
        )

        return {
            "success": True,
            "message": "检测报告已发送",
            "data": result,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"邮件发送失败：{str(e)}",
        )
