import api from '../utils/axiosConfig'
import { StatisticsDataType } from '../types/statistics'

/**
 * 从后端获取统计数据（数据库层聚合，大幅减少数据传输）
 */
export const getStatisticsData = async (
    startTime?: number,
    endTime?: number
): Promise<StatisticsDataType | null> => {
    try {
        const params: Record<string, number> = {}
        if (startTime) params.startTime = startTime
        if (endTime) params.endTime = endTime

        const { data } = await api.get<StatisticsDataType>('/statistics', { params })
        return data
    } catch (error) {
        console.error('获取统计数据失败:', error)
        return null
    }
}
