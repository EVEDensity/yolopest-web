<template>
  <view class="fav-container">
    <view class="header">
      <text class="title">我的收藏</text>
    </view>

    <view class="list">
      <view class="list-item" v-for="(item, idx) in favList" :key="idx" @tap="goToDetail(item)">
        <image class="item-image" :src="item.thumbnail || '/static/logo.png'" mode="aspectFill"></image>
        <view class="item-info">
          <text class="item-name">{{ item.type === 'image' ? '📷' : '🎬' }} {{ item.pest_name }}</text>
          <text class="item-time">{{ item.time }}</text>
          <text class="item-conf">置信度：{{ item.confidence > 0 ? item.confidence + '%' : '—' }}</text>
        </view>
        <view class="fav-icon active" @tap.stop="handleRemove(item, idx)">
          <text>❤️</text>
        </view>
      </view>
    </view>

    <view class="load-more" v-if="hasMore" @tap="loadMore">
      <text>加载更多</text>
    </view>
    <view class="load-more" v-else-if="favList.length > 0">
      <text>— 没有更多了 —</text>
    </view>

    <view class="empty" v-if="favList.length === 0 && !loading">
      <image class="empty-icon" src="/static/logo.png" mode="aspectFit"></image>
      <text class="empty-text">暂无收藏</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { get, post } from '../../api-config'

const favList = ref([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = ref(10)

onShow(() => {
  fetchFavs(true)
})

const fetchFavs = async (reset = true) => {
  if (reset) {
    page.value = 1
    favList.value = []
  }

  loading.value = true

  try {
    const data = await get('/history', {
      page: page.value,
      page_size: pageSize.value,
      keyword: '',
      time_filter: 'all',
      favorites: 'true'
    })

    if (reset) {
      favList.value = data.items || []
    } else {
      favList.value = [...favList.value, ...(data.items || [])]
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
    fetchFavs(false)
  }
}

const goToDetail = (item) => {
  uni.navigateTo({ url: `/pages/detail/index?id=${item.id}` })
}

const handleRemove = async (item, idx) => {
  try {
    await post(`/history/${item.id}/favorite`)
    favList.value.splice(idx, 1)
    uni.showToast({ title: '已取消收藏', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: e.message || '操作失败', icon: 'none' })
  }
}
</script>

<style scoped>
.fav-container {
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

.list-item {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04);
}

.list-item:active {
  opacity: 0.7;
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

.fav-icon {
  padding: 10rpx;
  font-size: 40rpx;
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