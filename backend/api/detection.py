from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)
from sqlalchemy.orm import Session

from backend.database.database import get_db

from backend.services.video_upload_service import (
    VideoUploadService
)

from fastapi.responses import FileResponse

from backend.services.image_upload_service import ImageService

from backend.services.download_service import (
    DownloadService
)

from backend.utils.image_utils import (
    check_image,
    get_image_size
)
from pathlib import Path
import shutil
from backend.config.settings import (
    ORIGINAL_DIR,
    VIDEO_EXTENSIONS
)

from backend.services.detection_service import detection_service

from backend.utils.file_utils import (
    generate_unique_filename,
    is_video_file
)

router = APIRouter(
    prefix="/api/detection",
    tags=["目标检测"]
)

@router.post("/image")
async def upload_image(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传无人机图片并进行目标检测。
    """

    # ==================================
    # 1. 保存上传文件
    # ==================================

    try:

        image_path = (
            await ImageService.save_upload_iamgefile(
                file
            )
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"图片上传失败：{str(e)}"
        )

    # ==================================
    # 2. 检查图片是否有效
    # ==================================

    try:

        if not check_image(image_path):

            ImageService.delete_file(
                image_path
            )

            raise HTTPException(
                status_code=400,
                detail="上传的文件不是有效图片"
            )

    except HTTPException:

        raise

    except Exception as e:

        ImageService.delete_file(
            image_path
        )

        raise HTTPException(
            status_code=400,
            detail=f"图片检查失败：{str(e)}"
        )

    # ==================================
    # 3. 检查图片文件是否存在
    # ==================================

    image_file = Path(
        image_path
    )

    if not image_file.exists():

        raise HTTPException(
            status_code=400,
            detail="图片文件不存在"
        )

    # ==================================
    # 4. 调用YOLO图片推理
    # ==================================

    try:

        result = detection_service.detect_image(
            db=db,
            user_id=user_id,
            image_path=image_path,
            original_name=file.filename
        )

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"图片检测失败：{str(e)}"
        )

    # ==================================
    # 5. 返回检测结果
    # ==================================

    return {

        "success": True,

        "message": "图片检测完成",

        "data": {

            "user_id":
                user_id,

            "record_id":
                result["record_id"],

            "original_image":
                image_path,

            "result_image":
                result["result_path"],

            "objects":
                result["object_count"],

            "inference_time":
                result["inference_time"],

            "width":
                result["width"],

            "height":
                result["height"],

            "detections":
                result["detections"],

            "class_statistics":
                result["class_statistics"]
        }
    }

@router.post("/video")
async def detect_video(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    无人机视频目标检测接口

    参数：
        user_id：
            当前用户ID

        file：
            用户上传的视频文件

        db：
            数据库Session
    """

    try:

        # ==================================
        # 1. 保存上传视频
        # ==================================

        video_path = (
            await VideoUploadService.save_upload_video(
                file
            )
        )

        # ==================================
        # 2. 检查视频文件是否存在
        # ==================================

        video_file = Path(
            video_path
        )

        if not video_file.exists():

            raise HTTPException(
                status_code=400,
                detail="视频文件不存在"
            )

        # ==================================
        # 3. 调用YOLO视频推理
        # ==================================

        result = detection_service.detect_video(
            db=db,
            user_id=user_id,
            video_path=video_path,
            original_name=file.filename
        )

        # ==================================
        # 4. 返回检测结果
        # ==================================

        return {

            "success": True,

            "message":
                "视频检测完成",

            "data": {

                # ==============================
                # 用户ID
                # ==============================

                "user_id":
                    user_id,

                # ==============================
                # 数据库检测记录ID
                # ==============================

                "record_id":
                    result["record_id"],

                # ==============================
                # 原始视频
                # ==============================

                "original_video":
                    video_path,

                # ==============================
                # 检测结果视频
                # ==============================

                "result_video":
                    result["result_path"],

                # ==============================
                # 视频处理帧数
                # ==============================

                "frame_count":
                    result["frame_count"],

                # ==============================
                # 累计检测目标数
                # ==============================

                "object_count":
                    result["object_count"],

                # ==============================
                # 单帧最大目标数
                # ==============================

                "max_objects_in_frame":
                    result["max_objects_in_frame"],

                # ==============================
                # 平均每帧目标数
                # ==============================

                "average_objects_per_frame":
                    result[
                        "average_objects_per_frame"
                    ],

                # ==============================
                # 推理耗时
                # ==============================

                "inference_time":
                    result["inference_time"],

                # ==============================
                # 视频FPS
                # ==============================

                "fps":
                    result["fps"],

                # ==============================
                # 视频宽高
                # ==============================

                "width":
                    result["width"],

                "height":
                    result["height"],

                # ==============================
                # 类别统计
                # ==============================

                "class_statistics":
                    result["class_statistics"]
            }
        }

    except HTTPException:

        raise

    except ValueError as e:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"视频检测失败：{str(e)}"
        )

@router.get("/download/{record_id}")
async def download_detection_result(
    record_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    下载检测生成的结果文件。

    图片检测：
        下载检测结果图片

    视频检测：
        下载检测结果视频
    """

    try:

        # ==========================================
        # 1. 获取结果文件
        # ==========================================

        result = (
            DownloadService
            .get_result_file(
                db=db,
                user_id=user_id,
                record_id=record_id
            )
        )

        # ==========================================
        # 2. 返回文件
        # ==========================================

        return FileResponse(
            path=result["path"],
            filename=result["filename"],
            media_type="application/octet-stream"
        )

    except ValueError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"结果文件下载失败：{str(e)}"
        )