from pathlib import Path

from sqlalchemy.orm import Session

from backend.models.detection_record import DetectionRecord


class DownloadService:

    @staticmethod
    def get_result_file(
        db: Session,
        user_id: int,
        record_id: int,
        is_admin: bool = False
    ):
        """
        获取指定检测记录对应的结果文件。

        参数：
            db：
                数据库Session

            user_id：
                当前用户ID

            record_id：
                检测记录ID

        返回：
            result_path：
                结果文件路径

            filename：
                下载时使用的文件名
        """

        # ==========================================
        # 1. 查询检测记录
        # ==========================================

        query = (
            db.query(DetectionRecord)
            .filter(
                DetectionRecord.id == record_id
            )
        )

        if not is_admin:
            query = query.filter(
                DetectionRecord.user_id == user_id
            )

        record = query.first()

        # ==========================================
        # 2. 检查记录是否存在
        # ==========================================

        if record is None:

            raise ValueError(
                "检测记录不存在或无权访问"
            )

        # ==========================================
        # 3. 检查结果文件路径
        # ==========================================

        if not record.result_path:

            raise ValueError(
                "该检测记录没有结果文件"
            )

        result_path = Path(
            record.result_path
        )

        # ==========================================
        # 4. 检查文件是否存在
        # ==========================================

        if not result_path.exists():

            raise ValueError(
                "检测结果文件不存在"
            )

        if not result_path.is_file():

            raise ValueError(
                "检测结果路径不是有效文件"
            )

        # ==========================================
        # 5. 生成下载文件名
        # ==========================================

        if record.task_type == "image":

            filename = (
                f"{Path(record.original_name).stem}"
                f"_result.jpg"
            )

        elif record.task_type == "video":

            filename = (
                f"{Path(record.original_name).stem}"
                f"_result.mp4"
            )

        else:

            filename = result_path.name

        return {
            "path": str(result_path),
            "filename": filename,
            "task_type": record.task_type
        }
