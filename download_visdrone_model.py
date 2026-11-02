from pathlib import Path
import shutil

from huggingface_hub import hf_hub_download


# ============================================================
# 1. 项目根目录
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# 2. 模型保存目录
# ============================================================

MODEL_DIR = BASE_DIR / "models" / "pretrained"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 3. VisDrone YOLOv8m 模型信息
# ============================================================

REPO_ID = "dronefreak/visdrone-yolov8m"
MODEL_FILE = "best.pt"

TARGET_FILE = MODEL_DIR / "visdrone_yolov8m.pt"


# ============================================================
# 4. 开始下载
# ============================================================

print("=" * 70)
print("        VisDrone YOLOv8m 模型下载程序")
print("=" * 70)

print()
print("模型仓库：")
print(REPO_ID)

print()
print("模型文件：")
print(MODEL_FILE)

print()
print("保存位置：")
print(TARGET_FILE.resolve())

print()
print("开始下载，请稍候...")
print("=" * 70)


# ============================================================
# 5. 从 Hugging Face 下载模型
# ============================================================

try:

    downloaded_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=MODEL_FILE
    )

    print()
    print("Hugging Face 模型下载完成。")

    print("缓存位置：")
    print(downloaded_path)


# ============================================================
# 6. 复制模型到项目目录
# ============================================================

    shutil.copy2(
        downloaded_path,
        TARGET_FILE
    )

    print()
    print("=" * 70)
    print("模型保存成功！")
    print("=" * 70)

    print()
    print("最终模型路径：")
    print(TARGET_FILE.resolve())

    print()
    print("模型大小：")
    print(
        round(
            TARGET_FILE.stat().st_size / 1024 / 1024,
            2
        ),
        "MB"
    )

    print()
    print("最终目录：")
    print(MODEL_DIR.resolve())

    print()
    print("下载完成。")


# ============================================================
# 7. 异常处理
# ============================================================

except Exception as e:

    print()
    print("=" * 70)
    print("模型下载失败！")
    print("=" * 70)

    print()
    print("错误信息：")
    print(e)

    print()
    print("请检查：")
    print("1. 当前 Conda 环境是否正确")
    print("2. huggingface_hub 是否安装")
    print("3. 当前网络是否可以访问 Hugging Face")