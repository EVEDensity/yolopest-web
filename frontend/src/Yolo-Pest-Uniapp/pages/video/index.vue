<template>
  <scroll-view scroll-y="true" class="video-container" :style="{ height: pageHeight + 'px' }">
    <view class="header">
      <text class="title">视频检测</text>
      <text class="subtitle">上传害虫视频进行逐帧分析</text>
    </view>

    <view class="upload-card" @tap="chooseVideo">
      <image class="upload-icon" src="/static/video.png" mode="aspectFit"></image>
      <text class="upload-text">选择视频</text>
      <text class="upload-desc">支持 MP4 / WebM / MOV 格式</text>
    </view>

    <view class="video-preview" v-if="videoUrl">
      <video
        class="video-player"
        :src="videoUrl"
        controls
        :show-play-btn="true"
      ></video>
      <view class="video-info">
        <text>文件大小：{{ fileSize }}</text>
        <text @tap="startDetect" class="detect-btn" :class="{ disabled: processing }">
          {{ processing ? '处理中...' : '开始检测' }}
        </text>
      </view>
    </view>

    <!-- 进度条 -->
    <view class="progress-area" v-if="processing">
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: progress + '%' }"></view>
      </view>
      <text class="progress-text">{{ progress }}% — {{ statusText }}</text>
    </view>

    <!-- 检测结果 -->
    <view class="result-area" v-if="videoResult">
      <view class="result-header">
        <text class="result-title">检测统计</text>
      </view>
      <view class="stat-grid">
        <view class="stat-item">
          <text class="stat-number">{{ videoResult.processed_frames }}</text>
          <text class="stat-label">已处理帧</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ videoResult.pest_count }}</text>
          <text class="stat-label">害虫出现次数</text>
        </view>
        <view class="stat-item">
          <text class="stat-number">{{ videoResult.pest_types.length }}</text>
          <text class="stat-label">害虫种类</text>
        </view>
      </view>

      <!-- 耗时信息 -->
      <view class="meta-row" v-if="videoResult.time_cost">
        <text>处理耗时：{{ videoResult.time_cost }}s</text>
        <text>视频时长：{{ videoResult.video_length }}s</text>
      </view>

      <!-- 害虫种类分布 -->
      <view class="pest-types" v-if="videoResult.pest_types.length > 0">
        <text class="type-item" v-for="(item, idx) in videoResult.pest_types" :key="idx">
          {{ item.name }}：{{ item.count }}次
        </text>
      </view>

      <!-- 逐帧检测结果 -->
      <view class="frames-section" v-if="videoResult.frames && videoResult.frames.length > 0">
        <text class="section-title">逐帧检测详情（有检出害虫的帧）</text>
        <view
          class="frame-item"
          v-for="(frame, idx) in framesWithPests"
          :key="idx"
        >
          <view class="frame-header">
            <text class="frame-index">第 {{ frame.frame_index }} 帧</text>
            <text class="frame-time">{{ formatMs(frame.timestamp_ms) }}</text>
          </view>
          <image
            v-if="frame.annotated_frame"
            class="frame-image"
            :src="frame.annotated_frame"
            mode="aspectFit"
          ></image>
          <view class="frame-detections">
            <text class="frame-det-item" v-for="(d, di) in frame.detections" :key="di">
              {{ d.name }} — {{ d.confidence }}%
            </text>
          </view>
        </view>
      </view>

      <view class="fav-btn" :class="{ active: isFav }" @tap="toggleFavorite">
        <text>{{ isFav ? '❤️ 已收藏' : '🤍 加入收藏' }}</text>
      </view>
    </view>

    <!-- 空状态 -->
    <view class="empty-area" v-if="!videoResult && !processing">
      <image class="empty-icon" src="/static/empty.png" mode="aspectFit"></image>
      <text class="empty-text">选择视频开始害虫检测</text>
    </view>
  </scroll-view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow, onUnload, onLoad } from '@dcloudio/uni-app'
