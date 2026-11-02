# 无人机智能巡检与目标检测系统

## 1. 项目简介

本项目面向无人机巡检场景，设计并实现一套基于YOLOv8目标检测模型的无人机图像智能分析系统。

系统采用前后端分离的B/S架构，通过Web界面完成无人机图像上传、目标检测、结果可视化、历史记录查询以及检测数据统计等功能。

模型部分采用YOLOv8预训练模型，并结合VisDrone无人机目标检测数据集进行验证和模型微调。

---

## 2. 主要功能

- 用户登录
- 无人机图像上传
- 图像格式及大小校验
- YOLOv8目标检测
- 检测结果可视化
- 检测结果保存
- 历史检测任务查询
- 检测任务详情查看
- 检测记录删除
- 检测数据统计
- VisDrone数据集验证
- YOLOv8模型微调
- 模型性能测试

---

## 3. 技术栈

### 后端

- Python
- FastAPI
- SQLAlchemy
- SQLite

### AI

- PyTorch
- Ultralytics YOLOv8
- OpenCV
- NumPy

### 前端

- HTML
- CSS
- JavaScript

### 数据集

VisDrone Dataset

---

## 4. 项目运行

安装依赖：

```bash
pip install -r requirements.txt