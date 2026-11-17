
import torch
import torch.nn as nn
import torch


def calculate_iou(box1, boxes):
    """
    计算一个框 box1 与多个框 boxes 的 IoU

    box1:  [4]       -> x1, y1, x2, y2
    boxes: [N, 4]    -> x1, y1, x2, y2

    return: [N]
    """

    # 计算交集区域左上角坐标
    inter_x1 = torch.maximum(box1[0], boxes[:, 0])
    inter_y1 = torch.maximum(box1[1], boxes[:, 1])

    # 计算交集区域右下角坐标
    inter_x2 = torch.minimum(box1[2], boxes[:, 2])
    inter_y2 = torch.minimum(box1[3], boxes[:, 3])

    # 计算交集区域宽度和高度
    inter_w = (inter_x2 - inter_x1).clamp(min=0)
    inter_h = (inter_y2 - inter_y1).clamp(min=0)

    # 计算交集面积
    inter_area = inter_w * inter_h

    # 计算 box1 面积
    area1 = (
        (box1[2] - box1[0]).clamp(min=0)
        * (box1[3] - box1[1]).clamp(min=0)
    )

    # 计算 boxes 中每个框的面积
    area2 = (
        (boxes[:, 2] - boxes[:, 0]).clamp(min=0)
        * (boxes[:, 3] - boxes[:, 1]).clamp(min=0)
    )

    # 计算并集面积
    union_area = area1 + area2 - inter_area

    # 防止除以 0
    iou = inter_area / union_area.clamp(min=1e-6)

    return iou
def nms(boxes, scores, iou_threshold):
    """
    非极大值抑制

    boxes: [N, 4]，格式 xyxy
    scores: [N]，每个框的置信度
    iou_threshold: IoU 阈值

    return: 保留下来的框索引
    """

    # 按置信度从高到低排序
    order = scores.argsort(descending=True)

    # 保存最终保留框的索引
    keep = []

    while order.numel() > 0:

        # 取当前置信度最高的框
        current = order[0]

        # 将当前框加入最终结果
        keep.append(current)

        # 如果只剩一个框，结束循环
        if order.numel() == 1:
            break

        # 获取剩余候选框
        remaining = order[1:]

        # 计算当前框与剩余框的 IoU
        ious = calculate_iou(
            boxes[current],
            boxes[remaining]
        )

        # 保留 IoU 小于阈值的框
        # IoU 大于阈值的框被认为是重复检测
        mask = ious <= iou_threshold

        order = remaining[mask]

    # 返回保留框索引
    return torch.stack(keep)
