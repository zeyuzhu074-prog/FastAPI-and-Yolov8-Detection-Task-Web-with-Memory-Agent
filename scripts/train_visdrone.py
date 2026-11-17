# -*- coding: utf-8 -*-
"""
YOLOv8m fine-tuning / training entry point for VisDrone.
Run this script after installing ultralytics and preparing a dataset YAML.

Example:
  python train_visdrone.py

Important:
- This script fine-tunes an existing .pt checkpoint by default.
- Set WEIGHTS to yolov8m.yaml if you intend to train from scratch (not recommended
  unless you have sufficient data and compute).
"""

from pathlib import Path
from ultralytics import YOLO

# ------------------ User configuration ------------------
PROJECT_ROOT = Path(__file__).resolve().parent

# Fine-tune from the same checkpoint used in the project.
# Change this path to your local visdrone_yolov8m.pt file.
WEIGHTS = PROJECT_ROOT / "visdrone_yolov8m.pt"

# Dataset configuration file. Edit it to match your local dataset paths.
DATA_YAML = PROJECT_ROOT / "visdrone.yaml"

RUNS_DIR = PROJECT_ROOT / "runs"
RUN_NAME = "visdrone_yolov8m_finetune"

EPOCHS = 100
IMAGE_SIZE = 640
BATCH_SIZE = 8
DEVICE = 0                 # 0 = first CUDA GPU; use "cpu" for CPU
WORKERS = 4
# --------------------------------------------------------


def main():
    if not DATA_YAML.exists():
        raise FileNotFoundError(
            f"Dataset YAML not found: {DATA_YAML}\n"
            "Please create visdrone.yaml and update train/val paths."
        )

    if not WEIGHTS.exists():
        raise FileNotFoundError(
            f"Checkpoint not found: {WEIGHTS}\n"
            "Copy visdrone_yolov8m.pt here or update WEIGHTS."
        )

    # Load pretrained model weights and architecture from the checkpoint.
    model = YOLO(str(WEIGHTS))

    # Training/fine-tuning. Ultralytics handles dataloading, augmentation,
    # forward pass, loss calculation, backpropagation, optimizer and validation.
    results = model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        workers=WORKERS,
        project=str(RUNS_DIR),
        name=RUN_NAME,
        exist_ok=True,
        pretrained=True,
        optimizer="auto",
        patience=30,
        save=True,
        plots=True,
        val=True,
    )

    print("Training completed.")
    print(f"Results: {results}")
    print(f"Best checkpoint: {RUNS_DIR / RUN_NAME / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
