import io
import uuid
from pathlib import Path

from fastapi import UploadFile
from PIL import Image

from backend.config.settings import (
    AVATAR_DIR,
    AVATAR_EXTENSIONS,
    MAX_AVATAR_SIZE_MB,
)


async def save_avatar_file(upload_file: UploadFile) -> str:
    """
    校验并保存头像，返回保存后的文件名。
    """

    filename = upload_file.filename

    if not filename:
        raise ValueError("头像文件名不能为空")

    extension = Path(filename).suffix.lower()

    if extension not in AVATAR_EXTENSIONS:
        raise ValueError(
            "不支持的头像格式，仅支持："
            + " / ".join(AVATAR_EXTENSIONS)
        )

    content = await upload_file.read()

    if not content:
        raise ValueError("头像文件不能为空")

    max_size = MAX_AVATAR_SIZE_MB * 1024 * 1024

    if len(content) > max_size:
        raise ValueError(
            f"头像大小不能超过 {MAX_AVATAR_SIZE_MB} MB"
        )

    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
    except Exception:
        raise ValueError("上传的文件不是有效图片")

    AVATAR_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    unique_name = f"{uuid.uuid4().hex}{extension}"

    (AVATAR_DIR / unique_name).write_bytes(content)

    return unique_name


def delete_avatar_file(filename: str):
    """
    删除头像文件；文件不存在时忽略。
    """

    if not filename:
        return

    try:
        path = AVATAR_DIR / Path(filename).name

        if path.exists() and path.is_file():
            path.unlink()

    except OSError:
        pass
