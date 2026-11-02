import json


def detection_result_to_json(
    detections: list
) -> str:
    """
    将检测结果转换为JSON字符串。
    """

    return json.dumps(
        detections,
        ensure_ascii=False
    )


def detection_result_from_json(
    result_text: str
):
    """
    将JSON字符串恢复为Python对象。
    """

    if not result_text:
        return []

    return json.loads(result_text)