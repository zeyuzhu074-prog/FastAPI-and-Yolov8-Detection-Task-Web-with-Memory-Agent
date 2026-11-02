from backend.database.database import SessionLocal, Base, engine
from backend.models.user import User


def create_default_user():
    # 创建数据库表
    Base.metadata.create_all(bind=engine)

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 检查默认用户是否已经存在
        existing_user = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if existing_user:
            print("默认用户 admin 已经存在。")
            return

        # 创建默认用户
        user = User(
            username="admin",
            password="123456",
            role="admin"
        )

        db.add(user)
        db.commit()

        print("默认用户创建成功！")
        print("用户名：admin")
        print("密码：123456")

    except Exception as e:
        db.rollback()
        print(f"创建用户失败：{e}")

    finally:
        db.close()


if __name__ == "__main__":
    create_default_user()