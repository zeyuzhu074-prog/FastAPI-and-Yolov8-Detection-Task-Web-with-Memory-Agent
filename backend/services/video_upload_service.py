from pathlib import Path

from fastapi import UploadFile

from backend.config.settings import (
    ORIGINAL_DIR,
    MAX_UPLOAD_SIZE_MB,
    VIDEO_EXTENSIONS
)

from backend.utils.file_utils import (
    generate_unique_filename,
    is_allowed_extension
)


class VideoUploadService:


    @staticmethod
    async def save_upload_video(
        upload_file: UploadFile
    ) -> str:
        """
        保存用户上传的视频文件

        返回:
            视频绝对路径
        """


        filename = upload_file.filename


        print("=" * 60)
        print("开始处理视频上传")
        print("原始文件名：", filename)
        print("上传目录：", ORIGINAL_DIR)


        # ==================================
        # 1. 文件名检查
        # ==================================

        if not filename:

            raise ValueError(
                "视频文件名不能为空"
            )


        # ==================================
        # 2. 视频格式检查
        # ==================================

        if not is_allowed_extension(
            filename,
            VIDEO_EXTENSIONS
        ):

            raise ValueError(
                "不支持的视频格式，仅支持："
                f"{','.join(VIDEO_EXTENSIONS)}"
            )


        # ==================================
        # 3. 生成唯一文件名
        # ==================================

        unique_filename = generate_unique_filename(
            filename
        )


        print(
            "生成的视频文件名：",
            unique_filename
        )


        # ==================================
        # 4. 保存路径
        # ==================================

        video_path = (
            ORIGINAL_DIR /
            unique_filename
        )


        print(
            "视频保存路径：",
            video_path
        )


        # ==================================
        # 5. 读取视频文件
        # ==================================

        content = await upload_file.read()


        print(
            "视频大小:",
            len(content),
            "bytes"
        )


        # ==================================
        # 6. 文件大小限制
        # ==================================

        max_size = (
            MAX_UPLOAD_SIZE_MB *
            1024 *
            1024
        )


        if len(content) > max_size:

            raise ValueError(
                f"视频大小不能超过"
                f"{MAX_UPLOAD_SIZE_MB}MB"
            )


        # ==================================
        # 7. 创建目录
        # ==================================

        ORIGINAL_DIR.mkdir(
            parents=True,
            exist_ok=True
        )


        # ==================================
        # 8. 写入文件
        # ==================================

        with open(
            video_path,
            "wb"
        ) as f:

            f.write(content)



        # ==================================
        # 9. 保存检查
        # ==================================

        print(
            "文件是否存在:",
            video_path.exists()
        )


        if video_path.exists():

            print(
                "保存大小:",
                video_path.stat().st_size,
                "bytes"
            )


        print("=" * 60)


        return str(video_path)