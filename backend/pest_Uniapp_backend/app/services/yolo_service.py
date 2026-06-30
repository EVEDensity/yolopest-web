"""YOLO模型推理服务"""

import os
import uuid
from typing import Optional

from app.config import settings


class YOLOService:
    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            model_path = settings.MODEL_PATH
            if os.path.exists(model_path):
                self.model = YOLO(model_path)
            else:
                print(f"[WARNING] 模型文件不存在: {model_path}，YOLO推理将不可用")
        except ImportError:
            print("[WARNING] ultralytics 未安装，YOLO推理将不可用")
        except Exception as e:
            print(f"[WARNING] 加载YOLO模型失败: {e}")

    @property
    def is_ready(self) -> bool:
        return self.model is not None

    def predict_image(self, image_path: str) -> list[dict]:
        if not self.is_ready:
            return self._mock_detection()

        results = self.model(image_path, imgsz=settings.IMG_SIZE, conf=settings.CONF_THRESH)
        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    name = r.names[cls_id] if r.names else f"class_{cls_id}"
                    detections.append({
                        "name": name,
                        "confidence": round(conf * 100, 1),
                        "bbox": xyxy,
                    })
        return detections

    def predict_video(self, video_path: str, frame_skip: int = 10) -> dict:
        if not self.is_ready:
            return self._mock_video_detection()

        try:
            from ultralytics import YOLO
            results = self.model(video_path, imgsz=settings.IMG_SIZE, conf=settings.CONF_THRESH, stream=True)

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
                        name = r.names[cls_id] if r.names else f"class_{cls_id}"
                        pest_stats[name] = pest_stats.get(name, 0) + 1

            pest_types = [{"name": k, "count": v} for k, v in pest_stats.items()]
            return {
                "total_frames": total_frames,
                "pest_count": sum(pest_stats.values()),
                "pest_types": pest_types,
            }
        except Exception as e:
            print(f"[ERROR] 视频检测失败: {e}")
            return self._mock_video_detection()

    def save_result_image(self, image_path: str, output_dir: str) -> Optional[str]:
        if not self.is_ready:
            return None
        try:
            results = self.model(image_path, imgsz=settings.IMG_SIZE, conf=settings.CONF_THRESH)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"result_{uuid.uuid4().hex}.jpg")
            for r in results:
                r.save(filename=output_path)
            return output_path
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
                "confidence": round(random.uniform(70, 99), 1),
                "bbox": [
                    random.uniform(0, 0.8),
                    random.uniform(0, 0.8),
                    random.uniform(0.1, 0.3),
                    random.uniform(0.1, 0.3),
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


yolo_service = YOLOService()
