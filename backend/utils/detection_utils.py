from pathlib import Path
from collections import Counter

import cv2


def parse_detections(result, model_names):
    """
    解析YOLO检测结果。

    参数：
        result：
            YOLO单张图片的检测结果

        model_names：
            YOLO模型类别名称，例如：
            {
                0: "pedestrian",
                1: "people",
                2: "bicycle",
                ...
            }

    返回：
        detections:
            详细检测结果列表
    """

    detections = []

    boxes = result.boxes

    if boxes is None:
        return detections

    for box in boxes:

        # ==========================
        # 1. 获取检测框坐标
        # ==========================

        xyxy = box.xyxy[0].cpu().numpy()

        x1, y1, x2, y2 = xyxy.tolist()

        # ==========================
        # 2. 获取置信度
        # ==========================

        confidence = float(
            box.conf[0].cpu().item()
        )

        # ==========================
        # 3. 获取类别ID
        # ==========================

        class_id = int(
            box.cls[0].cpu().item()
        )

        # ==========================
        # 4. 获取类别名称
        # ==========================

        class_name = model_names[class_id]

        # ==========================
        # 5. 保存检测结果
        # ==========================

        detections.append(
            {
                "class_id": class_id,
                "class_name": class_name,
                "confidence": round(
                    confidence,
                    4
                ),
                "bbox": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2)
                }
            }
        )

    return detections


def calculate_class_statistics(detections):
    """
    根据检测结果统计各类别目标数量。

    返回：

    {
        0: {
            "class_name": "pedestrian",
            "count": 10
        },
        3: {
            "class_name": "car",
            "count": 25
        }
    }
    """

    statistics = {}

    for detection in detections:

        class_id = detection["class_id"]
        class_name = detection["class_name"]

        if class_id not in statistics:

            statistics[class_id] = {
                "class_name": class_name,
                "count": 0
            }

        statistics[class_id]["count"] += 1

    return statistics


def save_annotated_image(
    result,
    result_dir,
    image_path
):
    """
    绘制检测结果并保存图片。

    返回：
        result_path
    """

    # YOLO绘制检测框
    annotated_image = result.plot()

    # 原始文件名
    original_name = Path(
        image_path
    ).stem

    result_filename = (
        f"{original_name}_result.jpg"
    )

    result_path = (
        result_dir / result_filename
    )

    # 确保目录存在
    result_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # 保存图片
    success = cv2.imwrite(
        str(result_path),
        annotated_image
    )

    if not success:
        raise RuntimeError(
            f"检测结果图片保存失败：{result_path}"
        )

    return str(result_path)


def get_image_size(image_path):
    """
    获取图片宽高。

    返回：
        width, height
    """

    image = cv2.imread(
        str(image_path)
    )

    if image is None:
        raise ValueError(
            f"无法读取图片：{image_path}"
        )

    height, width = image.shape[:2]

    return width, height

def update_class_statistics(
    class_statistics,
    detections
):
    """
    将当前帧的检测结果累加到总类别统计中。

    参数：
        class_statistics：
            整个视频累计的类别统计

        detections：
            当前帧的检测结果

    例如：

        当前累计：
        car = 20

        当前帧：
        car = 5

        更新后：
        car = 25
    """

    for detection in detections:

        class_id = detection["class_id"]

        class_name = detection["class_name"]

        if class_id not in class_statistics:

            class_statistics[class_id] = {
                "class_name": class_name,
                "count": 0
            }

        class_statistics[class_id]["count"] += 1

    return class_statistics