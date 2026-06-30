<template>
  <view class="profile-container">
    <view class="user-card">
      <image class="avatar" :src="userInfo.avatar || '/static/logo.png'" mode="aspectFill"></image>
      <view class="user-info">
        <text class="user-name">{{ userInfo.username || '未命名用户' }}</text>
        <text class="user-email">{{ userInfo.email || '未绑定邮箱' }}</text>
      </view>
      <view class="edit-btn" @tap="goToEdit">
        <text>编辑</text>
      </view>
    </view>

    <view class="stat-card">
      <view class="stat-item" @tap="goToHistory">
        <text class="stat-number">{{ stats.total }}</text>
        <text class="stat-label">总检测次数</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-number">{{ stats.pests }}</text>
        <text class="stat-label">发现害虫种类</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-number">{{ stats.images }}</text>
        <text class="stat-label">图片检测</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-number">{{ stats.videos }}</text>
        <text class="stat-label">视频检测</text>
      </view>
    </view>

    <view class="menu-group">
      <view class="menu-item" @tap="goToHistory">
        <text class="menu-icon">📋</text>
        <text class="menu-name">我的历史记录</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="goToFavorites">
        <text class="menu-icon">⭐</text>
        <text class="menu-name">收藏的检测</text>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu-item" @tap="showAbout">
        <text class="menu-icon">ℹ️</text>
        <text class="menu-name">关于我们</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <view class="logout-btn" @tap="handleLogout">
      <text>退出登录</text>
    </view>

    <view class="version">
      <text>版本 1.0.0</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { get, post } from '../../api-config'

const userInfo = ref({
  avatar: '',
  username: '',
  email: ''
})

const stats = ref({
  total: 0,
  pests: 0,
  images: 0,
  videos: 0
})

onShow(() => {
  // 优先从本地读取缓存
  const saved = uni.getStorageSync('userInfo')
  if (saved) userInfo.value = saved
  // 从后端拉取最新数据
  fetchProfile()
  fetchStats()
})

const fetchProfile = async () => {
  try {
    const data = await get('/users/profile')
    userInfo.value = {
      avatar: data.avatar || '',
      username: data.username || '',
      email: data.email || ''
    }
    uni.setStorageSync('userInfo', userInfo.value)
  } catch (e) {
    // 静默失败，使用缓存数据
  }
}

const fetchStats = async () => {
  try {
    const data = await get('/users/stats')
    stats.value = {
      total: data.total || 0,
      pests: data.pests || 0,
      images: data.images || 0,
      videos: data.videos || 0
    }
  } catch (e) {
    // 静默失败
  }
}

const goToEdit = () => {
  uni.navigateTo({ url: '/pages/profile/edit/index' })
}

const goToHistory = () => {
  uni.switchTab({ url: '/pages/history/index' })
}

const goToFavorites = () => {
  uni.navigateTo({ url: '/pages/favorites/index' })
}

const showAbout = () => {
  uni.showModal({
    title: '关于 Yolo-Pest',
    content: '农作物害虫智能检测系统 v1.0.0\n基于 YOLO + uni-app 开发',
    showCancel: false
  })
}

const handleLogout = () => {
  uni.showModal({
    title: '提示',
    content: '确定要退出登录吗？',
    success: async (res) => {
      if (res.confirm) {
        // 尝试调用后端登出接口（忽略网络错误）
        try { await post('/auth/logout') } catch (e) { /* 忽略 */ }

        uni.removeStorageSync('token')
        uni.removeStorageSync('isLogin')
        uni.removeStorageSync('userInfo')

        uni.showToast({ title: '已退出', icon: 'success' })

        setTimeout(() => {
          uni.reLaunch({ url: '/pages/login/index' })
        }, 500)
      }
    }
  })
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
  box-sizing: border-box;
}

.user-card {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #007aff, #0051d5);
  border-radius: 30rpx;
  padding: 40rpx 30rpx;
  box-shadow: 0 10rpx 40rpx rgba(0, 122, 255, 0.3);
}

.avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
  background: #fff;
}

.user-info {
  flex: 1;
  margin-left: 24rpx;
}

.user-name {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  color: #fff;
}

.user-email {
  display: block;
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 6rpx;
}

.edit-btn {
  background: rgba(255, 255, 255, 0.25);
  padding: 12rpx 28rpx;
  border-radius: 30rpx;
  color: #fff;
  font-size: 26rpx;
}

.edit-btn:active {
  opacity: 0.7;
}

.stat-card {
  display: flex;
  background: #fff;
  border-radius: 30rpx;
  padding: 30rpx 0;
  margin-top: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #2c3e50;
}

.stat-label {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 6rpx;
}

.stat-divider {
  width: 2rpx;
  height: 60rpx;
  background: #e8ecf1;
  align-self: center;
}

.menu-group {
  background: #fff;
  border-radius: 30rpx;
  margin-top: 30rpx;
  padding: 0 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-icon {
  font-size: 36rpx;
  margin-right: 20rpx;
}

.menu-name {
  flex: 1;
  font-size: 30rpx;
  color: #333;
}

.menu-arrow {
  font-size: 36rpx;
  color: #ccc;
}

.menu-item:active {
  opacity: 0.6;
}

.logout-btn {
  margin-top: 50rpx;
  background: #fff;
  border-radius: 30rpx;
  padding: 30rpx;
  text-align: center;
  font-size: 32rpx;
  color: #ff4444;
  font-weight: 500;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.04);
}

.logout-btn:active {
  opacity: 0.6;
}

.version {
  text-align: center;
  margin-top: 40rpx;
  font-size: 24rpx;
  color: #ccc;
}
</style>
