"""
兼容旧调用方式的默认管理员创建脚本。

新流程请优先使用：
    python -m backend.database.create_admin --username admin --password 你的密码
"""

from backend.database.create_admin import create_admin


def create_default_user():
    create_admin(
        username="admin",
        password="123456",
        promote_existing=True,
    )


if __name__ == "__main__":
    create_default_user()
