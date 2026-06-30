import cv2
import numpy as np
import tempfile
import os
from typing import List, Dict, Any, Optional
import asyncio
from app.core.config import get_settings
from app.services.detector import detector, cv2_puttext_zh
import base64
import time
import uuid
from redis.asyncio import Redis
import shutil

settings = get_settings()

# 视频处理任务状态
class VideoTaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoProcessor:
    def __init__(self):
        self.redis: Optional[Redis] = None
        self._use_redis = False
        self._tasks: Dict[str, Dict] = {}
        self._results: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
        self._store_initialized = False

    async def _init_store(self):
        if self._store_initialized:
            return
        self._store_initialized = True
        try:
            self.redis = Redis.from_url(settings.redis_url)
            await self.redis.ping()
            self._use_redis = True
            print("[VideoProcessor] Redis 连接成功，使用 Redis 存储")
        except Exception as e:
            print(f"[VideoProcessor] Redis 不可用 ({str(e)})，回退到内存存储")
            self._use_redis = False
            self.redis = None

    async def _set_task(self, task_id: str, task_info: Dict):
        if self._use_redis:
            await self.redis.set(f"video_task:{task_id}", repr(task_info))
        else:
            async with self._lock:
                self._tasks[task_id] = task_info.copy()

    async def _get_task(self, task_id: str) -> Optional[Dict]:
        if self._use_redis:
            raw = await self.redis.get(f"video_task:{task_id}")
            return eval(raw) if raw else None
        else:
            async with self._lock:
                info = self._tasks.get(task_id)
                return info.copy() if info else None

    async def _set_result(self, task_id: str, result: Dict):
        if self._use_redis:
            await self.redis.set(f"video_result:{task_id}", repr(result), ex=60*60*24*7)
        else:
            async with self._lock:
                self._results[task_id] = result.copy()

    async def _get_result(self, task_id: str) -> Optional[Dict]:
        if self._use_redis:
            raw = await self.redis.get(f"video_result:{task_id}")
            return eval(raw) if raw else None
        else:
            async with self._lock:
                res = self._results.get(task_id)
                return res.copy() if res else None

    async def create_task(self, video_bytes: bytes) -> str:
        try:
            await self._init_store()
            task_id = str(uuid.uuid4())

            temp_dir = tempfile.gettempdir()
            os.makedirs(os.path.join(temp_dir, "yolopest_videos"), exist_ok=True)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', dir=os.path.join(temp_dir, "yolopest_videos")) as tmp:
                tmp.write(video_bytes)
                video_path = tmp.name

            try:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise Exception(f"无法打开视频文件: {video_path}")
                cap.release()
            except Exception as video_error:
                os.unlink(video_path)
                raise Exception(f"视频格式无效或不受支持: {str(video_error)}")

            task_info = {
                "id": task_id,
                "status": VideoTaskStatus.PENDING,
                "video_path": video_path,
                "created_at": time.time(),
                "progress": 0
            }

            await self._set_task(task_id, task_info)

            asyncio.create_task(self._process_video(task_id))

            return task_id
        except Exception as e:
            import traceback
            stack_trace = traceback.format_exc()
            print(f"创建视频处理任务失败: {str(e)}\n{stack_trace}")
            raise

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        await self._init_store()
        task_info = await self._get_task(task_id)

        if not task_info:
            return {"status": "not_found"}

        if "video_path" in task_info:
            del task_info["video_path"]
        return task_info

    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        await self._init_store()
        task_info = await self._get_task(task_id)

        if not task_info:
            return {"status": "not_found"}

        result = await self._get_result(task_id)
        if not result:
            return {"status": task_info.get("status", "unknown"), "progress": task_info.get("progress", 0)}

        return result

    async def _process_video(self, task_id: str):
        task_info = await self._get_task(task_id)
        if not task_info:
            return

        video_path = task_info["video_path"]

        task_info["status"] = VideoTaskStatus.PROCESSING
        await self._set_task(task_id, task_info)

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("无法打开视频文件")

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_length = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            print(f"[视频任务 {task_id}] 视频信息: {width}x{height}, {fps:.2f}fps, 总帧数 {frame_count}, 时长 {video_length:.2f}s")

            MAX_WIDTH = 1280
            scale = 1.0
            if width > MAX_WIDTH:
                scale = MAX_WIDTH / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                print(f"[视频任务 {task_id}] 分辨率过大，缩放至 {new_width}x{new_height}")
            else:
                new_width, new_height = width, height

            TARGET_FPS = 4
            frame_interval = max(1, int(round(fps / TARGET_FPS)))
            output_fps = TARGET_FPS

            output_path = f"{tempfile.gettempdir()}/{task_id}_annotated.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (new_width, new_height))
            if not out.isOpened():
                print(f"[视频任务 {task_id}] avc1 编码器不可用，回退到 mp4v")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, output_fps, (new_width, new_height))

            results = []
            processed_frames = 0
            total_detections = 0

            start_time = time.time()

            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    if scale < 1.0:
                        process_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    else:
                        process_frame = frame

                    encode_ok, jpg_buffer = cv2.imencode('.jpg', process_frame)
                    if not encode_ok:
                        print(f"[视频任务 {task_id}] 帧 {frame_idx} 编码失败，跳过")
                        frame_idx += 1
                        continue

                    predictions = await asyncio.to_thread(detector.predict, jpg_buffer.tobytes())
                    print(f"[视频任务 {task_id}] 帧 {frame_idx} 检测到 {len(predictions)} 个目标")

                    output_frame = process_frame.copy()
                    annotated_frame = None
                    if predictions:
                        total_detections += len(predictions)
                        for pred in predictions:
                            bbox = pred["bbox"]
                            x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])
                            conf = pred.get("confidence", 0)
                            if conf >= 0.8:
                                box_color = (0, 255, 0)
                            elif conf >= 0.6:
                                box_color = (255, 215, 0)
                            elif conf >= 0.4:
                                box_color = (255, 140, 0)
                            else:
                                box_color = (128, 128, 128)
                            cv2.rectangle(output_frame, (x1, y1), (x2, y2), box_color, 2)
                            label_name = pred.get("class_zh") or pred.get("class", "未知")
                            label = f"{label_name} {conf:.2f}"
                            output_frame = cv2_puttext_zh(
                                output_frame, label, (x1, y1 - 2), color=box_color, font_size=16
                            )

                        _, buffer = cv2.imencode('.jpg', output_frame)
                        annotated_frame = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')

                    timestamp_ms = int(frame_idx / fps * 1000)
                    results.append({
                        "timestamp": timestamp_ms,
                        "frame_index": frame_idx,
                        "detections": predictions,
                        "annotated_frame": annotated_frame
                    })

                    processed_frames += 1

                    out.write(output_frame)

                progress = int((frame_idx / frame_count) * 100) if frame_count > 0 else 0
                task_info["progress"] = progress
                await self._set_task(task_id, task_info)

                frame_idx += 1

            print(f"[视频任务 {task_id}] 处理完成: 处理 {processed_frames} 帧, 总检测目标 {total_detections}")

            cap.release()
            out.release()

            end_time = time.time()
            processing_time = end_time - start_time

            static_dir = os.path.join("app", "static", "videos")
            os.makedirs(static_dir, exist_ok=True)

            annotated_video_url = f"/api/static/videos/{task_id}_annotated.mp4"

            final_path = os.path.join(static_dir, f"{task_id}_annotated.mp4")

            try:
                shutil.move(output_path, final_path)
            except Exception as e:
                print(f"移动文件失败，尝试复制: {str(e)}")
                shutil.copy(output_path, final_path)
                os.remove(output_path)

            result = {
                "status": "completed",
                "video_length": video_length,
                "processed_frames": processed_frames,
                "time_cost": processing_time,
                "fps": processed_frames / processing_time if processing_time > 0 else 0,
                "results": results,
                "annotated_video_url": annotated_video_url
            }

            task_info["status"] = VideoTaskStatus.COMPLETED
            task_info["progress"] = 100
            task_info["completed_at"] = time.time()
            task_info["annotated_video_path"] = final_path

            await self._set_task(task_id, task_info)
            await self._set_result(task_id, result)

        except Exception as e:
            print(f"视频处理失败: {str(e)}")
            task_info["status"] = VideoTaskStatus.FAILED
            task_info["error"] = str(e)
            await self._set_task(task_id, task_info)

        finally:
            try:
                if os.path.exists(video_path):
                    os.unlink(video_path)
            except:
                pass


video_processor = VideoProcessor()