import { upload, get, post } from '../../api-config'

const pageHeight = ref(600) // 默认高度

onLoad(() => {
  const info = uni.getSystemInfoSync()
  pageHeight.value = info.windowHeight
})

const videoUrl = ref('')
const fileSize = ref('')
const videoResult = ref(null)
const isFav = ref(false)
const recordId = ref(0)

// 异步轮询状态
const processing = ref(false)
const progress = ref(0)
const statusText = ref('')
let pollTimer = null
let taskId = ''

onShow(() => {
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.reLaunch({ url: '/pages/login/index' })
  }
})

onUnload(() => {
  // 页面卸载时清除轮询
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})

const chooseVideo = () => {
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.reLaunch({ url: '/pages/login/index' }), 500)
    return
  }

  uni.chooseVideo({
    sourceType: ['album', 'camera'],
    maxDuration: 60,
    success: (res) => {
      videoUrl.value = res.tempFilePath
      const size = (res.size / 1024 / 1024).toFixed(2)
      fileSize.value = size + ' MB'
      videoResult.value = null
    }
  })
}

const startDetect = async () => {
  if (!videoUrl.value || processing.value) return

  processing.value = true
  progress.value = 0
  statusText.value = '上传中...'
  videoResult.value = null

  try {
    // Step 1: 上传视频获取 task_id
    uni.showLoading({ title: '上传视频中...' })
    const uploadRes = await upload('/detect/video', videoUrl.value, 'file')
    uni.hideLoading()

    taskId = uploadRes.task_id
    if (!taskId) throw new Error('未获取到任务ID')

    statusText.value = '排队中...'
    progress.value = 5

    // Step 2: 开始轮询状态
    pollTimer = setInterval(async () => {
      try {
        const statusRes = await get(`/detect/video/status/${taskId}`)
        progress.value = Math.max(progress.value, statusRes.progress || 0)

        if (statusRes.status === 'completed') {
          // Step 3: 获取完整结果
          clearInterval(pollTimer)
          pollTimer = null
          statusText.value = '获取结果...'
          await fetchResult()
        } else if (statusRes.status === 'failed') {
          clearInterval(pollTimer)
          pollTimer = null
          processing.value = false
          uni.showToast({ title: statusRes.error || '检测失败', icon: 'none' })
        } else if (statusRes.status === 'processing') {
          statusText.value = `处理中 (${statusRes.progress}%)`
        }
      } catch (e) {
        if (e.message && e.message.includes('任务不存在')) {
          clearInterval(pollTimer)
          pollTimer = null
          processing.value = false
          uni.showToast({ title: '任务已失效', icon: 'none' })
        }
      }
    }, 2000)

  } catch (error) {
    processing.value = false
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
    uni.hideLoading()
    uni.showToast({ title: error.message || '上传失败，请重试', icon: 'none' })
  }
}

const fetchResult = async () => {
  try {
    const data = await get(`/detect/video/result/${taskId}`)
    videoResult.value = data
    recordId.value = data.record_id || 0
    isFav.value = false
    processing.value = false
    uni.showToast({ title: '检测完成', icon: 'success' })
  } catch (e) {
    processing.value = false
    uni.showToast({ title: e.message || '获取结果失败', icon: 'none' })
  }
}

// 筛选出有检出害虫的帧
const framesWithPests = computed(() => {
  if (!videoResult.value?.frames) return []
  return videoResult.value.frames.filter(f => f.detections && f.detections.length > 0)
})

