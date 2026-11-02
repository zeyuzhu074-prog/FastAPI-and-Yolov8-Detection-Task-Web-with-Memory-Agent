from sqlalchemy.orm import Session

from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import (
    DetectionClassStatistics
)


class DetectionRecordService:

    @staticmethod
    def create_image_record(
        db: Session,
        user_id: int,
        original_name: str,
        original_path: str,
        result_path: str,
        model_name: str,
        object_count: int,
        inference_time: float,
        width: int,
        height: int,
        class_statistics: dict
    ):
        """
        创建一条图片检测记录，
        同时保存类别统计信息。
        """

        try:

            # ==================================
            # 1. 创建检测主记录
            # ==================================

            record = DetectionRecord(
                user_id=user_id,
                task_type="image",

                original_name=original_name,
                original_path=original_path,
                result_path=result_path,

                model_name=model_name,

                status="completed",

                object_count=object_count,

                max_objects=object_count,

                average_objects=float(
                    object_count
                ),

                inference_time=inference_time,

                frame_count=None,

                width=width,
                height=height,

                fps=None,

                error_message=None
            )

            db.add(record)

            # ==================================
            # 2. 先提交到当前事务
            #    获取 record.id
            # ==================================

            db.flush()

            # ==================================
            # 3. 保存类别统计
            # ==================================

            for class_id, statistics in class_statistics.items():

                class_statistics_record = (
                    DetectionClassStatistics(
                        record_id=record.id,
                        class_id=class_id,
                        class_name=statistics["class_name"],
                        count=statistics["count"]
                    )
                )

                db.add(
                    class_statistics_record
                )

            # ==================================
            # 4. 提交事务
            # ==================================

            db.commit()

            # ==================================
            # 5. 刷新对象
            # ==================================

            db.refresh(record)

            return record

        except Exception:

            db.rollback()

            raise

    @staticmethod
    def create_video_record(
            db: Session,
            user_id: int,
            original_name: str,
            original_path: str,
            result_path: str,
            model_name: str,
            object_count: int,
            max_objects: int,
            average_objects: float,
            inference_time: float,
            frame_count: int,
            width: int,
            height: int,
            fps: float,
            class_statistics: dict
    ):
        """
        创建一条视频检测记录，
        同时保存整个视频的类别统计信息。
        """

        try:

            # ==================================
            # 1. 创建视频检测主记录
            # ==================================

            record = DetectionRecord(

                user_id=user_id,

                task_type="video",

                original_name=original_name,

                original_path=original_path,

                result_path=result_path,

                model_name=model_name,

                status="completed",

                object_count=object_count,

                max_objects=max_objects,

                average_objects=average_objects,

                inference_time=inference_time,

                frame_count=frame_count,

                width=width,

                height=height,

                fps=fps,

                error_message=None
            )

            db.add(record)

            # ==================================
            # 2. 获取record.id
            # ==================================

            db.flush()

            # ==================================
            # 3. 保存类别统计
            # ==================================

            for class_id, statistics in class_statistics.items():
                class_statistics_record = (
                    DetectionClassStatistics(

                        record_id=record.id,

                        class_id=class_id,

                        class_name=statistics["class_name"],

                        count=statistics["count"]
                    )
                )

                db.add(
                    class_statistics_record
                )

            # ==================================
            # 4. 提交事务
            # ==================================

            db.commit()

            # ==================================
            # 5. 刷新记录
            # ==================================

            db.refresh(record)

            return record

        except Exception:

            db.rollback()

            raise