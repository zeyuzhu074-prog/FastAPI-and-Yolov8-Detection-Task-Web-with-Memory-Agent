from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey
)

from backend.database.database import Base


class DetectionRecord(Base):
    __tablename__ = "detection_record"

    # 检测记录ID
    id = Column(Integer, primary_key=True, index=True)

    # 所属用户
    user_id = Column(
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    # 任务类型：image / video
    task_type = Column(String(20), nullable=False)

    # 用户上传时的原始文件名
    original_name = Column(String(255), nullable=False)

    # 原始文件保存路径
    original_path = Column(String(500), nullable=False)

    # 推理结果文件路径
    result_path = Column(String(500), nullable=True)

    # 使用的模型名称
    model_name = Column(String(100), nullable=False)

    # 任务状态：
    # processing / completed / failed
    status = Column(String(20), nullable=False, default="processing")

    # 检测目标总数量
    object_count = Column(Integer, default=0)

    # 单帧最大目标数量
    max_objects = Column(Integer, nullable=True)

    # 平均每帧目标数量
    average_objects = Column(Float, nullable=True)

    # 推理耗时，单位：秒
    inference_time = Column(Float, nullable=True)

    # 视频总帧数
    # 图片任务可以为空
    frame_count = Column(Integer, nullable=True)

    # 图片/视频宽度
    width = Column(Integer, nullable=True)

    # 图片/视频高度
    height = Column(Integer, nullable=True)

    # 视频FPS
    # 图片任务可以为空
    fps = Column(Float, nullable=True)

    # 失败原因
    error_message = Column(String(1000), nullable=True)

    # 管理员备注
    remark = Column(String(500), nullable=True)

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow)
