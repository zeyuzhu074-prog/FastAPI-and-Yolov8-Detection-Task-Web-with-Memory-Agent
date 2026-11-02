from sqlalchemy.orm import Session

from backend.models.user import User
from backend.utils.avatar_utils import (
    delete_avatar_file,
    save_avatar_file,
)
from backend.utils.validators import (
    is_valid_email,
    normalize_email,
)


def user_to_dict(user: User):
    """
    用户资料的安全序列化，不返回 password_hash。
    """

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": (
            f"/uploads/avatars/{user.avatar_path}"
            if user.avatar_path
            else None
        ),
        "role": user.role,
        "status": user.status,
        "created_at": (
            user.created_at.isoformat()
            if user.created_at
            else None
        ),
        "updated_at": (
            user.updated_at.isoformat()
            if user.updated_at
            else None
        ),
    }


class ProfileService:

    @staticmethod
    def get_profile(user: User):
        return user_to_dict(user)

    @staticmethod
    def update_profile(
        db: Session,
        user: User,
        username: str = None,
        email: str = None,
    ):
        if username is not None:

            username = username.strip()

            if len(username) < 3:
                raise ValueError("用户名长度不能少于3位")

            if len(username) > 50:
                raise ValueError("用户名长度不能超过50位")

            existing = (
                db.query(User)
                .filter(
                    User.username == username,
                    User.id != user.id,
                )
                .first()
            )

            if existing:
                raise ValueError("用户名已经存在")

            user.username = username

        if email is not None:

            email = normalize_email(email)

            if email:

                if not is_valid_email(email):
                    raise ValueError("邮箱格式不正确")

                existing = (
                    db.query(User)
                    .filter(
                        User.email == email,
                        User.id != user.id,
                    )
                    .first()
                )

                if existing:
                    raise ValueError("邮箱已经被使用")

            user.email = email

        db.commit()
        db.refresh(user)

        return user_to_dict(user)

    @staticmethod
    async def upload_avatar(
        db: Session,
        user: User,
        upload_file,
    ):
        old_avatar = user.avatar_path

        filename = await save_avatar_file(upload_file)

        user.avatar_path = filename

        db.commit()
        db.refresh(user)

        delete_avatar_file(old_avatar)

        return user_to_dict(user)

    @staticmethod
    def delete_avatar(
        db: Session,
        user: User,
    ):
        old_avatar = user.avatar_path

        user.avatar_path = None

        db.commit()
        db.refresh(user)

        delete_avatar_file(old_avatar)

        return user_to_dict(user)
