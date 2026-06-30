import { useState, useCallback, useEffect } from 'react'
import dayjs from 'dayjs'
import { HistoryRecord } from '../../../types/history'
import { StatisticsDataType } from '../../../types/statistics'
import { getStatisticsData } from '../../../services/statisticsService'

export const useStatisticsData = (
    records: HistoryRecord[],
    dateRange: [dayjs.Dayjs, dayjs.Dayjs]
) => {
    const [loading, setLoading] = useState<boolean>(true)
    const [statisticsData, setStatisticsData] =
        useState<StatisticsDataType | null>(null)

    const processStatisticsData = useCallback(
        (records: HistoryRecord[]): StatisticsDataType => {
            const pestTypesMap = new Map<string, number>()
            const confidenceData: number[] = []
            const trendData: Array<{ date: string; count: number }> = []

            records.forEach((record) => {
                if (record.type === 'image') {
                    const result = record.result
                    if (result.predictions && result.predictions.length) {
                        result.predictions.forEach(
                            (pred: { class?: string; pest?: string; confidence: number }) => {
                                const type =
                                    pred.class || pred.pest || '未知'
                                pestTypesMap.set(
                                    type,
                                    (pestTypesMap.get(type) || 0) + 1
                                )
                                confidenceData.push(pred.confidence)
                            }
                        )

                        const day = dayjs(record.timestamp).format('YYYY-MM-DD')
                        const existingDay = trendData.find(
                            (item) => item.date === day
                        )
                        if (existingDay) {
                            existingDay.count += result.predictions.length
                        } else {
                            trendData.push({
                                date: day,
                                count: result.predictions.length,
                            })
                        }
                    }
                }
            })

            const pestDistribution = Array.from(pestTypesMap.entries()).map(
                ([name, value]) => ({ name, value })
            )

            trendData.sort(
                (a, b) => dayjs(a.date).valueOf() - dayjs(b.date).valueOf()
            )

            return {
                pestDistribution,
                confidenceData,
                trendData,
                totalDetections: confidenceData.length,
                uniquePestTypes: pestTypesMap.size,
                averageConfidence: confidenceData.length
                    ? confidenceData.reduce((sum, val) => sum + val, 0) /
                      confidenceData.length
                    : 0,
            }
        },
        []
    )

    const fetchData = useCallback(async () => {
        setLoading(true)
        try {
            const startTime = dateRange[0].valueOf()
            const endTime = dateRange[1].valueOf()

            // 优先调用后端聚合接口（数据库层面计算，速度快10-100倍）
            const serverData = await getStatisticsData(startTime, endTime)
            if (serverData) {
                setStatisticsData(serverData)
                setLoading(false)
                return
            }
        } catch {
            // 后端接口不可用时静默降级
        }

        // 降级：前端客户端聚合
        try {
            const startTime = dateRange[0].valueOf()
            const endTime = dateRange[1].valueOf()

            const filteredRecords = records.filter((record) => {
                return (
                    record.timestamp >= startTime && record.timestamp <= endTime
                )
            })

            const processedData = processStatisticsData(filteredRecords)
            setStatisticsData(processedData)
        } catch (error) {
            console.error('统计数据计算失败:', error)
        } finally {
            setLoading(false)
        }
    }, [dateRange, records, processStatisticsData])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const calculateAvgConfidence = useCallback(
        (pestName: string): number => {
            if (!statisticsData) return 0

            let total = 0
            let count = 0

            records.forEach((record) => {
                if (record.type === 'image' && record.result.predictions) {
                    record.result.predictions.forEach(
                        (pred: { class?: string; pest?: string; confidence: number }) => {
                            const type = pred.class || pred.pest || '未知'
                            if (type === pestName) {
                                total += pred.confidence
                                count++
                            }
                        }
                    )
                }
            })

            return count > 0 ? total / count : 0
        },
        [records, statisticsData]
    )

    return {
        loading,
        statisticsData,
        calculateAvgConfidence,
        fetchData,
        processStatisticsData,
    }
}
