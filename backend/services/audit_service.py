from datetime import datetime, timedelta

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.models.admin_operation_log import AdminOperationLog
from backend.models.user import User


ALLOWED_OPERATION_TYPES = (
    "create",
    "update",
    "delete",
    "disable",
    "enable",
    "reset_password",
)

ALLOWED_TARGET_TYPES = (
    "user",
    "detection_record",
)


def _parse_day(value: str, field_name: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValueError(f"{field_name}格式应为 YYYY-MM-DD")


class AuditService:

    @staticmethod
    def log(
        db: Session,
        admin_id: int,
        operation_type: str,
        target_type: str,
        target_id: int = None,
        description: str = None,
    ):
        """
        记录管理员重要操作，便于后续追溯。
        """

        record = AdminOperationLog(
            admin_id=admin_id,
            operation_type=operation_type,
            target_type=target_type,
            target_id=target_id,
            description=description,
        )

        db.add(record)
        db.commit()

        return record

    @staticmethod
    def list_logs(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        operation_type: str = None,
        target_type: str = None,
        admin_id: int = None,
        start_date: str = None,
        end_date: str = None,
        keyword: str = None,
    ):
        """
        分页查询管理员操作日志。
        """

        if page < 1:
            raise ValueError("页码必须大于等于1")

        if page_size < 1:
            raise ValueError("每页数量必须大于等于1")

        if page_size > 100:
            raise ValueError("每页数量不能超过100")

        if (
            operation_type
            and operation_type not in ALLOWED_OPERATION_TYPES
        ):
            raise ValueError("不支持的操作类型")

        if (
            target_type
            and target_type not in ALLOWED_TARGET_TYPES
        ):
            raise ValueError("不支持的对象类型")

        query = db.query(AdminOperationLog)

        if operation_type:
            query = query.filter(
                AdminOperationLog.operation_type
                == operation_type
            )

        if target_type:
            query = query.filter(
                AdminOperationLog.target_type
                == target_type
            )

        if admin_id is not None:
            query = query.filter(
                AdminOperationLog.admin_id == admin_id
            )

        if start_date:
            start_dt = _parse_day(start_date, "开始日期")
            query = query.filter(
                AdminOperationLog.created_at >= start_dt
            )

        if end_date:
            end_dt = (
                _parse_day(end_date, "结束日期")
                + timedelta(days=1)
            )
            query = query.filter(
                AdminOperationLog.created_at < end_dt
            )

        if keyword:
            query = query.filter(
                AdminOperationLog.description.like(
                    f"%{keyword.strip()}%"
                )
            )

        total = query.count()

        logs = (
            query
            .order_by(desc(AdminOperationLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        admin_ids = {log.admin_id for log in logs}
        admin_names = {}

        if admin_ids:
            admins = (
                db.query(User)
                .filter(User.id.in_(admin_ids))
                .all()
            )
            admin_names = {
                admin.id: admin.username
                for admin in admins
            }

        items = [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "admin_username": admin_names.get(log.admin_id),
                "operation_type": log.operation_type,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "description": log.description,
                "created_at": (
                    log.created_at.isoformat()
                    if log.created_at
                    else None
                ),
            }
            for log in logs
        ]

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (
                (total + page_size - 1) // page_size
                if total > 0
                else 0
            ),
        }
