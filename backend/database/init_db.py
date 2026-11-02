from backend.database.database import Base, engine

# 导入所有模型，确保 SQLAlchemy 注册这些表
from backend.models.user import User
from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics


def init_database():
    print("开始创建数据库表...")

    Base.metadata.create_all(bind=engine)

    print("数据库表创建完成")


if __name__ == "__main__":
    init_database()