from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database.database import Base, engine
from backend.database.migrate_round1 import ensure_schema

from backend.models.user import User
from backend.models.detection_record import DetectionRecord
from backend.models.detection_class_statistics import DetectionClassStatistics
from backend.models.admin_operation_log import AdminOperationLog

from backend.api.auth import router as auth_router
from backend.api.detection import router as detection_router
from backend.api.statistics import router as statistics_router
from backend.api.history import router as history_router
from backend.api.profile import router as profile_router
from backend.api.admin import router as admin_router
from backend.api.email import router as email_router

from backend.config.settings import AVATAR_DIR

# ==========================================
# 创建数据库表
# ==========================================

# 先执行第一轮结构迁移，再创建缺失的表
#ensure_schema()

#Base.metadata.create_all(bind=engine)


# ==========================================
# 创建 FastAPI 应用
# ==========================================

app = FastAPI(
    title="无人机智能巡检与目标检测系统",
    version="1.0.0",
    description="基于YOLOv8的无人机智能巡检与目标检测系统"
)


# ==========================================
# 配置跨域
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)


# ==========================================
# 注册用户认证接口
# ==========================================

app.include_router(
    auth_router
)


# ==========================================
# 注册图片检测接口
# ==========================================

app.include_router(
    detection_router
)
# ==========================================
# 结果分析检测接口
# ==========================================
app.include_router(
    statistics_router
)
# ==========================================
# 历史记录接口
# ==========================================
app.include_router(
    history_router
)
# ==========================================
# 个人信息接口
# ==========================================
app.include_router(profile_router)

# ==========================================
# 历史记录接口
# ==========================================
app.include_router(admin_router)

# ==========================================
# 邮箱发送接口
# ==========================================
app.include_router(email_router)


# 头像静态访问
app.mount(
    "/uploads/avatars",
    StaticFiles(directory=str(AVATAR_DIR)),
    name="avatars"
)

# ==========================================
# 系统首页
# ==========================================

@app.get("/")
def root():

    return {
        "system": "无人机智能巡检与目标检测系统",
        "version": "1.0.0",
        "status": "running",
        "message": "系统运行正常"
    }


# ==========================================
# 健康检查
# ==========================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }
