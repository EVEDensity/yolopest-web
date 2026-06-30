<template>
  <view class="edit-container">
    <view class="avatar-section" @tap="chooseAvatar">
      <image class="avatar" :src="form.avatar || '/static/logo.png'" mode="aspectFill"></image>
      <text class="avatar-tip">点击更换头像</text>
    </view>

    <view class="form-card">
      <view class="form-item">
        <text class="form-label">用户名</text>
        <input class="form-input" v-model="form.username" placeholder="请输入用户名" maxlength="50" />
      </view>
      <view class="form-item">
        <text class="form-label">邮箱</text>
        <input class="form-input form-input-disabled" :value="email" disabled placeholder="邮箱不可更改" />
      </view>
    </view>

    <view class="save-btn" @tap="handleSave">
      <text>保存修改</text>
    </view>

    <view class="change-pwd-section">
      <text class="section-title">修改密码</text>
      <view class="form-item">
        <text class="form-label">旧密码</text>
        <input class="form-input" v-model="pwdForm.old_password" type="password" placeholder="请输入旧密码" />
      </view>
      <view class="form-item">
        <text class="form-label">新密码</text>
        <input class="form-input" v-model="pwdForm.new_password" type="password" placeholder="至少8位" />
      </view>
      <view class="form-item">
        <text class="form-label">确认密码</text>
        <input class="form-input" v-model="pwdForm.confirm_password" type="password" placeholder="再次输入新密码" />
      </view>
      <view class="change-pwd-btn" @tap="handleChangePassword">
        <text>修改密码</text>
      </view>
    </view>

    <view class="cancel-btn" @tap="goBack">
      <text>取消</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { get, put, post, upload } from '../../../api-config'

const form = ref({
  username: '',
  avatar: ''
})
const email = ref('')

const pwdForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

onShow(() => {
  loadProfile()
})

const loadProfile = async () => {
  try {
    const data = await get('/users/profile')
    form.value.username = data.username || ''
    form.value.avatar = data.avatar || ''
    email.value = data.email || ''
  } catch (e) {
    uni.showToast({ title: '加载用户信息失败', icon: 'none' })
  }
}

const chooseAvatar = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: (res) => {
      const tempPath = res.tempFilePaths[0]
      // 先上传头像
      uni.showLoading({ title: '上传中...' })
      upload('/users/upload_avatar', tempPath, 'file')
        .then((data) => {
          uni.hideLoading()
          form.value.avatar = data.url || tempPath
        })
        .catch(() => {
          uni.hideLoading()
          // 上传失败则临时显示本地图片
          form.value.avatar = tempPath
        })
    }
  })
}

const handleSave = async () => {
  if (!form.value.username.trim()) {
    uni.showToast({ title: '用户名不能为空', icon: 'none' })
    return
  }

  uni.showLoading({ title: '保存中...' })

  try {
    const data = await put('/users/profile', {
      username: form.value.username.trim(),
      avatar: form.value.avatar
    })
    uni.hideLoading()
    uni.showToast({ title: '保存成功', icon: 'success' })

    // 更新本地缓存
    const saved = uni.getStorageSync('userInfo') || {}
    saved.username = data.username
    saved.avatar = data.avatar
    uni.setStorageSync('userInfo', saved)

    setTimeout(() => {
      uni.navigateBack()
    }, 500)
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: e.message || '保存失败', icon: 'none' })
  }
}

const goBack = () => {
  uni.navigateBack()
}

const handleChangePassword = async () => {
  const { old_password, new_password, confirm_password } = pwdForm.value

  if (!old_password) {
    uni.showToast({ title: '请输入旧密码', icon: 'none' })
    return
  }
  if (new_password.length < 8) {
    uni.showToast({ title: '新密码至少8位', icon: 'none' })
    return
  }
  if (new_password !== confirm_password) {
    uni.showToast({ title: '两次输入的新密码不一致', icon: 'none' })
    return
  }
  if (old_password === new_password) {
    uni.showToast({ title: '新密码不能与旧密码相同', icon: 'none' })
    return
  }

  uni.showLoading({ title: '修改中...' })
  try {
    await post('/users/change-password', {
      old_password,
      new_password
    })
    uni.hideLoading()
    uni.showToast({ title: '密码修改成功', icon: 'success' })
    pwdForm.value = { old_password: '', new_password: '', confirm_password: '' }
  } catch (e) {
    uni.hideLoading()
    uni.showToast({ title: e.message || '密码修改失败', icon: 'none' })
  }
}

</script>

<style scoped>
.edit-container {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 30rpx;
  box-sizing: border-box;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 50rpx 0;
}

.avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  border: 4rpx solid #007aff;
  background: #fff;
}

.avatar-tip {
  font-size: 26rpx;
  color: #007aff;
  margin-top: 16rpx;
}

.form-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 0 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
}

.form-item {
  display: flex;
  align-items: center;
  padding: 30rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.form-item:last-child {
  border-bottom: none;
}

.form-label {
  font-size: 30rpx;
  color: #333;
  width: 140rpx;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  height: 48rpx;
  font-size: 30rpx;
  color: #333;
  text-align: right;
}

.form-input-disabled {
  color: #999;
}

.save-btn {
  margin-top: 60rpx;
  background: #007aff;
  border-radius: 50rpx;
  padding: 28rpx;
  text-align: center;
  font-size: 32rpx;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 8rpx 30rpx rgba(0, 122, 255, 0.3);
}

.save-btn:active {
  opacity: 0.8;
}

.cancel-btn {
  margin-top: 30rpx;
  background: #fff;
  border-radius: 50rpx;
  padding: 26rpx;
  text-align: center;
  font-size: 30rpx;
  color: #999;
  font-weight: 500;
}

.cancel-btn:active {
  opacity: 0.6;
}

/* 修改密码 */
.change-pwd-section {
  margin-top: 40rpx;
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04);
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #666;
  display: block;
  padding: 10rpx 0 20rpx;
  border-bottom: 2rpx solid #f5f5f5;
}

.change-pwd-section .form-item {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.change-pwd-section .form-item:last-of-type {
  border-bottom: none;
}

.change-pwd-section .form-label {
  font-size: 28rpx;
  color: #333;
  width: 160rpx;
  flex-shrink: 0;
}

.change-pwd-section .form-input {
  flex: 1;
  height: 48rpx;
  font-size: 28rpx;
  color: #333;
  text-align: right;
}

.change-pwd-btn {
  margin-top: 30rpx;
  background: #ff6b35;
  border-radius: 30rpx;
  padding: 22rpx;
  text-align: center;
  font-size: 30rpx;
  color: #fff;
  font-weight: 500;
}

.change-pwd-btn:active {
  opacity: 0.8;
}
</style>
