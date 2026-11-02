from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey
)

from backend.database.database import Base


class DetectionClassStatistics(Base):
    __tablename__ = "detection_class_statistics"

    # 统计记录ID
    id = Column(Integer, primary_key=True, index=True)

    # 所属检测任务
    record_id = Column(
        Integer,
        ForeignKey("detection_record.id"),
        nullable=False,
        index=True
    )

    # 模型类别ID
    class_id = Column(Integer, nullable=False)

    # 类别名称
    class_name = Column(String(100), nullable=False)

    # 该类别检测数量
    count = Column(Integer, nullable=False, default=0)