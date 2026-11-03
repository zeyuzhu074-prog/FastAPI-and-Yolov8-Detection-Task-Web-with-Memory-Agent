# 无人机智能巡检与目标检测系统

## 1. 项目简介

本项目面向无人机巡检场景，基于 YOLOv8 目标检测模型，提供航拍图片和视频的目标检测、结果可视化、历史记录查询与统计分析能力。

系统采用前后端分离的 B/S 架构：

- 后端：Python、FastAPI、SQLAlchemy、SQLite
- AI：PyTorch、Ultralytics YOLOv8、OpenCV、NumPy
- 前端：原生 HTML、CSS、JavaScript、ECharts
- 认证：JWT（Bearer Token）+ bcrypt 密码哈希

## 2. 主要功能

### 普通用户

- 用户注册、登录、修改密码
- 个人中心：用户名、邮箱、头像、角色、注册时间
- 航拍图片上传与目标检测
- 航拍视频上传与逐帧目标检测
- 检测结果可视化、播放与下载
- 检测报告发送到邮箱
- 历史记录查询：时间范围、文件名、类型、状态、分页
- 检测详情查看
- 统计分析：今日目标占比、类别数量、每日趋势、类别趋势

### 管理员

在普通用户功能基础上，管理员还可以：

- 查询全部用户
- 新增用户
- 修改用户资料
- 禁用 / 启用用户
- 重置用户密码
- 删除用户（同时删除其检测记录和文件）
- 查询全部用户的检测记录
- 修改检测记录的文件名、备注和状态
- 物理删除检测记录及其原始文件、结果文件和类别统计
- 查看管理员操作审计日志（按操作类型、对象类型、日期和关键词筛选）
- 所有重要操作写入管理员操作审计日志

## 3. 项目结构

```text
backend/
├── app.py                    # FastAPI 入口
├── config/settings.py        # 配置读取
├── database/                 # 引擎、迁移、管理员创建
├── models/                   # ORM 模型
├── api/                      # 路由层
├── services/                 # 业务逻辑层
├── utils/                    # 工具函数
└── dependencies/             # JWT 认证与权限依赖

frontend/
├── index.html                # 入口页
├── login.html                # 登录/注册
├── statistics.html           # 统计分析
├── detection.html            # 图片/视频检测
├── history.html              # 历史记录
├── profile.html              # 个人中心
├── admin.html                # 管理员后台
├── css/style.css
├── js/
├── assets/
└── vendor/                   # 本地 ECharts / Lucide

uploads/
├── original/                 # 原始上传文件
├── results/                  # 检测结果
└── avatars/                  # 用户头像
```

## 4. 快速开始

### 4.1 安装依赖

```bash
conda activate 你的环境名
pip install -r requirements.txt
```

### 4.2 准备模型

默认模型路径为 `models/pretrained/visdrone_yolov8m.pt`。

如果模型不存在，可以执行：

```bash
python download_visdrone_model.py
```

### 4.3 数据库迁移

首次升级或已有数据库时执行：

```bash
python -m backend.database.migrate_round1
```

脚本只新增字段和表，不删除、不重建已有数据，可重复执行。

### 4.4 创建管理员

```bash
python -m backend.database.create_admin --username admin --password 你的密码 --email admin@example.com
```

如果用户已存在，可加 `--promote-existing` 提升为管理员。

### 4.5 配置邮件（可选）

163 邮箱示例：

```powershell
$env:UAV_SMTP_USER="你的163邮箱@163.com"
$env:UAV_SMTP_PASSWORD="你的163授权码"
```

JWT 密钥建议在生产环境通过环境变量覆盖：

```powershell
$env:UAV_JWT_SECRET="一个足够长的随机字符串"
```

### 4.6 启动后端

```bash
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

接口文档：`http://127.0.0.1:8000/docs`

### 4.7 启动前端

方式一：直接打开 `frontend/index.html`。

方式二（推荐）：

```bash
python -m http.server 5500 --directory frontend
```

然后访问 `http://127.0.0.1:5500/index.html`。

## 5. 权限说明

- 登录成功后返回 JWT，前端保存在 `localStorage["uav.session"]`。
- 所有用户级接口要求 `Authorization: Bearer <token>`。
- 后端从数据库读取角色，不信任前端传入的 role。
- 普通用户只能访问自己的检测记录和统计。
- 管理员通过 `/api/admin/*` 管理用户，并可管理全部检测记录。
- 不能禁用/删除当前登录管理员，不能移除最后一个有效管理员。

## 6. 数据库说明

当前生效数据库为项目根目录 `uav_inspection.db`。

主要表：

- `user`：用户、邮箱、头像、角色、状态
- `detection_record`：检测任务、文件路径、统计字段、备注
- `detection_class_statistics`：每条记录的类别统计
- `admin_operation_log`：管理员操作审计

`backend/uav_inspection.db` 是旧版遗留库，当前代码不读取。

## 7. 已知事项

- `scripts/` 下的训练、验证、基准测试脚本目前为空文件，尚未实现。
- `models/finetuned/visdrone_yolov8/best.pt` 当前为 0 字节占位文件。
- 视频检测为请求内同步逐帧推理，长视频会长时间占用请求。
- 结果视频使用 H.264 编码，保证浏览器可播放。
- 修改前端文件后如页面未更新，请使用 `Ctrl+Shift+R` 强制刷新。

## 8. 第二轮规划

第二轮计划在现有用户、检测记录和权限基础上增加：

- RAG：无人机巡检相关文档知识库
- Function Calling：查询历史、查询统计、生成报告
- Skills：可复用的领域能力
- Agent Memory：用户偏好与任务上下文
- ReAct 流程：思考 → 行动 → 观察 → 最终回答

详细设计见 `docs/10_第一轮升级说明.md`。
