<template>
  <view class="register-container">
    <view class="header">
      <text class="back" @tap="goBack">‹</text>
      <text class="title">注册新账号</text>
      <text class="placeholder"></text>
    </view>

    <view class="form">
      <view class="input-group">
        <text class="input-label">邮箱</text>
        <input
          class="input"
          v-model="email"
          placeholder="请输入邮箱"
          type="text"
        />
      </view>

      <view class="input-group">
        <text class="input-label">用户名</text>
        <input
          class="input"
          v-model="username"
          placeholder="请输入用户名（至少3个字符）"
          type="text"
          maxlength="50"
        />
      </view>

      <view class="input-group">
        <text class="input-label">密码</text>
        <input
          class="input"
          v-model="password"
          placeholder="请设置密码（至少8位）"
          :password="true"
        />
      </view>

      <view class="input-group">
        <text class="input-label">确认密码</text>
        <input
          class="input"
          v-model="confirmPassword"
          placeholder="请再次输入密码"
          :password="true"
        />
      </view>

      <button class="register-btn" @tap="handleRegister">注 册</button>

      <view class="login-tip">
        <text>已有账号？</text>
        <text class="login-link" @tap="goToLogin">去登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { post } from '../../api-config'

const email = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')

const handleRegister = async () => {
  if (!email.value || !username.value || !password.value || !confirmPassword.value) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  // 邮箱格式校验
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  if (!emailRegex.test(email.value)) {
    uni.showToast({ title: '请输入正确的邮箱地址', icon: 'none' })
    return
  }
  // 用户名长度校验（与Web端一致：至少3个字符）
  if (username.value.length < 3) {
    uni.showToast({ title: '用户名至少3个字符', icon: 'none' })
    return
  }
  // 密码长度校验（与Web端一致：至少8个字符）
  if (password.value.length < 8) {
    uni.showToast({ title: '密码长度不能少于8位', icon: 'none' })
    return
  }
  if (password.value !== confirmPassword.value) {
    uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
    return
  }

  uni.showLoading({ title: '注册中...' })

  try {
    const data = await post('/auth/register', {
      email: email.value,
      username: username.value,
      password: password.value
    })

    // 注册成功自动登录
    uni.setStorageSync('token', data.access_token)
    uni.setStorageSync('isLogin', true)

    uni.hideLoading()
    uni.showToast({ title: '注册成功', icon: 'success' })

    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 500)
  } catch (error) {
    uni.hideLoading()
    uni.showToast({ title: error.message || '注册失败，请重试', icon: 'none' })
  }
}

const goBack = () => uni.navigateBack()
const goToLogin = () => uni.navigateBack()
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 0 40rpx 40rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60rpx 0 40rpx;
}

.back {
  font-size: 48rpx;
  color: #333;
  padding: 10rpx;
}

.header .title {
  font-size: 38rpx;
  font-weight: bold;
  color: #2c3e50;
}

.placeholder {
  width: 60rpx;
}

.form {
  background: #fff;
  border-radius: 30rpx;
  padding: 40rpx 36rpx;
  box-shadow: 0 10rpx 40rpx rgba(0,0,0,0.06);
}

.input-group {
  margin-bottom: 30rpx;
}

.input-label {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 12rpx;
}

.input {
  width: 100%;
  height: 80rpx;
  border-bottom: 2rpx solid #e8ecf1;
  font-size: 32rpx;
  padding: 0 10rpx;
  box-sizing: border-box;
}

.input:focus {
  border-bottom-color: #007aff;
}

.register-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, #007aff, #0051d5);
  color: #fff;
  border-radius: 44rpx;
  font-size: 34rpx;
  font-weight: 600;
  border: none;
  margin-top: 10rpx;
}

.register-btn:active {
  opacity: 0.8;
}

.login-tip {
  display: flex;
  justify-content: center;
  gap: 12rpx;
  margin-top: 30rpx;
  font-size: 28rpx;
  color: #999;
}

.login-link {
  color: #007aff;
}
</style>