const formatMs = (ms) => {
  const totalSec = Math.floor(ms / 1000)
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${String(sec).padStart(2, '0')}`
}

const toggleFavorite = async () => {
  if (!recordId.value) {
    uni.showToast({ title: '检测记录尚未保存', icon: 'none' })
    return
  }
  try {
    const data = await post(`/history/${recordId.value}/favorite`)
    isFav.value = data.is_favorite
    uni.showToast({
      title: data.is_favorite ? '已收藏' : '已取消收藏',
      icon: 'success'
    })
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}
</script>

<style scoped>
.video-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
  box-sizing: border-box;
}

.header {
  text-align: center;
  padding: 30rpx 0;
}

.title {
  font-size: 44rpx;
  font-weight: bold;
  color: #2c3e50;
  display: block;
}

.subtitle {
  font-size: 28rpx;
  color: #999;
  margin-top: 10rpx;
  display: block;
}

.upload-card {
  background: #fff;
  border-radius: 30rpx;
  padding: 50rpx 40rpx;
  text-align: center;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
  border: 2rpx dashed #ff6b35;
  margin-top: 20rpx;
  transition: all 0.3s;
}

.upload-card:active {
  background: #fff5f0;
  transform: scale(0.98);
}

.upload-icon {
  width: 100rpx;
  height: 100rpx;
  margin: 0 auto 20rpx;
}

.upload-text {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  display: block;
}

.upload-desc {
  font-size: 26rpx;
  color: #999;
  display: block;
  margin-top: 10rpx;
}

.video-preview {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 30rpx;
  padding: 20rpx;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
}

.video-player {
  width: 100%;
  height: 400rpx;
  border-radius: 16rpx;
  background: #000;
}

.video-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 10rpx 10rpx;
  font-size: 26rpx;
  color: #666;
}

.detect-btn {
  background: #ff6b35;
  color: #fff;
  padding: 12rpx 36rpx;
  border-radius: 30rpx;
  font-size: 28rpx;
}

.detect-btn.disabled {
  background: #ccc;
  color: #999;
}

.detect-btn:active {
  opacity: 0.8;
}

/* 进度条 */
.progress-area {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
  text-align: center;
}

.progress-bar {
  height: 16rpx;
  background: #eee;
  border-radius: 8rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b35, #ff8c60);
  border-radius: 8rpx;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 26rpx;
  color: #999;
}

.result-area {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 30rpx;
  padding: 30rpx;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
}

.result-header {
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 32rpx;
  font-weight: bold;
}

.stat-grid {
  display: flex;
  justify-content: space-around;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 44rpx;
  font-weight: bold;
  color: #ff6b35;
}

.stat-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  font-size: 26rpx;
  color: #999;
  border-bottom: 2rpx solid #f5f5f5;
}

.pest-types {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  padding-top: 20rpx;
}

.type-item {
  background: #fff5f0;
  color: #ff6b35;
  padding: 10rpx 24rpx;
  border-radius: 20rpx;
  font-size: 26rpx;
}

/* 逐帧检测 */
.frames-section {
  margin-top: 30rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.frame-item {
  background: #fafafa;
  border-radius: 16rpx;
  padding: 16rpx;
  margin-bottom: 16rpx;
}

.frame-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.frame-index {
  font-size: 26rpx;
  color: #333;
  font-weight: 600;
}

.frame-time {
  font-size: 24rpx;
  color: #999;
}

.frame-image {
  width: 100%;
  height: 300rpx;
  border-radius: 10rpx;
  background: #eee;
  margin-bottom: 10rpx;
}

.frame-detections {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.frame-det-item {
  background: #e8f4fd;
  color: #007aff;
  padding: 6rpx 16rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
}

.fav-btn {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 50rpx;
  padding: 22rpx;
  text-align: center;
  font-size: 30rpx;
  color: #999;
  font-weight: 500;
  border: 2rpx solid #eee;
}

.fav-btn.active {
  color: #ff4444;
  border-color: #ff4444;
  background: #fff5f5;
}

.fav-btn:active {
  opacity: 0.7;
}

.empty-area {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 30rpx;
  padding: 80rpx 40rpx;
  text-align: center;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
}

.empty-icon {
  width: 160rpx;
  height: 160rpx;
  margin: 0 auto 30rpx;
}

.empty-text {
  font-size: 28rpx;
  color: #bbb;
}
</style>
