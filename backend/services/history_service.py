from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics


class HistoryService:

    @staticmethod
    def get_history_list(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        task_type: str = None
    ):
        """
        查询用户的历史检测记录

        参数：
            db：数据库会话
            user_id：用户ID
            page：当前页
            page_size：每页数量
            task_type：任务类型，可选 image / video

        返回：
            历史记录列表以及分页信息
        """

        # ==========================
        # 1. 参数校验
        # ==========================

        if page < 1:
            raise ValueError("页码必须大于等于1")

        if page_size < 1:
            raise ValueError("每页数量必须大于等于1")

        if page_size > 100:
            raise ValueError("每页数量不能超过100")

        # ==========================
        # 2. 创建基础查询
        # ==========================

        query = (
            db.query(DetectionRecord)
            .filter(
                DetectionRecord.user_id == user_id
            )
        )

        # ==========================
        # 3. 根据任务类型筛选
        # ==========================

        if task_type:
            if task_type not in ["image", "video"]:
                raise ValueError("任务类型只能是image或video")

            query = query.filter(
                DetectionRecord.task_type == task_type
            )

        # ==========================
        # 4. 查询总记录数
        # ==========================

        total = query.count()

        # ==========================
        # 5. 按创建时间倒序
        # ==========================

        query = query.order_by(
            desc(DetectionRecord.created_at)
        )

        # ==========================
        # 6. 分页查询
        # ==========================

        offset = (page - 1) * page_size

        records = (
            query
            .offset(offset)
            .limit(page_size)
            .all()
        )

        # ==========================
        # 7. 计算总页数
        # ==========================

        pages = (total + page_size - 1) // page_size

        # ==========================
        # 8. 转换数据
        # ==========================

        items = []

        for record in records:
            items.append({
                "id": record.id,
                "task_type": record.task_type,
                "original_name": record.original_name,
                "model_name": record.model_name,
                "status": record.status,

                "object_count": record.object_count,
                "max_objects": record.max_objects,
                "average_objects": record.average_objects,

                "inference_time": record.inference_time,

                "frame_count": record.frame_count,
                "width": record.width,
                "height": record.height,
                "fps": record.fps,

                "created_at": (
                    record.created_at.isoformat()
                    if record.created_at
                    else None
                )
            })

        # ==========================
        # 9. 返回结果
        # ==========================

        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages
        }

    @staticmethod
    def get_history_detail(
        db: Session,
        user_id: int,
        record_id: int
    ):
        """
        查询单条历史检测记录的详细信息
        """

        # ==========================
        # 1. 查询检测记录
        # ==========================

        record = (
            db.query(DetectionRecord)
            .filter(
                DetectionRecord.id == record_id,
                DetectionRecord.user_id == user_id
            )
            .first()
        )

        # ==========================
        # 2. 判断记录是否存在
        # ==========================

        if record is None:
            raise ValueError("检测记录不存在或无权访问")

        # ==========================
        # 3. 查询类别统计信息
        # ==========================

        class_statistics = (
            db.query(DetectionClassStatistics)
            .filter(
                DetectionClassStatistics.record_id == record.id
            )
            .all()
        )

        # ==========================
        # 4. 转换类别统计数据
        # ==========================

        class_statistics_data = []

        for item in class_statistics:
            class_statistics_data.append({
                "class_id": item.class_id,
                "class_name": item.class_name,
                "count": item.count
            })

        # ==========================
        # 5. 组织完整历史记录
        # ==========================

        return {
            "id": record.id,
            "user_id": record.user_id,

            "task_type": record.task_type,
            "original_name": record.original_name,

            "model_name": record.model_name,
            "status": record.status,

            "object_count": record.object_count,
            "max_objects": record.max_objects,
            "average_objects": record.average_objects,

            "inference_time": record.inference_time,

            "frame_count": record.frame_count,

            "width": record.width,
            "height": record.height,
            "fps": record.fps,

            "original_path": record.original_path,
            "result_path": record.result_path,

            "error_message": record.error_message,

            "created_at": (
                record.created_at.isoformat()
                if record.created_at
                else None
            ),

            "class_statistics": class_statistics_data
        }