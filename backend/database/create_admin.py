"""
创建独立的管理员账号。

用法：
    python -m backend.database.create_admin --username admin --password 123456
    python -m backend.database.create_admin --username admin --password 123456 \
        --email admin@example.com --promote-existing
"""

import argparse
import getpass

from backend.database.database import SessionLocal
from backend.database.migrate_round1 import ensure_schema
from backend.models.user import User
from backend.services.auth_service import AuthService


def create_admin(username, password, email=None, promote_existing=False):
    ensure_schema()

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if user is not None:

            if not promote_existing:
                raise ValueError(
                    f"用户 {username} 已存在；"
                    "如需将该用户提升为管理员，请加 --promote-existing"
                )

            user.role = "admin"
            user.status = 1
            user.password_hash = AuthService.hash_password(password)

            if email:
                user.email = email

            print(f"已将用户 {username} 提升为管理员并重置密码。")

        else:
            user = User(
                username=username,
                password_hash=AuthService.hash_password(password),
                email=email,
                role="admin",
                status=1,
            )
            db.add(user)
            print(f"管理员 {username} 创建成功。")

        db.commit()
        db.refresh(user)

        print(f"用户 ID：{user.id}")
        print(f"角色：{user.role}")

        return user

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="创建无人机巡检系统管理员账号"
    )
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=None)
    parser.add_argument("--email", default=None)
    parser.add_argument("--promote-existing", action="store_true")

    args = parser.parse_args()

    password = args.password

    if not password:
        password = getpass.getpass("请输入管理员密码：")

    create_admin(
        username=args.username,
        password=password,
        email=args.email,
        promote_existing=args.promote_existing,
    )


if __name__ == "__main__":
    main()
