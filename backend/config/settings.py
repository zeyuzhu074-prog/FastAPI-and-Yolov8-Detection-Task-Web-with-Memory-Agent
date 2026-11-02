from pathlib import Path
import yaml


# ============================================================
# 项目根目录
# ============================================================

# settings.py
# E:\朱泽宇\本科\大四\UAV-Inspection-System\backend\config\settings.py
#
# parents[2]：
# settings.py
#   ↓ parents[0] = config
#   ↓ parents[1] = backend
#   ↓ parents[2] = UAV-Inspection-System

BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================================
# 加载配置文件
# ============================================================

CONFIG_PATH = BASE_DIR / "config.yaml"


def load_config():
    """
    读取项目根目录下的config.yaml。
    """

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"配置文件不存在：{CONFIG_PATH}"
        )

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return yaml.safe_load(file)


config = load_config()


# ============================================================
# 系统配置
# ============================================================

SYSTEM_NAME = config["system"]["name"]

SYSTEM_VERSION = config["system"]["version"]

DEBUG = config["system"]["debug"]


# ============================================================
# 数据库配置
# ============================================================

DATABASE_URL = config["database"]["url"]


# ============================================================
# YOLO模型配置
# ============================================================

MODEL_PATH = (
    BASE_DIR /
    config["model"]["path"]
)

MODEL_CONFIDENCE = (
    config["model"]["confidence"]
)

MODEL_IOU = (
    config["model"]["iou"]
)

MODEL_IMAGE_SIZE = (
    config["model"]["image_size"]
)


# ============================================================
# 文件上传配置
# ============================================================

IMAGE_EXTENSIONS = (
    config["upload"]["image_extensions"]
)

VIDEO_EXTENSIONS = (
    config["upload"]["video_extensions"]
)

MAX_UPLOAD_SIZE_MB = (
    config["upload"]["max_size_mb"]
)




# ============================================================
# 文件存储目录
# ============================================================

ORIGINAL_DIR = (
    BASE_DIR /
    config["storage"]["original_dir"]
)

RESULT_DIR = (
    BASE_DIR /
    config["storage"]["result_dir"]
)


# ============================================================
# 日志配置
# ============================================================

LOG_LEVEL = (
    config["logging"]["level"]
)

LOG_FILE = (
    BASE_DIR /
    config["logging"]["file"]
)


# ============================================================
# 自动创建必要目录
# ============================================================

ORIGINAL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LOG_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

