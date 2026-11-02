from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics


class StatisticsService:

    @staticmethod
    def get_user_overview(
        db: Session,
        user_id: int
    ):
        """
        获取当前用户的总体统计信息
        """

        # 查询当前用户已经完成的检测任务
        records = (
            db.query(DetectionRecord)
            .filter(
                DetectionRecord.user_id == user_id,
                DetectionRecord.status == "completed"
            )
            .all()
        )

        # 检测任务总数
        total_tasks = len(records)

        # 图片检测数量
        image_tasks = sum(
            1 for record in records
            if record.task_type == "image"
        )

        # 视频检测数量
        video_tasks = sum(
            1 for record in records
            if record.task_type == "video"
        )

        # 总检测目标数量
        total_objects = sum(
            record.object_count or 0
            for record in records
        )

        # 总推理时间
        total_inference_time = sum(
            record.inference_time or 0
            for record in records
        )

        # 平均推理时间
        if total_tasks > 0:
            average_inference_time = (
                total_inference_time / total_tasks
            )
        else:
            average_inference_time = 0

        return {
            "total_tasks": total_tasks,
            "image_tasks": image_tasks,
            "video_tasks": video_tasks,
            "total_objects": total_objects,
            "average_inference_time": round(
                average_inference_time,
                4
            )
        }

    @staticmethod
    def get_user_class_statistics(
        db: Session,
        user_id: int
    ):
        """
        获取当前用户所有检测任务中的目标类别统计
        """

        results = (
            db.query(
                DetectionClassStatistics.class_id,
                DetectionClassStatistics.class_name,
                func.sum(
                    DetectionClassStatistics.count
                ).label("count")
            )
            .join(
                DetectionRecord,
                DetectionClassStatistics.record_id
                == DetectionRecord.id
            )
            .filter(
                DetectionRecord.user_id == user_id,
                DetectionRecord.status == "completed"
            )
            .group_by(
                DetectionClassStatistics.class_id,
                DetectionClassStatistics.class_name
            )
            .order_by(
                func.sum(
                    DetectionClassStatistics.count
                ).desc()
            )
            .all()
        )

        return [
            {
                "class_id": item.class_id,
                "class_name": item.class_name,
                "count": item.count
            }
            for item in results
        ]

    @staticmethod
    def get_record_statistics(
        db: Session,
        user_id: int,
        record_id: int
    ):
        """
        获取某一次检测任务的详细统计信息
        """

        # 先查询检测记录
        record = (
            db.query(DetectionRecord)
            .filter(
                DetectionRecord.id == record_id,
                DetectionRecord.user_id == user_id
            )
            .first()
        )

        # 不存在或者不属于当前用户
        if record is None:
            return None

        # 查询该检测任务的类别统计
        class_statistics = (
            db.query(DetectionClassStatistics)
            .filter(
                DetectionClassStatistics.record_id
                == record_id
            )
            .order_by(
                DetectionClassStatistics.count.desc()
            )
            .all()
        )

        return {
            "record_id": record.id,
            "task_type": record.task_type,
            "original_name": record.original_name,
            "model_name": record.model_name,
            "status": record.status,

            "object_count": record.object_count or 0,

            "max_objects": record.max_objects,

            "average_objects": record.average_objects,

            "inference_time": record.inference_time,

            "frame_count": record.frame_count,

            "width": record.width,

            "height": record.height,

            "fps": record.fps,

            "created_at": record.created_at,

            "class_statistics": [
                {
                    "class_id": item.class_id,
                    "class_name": item.class_name,
                    "count": item.count
                }
                for item in class_statistics
            ]
        }

    @staticmethod
    def get_detection_trend(
        db: Session,
        user_id: int
    ):
        """
        获取当前用户的检测任务趋势。

        按日期统计：
        - 检测次数
        - 检测目标数量
        """

        results = (
            db.query(
                func.date(
                    DetectionRecord.created_at
                ).label("date"),

                func.count(
                    DetectionRecord.id
                ).label("task_count"),

                func.sum(
                    DetectionRecord.object_count
                ).label("object_count")
            )
            .filter(
                DetectionRecord.user_id == user_id,
                DetectionRecord.status == "completed"
            )
            .group_by(
                func.date(
                    DetectionRecord.created_at
                )
            )
            .order_by(
                func.date(
                    DetectionRecord.created_at
                )
            )
            .all()
        )

        return [
            {
                "date": str(item.date),
                "task_count": item.task_count,
                "object_count": item.object_count or 0
            }
            for item in results
        ]
    @staticmethod
    def get_class_trend(
        db: Session,
        user_id: int
    ):
        """
        获取当前用户各目标类别的每日检测趋势。

        返回：
        {
            "dates": ["2026-10-01", "2026-10-02"],
            "series": {
                "car": [120, 180],
                "truck": [30, 42],
                "pedestrian": [50, 65]
            }
        }
        """

        # ==========================================
        # 1. 查询每日各类别统计
        # ==========================================

        results = (
            db.query(
                func.date(
                    DetectionRecord.created_at
                ).label("date"),

                DetectionClassStatistics.class_id,

                DetectionClassStatistics.class_name,

                func.sum(
                    DetectionClassStatistics.count
                ).label("count")
            )
            .join(
                DetectionRecord,
                DetectionClassStatistics.record_id
                == DetectionRecord.id
            )
            .filter(
                DetectionRecord.user_id == user_id,
                DetectionRecord.status == "completed"
            )
            .group_by(
                func.date(
                    DetectionRecord.created_at
                ),
                DetectionClassStatistics.class_id,
                DetectionClassStatistics.class_name
            )
            .order_by(
                func.date(
                    DetectionRecord.created_at
                )
            )
            .all()
        )

        # ==========================================
        # 2. 保存所有日期
        # ==========================================

        dates = sorted(
            list(
                set(
                    str(item.date)
                    for item in results
                )
            )
        )

        # ==========================================
        # 3. 保存每个类别的数据
        # ==========================================

        class_data = {}

        for item in results:

            class_name = item.class_name

            if class_name not in class_data:
                class_data[class_name] = {}

            class_data[class_name][
                str(item.date)
            ] = item.count

        # ==========================================
        # 4. 按日期补齐数据
        # ==========================================

        series = {}

        for class_name, daily_data in class_data.items():

            series[class_name] = [
                daily_data.get(date, 0)
                for date in dates
            ]

        # ==========================================
        # 5. 返回结果
        # ==========================================

        return {
            "dates": dates,
            "series": series
        }