class YOLOv8PostProcess(nn.Module):

    def __init__(
        self,
        nc=10,                 # VisDrone 10 个类别
        reg_max=16,            # 每个方向 16 个离散分布值
        conf_threshold=0.25,   # 置信度阈值
        iou_threshold=0.45     # NMS 的 IoU 阈值
    ):
        super().__init__()

        self.nc = nc
        self.reg_max = reg_max
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

        # DFL 使用的离散位置：
        # [0, 1, 2, ..., 15]
        self.register_buffer(
            "project",
            torch.arange(reg_max, dtype=torch.float)
        )

    def decode_dfl(self, box_logits):
        """
        将 DFL 的离散分布转换为 4 个距离值。

        输入：
            box_logits: [B, 64, H, W]

        输出：
            distances: [B, 4, H, W]

        64 = 4 个方向 * 16 个离散值
        """

        B, _, H, W = box_logits.shape

        # [B, 64, H, W]
        # -> [B, 4, 16, H, W]
        box_logits = box_logits.reshape(
            B, 4, self.reg_max, H, W
        )

        # 对每个方向的 16 个离散值做 Softmax
        # 得到每个方向的概率分布
        box_prob = box_logits.softmax(dim=2)

        # 使用期望值将概率分布转换为连续距离
        # 例如：0*p0 + 1*p1 + ... + 15*p15
        distances = (
            box_prob
            * self.project.view(1, 1, self.reg_max, 1, 1)
        ).sum(dim=2)

        # [B, 4, H, W]
        return distances

    def make_anchors(self, H, W, stride, device):
        """
        为特征图每个网格生成 anchor point。

        YOLOv8 使用网格中心点作为参考点。
        """

        # 网格坐标
        y, x = torch.meshgrid(
            torch.arange(H, device=device),
            torch.arange(W, device=device),
            indexing="ij"
        )

        # 网格中心偏移 0.5
        # [H, W, 2]，最后一维为 x、y
        points = torch.stack(
            (x, y),
            dim=-1
        ).float() + 0.5

        # [H*W, 2]
        points = points.reshape(-1, 2)

        return points, stride

    def decode_boxes(self, distances, anchor_points, stride):
        """
        根据 anchor point 和 ltrb 距离解码边界框。

        distances:
            [B, 4, H*W]

        anchor_points:
            [H*W, 2]

        输出：
            boxes: [B, H*W, 4]，xyxy 格式
        """

        # [B, 4, H*W] -> [B, H*W, 4]
        distances = distances.permute(0, 2, 1)

        # anchor points: [H*W, 2]
        # 转成 [1, H*W, 2]，方便与 batch 维度广播
        anchor_points = anchor_points.unsqueeze(0)

        # 左上角坐标
        x1y1 = anchor_points - distances[..., :2]

        # 右下角坐标
        x2y2 = anchor_points + distances[..., 2:]

        # 合并为 xyxy
        boxes = torch.cat(
            (x1y1, x2y2),
            dim=-1
        )

        # 网格坐标转换为原图坐标
        boxes = boxes * stride

        return boxes

    def process_one_scale(self, feature, stride):
        """
        处理一个尺度的 Detect Head 输出。

        feature:
            [B, 74, H, W]

        74 = 64 个 bbox 分布值 + 10 个类别分数
        """

        B, _, H, W = feature.shape

        # --------------------------------
        # 1. 拆分边界框分支与分类分支
        # --------------------------------

        # [B, 64, H, W]
        box_logits = feature[:, :4 * self.reg_max]

        # [B, 10, H, W]
        cls_logits = feature[:, 4 * self.reg_max:]

        # --------------------------------
        # 2. DFL 解码
        # --------------------------------

        # [B, 64, H, W]
        # -> [B, 4, H, W]
        distances = self.decode_dfl(box_logits)

        # --------------------------------
        # 3. 创建网格参考点
        # --------------------------------

        anchor_points, stride = self.make_anchors(
            H, W, stride, feature.device
        )

        # --------------------------------
        # 4. 边界框坐标解码
        # --------------------------------

        # [B, 4, H, W]
        # -> [B, H*W, 4]
        boxes = self.decode_boxes(
            distances.reshape(B, 4, -1),
            anchor_points,
            stride
        )

        # --------------------------------
        # 5. 解码类别置信度
        # --------------------------------

        # 分类分支是 logits，需要 sigmoid
        # [B, 10, H, W]
        # -> [B, H*W, 10]
        cls_scores = cls_logits.sigmoid()
        cls_scores = cls_scores.flatten(2).transpose(1, 2)

        return boxes, cls_scores

    def forward(self, features):
        """
        features:
            三个尺度的原始输出

            P3: [B, 74, 80, 80]
            P4: [B, 74, 40, 40]
            P5: [B, 74, 20, 20]

        返回：
            每张图片最终检测结果
        """

        # 三个尺度分别对应 stride 8、16、32
        strides = [8, 16, 32]

        all_boxes = []
        all_scores = []

        # --------------------------------
        # 1. 逐尺度处理
        # --------------------------------

        for feature, stride in zip(features, strides):

            boxes, scores = self.process_one_scale(
                feature,
                stride
            )

            all_boxes.append(boxes)
            all_scores.append(scores)

        # --------------------------------
        # 2. 合并三个尺度
        # --------------------------------

        # [B, 6400+1600+400, 4]
        boxes = torch.cat(all_boxes, dim=1)

        # [B, 8400, 10]
        scores = torch.cat(all_scores, dim=1)

        # --------------------------------
        # 3. 逐张图片进行置信度过滤和 NMS
        # --------------------------------

        batch_results = []

        for batch_idx in range(boxes.shape[0]):

            image_boxes = boxes[batch_idx]
            image_scores = scores[batch_idx]

            # 每个候选位置取置信度最高的类别
            confidence, class_ids = image_scores.max(dim=1)

            # 置信度过滤
            mask = confidence >= self.conf_threshold

            image_boxes = image_boxes[mask]
            confidence = confidence[mask]
            class_ids = class_ids[mask]

            # 空结果处理
            if image_boxes.shape[0] == 0:
                batch_results.append(
                    torch.empty(
                        (0, 6),
                        device=boxes.device
                    )
                )
                continue

            # --------------------------------
            # 4. 按类别执行 NMS
            # --------------------------------

            final_detections = []

            for cls_id in class_ids.unique():

                cls_mask = class_ids == cls_id

                cls_boxes = image_boxes[cls_mask]
                cls_scores = confidence[cls_mask]

                # 这里调用前面实现的手动 NMS
                keep = nms(
                    cls_boxes,
                    cls_scores,
                    self.iou_threshold
                )

                selected_boxes = cls_boxes[keep]
                selected_scores = cls_scores[keep]

                # 生成类别列
                selected_class = torch.full_like(
                    selected_scores,
                    cls_id
                )

                # [M, 6]
                # x1, y1, x2, y2, confidence, class_id
                detections = torch.cat(
                    [
                        selected_boxes,
                        selected_scores[:, None],
                        selected_class[:, None]
                    ],
                    dim=1
                )

                final_detections.append(detections)

            # 合并当前图片所有类别
            if len(final_detections) > 0:
                image_result = torch.cat(
                    final_detections,
                    dim=0
                )
            else:
                image_result = torch.empty(
                    (0, 6),
                    device=boxes.device
                )

            batch_results.append(image_result)

        return batch_results
