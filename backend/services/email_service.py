import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from sqlalchemy.orm import Session

from backend.config.settings import (
    PUBLIC_BASE_URL,
    SMTP_FROM_NAME,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_SSL,
    SMTP_USERNAME,
)
from backend.models.detection_class_statistics import (
    DetectionClassStatistics,
)
from backend.models.detection_record import DetectionRecord
from backend.models.user import User
from backend.utils.validators import is_valid_email


MAX_IMAGE_ATTACHMENT_MB = 10


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


def _format_time(value):
    if not value:
        return "-"

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def _build_html(record, class_statistics):
    is_video = record.task_type == "video"

    rows = [
        ("检测记录编号", f"#{record.id}"),
        ("原始文件名", record.original_name),
        ("检测类型", "视频检测" if is_video else "图片检测"),
        ("检测时间", _format_time(record.created_at)),
        ("任务状态", record.status),
        ("检测目标总数", record.object_count or 0),
        ("推理耗时", f"{record.inference_time or 0:.4f} 秒"),
        ("媒体尺寸", f"{record.width or '-'} × {record.height or '-'}"),
    ]

    if is_video:
        rows.extend([
            ("视频帧数", record.frame_count or 0),
            ("视频帧率", f"{record.fps or '-'} FPS"),
            ("单帧最大目标数", record.max_objects or 0),
            ("平均每帧目标数", record.average_objects or 0),
        ])

    info_rows = "".join(
        f"<tr><td style='padding:6px 10px;color:#6b7280;"
        f"border-bottom:1px solid #eef0f3'>{key}</td>"
        f"<td style='padding:6px 10px;border-bottom:1px solid #eef0f3'>"
        f"{value}</td></tr>"
        for key, value in rows
    )

    class_rows = "".join(
        f"<tr><td style='padding:6px 10px;border-bottom:1px solid #eef0f3'>"
        f"{item.class_name}</td>"
        f"<td style='padding:6px 10px;text-align:right;"
        f"border-bottom:1px solid #eef0f3'>{item.count}</td></tr>"
        for item in class_statistics
    ) or (
        "<tr><td colspan='2' style='padding:10px;color:#9aa1ad'>"
        "本次检测没有类别统计</td></tr>"
    )

    video_note = ""

    if is_video:
        video_note = (
            "<p style='color:#6b7280;font-size:13px;line-height:1.7'>"
            "视频结果文件较大，未作为附件发送。"
            "请登录系统，在历史记录中查看或下载该检测结果。"
            "</p>"
        )

    return f"""
    <div style="font-family:'Microsoft YaHei',Arial,sans-serif;color:#14161a;max-width:640px">
      <h2 style="font-size:18px;margin:0 0 6px">无人机巡检检测报告</h2>
      <p style="color:#6b7280;font-size:13px;margin:0 0 18px">
        系统自动生成，记录编号 #{record.id}
      </p>
      <table style="border-collapse:collapse;width:100%;font-size:13px">
        {info_rows}
      </table>
      <h3 style="font-size:14px;margin:20px 0 8px">类别统计</h3>
      <table style="border-collapse:collapse;width:100%;font-size:13px">
        <tr style="background:#f7f8fa">
          <th style="text-align:left;padding:6px 10px;border-bottom:1px solid #eef0f3">类别</th>
          <th style="text-align:right;padding:6px 10px;border-bottom:1px solid #eef0f3">数量</th>
        </tr>
        {class_rows}
      </table>
      {video_note}
      <p style="color:#9aa1ad;font-size:12px;margin-top:20px">
        本邮件由 {PUBLIC_BASE_URL} 自动发送。
      </p>
    </div>
    """


def send_report(
    db: Session,
    record: DetectionRecord,
    recipient_email: str,
):
    """
    将检测报告发送到指定邮箱。
    """

    if not _smtp_configured():
        raise ValueError(
            "邮件服务尚未配置，请设置环境变量 "
            "UAV_SMTP_USER 和 UAV_SMTP_PASSWORD"
        )

    recipient_email = (recipient_email or "").strip()

    if not is_valid_email(recipient_email):
        raise ValueError("收件邮箱格式不正确")

    class_statistics = (
        db.query(DetectionClassStatistics)
        .filter(
            DetectionClassStatistics.record_id
            == record.id
        )
        .order_by(DetectionClassStatistics.count.desc())
        .all()
    )

    is_video = record.task_type == "video"

    message = EmailMessage()
    message["Subject"] = (
        f"【无人机巡检】{record.original_name} 检测报告"
    )
    message["From"] = formataddr(
        (SMTP_FROM_NAME, SMTP_USERNAME)
    )
    message["To"] = recipient_email

    message.set_content(
        "您的无人机巡检检测报告已生成，请使用支持 HTML 的邮件客户端查看。"
    )

    message.add_alternative(
        _build_html(record, class_statistics),
        subtype="html",
    )

    attached = False

    if not is_video and record.result_path:

        result_path = Path(record.result_path)

        if (
            result_path.exists()
            and result_path.is_file()
            and result_path.stat().st_size
            <= MAX_IMAGE_ATTACHMENT_MB * 1024 * 1024
        ):
            message.add_attachment(
                result_path.read_bytes(),
                maintype="image",
                subtype="jpeg",
                filename=f"{Path(record.original_name).stem}_result.jpg",
            )
            attached = True

    context = ssl.create_default_context()

    try:

        if SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(
                SMTP_HOST,
                SMTP_PORT,
                timeout=20,
                context=context,
            )
        else:
            server = smtplib.SMTP(
                SMTP_HOST,
                SMTP_PORT,
                timeout=20,
            )
            server.starttls(context=context)

        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(message)
        server.quit()

    except Exception as error:
        raise ValueError(f"邮件发送失败：{error}")

    return {
        "record_id": record.id,
        "to": recipient_email,
        "attached_result_image": attached,
        "is_video": is_video,
    }
