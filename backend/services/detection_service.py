import time
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
from ultralytics import YOLO
from sqlalchemy.orm import Session
from backend.utils.detection_utils import (
    parse_detections,
    calculate_class_statistics,
    save_annotated_image,
    get_image_size,
    update_class_statistics
)

from backend.services.detection_record_service import (
    DetectionRecordService
)
from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics
from backend.config.settings import (
    MODEL_PATH,
    MODEL_CONFIDENCE,
    MODEL_IOU,
    MODEL_IMAGE_SIZE,
    RESULT_DIR
)


# ============================================================
# 结果视频编码
# ============================================================

# 按优先级排列的候选编码。
#
# 浏览器（Chrome / Edge / Firefox）的 HTML5 <video> 不支持
# MPEG-4 Part 2（mp4v）：用它生成的结果视频在网页里时长显示为 0、
# 完全无法播放，但下载后本地播放器（如 VLC）可以正常播放。
# 因此优先使用 H.264（avc1），并做一次极小样本探测，确认编码器
# 真的可用、真的写出 H.264 之后再用于正式输出。
BROWSER_VIDEO_CODECS = ("avc1", "H264", "mp4v")


def resolve_video_fourcc(width: int, height: int, fps: float):
    """
    选择一个浏览器可以播放的结果视频编码。

    逐个尝试候选编码，写出一个单帧的探测视频并校验：
    - 编码器能正常打开；
    - 探测文件非空；
    - 声明为 H.264 时，文件里必须真的有 avcC 描述块。

    全部失败时回退到 mp4v，保证检测流程本身不会中断。
    """

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for codec in BROWSER_VIDEO_CODECS:

        probe_path = (
            RESULT_DIR /
            f".codec_probe_{codec}_{uuid4().hex}.mp4"
        )

        writer = None

        try:

            writer = cv2.VideoWriter(
                str(probe_path),
                cv2.VideoWriter_fourcc(*codec),
                fps,
                (width, height)
            )

            if not writer.isOpened():
                continue

            writer.write(
                np.zeros(
                    (height, width, 3),
                    dtype=np.uint8
                )
            )

            writer.release()
            writer = None

            if (
                not probe_path.exists() or
                probe_path.stat().st_size == 0
            ):
                continue

            # avc1 / H264 必须真的写出 H.264 描述块
            if codec.lower() in ("avc1", "h264"):

                if b"avcC" not in probe_path.read_bytes():

                    print(
                        f"视频编码 {codec} 未真正生成 H.264，继续尝试下一项。"
                    )

                    continue

            print(f"结果视频编码：{codec}")

            return cv2.VideoWriter_fourcc(*codec)

        except Exception as error:

            print(f"视频编码 {codec} 不可用：{error}")

        finally:

            if writer is not None:
                writer.release()

            try:
                if probe_path.exists():
                    probe_path.unlink()
            except OSError:
                pass

    print(
        "警告：当前环境没有可用的 H.264 编码器，"
        "回退到 mp4v，网页预览可能无法播放。"
    )

    return cv2.VideoWriter_fourcc(*"mp4v")


