<template>
  <scroll-view scroll-y="true" class="detail-container" :style="{ height: pageHeight + 'px' }">
    <!-- 加载中 -->
    <view class="loading" v-if="loading">
      <text>加载中...</text>
    </view>

    <!-- 错误 -->
    <view class="error" v-else-if="error">
      <text>{{ error }}</text>
    </view>

    <!-- 详情内容 -->
    <template v-else-if="detail">
      <!-- 头部信息 -->
      <view class="header-card">
        <view class="header-top">
          <text class="type-tag">{{ detail.type === 'image' ? '图片检测' : '视频检测' }}</text>
          <text class="detail-time">{{ detail.time }}</text>
        </view>
        <view class="header-bottom">
          <text class="pest-name">{{ detail.pest_name }}</text>
          <text class="conf" v-if="detail.type === 'image'">置信度 {{ detail.confidence }}%</text>
          <text class="conf" v-else-if="videoResult">
            检出 {{ videoResult.pest_count || 0 }} 次 · {{ videoResult.pest_types?.length || 0 }} 种害虫
          </text>
        </view>
      </view>

      <!-- ===== 视频检测结果 ===== -->
      <template v-if="detail.type === 'video' && videoResult">
        <!-- 统计卡片 -->
        <view class="video-stats-card">
          <view class="card-title">检测统计</view>
          <view class="stat-grid">
            <view class="stat-item">
              <text class="stat-number">{{ videoResult.processed_frames || 0 }}</text>
              <text class="stat-label">已处理帧</text>
            </view>
            <view class="stat-item">
              <text class="stat-number">{{ videoResult.pest_count || 0 }}</text>
              <text class="stat-label">害虫出现次数</text>
            </view>
            <view class="stat-item">
              <text class="stat-number">{{ videoResult.pest_types?.length || 0 }}</text>
              <text class="stat-label">害虫种类</text>
            </view>
            <view class="stat-item">
              <text class="stat-number">{{ videoResult.time_cost || 0 }}s</text>
              <text class="stat-label">处理耗时</text>
            </view>
          </view>

          <!-- 视频元信息 -->
          <view class="video-meta">
            <text>视频时长：{{ formatDuration(videoResult.video_length) }}</text>
            <text>检测帧率：{{ videoResult.fps || 0 }} FPS</text>
            <text>文件大小：{{ formatSize(detail.file_size) }}</text>
          </view>

          <!-- 害虫种类分布 -->
          <view class="pest-types" v-if="videoResult.pest_types?.length">
            <text class="type-item" v-for="(item, idx) in videoResult.pest_types" :key="idx">
              {{ item.name }}：{{ item.count }}次
            </text>
          </view>

          <!-- 逐帧详情 -->
          <view class="frames-section" v-if="framesWithPests.length > 0">
            <text class="section-title">逐帧检测详情（共 {{ framesWithPests.length }} 帧有检出）</text>
            <view class="frame-item" v-for="(frame, idx) in framesWithPests" :key="idx">
              <view class="frame-header">
                <text class="frame-index">第 {{ frame.frame_index }} 帧</text>
                <text class="frame-time">{{ formatMs(frame.timestamp_ms) }}</text>
              </view>
              <image
                v-if="frame.annotated_frame"
                class="frame-image"
                :src="frame.annotated_frame"
                mode="widthFix"
                lazy-load
              ></image>
              <view class="frame-detections" v-if="frame.detections?.length">
                <text class="frame-det-item" v-for="(d, di) in frame.detections" :key="di">
                  {{ d.name }} — {{ d.confidence }}%
                </text>
              </view>
            </view>
          </view>
          <view class="no-detections" v-else>
            <text>该视频各帧均未检出害虫</text>
          </view>
        </view>
      </template>

      <!-- ===== 图片检测结果（保持原布局） ===== -->
      <template v-if="detail.type === 'image'">
        <view class="image-card" v-if="detail.result_image_path">
          <image class="preview-image" :src="detail.result_image_path" mode="aspectFit"></image>
        </view>

        <view class="info-card">
          <text class="card-title">基本信息</text>
          <view class="info-row">
            <text class="info-label">检测类型</text>
            <text class="info-value">图片</text>
          </view>
          <view class="info-row">
            <text class="info-label">文件大小</text>
            <text class="info-value">{{ formatSize(detail.file_size) }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">害虫名称</text>
            <text class="info-value">{{ detail.pest_name }}</text>
          </view>
          <view class="info-row">
            <text class="info-label">置信度</text>
            <text class="info-value">{{ detail.confidence }}%</text>
          </view>
        </view>
      </template>

      <!-- 收藏按钮 -->
      <view class="fav-btn" :class="{ active: detail.is_favorite }" @tap="toggleFavorite">
        <text>{{ detail.is_favorite ? '❤️ 已收藏' : '🤍 加入收藏' }}</text>
      </view>
    </template>
  </scroll-view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { get, post } from '../../api-config'

const pageHeight = ref(600)
const loading = ref(true)
const error = ref('')
const detail = ref(null)
const videoResult = ref(null)
let recordId = 0

onLoad((options) => {
  const info = uni.getSystemInfoSync()
  pageHeight.value = info.windowHeight

  recordId = parseInt(options.id || '0')
  if (!recordId) {
    error.value = '参数错误'
    loading.value = false
    return
  }
  fetchDetail()
})

const fetchDetail = async () => {
  try {
    const data = await get(`/history/${recordId}`)
    detail.value = data

    // 解析视频检测的完整结果
    if (data.type === 'video' && data.result_json) {
      try {
        const parsed = typeof data.result_json === 'string'
          ? JSON.parse(data.result_json)
          : data.result_json
        videoResult.value = parsed
      } catch (e) {
        console.error('解析视频结果失败:', e)
        videoResult.value = null
      }
    }
  } catch (e) {
    error.value = e.message || '加载失败'
  }
  loading.value = false
}

// 过滤出有检出害虫的帧
const framesWithPests = computed(() => {
  if (!videoResult.value?.frames) return []
  return videoResult.value.frames.filter(f => f.detections && f.detections.length > 0)
})

const toggleFavorite = async () => {
  try {
    const data = await post(`/history/${recordId}/favorite`)
    detail.value.is_favorite = data.is_favorite
    uni.showToast({
      title: data.is_favorite ? '已收藏' : '已取消收藏',
      icon: 'success'
    })
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return size.toFixed(1) + ' ' + units[i]
}

const formatDuration = (seconds) => {
  if (!seconds) return '0秒'
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return min > 0 ? `${min}分${sec}秒` : `${sec}秒`
}

const formatMs = (ms) => {
  if (!ms) return '0:00'
  const totalSec = Math.floor(ms / 1000)
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  return `${min}:${String(sec).padStart(2, '0')}`
}
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
  box-sizing: border-box;
}

.loading, .error {
  text-align: center;
  padding: 100rpx 0;
  font-size: 28rpx;
  color: #999;
}

/* ── 头部卡片（图片用蓝，视频用橙） ── */
.header-card {
  background: linear-gradient(135deg, #007aff, #0051d5);
  border-radius: 24rpx;
  padding: 30rpx;
  box-shadow: 0 8rpx 30rpx rgba(0,122,255,0.3);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-tag {
  font-size: 28rpx;
  color: rgba(255,255,255,0.9);
}

.detail-time {
  font-size: 24rpx;
  color: rgba(255,255,255,0.7);
}

.header-bottom {
  margin-top: 16rpx;
}

.pest-name {
  font-size: 38rpx;
  font-weight: bold;
  color: #fff;
}

.conf {
  font-size: 28rpx;
  color: rgba(255,255,255,0.8);
  margin-top: 8rpx;
  display: block;
}

/* ── 图片预览 ── */
.image-card {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
}

.preview-image {
  width: 100%;
  height: 400rpx;
  border-radius: 16rpx;
  background: #f0f0f0;
}

/* ── 基本信息 ── */
.info-card {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
}

.card-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  display: block;
  margin-bottom: 20rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 28rpx;
  color: #999;
}

.info-value {
  font-size: 28rpx;
  color: #333;
}

/* ── 视频统计卡片 ── */
.video-stats-card {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
}

.stat-grid {
  display: flex;
  justify-content: space-around;
  padding: 10rpx 0 20rpx;
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

.video-meta {
  display: flex;
  flex-wrap: wrap;
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

/* ── 逐帧检测 ── */
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

.no-detections {
  text-align: center;
  padding: 40rpx 0;
  font-size: 28rpx;
  color: #bbb;
}

/* ── 收藏按钮 ── */
.fav-btn {
  margin: 50rpx 30rpx;
  background: #fff;
  border-radius: 50rpx;
  padding: 28rpx;
  text-align: center;
  font-size: 32rpx;
  color: #999;
  font-weight: 500;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
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
</style>
