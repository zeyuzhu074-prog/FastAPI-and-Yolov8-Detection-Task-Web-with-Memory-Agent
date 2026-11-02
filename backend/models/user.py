from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from backend.database.database import Base


class User(Base):
    __tablename__ = "user"

    # 用户ID
    id = Column(Integer, primary_key=True, index=True)

    # 用户名
    username = Column(String(50), unique=True, nullable=False, index=True)

    # 密码哈希
    password_hash = Column(String(255), nullable=False)

    # 邮箱（可空，唯一）
    email = Column(String(255), unique=True, nullable=True, index=True)

    # 头像文件名（相对于 uploads/avatars）
    avatar_path = Column(String(500), nullable=True)

    # 用户角色：admin / user
    role = Column(String(20), nullable=False, default="user")

    # 用户状态：1正常，0禁用
    status = Column(Integer, nullable=False, default=1)

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)

    # 资料最后更新时间
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
