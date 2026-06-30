import api from './axiosConfig'
import { AxiosRequestConfig, AxiosResponse } from 'axios'

interface ApiRequestOptions extends AxiosRequestConfig {
    url: string
    method: 'GET' | 'POST' | 'PUT' | 'DELETE'
    data?: Record<string, unknown>
    params?: Record<string, unknown>
}

/**
 * 通用API请求函数
 * 复用 axiosConfig 中的 api 实例，统一走请求拦截器自动附加 token
 */
export const apiRequest = async <T = Record<string, unknown>>(
    options: ApiRequestOptions
): Promise<T> => {
    try {
        // AI 分析接口可能需要等待大模型生成，单独给 60 秒超时
            const isAnalysis = options.url?.includes('/ai-analysis')
            const response: AxiosResponse<T> = await api.request({
                ...options,
                timeout: isAnalysis ? 60000 : 10000,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            })

        // 直接返回后端原始响应结构
        return response.data
    } catch (error: unknown) {
        if ((error as { response?: { data?: unknown } }).response) {
            const errData = (error as { response: { data: { detail?: string; message?: string } } }).response.data
            const detail = errData?.detail || errData?.message || '请求失败'
            console.error('API请求错误:', errData)
            throw new Error(detail)
        } else if ((error as { request?: unknown }).request) {
            console.error('无法连接服务器:', (error as { request: unknown }).request)
            throw new Error('无法连接服务器，请检查网络连接')
        } else {
            const errorMessage = error instanceof Error ? error.message : '请求错误'
            console.error('请求错误:', errorMessage)
            throw new Error(errorMessage)
        }
    }
}
