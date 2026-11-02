"""
第一轮升级数据库迁移脚本。

原则：
1. 只新增字段和表，不删除、不重建已有表；
2. 可重复执行（幂等）；
3. 迁移后保留原有用户、检测记录和类别统计。

执行方式（项目根目录）：
    python -m backend.database.migrate_round1
"""

from sqlalchemy import inspect, text

from backend.database.database import Base, engine

# 导入所有模型，确保 create_all 能注册到新表
from backend.models.user import User
from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics
from backend.models.admin_operation_log import AdminOperationLog


USER_NEW_COLUMNS = {
    "email": "VARCHAR(255)",
    "avatar_path": "VARCHAR(500)",
    "updated_at": "DATETIME",
}

DETECTION_NEW_COLUMNS = {
    "remark": "VARCHAR(500)",
}


def _existing_columns(connection, table_name: str):
    rows = connection.execute(
        text(f'PRAGMA table_info("{table_name}")')
    ).fetchall()
    return {row[1] for row in rows}


def _add_missing_columns(
    connection,
    table_name: str,
    columns: dict
):
    existing = _existing_columns(connection, table_name)

    for name, column_type in columns.items():

        if name in existing:
            print(f"  [skip] {table_name}.{name} 已存在")
            continue

        connection.execute(
            text(
                f'ALTER TABLE "{table_name}" '
                f'ADD COLUMN "{name}" {column_type}'
            )
        )

        print(f"  [add ] {table_name}.{name}")


def ensure_schema():
    """
    执行第一轮所需的结构迁移，可安全重复调用。
    """

    print("开始执行第一轮数据库迁移...")

    with engine.begin() as connection:

        tables = {
            row[0]
            for row in connection.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table'"
                )
            ).fetchall()
        }

        if "user" in tables:
            print("检查 user 表：")
            _add_missing_columns(
                connection,
                "user",
                USER_NEW_COLUMNS
            )
        else:
            print("user 表尚不存在，将由 create_all 创建。")

        if "detection_record" in tables:
            print("检查 detection_record 表：")
            _add_missing_columns(
                connection,
                "detection_record",
                DETECTION_NEW_COLUMNS
            )
        else:
            print("detection_record 表尚不存在，将由 create_all 创建。")

        # 创建缺失的表（如 admin_operation_log）
        Base.metadata.create_all(bind=engine)

        # 回填 updated_at
        connection.execute(
            text(
                "UPDATE user SET updated_at = created_at "
                "WHERE updated_at IS NULL AND created_at IS NOT NULL"
            )
        )

        # 邮箱唯一（NULL 不参与唯一约束，使用部分索引）
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_user_email "
                "ON user (email) WHERE email IS NOT NULL"
            )
        )

    print("第一轮数据库迁移完成。")


def main():
    ensure_schema()


if __name__ == "__main__":
    main()
