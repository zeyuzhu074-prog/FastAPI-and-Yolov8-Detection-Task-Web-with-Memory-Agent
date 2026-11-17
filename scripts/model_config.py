# model_config.py

import math

# VisDrone 数据集包含 10 个类别
NC = 10

# YOLOv8m 模型缩放参数
DEPTH = 0.67
WIDTH = 0.75
MAX_CHANNELS = 768


def make_divisible(x, divisor=8):
    """
    将通道数调整为 divisor 的整数倍
    """
    return math.ceil(x / divisor) * divisor


def scale_channels(c):
    """
    根据 YOLOv8m YAML 缩放通道数
    """
    return make_divisible(
        min(c, MAX_CHANNELS) * WIDTH,
        8
    )


def scale_depth(n):
    """
    根据 YOLOv8m YAML 缩放模块重复次数
    """
    return max(round(n * DEPTH), 1)


# YAML 中的原始通道数经过 width scaling 后的结果
CHANNELS = [
    scale_channels(64),     # 48
    scale_channels(128),    # 96
    scale_channels(256),    # 192
    scale_channels(512),    # 384
    scale_channels(1024)   # 576
]


if __name__ == "__main__":

    print("实际通道配置:", CHANNELS)

    print("C2f重复3次:", scale_depth(3))

    print("C2f重复6次:", scale_depth(6))