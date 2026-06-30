<template>
  <view class="login-container">
    <view class="header">
      <image class="logo" src="/static/logo.png" mode="aspectFit"></image>
      <text class="title">害虫智能检测</text>
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
        <text class="input-label">密码</text>
        <input
          class="input"
          v-model="password"
          placeholder="请输入密码"
          :password="true"
        />
      </view>

      <view class="options">
        <label class="remember">
          <checkbox :checked="remember" @tap="toggleRemember" />
          记住我
        </label>
        <text class="forgot" @tap="goToForgot">忘记密码？</text>
      </view>

      <button class="login-btn" @tap="handleLogin">登 录</button>

      <view class="register-tip">
        <text>还没有账号？</text>
        <text class="register-link" @tap="goToRegister">立即注册</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { post } from '../../api-config'

const email = ref('')
const password = ref('')
const remember = ref(false)

onLoad(() => {
  const savedEmail = uni.getStorageSync('savedEmail')
  if (savedEmail) {
    email.value = savedEmail
    remember.value = true
  }
})

const toggleRemember = () => {
  remember.value = !remember.value
}

const handleLogin = async () => {
  if (!email.value || !password.value) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  // 简单的邮箱格式校验
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  if (!emailRegex.test(email.value)) {
    uni.showToast({ title: '请输入正确的邮箱地址', icon: 'none' })
    return
  }

  uni.showLoading({ title: '登录中...' })

  try {
    const data = await post('/auth/login', {
      email: email.value,
      password: password.value
    })

    if (remember.value) {
      uni.setStorageSync('savedEmail', email.value)
    } else {
      uni.removeStorageSync('savedEmail')
    }

    // 保存 token 和登录状态
    uni.setStorageSync('token', data.access_token)
    uni.setStorageSync('isLogin', true)

    uni.hideLoading()
    uni.showToast({ title: '登录成功', icon: 'success' })

    setTimeout(() => {
      uni.switchTab({ url: '/pages/index/index' })
    }, 500)

  } catch (error) {
    uni.hideLoading()
    uni.showToast({ title: error.message || '登录失败，请重试', icon: 'none' })
  }
}

const goToRegister = () => {
  uni.navigateTo({ url: '/pages/register/index' })
}

const goToForgot = () => {
  uni.showToast({ title: '请联系管理员重置密码', icon: 'none' })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 40rpx 50rpx;
  box-sizing: border-box;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 80rpx;
  padding-bottom: 60rpx;
}

.logo {
  width: 160rpx;
  height: 160rpx;
  border-radius: 40rpx;
  background: #fff;
  padding: 20rpx;
}

.title {
  margin-top: 30rpx;
  font-size: 44rpx;
  font-weight: bold;
  color: #2c3e50;
  letter-spacing: 4rpx;
}

.form {
  background: #ffffff;
  border-radius: 30rpx;
  padding: 40rpx 36rpx;
  box-shadow: 0 10rpx 40rpx rgba(0, 0, 0, 0.08);
}

.input-group {
  margin-bottom: 30rpx;
}

.input-label {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 12rpx;
  font-weight: 500;
}

.input {
  width: 100%;
  height: 80rpx;
  border-bottom: 2rpx solid #e8ecf1;
  font-size: 32rpx;
  padding: 0 10rpx;
  box-sizing: border-box;
  color: #333;
}

.input:focus {
  border-bottom-color: #007aff;
}

.options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 10rpx 0 40rpx;
}

.remember {
  font-size: 28rpx;
  color: #666;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.remember checkbox {
  transform: scale(0.8);
}

.forgot {
  font-size: 28rpx;
  color: #007aff;
}

.login-btn {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: linear-gradient(135deg, #007aff, #0051d5);
  color: #fff;
  border-radius: 44rpx;
  font-size: 34rpx;
  font-weight: 600;
  border: none;
  letter-spacing: 6rpx;
}

.login-btn:active {
  opacity: 0.8;
}

.register-tip {
  display: flex;
  justify-content: center;
  gap: 12rpx;
  margin-top: 30rpx;
  font-size: 28rpx;
  color: #999;
}

.register-link {
  color: #007aff;
  font-weight: 500;
}
</style>
