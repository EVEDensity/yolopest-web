<template>
  <view class="history-container">
    <view class="header">
      <text class="title">历史记录</text>
    </view>

    <view class="filter-bar">
      <input 
        class="search-input" 
        v-model="keyword" 
        placeholder="搜索害虫名称"
        @input="handleSearch"
      />
      <picker 
        mode="selector" 
        :range="timeOptions" 
        @change="handleTimeChange"
      >
        <view class="filter-btn">{{ currentTimeLabel }} ▼</view>
      </picker>
    </view>

    <view class="list">
      <view
        class="list-item"
        v-for="(item, idx) in historyList"
        :key="idx"
        @tap="goToDetail(item)"
      >
        <!-- 类型角标 -->
        <view class="item-badge" :class="item.type === 'video' ? 'badge-video' : 'badge-image'">
          <text>{{ item.type === 'video' ? '视频' : '图片' }}</text>
        </view>

        <image
          class="item-image"
          :src="item.thumbnail || (item.type === 'video' ? '/static/video.png' : '/static/logo.png')"
          mode="aspectFill"
        ></image>

        <view class="item-info">
          <text class="item-name">{{ item.pest_name }}</text>
          <text class="item-time">{{ item.time }}</text>

          <!-- 类型相关的辅助信息 -->
          <template v-if="item.type === 'video'">
            <view class="item-video-stats">
              <text v-if="item.pest_count === null && item.pest_name === '检测中...'" class="video-processing">处理中...</text>
              <text v-else-if="item.pest_count === null">—</text>
              <template v-else>
                <text v-if="item.pest_count > 0" class="video-pest-count">🦗 {{ item.pest_count }}次</text>
                <text v-else class="video-no-pest">未检出</text>
                <text v-if="item.video_duration" class="video-dur">{{ formatDuration(item.video_duration) }}</text>
              </template>
            </view>
          </template>
          <template v-else>
            <text class="item-conf">置信度 {{ item.confidence > 0 ? item.confidence + '%' : '—' }}</text>
          </template>
        </view>

        <text class="item-arrow" @tap.stop="goToDetail(item)">›</text>
        <text class="item-delete" @tap.stop="confirmDelete(item, idx)">🗑</text>
      </view>
    </view>

    <view class="load-more" v-if="hasMore" @tap="loadMore">
      <text>加载更多</text>
    </view>
    <view class="load-more" v-else-if="historyList.length > 0">
      <text>— 没有更多了 —</text>
    </view>

    <view class="empty" v-if="historyList.length === 0 && !loading">
      <image class="empty-icon" src="/static/logo.png" mode="aspectFit"></image>
      <text class="empty-text">暂无检测记录</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { get, del } from '../../api-config'

const historyList = ref([])
const keyword = ref('')
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = ref(10)

const timeOptions = ['全部', '今天', '本周', '本月']
const currentTimeLabel = ref('全部')
const currentTimeFilter = ref('all')

onShow(() => {
  fetchHistory(true)
})

const fetchHistory = async (reset = true) => {
  if (reset) {
    page.value = 1
    historyList.value = []
  }
  
  loading.value = true
  
  try {
    const data = await get('/history', {
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value,
      time_filter: currentTimeFilter.value,
    })
    
    if (reset) {
      historyList.value = data.items || []
    } else {
      historyList.value = [...historyList.value, ...(data.items || [])]
    }
    
    hasMore.value = data.has_more || false
    page.value++
    
  } catch (error) {
    uni.showToast({ title: error.message || '加载失败', icon: 'none' })
  }
  
  loading.value = false
}

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    fetchHistory(false)
  }
}

let searchTimer = null
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    fetchHistory(true)
  }, 300)
}

const handleTimeChange = (e) => {
  const index = e.detail.value
  currentTimeLabel.value = timeOptions[index]
  const map = { '全部': 'all', '今天': 'today', '本周': 'week', '本月': 'month' }
  currentTimeFilter.value = map[currentTimeLabel.value]
  fetchHistory(true)
}

const goToDetail = (item) => {
  uni.navigateTo({ url: `/pages/detail/index?id=${item.id}` })
}

const formatDuration = (seconds) => {
  if (!seconds) return ''
  const min = Math.floor(seconds / 60)
  const sec = Math.floor(seconds % 60)
  return min > 0 ? `${min}分${sec}秒` : `${sec}秒`
}

const confirmDelete = (item, idx) => {
  uni.showModal({
    title: '删除记录',
    content: `确定删除 "${item.pest_name}" 的检测记录吗？`,
    success: async (res) => {
      if (res.confirm) {
        try {
          await del(`/history/${item.id}`)
          historyList.value.splice(idx, 1)
          uni.showToast({ title: '已删除', icon: 'success' })
        } catch (e) {
          uni.showToast({ title: e.message || '删除失败', icon: 'none' })
        }
      }
    }
  })
}
</script>

<style scoped>
.history-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
  box-sizing: border-box;
}

.header {
  padding: 20rpx 0 30rpx;
}

.title {
  font-size: 44rpx;
  font-weight: bold;
  color: #2c3e50;
}

.filter-bar {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.search-input {
  flex: 1;
  height: 72rpx;
  background: #fff;
  border-radius: 36rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04);
}

.filter-btn {
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 30rpx;
  background: #fff;
  border-radius: 36rpx;
  font-size: 26rpx;
  color: #666;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04);
}

.list-item {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04);
  position: relative;
}

.list-item:active {
  transform: scale(0.98);
}

/* ── 类型角标 ── */
.item-badge {
  position: absolute;
  top: -6rpx;
  right: 70rpx;
  padding: 4rpx 16rpx;
  border-radius: 12rpx;
  font-size: 22rpx;
  font-weight: 600;
}

.badge-image {
  background: #e8f4fd;
  color: #007aff;
}

.badge-video {
  background: #fff5f0;
  color: #ff6b35;
}

.item-image {
  width: 120rpx;
  height: 120rpx;
  border-radius: 16rpx;
  flex-shrink: 0;
  background: #f0f0f0;
}

.item-info {
  flex: 1;
  margin-left: 20rpx;
}

.item-name {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.item-time {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 6rpx;
}

.item-conf {
  display: block;
  font-size: 26rpx;
  color: #007aff;
  margin-top: 4rpx;
}

/* ── 视频统计行 ── */
.item-video-stats {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 4rpx;
}

.video-pest-count {
  font-size: 26rpx;
  color: #ff6b35;
}

.video-no-pest {
  font-size: 26rpx;
  color: #999;
}

.video-dur {
  font-size: 22rpx;
  color: #bbb;
}

.video-processing {
  font-size: 26rpx;
  color: #ff9500;
}

.item-arrow {
  font-size: 40rpx;
  color: #ccc;
}

.item-delete {
  font-size: 32rpx;
  padding: 10rpx 10rpx 10rpx 20rpx;
  color: #ccc;
}

.item-delete:active {
  color: #ff4444;
}

.load-more {
  text-align: center;
  padding: 30rpx;
  font-size: 26rpx;
  color: #999;
}

.empty {
  padding: 120rpx 0;
  text-align: center;
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