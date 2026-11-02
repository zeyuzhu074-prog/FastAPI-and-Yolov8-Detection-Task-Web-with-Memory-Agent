from pathlib import Path
import uuid


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一文件名。

    例如：
    drone.jpg

    转换为：
    8a72c3d1_drone.jpg
    """

    suffix = Path(original_filename).suffix.lower()

    unique_name = f"{uuid.uuid4().hex}{suffix}"

    return unique_name


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名。
    """
    return Path(filename).suffix.lower()


def is_allowed_extension(
    filename: str,
    allowed_extensions: list
) -> bool:
    """
    判断文件格式是否允许。
    """
    extension = get_file_extension(filename)

    return extension in allowed_extensions
def is_image_file(filename: str, allowed_extensions: list) -> bool:
    """
    判断是否为图片文件
    """

    suffix = Path(filename).suffix.lower()

    return suffix in allowed_extensions


def is_video_file(filename: str, allowed_extensions: list) -> bool:
    """
    判断是否为视频文件
    """

    suffix = Path(filename).suffix.lower()

    return suffix in allowed_extensions