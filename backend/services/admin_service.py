from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.detection_class_statistics import (
    DetectionClassStatistics,
)
from backend.models.detection_record import DetectionRecord
from backend.models.user import User
from backend.services.audit_service import AuditService
from backend.services.auth_service import AuthService
from backend.services.profile_service import user_to_dict
from backend.utils.avatar_utils import delete_avatar_file
from backend.utils.validators import is_valid_email, normalize_email


ALLOWED_ROLES = ("user", "admin")


class AdminService:

    @staticmethod
    def _count_active_admins(db: Session) -> int:
        return (
            db.query(User)
            .filter(
                User.role == "admin",
                User.status == 1,
            )
            .count()
        )

    @staticmethod
    def _get_user(db: Session, user_id: int) -> User:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if user is None:
            raise ValueError("用户不存在")

        return user

    @staticmethod
    def _validate_username(db: Session, username: str, exclude_id=None):
        username = (username or "").strip()

        if len(username) < 3:
            raise ValueError("用户名长度不能少于3位")

        if len(username) > 50:
            raise ValueError("用户名长度不能超过50位")

        query = db.query(User).filter(User.username == username)

        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)

        if query.first():
            raise ValueError("用户名已经存在")

        return username

    @staticmethod
    def _validate_email(db: Session, email, exclude_id=None):
        email = normalize_email(email)

        if not email:
            return None

        if not is_valid_email(email):
            raise ValueError("邮箱格式不正确")

        query = db.query(User).filter(User.email == email)

        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)

        if query.first():
            raise ValueError("邮箱已经被使用")

        return email

    @staticmethod
    def _validate_password(password: str):
        if not password:
            raise ValueError("密码不能为空")

        if len(password) < 6:
            raise ValueError("密码长度不能少于6位")

        if len(password.encode("utf-8")) > 72:
            raise ValueError("密码长度不能超过72个字节")

    @staticmethod
    def list_users(
        db: Session,
        page: int = 1,
        page_size: int = 10,
        keyword: str = None,
        status: int = None,
        role: str = None,
    ):
        if page < 1:
            raise ValueError("页码必须大于等于1")

        if page_size < 1:
            raise ValueError("每页数量必须大于等于1")

        if page_size > 100:
            raise ValueError("每页数量不能超过100")

        if role and role not in ALLOWED_ROLES:
            raise ValueError("角色只能是user或admin")

        query = db.query(User)

        if keyword:
            like = f"%{keyword.strip()}%"
            query = query.filter(
                (User.username.like(like)) |
                (User.email.like(like))
            )

        if status is not None:
            if status not in (0, 1):
                raise ValueError("状态只能是0或1")
            query = query.filter(User.status == status)

        if role:
            query = query.filter(User.role == role)

        total = query.count()

        users = (
            query
            .order_by(User.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        user_ids = [u.id for u in users]
        record_counts = {}

        if user_ids:
            rows = (
                db.query(
                    DetectionRecord.user_id,
                    func.count(DetectionRecord.id),
                )
                .filter(DetectionRecord.user_id.in_(user_ids))
                .group_by(DetectionRecord.user_id)
                .all()
            )
            record_counts = dict(rows)

        items = []

        for user in users:
            item = user_to_dict(user)
            item["record_count"] = record_counts.get(user.id, 0)
            items.append(item)

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

    @staticmethod
    def get_user(db: Session, user_id: int):
        user = AdminService._get_user(db, user_id)
        return user_to_dict(user)

    @staticmethod
    def create_user(
        db: Session,
        admin_id: int,
        username: str,
        password: str,
        email: str = None,
        role: str = "user",
    ):
        if role not in ALLOWED_ROLES:
            raise ValueError("角色只能是user或admin")

        username = AdminService._validate_username(db, username)
        email = AdminService._validate_email(db, email)
        AdminService._validate_password(password)

        user = User(
            username=username,
            password_hash=AuthService.hash_password(password),
            email=email,
            role=role,
            status=1,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="create",
            target_type="user",
            target_id=user.id,
            description=f"创建用户 {user.username}（{role}）",
        )

        return user_to_dict(user)

    @staticmethod
    def update_user(
        db: Session,
        admin_id: int,
        user_id: int,
        username: str = None,
        email: str = None,
        role: str = None,
        status: int = None,
    ):
        user = AdminService._get_user(db, user_id)

        if role is not None:
            if role not in ALLOWED_ROLES:
                raise ValueError("角色只能是user或admin")

        if status is not None:
            if status not in (0, 1):
                raise ValueError("状态只能是0或1")

        # 防止移除最后一个有效管理员
        losing_admin = (
            user.role == "admin"
            and user.status == 1
            and (
                (role is not None and role != "admin")
                or (status is not None and status != 1)
            )
        )

        if losing_admin and AdminService._count_active_admins(db) <= 1:
            raise ValueError("不能移除或禁用最后一个有效管理员")

        if username is not None:
            user.username = AdminService._validate_username(
                db, username, exclude_id=user.id
            )

        if email is not None:
            user.email = AdminService._validate_email(
                db, email, exclude_id=user.id
            )

        if role is not None:
            user.role = role

        if status is not None:
            user.status = status

        db.commit()
        db.refresh(user)

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="update",
            target_type="user",
            target_id=user.id,
            description=f"修改用户 {user.username}",
        )

        return user_to_dict(user)

    @staticmethod
    def set_status(
        db: Session,
        admin_id: int,
        user_id: int,
        status: int,
    ):
        if status not in (0, 1):
            raise ValueError("状态只能是0或1")

        user = AdminService._get_user(db, user_id)

        if (
            user.role == "admin"
            and user.status == 1
            and status == 0
            and AdminService._count_active_admins(db) <= 1
        ):
            raise ValueError("不能禁用最后一个有效管理员")

        if admin_id == user.id and status == 0:
            raise ValueError("不能禁用当前登录的管理员账号")

        user.status = status

        db.commit()
        db.refresh(user)

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="enable" if status == 1 else "disable",
            target_type="user",
            target_id=user.id,
            description=(
                f"{'启用' if status == 1 else '禁用'}用户 {user.username}"
            ),
        )

        return user_to_dict(user)

    @staticmethod
    def reset_password(
        db: Session,
        admin_id: int,
        user_id: int,
        new_password: str,
    ):
        user = AdminService._get_user(db, user_id)

        AdminService._validate_password(new_password)

        user.password_hash = AuthService.hash_password(new_password)

        db.commit()
        db.refresh(user)

        AuditService.log(
            db=db,
            admin_id=admin_id,
            operation_type="reset_password",
            target_type="user",
            target_id=user.id,
            description=f"重置用户 {user.username} 的密码",
        )

        return {"user_id": user.id, "username": user.username}

    @staticmethod
    def delete_user(
        db: Session,
        admin_id: int,
        user_id: int,
    ):
        user = AdminService._get_user(db, user_id)

        if user.id == admin_id:
            raise ValueError("不能删除当前登录的管理员账号")

        if (
            user.role == "admin"
            and user.status == 1
            and AdminService._count_active_admins(db) <= 1
        ):
            raise ValueError("不能删除最后一个有效管理员")

        records = (
            db.query(DetectionRecord)
            .filter(DetectionRecord.user_id == user.id)
            .all()
        )

        record_ids = [r.id for r in records]
        file_paths = []

        for record in records:
            file_paths.extend([
                record.original_path,
                record.result_path,
            ])

        if record_ids:
            (
                db.query(DetectionClassStatistics)
                .filter(
                    DetectionClassStatistics.record_id.in_(
                        record_ids
                    )
                )
                .delete(synchronize_session=False)
            )

            (
                db.query(DetectionRecord)
                .filter(DetectionRecord.id.in_(record_ids))
                .delete(synchronize_session=False)
            )

        avatar_path = user.avatar_path
        username = user.username

        db.delete(user)
        db.commit()

        delete_avatar_file(avatar_path)

        deleted_files = []

        for file_path in file_paths:

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
            target_type="user",
            target_id=user_id,
            description=(
                f"删除用户 {username}，"
                f"同时删除 {len(record_ids)} 条检测记录"
            ),
        )

        return {
            "user_id": user_id,
            "deleted_records": len(record_ids),
            "deleted_files": deleted_files,
        }
