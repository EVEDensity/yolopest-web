"""YOLO模型推理服务 — 供小程序检测路由使用
与 Web端 PestDetector 共享 pest_translator 中文翻译
"""

import os
import uuid
import threading
import time
from typing import Optional

from app.core.config import get_settings
from app.services.pest_translator import to_chinese, get_pest_aliases

settings = get_settings()

# 静态文件 URL 基础路径
STATIC_URL_BASE = "/api/static"


class YOLOService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            model_path = settings.model_path
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
                print(f"[YOLOService] 模型加载成功: {model_path}")
            else:
                print(f"[WARNING] 模型文件不存在: {model_path}，YOLO推理将不可用")
        except ImportError:
            print("[WARNING] ultralytics 未安装，YOLO推理将不可用")
        except Exception as e:
            print(f"[WARNING] 加载YOLO模型失败: {e}")

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def predict_image(self, image_path: str, output_dir: str = "") -> tuple[list[dict], str]:
        """图片检测，返回 (detections列表, result_filename或空字符串)"""
        import cv2

        if not self.is_ready:
            return self._mock_detection(), ""

        # 默认阈值降到 0.25，与 Web端 PestDetector 对齐，避免漏检
        threshold = min(settings.conf_thresh, 0.25)
        results = self.model(image_path, imgsz=settings.img_size, conf=threshold)
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    en_name = r.names[cls_id] if r.names else f"class_{cls_id}"
                    zh_name = to_chinese(en_name)
                    detections.append({
                        "name": zh_name,
                        "name_en": en_name,
                        "class_id": cls_id,
                        "aliases": get_pest_aliases(en_name),
                        "confidence": round(conf * 100, 1),
                        "bbox": xyxy,
                    })

        # 保存标注结果图（如果需要）
        result_filename = ""
        if output_dir:
            try:
                img = cv2.imread(image_path)
                if img is not None:
                    os.makedirs(output_dir, exist_ok=True)
                    result_filename = f"result_{uuid.uuid4().hex}.jpg"
                    output_path = os.path.join(output_dir, result_filename)
                    annotated = img
                    for r in results:
                        plotted = r.plot()
                        if plotted is not None:
                            annotated = cv2.cvtColor(plotted, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(output_path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            except Exception as e:
                print(f"[ERROR] 保存结果图片失败: {e}")

        return detections, result_filename

    def predict_video(self, video_path: str, frame_skip: int = 10) -> dict:
        """视频检测，返回汇总统计"""
        if not self.is_ready:
            return self._mock_video_detection()

        try:
            threshold = min(settings.conf_thresh, 0.25)
            results = self.model(video_path, imgsz=settings.img_size, conf=threshold, stream=True)
            pest_stats = {}
            total_frames = 0
            for i, r in enumerate(results):
                if i % frame_skip != 0:
                    continue
                total_frames += 1
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        en_name = r.names[cls_id] if r.names else f"class_{cls_id}"
                        zh_name = to_chinese(en_name)
                        pest_stats[zh_name] = pest_stats.get(zh_name, 0) + 1

            pest_types = [{"name": k, "count": v} for k, v in pest_stats.items()]
            return {
                "total_frames": total_frames,
                "pest_count": sum(pest_stats.values()),
                "pest_types": pest_types,
            }
        except Exception as e:
            print(f"[ERROR] 视频检测失败: {e}")
            return self._mock_video_detection()

    def predict_video_with_frames(
        self, video_path: str, output_dir: str,
        progress_callback=None, cancel_check=None
    ) -> dict:
        """
        视频逐帧检测（生成标注帧图），供异步任务使用。

        Args:
            video_path: 视频文件路径
            output_dir: 标注帧图输出目录
            progress_callback: 进度回调 callback(percent)
            cancel_check: 取消检查回调，返回True表示取消

        Returns:
            {
                "total_frames": int,
                "processed_frames": int,
                "pest_count": int,
                "pest_types": [{"name": str, "count": int}],
                "frames": [{"frame_index": int, "timestamp_ms": int,
                             "detections": [...], "annotated_frame": str|null}],
                "video_length": float,
                "fps": float,
            }
        """
        import cv2
        import base64

        if not self.is_ready:
            mock = self._mock_video_detection()
            mock["frames"] = []
            mock["video_length"] = 60.0
            mock["fps"] = 30.0
            return mock

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("无法打开视频文件")

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_length = frame_count / video_fps if video_fps > 0 else 0

            # 降采样：目标 ~4fps
            TARGET_FPS = 4
            frame_interval = max(1, int(round(video_fps / TARGET_FPS)))
            output_fps = TARGET_FPS

            os.makedirs(output_dir, exist_ok=True)

            pest_stats = {}
            total_pest_count = 0
            processed_frames = 0
            frames_data = []
            frame_idx = 0

            start_time = time.time()

            while cap.isOpened():
                if cancel_check and cancel_check():
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    # YOLO检测 — 直接传递BGR numpy数组（OpenCV帧格式）
                    threshold = min(settings.conf_thresh, 0.25)
                    temp_results = self.model(
                        frame,
                        imgsz=settings.img_size,
                        conf=threshold,
                        verbose=False
                    )

                    frame_detections = []
                    annotated_frame_b64 = None

                    for r in temp_results:
                        boxes = r.boxes
                        if boxes is not None and len(boxes) > 0:
                            for box in boxes:
                                cls_id = int(box.cls[0])
                                conf = float(box.conf[0])
                                xyxy = box.xyxy[0].tolist()
                                en_name = r.names[cls_id] if r.names else f"class_{cls_id}"
                                zh_name = to_chinese(en_name)
                                frame_detections.append({
                                    "name": zh_name,
                                    "name_en": en_name,
                                    "class_id": cls_id,
                                    "aliases": get_pest_aliases(en_name),
                                    "confidence": round(conf * 100, 1),
                                    "bbox": xyxy,
                                })

                            # 生成标注帧图
                            annotated = r.plot()
                            # annotated is RGB, convert to BGR for encoding
                            annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
                            _, buf = cv2.imencode('.jpg', annotated_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
                            annotated_frame_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode('utf-8')

                            # 统计
                            for d in frame_detections:
                                name = d["name"]
                                pest_stats[name] = pest_stats.get(name, 0) + 1
                                total_pest_count += 1

                    timestamp_ms = int(frame_idx / video_fps * 1000) if video_fps > 0 else 0
                    frames_data.append({
                        "frame_index": frame_idx,
                        "timestamp_ms": timestamp_ms,
                        "detections": frame_detections,
                        "annotated_frame": annotated_frame_b64,
                    })

                    processed_frames += 1

                if progress_callback:
                    progress = int((frame_idx / frame_count) * 100) if frame_count > 0 else 0
                    progress_callback(progress)

                frame_idx += 1

            cap.release()

            end_time = time.time()
            processing_time = end_time - start_time

            pest_types = [{"name": k, "count": v} for k, v in pest_stats.items()]

            return {
                "total_frames": frame_idx,  # 原始总帧数
                "processed_frames": processed_frames,
                "pest_count": total_pest_count,
                "pest_types": pest_types,
                "frames": frames_data,
                "video_length": round(video_length, 1),
                "fps": round(output_fps, 1),
                "time_cost": round(processing_time, 1),
            }

        except Exception as e:
            print(f"[ERROR] 视频逐帧检测失败: {e}")
            raise

    def save_result_image(self, image_path: str, output_dir: str) -> Optional[str]:
        """保存标注结果图，返回文件名（如 result_xxx.jpg），路径由调用方拼接"""
        if not self.is_ready:
            return None
        try:
            import cv2
            # 读取原图
            img = cv2.imread(image_path)
            if img is None:
                print(f"[ERROR] 无法读取图片: {image_path}")
                return None

            threshold = min(settings.conf_thresh, 0.25)
            results = self.model(image_path, imgsz=settings.img_size, conf=threshold)
            os.makedirs(output_dir, exist_ok=True)
            filename = f"result_{uuid.uuid4().hex}.jpg"
            output_path = os.path.join(output_dir, filename)

            # 用 YOLO plot() 绘制标注框，cv2.imwrite 保存（比 r.save() 路径处理更可靠）
            annotated = img
            for r in results:
                plotted = r.plot()  # RGB numpy array
                if plotted is not None:
                    annotated = cv2.cvtColor(plotted, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
            return filename
        except Exception as e:
            print(f"[ERROR] 保存结果图片失败: {e}")
            return None

    @staticmethod
    def _mock_detection() -> list[dict]:
        import random
        pests = ["稻飞虱", "棉铃虫", "玉米螟", "蚜虫", "红蜘蛛"]
        count = random.randint(1, 3)
        detections = []
        for _ in range(count):
            name = random.choice(pests)
            detections.append({
                "name": name,
                "name_en": name,
                "class_id": 0,
                "aliases": [],
                "confidence": round(random.uniform(70, 99), 1),
                "bbox": [
                    random.uniform(50, 200),
                    random.uniform(50, 200),
                    random.uniform(250, 400),
                    random.uniform(250, 400),
                ],
            })
        return detections

    @staticmethod
    def _mock_video_detection() -> dict:
        return {
            "total_frames": 1200,
            "pest_count": 47,
            "pest_types": [
                {"name": "稻飞虱", "count": 28},
                {"name": "棉铃虫", "count": 19},
            ],
        }


# ── 视频异步任务管理器（线程实现，兼容同步路由） ──

class VideoTaskManager:
    """小程序端视频异步任务管理器（基于线程）"""

    def __init__(self):
        self._tasks: dict = {}
        self._results: dict = {}
        self._lock = threading.Lock()

    def create_task(self, video_path: str, output_dir: str) -> str:
        """创建异步视频处理任务，返回 task_id"""
        task_id = uuid.uuid4().hex[:16]

        task_info = {
            "id": task_id,
            "status": "pending",
            "video_path": video_path,
            "created_at": time.time(),
            "progress": 0,
        }

        with self._lock:
            self._tasks[task_id] = task_info

        thread = threading.Thread(
            target=self._process_task,
            args=(task_id, video_path, output_dir),
            daemon=True
        )
        thread.start()

        return task_id

    def get_status(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return {
                "task_id": task["id"],
                "status": task["status"],
                "progress": task.get("progress", 0),
                "error": task.get("error"),
            }

    def get_result(self, task_id: str) -> dict | None:
        with self._lock:
            return self._results.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task["status"] in ("pending", "processing"):
                task["_cancel_flag"] = True
                return True
            return False

    def _process_task(self, task_id: str, video_path: str, output_dir: str):
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task["status"] = "processing"

        try:
            def progress_cb(pct):
                with self._lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["progress"] = pct

            def cancel_check():
                with self._lock:
                    return self._tasks.get(task_id, {}).get("_cancel_flag", False)

            result = yolo_service.predict_video_with_frames(
                video_path=video_path,
                output_dir=output_dir,
                progress_callback=progress_cb,
                cancel_check=cancel_check,
            )

            with self._lock:
                self._results[task_id] = result
                if task_id in self._tasks:
                    self._tasks[task_id]["status"] = "completed"
                    self._tasks[task_id]["progress"] = 100

        except Exception as e:
            print(f"[VideoTask] 任务 {task_id} 失败: {e}")
            with self._lock:
                if task_id in self._tasks:
                    self._tasks[task_id]["status"] = "failed"
                    self._tasks[task_id]["error"] = str(e)

        finally:
            # 清理临时视频文件
            try:
                if os.path.exists(video_path):
                    os.unlink(video_path)
            except Exception:
                pass


yolo_service = YOLOService()
video_task_manager = VideoTaskManager()
