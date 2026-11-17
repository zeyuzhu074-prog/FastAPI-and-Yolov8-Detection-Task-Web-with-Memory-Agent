import torch
import torch.nn as nn

# 直接调用 Ultralytics 官方模块
from ultralytics.nn.modules import (
    Conv,
    C2f,
    SPPF,
    Detect
)

from model_config import NC, CHANNELS


class YOLOv8Core(nn.Module):
    def __init__(self, nc=NC, channels=CHANNELS):
        super().__init__()

        # ================= Backbone =================

        # P1/2
        self.conv1 = Conv(
            3, channels[0], 3, 2
        )

        # P2/4
        self.conv2 = Conv(
            channels[0], channels[1], 3, 2
        )

        self.c2f1 = C2f(
            channels[1], channels[1], 3
        )

        # P3/8
        self.conv3 = Conv(
            channels[1], channels[2], 3, 2
        )

        self.c2f2 = C2f(
            channels[2], channels[2], 6
        )

        # P4/16
        self.conv4 = Conv(
            channels[2], channels[3], 3, 2
        )

        self.c2f3 = C2f(
            channels[3], channels[3], 6
        )

        # P5/32
        self.conv5 = Conv(
            channels[3], channels[4], 3, 2
        )

        self.c2f4 = C2f(
            channels[4], channels[4], 3
        )

        # SPPF
        self.sppf = SPPF(
            channels[4], channels[4], 5
        )

        # ================= Neck =================

        self.upsample = nn.Upsample(
            scale_factor=2,
            mode="nearest"
        )

        # P5 -> P4
        self.neck_c2f1 = C2f(
            channels[3] + channels[4],
            channels[3],
            3
        )

        # P4 -> P3
        self.neck_c2f2 = C2f(
            channels[2] + channels[3],
            channels[2],
            3
        )

        # P3 -> P4
        self.downsample1 = Conv(
            channels[2], channels[2], 3, 2
        )

        self.neck_c2f3 = C2f(
            channels[2] + channels[3],
            channels[3],
            3
        )

        # P4 -> P5
        self.downsample2 = Conv(
            channels[3], channels[3], 3, 2
        )

        self.neck_c2f4 = C2f(
            channels[3] + channels[4],
            channels[4],
            3
        )

        # ================= Detect =================

        self.detect = Detect(
            nc=nc,
            ch=(
                channels[2],
                channels[3],
                channels[4]
            )
        )

    def forward(self, x):
        # -------- Backbone --------
        x1 = self.conv1(x)

        x2 = self.c2f1(
            self.conv2(x1)
        )

        x3 = self.c2f2(
            self.conv3(x2)
        )

        x4 = self.c2f3(
            self.conv4(x3)
        )

        x5 = self.sppf(
            self.c2f4(
                self.conv5(x4)
            )
        )

        # -------- Neck: Top-down --------
        n4 = self.neck_c2f1(
            torch.cat(
                [self.upsample(x5), x4],
                dim=1
            )
        )

        n3 = self.neck_c2f2(
            torch.cat(
                [self.upsample(n4), x3],
                dim=1
            )
        )

        # -------- Neck: Bottom-up --------
        n4_out = self.neck_c2f3(
            torch.cat(
                [self.downsample1(n3), n4],
                dim=1
            )
        )

        n5_out = self.neck_c2f4(
            torch.cat(
                [self.downsample2(n4_out), x5],
                dim=1
            )
        )

        # -------- Detection --------
        return self.detect(
            (n3, n4_out, n5_out)
        )