class DetectionService:
    """
    YOLO目标检测服务。

    负责：
    1. 加载YOLO模型
    2. 执行图片推理
    3. 提取检测结果
    4. 保存可视化结果
    """

    def __init__(self):
        self.model = None

    def load_model(self):
        """
        加载YOLO模型。
        """

        if not Path(MODEL_PATH).exists():
            raise FileNotFoundError(
                f"模型文件不存在：{MODEL_PATH}"
            )

        print(
            f"正在加载YOLO模型：{MODEL_PATH}"
        )

        self.model = YOLO(
            str(MODEL_PATH)
        )

        print("YOLO模型加载完成。")

    def ensure_model(self):
        """
        确保模型已经加载。
        """

        if self.model is None:
            self.load_model()

    def detect_video(
            self,
            db: Session,
            user_id: int,
            video_path: str,
            original_name: str
    ):
        """
        对视频进行目标检测。

        流程：
        1. 加载YOLO模型
        2. 打开视频
        3. 逐帧进行目标检测
        4. 保存检测结果视频
        5. 统计检测信息
        6. 保存数据库记录
        7. 返回检测结果
        """

        # ==========================================
        # 1. 确保YOLO模型已经加载
        # ==========================================

        self.ensure_model()

        start_time = time.perf_counter()

        # ==========================================
        # 2. 打开视频
        # ==========================================

        cap = cv2.VideoCapture(
            str(video_path)
        )

        if not cap.isOpened():
            raise RuntimeError(
                f"无法打开视频文件：{video_path}"
            )

        # ==========================================
        # 3. 获取视频基本信息
        # ==========================================

        fps = cap.get(
            cv2.CAP_PROP_FPS
        )

        width = int(
            cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        frame_count = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        # 如果视频没有正确读取FPS
        if fps <= 0:
            fps = 25.0

        # ==========================================
        # 4. 创建结果视频
        # ==========================================

        video_name = Path(
            video_path
        ).stem

        result_filename = (
            f"{video_name}_result.mp4"
        )

        result_path = (
                RESULT_DIR /
                result_filename
        )

        RESULT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # MP4视频编码器
        # 优先 H.264，保证结果视频能在网页里播放
        fourcc = resolve_video_fourcc(
            width=width,
            height=height,
            fps=fps
        )

        writer = cv2.VideoWriter(
            str(result_path),
            fourcc,
            fps,
            (width, height)
        )

        if not writer.isOpened():
            cap.release()

            raise RuntimeError(
                "无法创建结果视频"
            )

        # ==========================================
        # 5. 初始化统计信息
        # ==========================================

        processed_frames = 0

        total_objects = 0

        max_objects_in_frame = 0

        class_statistics = {}

        # ==========================================
        # 6. 逐帧进行目标检测
        # ==========================================

        try:

            while True:

                ret, frame = cap.read()

                if not ret:
                    break

                # ----------------------------------
                # YOLO推理
                # ----------------------------------

                results = self.model.predict(
                    source=frame,
                    conf=MODEL_CONFIDENCE,
                    iou=MODEL_IOU,
                    imgsz=MODEL_IMAGE_SIZE,
                    verbose=False
                )

                result = results[0]

                # ----------------------------------
                # 解析当前帧检测结果
                # ----------------------------------

                detections = parse_detections(
                    result=result,
                    model_names=self.model.names
                )

                # 当前帧目标数量
                current_objects = len(
                    detections
                )

                # ----------------------------------
                # 累计目标数量
                # ----------------------------------

                total_objects += (
                    current_objects
                )

                # ----------------------------------
                # 更新最大目标数量
                # ----------------------------------

                max_objects_in_frame = max(
                    max_objects_in_frame,
                    current_objects
                )

                # ----------------------------------
                # 更新类别统计
                # ----------------------------------

                update_class_statistics(
                    class_statistics,
                    detections
                )

                # ----------------------------------
                # 绘制检测结果
                # ----------------------------------

                annotated_frame = result.plot()

                writer.write(
                    annotated_frame
                )

                processed_frames += 1

                # ----------------------------------
                # 输出处理进度
                # ----------------------------------

                if processed_frames % 30 == 0:
                    print(
                        f"视频处理进度："
                        f"{processed_frames}/"
                        f"{frame_count}"
                    )

        finally:

            # ======================================
            # 7. 释放视频资源
            # ======================================

            cap.release()

            writer.release()

        # ==========================================
        # 8. 计算推理时间
        # ==========================================

        end_time = time.perf_counter()

        inference_time = (
                end_time -
                start_time
        )

        # ==========================================
        # 9. 计算平均目标数量
        # ==========================================

        average_objects = (
            total_objects /
            processed_frames
            if processed_frames > 0
            else 0
        )

        average_objects = round(
            average_objects,
            2
        )

        inference_time = round(
            inference_time,
            4
        )

        fps = round(
            fps,
            2
        )

        # ==========================================
        # 10. 保存数据库记录
        # ==========================================

        record = (
            DetectionRecordService
            .create_video_record(
                db=db,

                user_id=user_id,

                original_name=original_name,

                original_path=video_path,

                result_path=str(
                    result_path
                ),

                model_name=Path(
                    MODEL_PATH
                ).name,

                object_count=total_objects,

                max_objects=max_objects_in_frame,

                average_objects=average_objects,

                inference_time=inference_time,

                frame_count=processed_frames,

                width=width,

                height=height,

                fps=fps,

                class_statistics=class_statistics
            )
        )

        # ==========================================
        # 11. 返回检测结果
        # ==========================================

        return {

            # 数据库记录ID
            "record_id":
                record.id,

            # 结果视频
            "result_path":
                str(result_path),

            # 视频帧数
            "frame_count":
                processed_frames,

            # 总检测目标数量
            "object_count":
                total_objects,

            # 单帧最大目标数量
            "max_objects_in_frame":
                max_objects_in_frame,

            # 平均每帧目标数量
            "average_objects_per_frame":
                average_objects,

            # 推理时间
            "inference_time":
                inference_time,

            # 视频FPS
            "fps":
                fps,

            # 视频宽度
            "width":
                width,

            # 视频高度
            "height":
                height,

            # 类别统计
            "class_statistics":
                class_statistics
        }

    def detect_image(
            self,
            db: Session,
            user_id: int,
            image_path: str,
            original_name: str
    ):
        """
        对单张图片进行目标检测。

        流程：

        1. 加载YOLO模型
        2. 执行目标检测
        3. 统计推理时间
        4. 解析检测结果
        5. 统计类别数量
        6. 保存可视化结果
        7. 保存数据库记录
        """

        # ==================================
        # 1. 确保模型已经加载
        # ==================================

        self.ensure_model()

        # ==================================
        # 2. 开始计时
        # ==================================

        start_time = time.perf_counter()

        # ==================================
        # 3. YOLO目标检测
        # ==================================

        results = self.model.predict(
            source=image_path,
            conf=MODEL_CONFIDENCE,
            iou=MODEL_IOU,
            imgsz=MODEL_IMAGE_SIZE,
            verbose=False
        )

        # ==================================
        # 4. 结束计时
        # ==================================

        end_time = time.perf_counter()

        inference_time = round(
            end_time - start_time,
            4
        )

        # ==================================
        # 5. 获取单张图片检测结果
        # ==================================

        result = results[0]

        # ==================================
        # 6. 解析检测框
        # ==================================

        detections = parse_detections(
            result=result,
            model_names=self.model.names
        )

        # ==================================
        # 7. 统计类别
        # ==================================

        class_statistics = (
            calculate_class_statistics(
                detections
            )
        )

        # ==================================
        # 8. 保存可视化结果
        # ==================================

        result_path = save_annotated_image(
            result=result,
            result_dir=RESULT_DIR,
            image_path=image_path
        )

        # ==================================
        # 9. 获取图片尺寸
        # ==================================

        width, height = get_image_size(
            image_path
        )

        # ==================================
        # 10. 保存数据库
        # ==================================

        record = (
            DetectionRecordService
            .create_image_record(
                db=db,
                user_id=user_id,

                original_name=original_name,
                original_path=image_path,
                result_path=result_path,

                model_name=Path(
                    MODEL_PATH
                ).name,

                object_count=len(
                    detections
                ),

                inference_time=inference_time,

                width=width,
                height=height,

                class_statistics=class_statistics
            )
        )

        # ==================================
        # 11. 返回检测结果
        # ==================================

        return {
            "record_id": record.id,

            "result_path": result_path,

            "object_count": len(
                detections
            ),

            "inference_time": inference_time,

            "width": width,

            "height": height,

            "detections": detections,

            "class_statistics": class_statistics
        }

# 创建全局检测服务对象
detection_service = DetectionService()
