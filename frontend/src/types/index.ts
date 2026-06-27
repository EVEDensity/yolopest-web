export interface DetectionBox {
    x1: number
    y1: number
    x2: number
    y2: number
}

export interface DetectionItem {
    class: string                // 主显示字段（兼容旧版，后端已返回中文）
    class_en?: string            // 英文原名（学名/数据集名）
    class_zh?: string            // 中文名（首选展示）
    class_id?: number            // 模型类别 ID
    aliases?: string[]           // 别名
    confidence: number
    pest?: string
    bbox?: DetectionBox
    box?: [number, number, number, number]
}

export interface PestResult {
    status: 'success' | 'no_detection' | 'error'
    message?: string
    time_cost: number
    results: DetectionItem[]
    annotated_image?: string | null
    error?: string
}

export interface BatchFileResult {
    filename: string
    status: 'success' | 'error' | 'no_detection'
    message?: string
    predictions?: DetectionItem[]
    annotated_image?: string | null
    error?: string
}

export interface BatchProcessResult {
    status: string
    time_cost: number
    processed_count: number
    detection_stats: {
        detected: number
        not_detected: number
        errors: number
    }
    results: BatchFileResult[]
}

export interface VideoDetectionFrame {
    timestamp: number
    frame_index: number
    detections: DetectionItem[]
    annotated_frame?: string | null
}

export interface VideoUploadResponse {
    status: string
    task_id: string
    message: string
}

export interface VideoResult {
    status: string
    time_cost?: number
    annotated_video_url?: string
    results: VideoDetectionFrame[]
    error?: string
    video_length?: number
    processed_frames?: number
    fps?: number
}

export * from './user'
export * from './detection'
export * from './history'
