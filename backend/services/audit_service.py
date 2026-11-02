from sqlalchemy.orm import Session

from backend.models.admin_operation_log import AdminOperationLog


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
