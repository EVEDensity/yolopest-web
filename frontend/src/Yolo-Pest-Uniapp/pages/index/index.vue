<template>
  <view class="index-container">
    <view class="header">
      <text class="title">害虫智能检测</text>
      <text class="subtitle">拍照识别农作物害虫</text>
    </view>

    <view class="action-area">
      <view class="upload-card" @tap="chooseImage">
        <image class="upload-icon" src="/static/camera.png" mode="aspectFit"></image>
        <text class="upload-text">拍照 / 相册</text>
        <text class="upload-desc">支持 JPG / PNG 格式</text>
      </view>
    </view>

    <view class="result-area" v-if="result">
      <view class="result-header">
        <text class="result-title">检测结果</text>
        <text class="result-time">{{ result.time }}</text>
      </view>
      
      <view class="result-image-wrapper">
        <image class="result-image" :src="result.result_image_url || result.imageUrl" mode="aspectFit"></image>
      </view>

      <view class="result-list">
        <view class="result-item" v-for="(item, idx) in result.detections" :key="idx">
          <text class="result-name">{{ item.name }}</text>
          <text class="result-conf">{{ item.confidence?.toFixed(1) }}%</text>
        </view>
      </view>

      <view class="fav-btn" :class="{ active: isFav }" @tap="toggleFavorite">
        <text>{{ isFav ? '❤️ 已收藏' : '🤍 加入收藏' }}</text>
      </view>
    </view>

    <view class="empty-area" v-else>
      <image class="empty-icon" src="/static/empty.png" mode="aspectFit"></image>
      <text class="empty-text">点击上方按钮上传图片进行检测</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { upload, post } from '../../api-config'

const result = ref(null)
const isFav = ref(false)
const recordId = ref(0)

onShow(() => {
  // 检查是否有 token
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.reLaunch({ url: '/pages/login/index' })
  }
})

const chooseImage = () => {
  // 检查登录状态
  const token = uni.getStorageSync('token')
  if (!token) {
    uni.showToast({ title: '请先登录', icon: 'none' })
    setTimeout(() => uni.reLaunch({ url: '/pages/login/index' }), 500)
    return
  }
  
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['camera', 'album'],
    success: (res) => {
      const tempFilePath = res.tempFilePaths[0]
      uploadImage(tempFilePath)
    },
    fail: (err) => {
      console.log('选择图片失败', err)
    }
  })
}

const uploadImage = async (filePath) => {
  uni.showLoading({ title: '检测中...' })
  
  try {
    const data = await upload('/detect/image', filePath, 'file')
    
    result.value = {
      ...data,
      imageUrl: filePath,
      imageUrlDisplay: data.result_image_url || filePath
    }
    recordId.value = data.record_id || 0
    isFav.value = false
    
    uni.hideLoading()
    uni.showToast({ title: '检测完成', icon: 'success' })
    
  } catch (error) {
    uni.hideLoading()
    uni.showToast({ title: error.message || '检测失败，请重试', icon: 'none' })
  }
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
.index-container {
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

.action-area {
  margin: 20rpx 0;
}

.upload-card {
  background: #fff;
  border-radius: 30rpx;
  padding: 60rpx 40rpx;
  text-align: center;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
  border: 2rpx dashed #007aff;
  transition: all 0.3s;
}

.upload-card:active {
  background: #f0f7ff;
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

.result-area {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 30rpx;
  padding: 30rpx;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 32rpx;
  font-weight: bold;
}

.result-time {
  font-size: 24rpx;
  color: #999;
}

.result-image-wrapper {
  position: relative;
  width: 100%;
  height: 400rpx;
  background: #f0f0f0;
  border-radius: 16rpx;
  overflow: hidden;
}

.result-image {
  width: 100%;
  height: 100%;
}

.result-list {
  margin-top: 20rpx;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.result-item:last-child {
  border-bottom: none;
}

.result-name {
  font-size: 30rpx;
  color: #333;
}

.result-conf {
  font-size: 28rpx;
  color: #007aff;
  font-weight: 600;
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