import re


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    """
    简单校验邮箱格式。
    """

    if not email:
        return False

    return bool(
        EMAIL_PATTERN.match(email.strip())
    )


def normalize_email(email):
    """
    去空格并转小写；空值统一返回 None。
    """

    if email is None:
        return None

    email = email.strip().lower()

    return email or None
