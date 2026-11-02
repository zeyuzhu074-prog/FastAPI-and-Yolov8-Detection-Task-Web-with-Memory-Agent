from pathlib import Path

from fastapi import UploadFile

from backend.config.settings import (
    ORIGINAL_DIR,
    MAX_UPLOAD_SIZE_MB,
    VIDEO_EXTENSIONS,
    IMAGE_EXTENSIONS
)

from backend.utils.file_utils import (
    generate_unique_filename,
    is_allowed_extension
)


class ImageService:

    @staticmethod
    async def save_upload_iamgefile(upload_file: UploadFile) -> str:
        """
        保存用户上传的图片
        """

        # ==========================================
        # 1. 获取原始文件名
        # ==========================================

        filename = upload_file.filename

        print("=" * 60)
        print("开始处理上传文件")
        print("原始文件名：", filename)
        print("上传目录：", ORIGINAL_DIR)
        print("上传目录是否存在：", ORIGINAL_DIR.exists())

        if not filename:
            raise ValueError("文件名不能为空")

        # ==========================================
        # 2. 检查文件扩展名
        # ==========================================

        if not is_allowed_extension(
            filename,
            #VIDEO_EXTENSIONS,
                IMAGE_EXTENSIONS
        ):
            raise ValueError(
                f"不支持的图片格式，仅支持："
                f"{', '.join(IMAGE_EXTENSIONS)}"
            )

        # ==========================================
        # 3. 生成唯一文件名
        # ==========================================

        unique_filename = generate_unique_filename(
            filename
        )

        print("生成的文件名：", unique_filename)

        # ==========================================
        # 4. 生成最终保存路径
        # ==========================================

        save_path = ORIGINAL_DIR / unique_filename

        print("最终保存路径：", save_path)
        print("绝对保存路径：", save_path.resolve())

        # ==========================================
        # 5. 读取上传文件
        # ==========================================

        content = await upload_file.read()

        print("读取到的文件大小：", len(content), "bytes")

        # ==========================================
        # 6. 检查文件大小
        # ==========================================

        max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(content) > max_size:
            raise ValueError(
                f"文件大小不能超过 {MAX_UPLOAD_SIZE_MB} MB"
            )

        # ==========================================
        # 7. 确保目录存在
        # ==========================================

        ORIGINAL_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        # ==========================================
        # 8. 保存文件
        # ==========================================

        with open(save_path, "wb") as file:
            file.write(content)

        # ==========================================
        # 9. 检查文件是否真的保存成功
        # ==========================================

        print("文件是否存在：", save_path.exists())

        if save_path.exists():
            print(
                "保存后的文件大小：",
                save_path.stat().st_size,
                "bytes"
            )

        print("=" * 60)

        return str(save_path)

    @staticmethod
    def delete_file(file_path: str):
        """
        删除指定文件
        """

        path = Path(file_path)

        if path.exists():
            path.unlink()