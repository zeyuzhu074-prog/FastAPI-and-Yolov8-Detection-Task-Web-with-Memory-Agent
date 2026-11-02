from sqlalchemy.orm import Session
from passlib.context import CryptContext

from backend.models.user import User


# 密码加密工具
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        """
        对用户密码进行哈希加密
        bcrypt 最多支持 72 字节
        """
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            raise ValueError("密码长度不能超过72个字节")
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(
        password: str,
        password_hash: str
    ) -> bool:
        """
        验证用户输入的密码是否正确
        """
        return pwd_context.verify(
            password,
            password_hash
        )

    @staticmethod
    def register_user(
        db: Session,
        username: str,
        password: str
    ):
        """
        用户注册
        """

        # 1. 检查用户名是否已经存在
        existing_user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if existing_user:
            raise ValueError("用户名已经存在")

        # 2. 检查用户名
        if not username or not username.strip():
            raise ValueError("用户名不能为空")

        username = username.strip()

        if len(username) < 3:
            raise ValueError("用户名长度不能少于3位")

        if len(username) > 50:
            raise ValueError("用户名长度不能超过50位")

        # 3. 检查密码
        if not password:
            raise ValueError("密码不能为空")

        if len(password) < 6:
            raise ValueError("密码长度不能少于6位")

        if len(password.encode("utf-8")) > 72:
            raise ValueError("密码长度不能超过72个字节")

        # 4. 密码加密
        password_hash = AuthService.hash_password(
            password
        )

        # 5. 创建用户
        user = User(
            username=username,
            password_hash=password_hash,
            role="user",
            status=1
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def login_user(
        db: Session,
        username: str,
        password: str
    ):
        """
        用户登录
        """

        # 查询用户
        user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if user is None:
            raise ValueError("用户名或密码错误")

        # 检查用户状态
        if user.status != 1:
            raise ValueError("用户账号已被禁用")

        # 验证密码
        if not AuthService.verify_password(
            password,
            user.password_hash
        ):
            raise ValueError("用户名或密码错误")

        return user

    @staticmethod
    def change_password(
        db: Session,
        user_id: int,
        old_password: str,
        new_password: str,
        two_new_password: str
    ):
        """
        修改用户密码
        """

        # 查询用户
        user = (
            db.query(User)
            .filter(
                User.id == user_id
            )
            .first()
        )

        if user is None:
            raise ValueError("用户不存在")

        # 验证旧密码
        if not AuthService.verify_password(
            old_password,
            user.password_hash
        ):
            raise ValueError("旧密码错误")

        # 检查新密码
        if not new_password:
            raise ValueError("新密码不能为空")

        if len(new_password) < 6:
            raise ValueError("新密码长度不能少于6位")

        # 不能和旧密码相同
        if AuthService.verify_password(
            new_password,
            user.password_hash
        ):
            raise ValueError("新密码不能与旧密码相同")

        if two_new_password != new_password:
            raise ValueError("2次密码不一致")

        # 更新密码
        user.password_hash = (
            AuthService.hash_password(new_password)
        )

        db.commit()
        db.refresh(user)

        return user