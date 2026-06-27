import type { DetectionItem, VideoDetectionFrame } from './index'

export interface HistoryRecord {
    id: string
    user_id?: number
    timestamp: number
    type: string
    filename: string
    thumbnail?: string
    result: {
        status: string
        predictions?: Array<{
            class: string
            confidence: number
            box: [number, number, number, number]
        }>
        detections?: DetectionItem[]
        results?: VideoDetectionFrame[]
        time_cost?: number
        video_length?: number
        fps?: number
        processed_frames?: number
    }
}
