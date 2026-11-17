# -*- coding: utf-8 -*-
"""YOLOv8m inference example with confidence filtering and NMS."""

from pathlib import Path
from ultralytics import YOLO

WEIGHTS = Path("visdrone_yolov8m.pt")  # update to your checkpoint path
SOURCE = Path("sample_uav_image.jpg")  # update to an image/video path

# Keep only these target categories for the UAV project.
# VisDrone common class IDs:
# 0 pedestrian, 1 people, 2 bicycle, 3 car, 4 van,
# 5 truck, 6 tricycle, 7 awning-tricycle, 8 bus, 9 motor.
# NOTE: Confirm model.names in your actual checkpoint before relying on IDs.
KEEP_CLASS_IDS = [0, 3, 5]

CONF = 0.25
IOU = 0.45
IMAGE_SIZE = 640


def main():
    model = YOLO(str(WEIGHTS))

    # predict() applies confidence filtering and NMS as part of the
    # Ultralytics prediction pipeline. These are inference settings.
    results = model.predict(
        source=str(SOURCE),
        imgsz=IMAGE_SIZE,
        conf=CONF,
        iou=IOU,
        classes=KEEP_CLASS_IDS,
        save=True,
        show=False,
    )

    for result in results:
        print(f"Detected objects: {len(result.boxes)}")
        for box in result.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = box.xyxy[0].tolist()
            print(
                f"class={model.names[cls_id]}, "
                f"confidence={conf:.3f}, box={xyxy}"
            )


if __name__ == "__main__":
    main()
