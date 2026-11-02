from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config.settings import DATABASE_URL


# SQLite需要这个参数允许多线程访问
connect_args = {
    "check_same_thread": False
}


# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
)


# 创建数据库会话
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ORM基类
Base = declarative_base()


def get_db():
    """
    获取数据库会话。

    FastAPI接口通过Depends调用该函数，
    请求结束后自动关闭数据库连接。
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()