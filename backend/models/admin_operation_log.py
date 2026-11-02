from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from backend.database.database import Base


class AdminOperationLog(Base):
    """
    管理员重要操作审计日志。
    """

    __tablename__ = "admin_operation_log"

    id = Column(Integer, primary_key=True, index=True)

    admin_id = Column(Integer, nullable=False, index=True)

    operation_type = Column(String(50), nullable=False)

    target_type = Column(String(50), nullable=False)

    target_id = Column(Integer, nullable=True)

    description = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
