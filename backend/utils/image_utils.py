import cv2


def check_image(image_path: str) -> bool:
    """
    检查图片是否能够正常读取。
    """

    image = cv2.imread(image_path)

    if image is None:
        return False

    return True


def get_image_size(image_path: str):
    """
    获取图片尺寸。

    返回：
    width, height
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    height, width = image.shape[:2]

    return width, height