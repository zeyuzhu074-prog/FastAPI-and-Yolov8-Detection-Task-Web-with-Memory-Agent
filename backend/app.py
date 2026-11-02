from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import Base, engine

from backend.models.user import User
from backend.models.detection_record import DetectionRecord

from backend.api.auth import router as auth_router
from backend.api.detection import router as detection_router
from backend.api.statistics import router as statistics_router
from backend.api.history import router as history_router

# ==========================================
# 创建数据库表
# ==========================================

Base.metadata.create_all(
    bind=engine
)


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
    allow_headers=["*"]
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
app.include_router(
    history_router
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