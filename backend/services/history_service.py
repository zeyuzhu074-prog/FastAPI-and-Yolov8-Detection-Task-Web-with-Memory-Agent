from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import (
    DetectionClassStatistics,
)
from backend.models.user import User
from backend.services.audit_service import AuditService


ALLOWED_TASK_TYPES = ("image", "video")
ALLOWED_STATUSES = ("processing", "completed", "failed")


def _parse_day(value: str, field_name: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name}格式应为 YYYY-MM-DD"
        )


def _record_to_item(record, username=None):
    return {
        "id": record.id,
        "user_id": record.user_id,
        "username": username,
        "task_type": record.task_type,
        "original_name": record.original_name,
        "model_name": record.model_name,
        "status": record.status,
        "object_count": record.object_count,
        "max_objects": record.max_objects,
        "average_objects": record.average_objects,
        "inference_time": record.inference_time,
        "frame_count": record.frame_count,
        "width": record.width,
        "height": record.height,
        "fps": record.fps,
        "remark": record.remark,
        "created_at": (
            record.created_at.isoformat()
            if record.created_at
            else None
        ),
    }


class HistoryService:

    @staticmethod
    def get_history_list(
        db: Session,
        user_id: int = None,
        is_admin: bool = False,
        page: int = 1,
        page_size: int = 10,
        task_type: str = None,
        status: str = None,
        start_date: str = None,
        end_date: str = None,
        filename: str = None,
        target_user_id: int = None,
        username: str = None,
    ):
        """
        查询历史检测记录。

        普通用户只能查询自己的记录；管理员可以查询全部记录，
        并可按 user_id / username 过滤。
        """

        if page < 1:
            raise ValueError("页码必须大于等于1")

        if page_size < 1:
            raise ValueError("每页数量必须大于等于1")

        if page_size > 100:
            raise ValueError("每页数量不能超过100")

        if task_type and task_type not in ALLOWED_TASK_TYPES:
            raise ValueError("任务类型只能是image或video")

        if status and status not in ALLOWED_STATUSES:
            raise ValueError(
                "状态只能是processing、completed或failed"
            )

        query = db.query(DetectionRecord)

        # 权限范围
        if not is_admin:
            query = query.filter(
                DetectionRecord.user_id == user_id
            )
        elif target_user_id is not None:
            query = query.filter(
                DetectionRecord.user_id == target_user_id
            )

        # 管理员按用户名过滤
        if is_admin and username:
            query = query.join(
                User,
                User.id == DetectionRecord.user_id
            ).filter(
                User.username.like(f"%{username.strip()}%")
            )

        if task_type:
            query = query.filter(
                DetectionRecord.task_type == task_type
            )

        if status:
            query = query.filter(
                DetectionRecord.status == status
            )

        if filename:
            query = query.filter(
                DetectionRecord.original_name.like(
                    f"%{filename.strip()}%"
                )
            )

        if start_date:
            start_dt = _parse_day(start_date, "开始日期")
            query = query.filter(
                DetectionRecord.created_at >= start_dt
            )

        if end_date:
            end_dt = (
                _parse_day(end_date, "结束日期")
                + timedelta(days=1)
            )
            query = query.filter(
                DetectionRecord.created_at < end_dt
            )

        total = query.count()

        records = (
            query
            .order_by(desc(DetectionRecord.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        usernames = {}
        user_ids = {r.user_id for r in records}

        if user_ids:
            users = (
                db.query(User)
                .filter(User.id.in_(user_ids))
                .all()
            )
            usernames = {
                u.id: u.username
                for u in users
            }

        items = [
            _record_to_item(
                record,
                usernames.get(record.user_id)
            )
            for record in records
        ]

        pages = (
            (total + page_size - 1) // page_size
            if total > 0
            else 0
        )

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
        }

    @staticmethod
    def get_history_detail(
        db: Session,
        record_id: int,
        user_id: int = None,
        is_admin: bool = False,
    ):
        """
        查询单条历史检测记录详情。
        """

        query = db.query(DetectionRecord).filter(
            DetectionRecord.id == record_id
        )

        if not is_admin:
            query = query.filter(
                DetectionRecord.user_id == user_id
            )

        record = query.first()

        if record is None:
            raise ValueError("检测记录不存在或无权访问")

        class_statistics = (
            db.query(DetectionClassStatistics)
            .filter(
                DetectionClassStatistics.record_id
                == record.id
            )
            .order_by(
                DetectionClassStatistics.count.desc()
            )
            .all()
        )

        owner = (
            db.query(User)
            .filter(User.id == record.user_id)
            .first()
        )

        data = _record_to_item(
            record,
            owner.username if owner else None
        )

        data.update({
            "original_path": record.original_path,
            "result_path": record.result_path,
            "error_message": record.error_message,
            "class_statistics": [
                {
                    "class_id": item.class_id,
                    "class_name": item.class_name,
                    "count": item.count,
                }
                for item in class_statistics
            ],
        })

        return data

    @staticmethod
    def update_record(
        db: Session,
        record_id: int,
        admin_id: int,
        original_name: str = None,
        remark: str = None,
        status: str = None,
    ):
        """
        管理员修改检测记录的展示字段。
        不允许修改 user_id、文件路径等关键字段。
        """

        record = (
            db.query(DetectionRecord)
            .filter(DetectionRecord.id == record_id)
            .first()
        )

        if record is None:
            raise ValueError("检测记录不存在")

        if original_name is not None:

            original_name = original_name.strip()

            if not original_name:
                raise ValueError("文件名不能为空")

            if len(original_name) > 255:
                raise ValueError("文件名长度不能超过255位")

            record.original_name = original_name

        if remark is not None:

            remark = remark.strip()

            if len(remark) > 500:
                raise ValueError("备注长度不能超过500位")

            record.remark = remark or None

        if status is not None:

            if status not in ALLOWED_STATUSES:
                raise ValueError(
                    "状态只能是processing、completed或failed"
                )

            record.status = status

        db.commit()
        db.refresh(record)

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="update",
            target_type="detection_record",
            target_id=record.id,
            description=(
                f"修改检测记录 #{record.id}："
                f"name={record.original_name}, "
                f"status={record.status}"
            ),
        )

        owner = (
            db.query(User)
            .filter(User.id == record.user_id)
            .first()
        )

        return _record_to_item(
            record,
            owner.username if owner else None
        )

    @staticmethod
    def delete_record(
        db: Session,
        record_id: int,
        admin_id: int,
    ):
        """
        管理员物理删除检测记录，同时删除类别统计和结果文件。
        """

        record = (
            db.query(DetectionRecord)
            .filter(DetectionRecord.id == record_id)
            .first()
        )

        if record is None:
            raise ValueError("检测记录不存在")

        original_path = record.original_path
        result_path = record.result_path
        original_name = record.original_name

        (
            db.query(DetectionClassStatistics)
            .filter(
                DetectionClassStatistics.record_id
                == record.id
            )
            .delete(synchronize_session=False)
        )

        db.delete(record)
        db.commit()

        deleted_files = []

        for file_path in (original_path, result_path):

            if not file_path:
                continue

            try:
                path = Path(file_path)

                if path.exists() and path.is_file():
                    path.unlink()
                    deleted_files.append(str(path))

            except OSError:
                pass

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="delete",
            target_type="detection_record",
            target_id=record_id,
            description=f"删除检测记录 #{record_id}（{original_name}）",
        )

        return {
            "record_id": record_id,
            "deleted_files": deleted_files,
        }
