// API 配置
const API_BASE = 'http://localhost:8000/api/miniapp'

// 带 token 的请求头
function authHeader() {
  const token = uni.getStorageSync('token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

// 封装 GET 请求
function get(path, data = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method: 'GET',
      data,
      header: { ...authHeader() },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('isLogin')
          uni.removeStorageSync('userInfo')
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
        } else reject(new Error(res.data?.detail || '请求失败'))
      },
      fail: (err) => reject(new Error('网络错误：' + err.errMsg))
    })
  })
}

// 封装 POST 请求
function post(path, data = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method: 'POST',
      data,
      header: { 'Content-Type': 'application/json', ...authHeader() },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('isLogin')
          uni.removeStorageSync('userInfo')
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
        } else reject(new Error(res.data?.detail || '请求失败'))
      },
      fail: (err) => reject(new Error('网络错误：' + err.errMsg))
    })
  })
}

// 封装上传文件请求
function upload(path, filePath, name = 'file') {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token')
    uni.uploadFile({
      url: `${API_BASE}${path}`,
      filePath,
      name,
      header: token ? { 'Authorization': `Bearer ${token}` } : {},
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(JSON.parse(res.data))
        } else {
          try { reject(new Error(JSON.parse(res.data).detail)) }
          catch { reject(new Error('上传失败')) }
        }
      },
      fail: (err) => reject(new Error('网络错误：' + err.errMsg))
    })
  })
}

// 封装 DELETE 请求
function del(path) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method: 'DELETE',
      header: { ...authHeader() },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('isLogin')
          uni.removeStorageSync('userInfo')
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
        } else reject(new Error(res.data?.detail || '请求失败'))
      },
      fail: (err) => reject(new Error('网络错误：' + err.errMsg))
    })
  })
}

// 封装 PUT 请求
function put(path, data = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}${path}`,
      method: 'PUT',
      data,
      header: { 'Content-Type': 'application/json', ...authHeader() },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('isLogin')
          uni.removeStorageSync('userInfo')
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('登录已过期'))
        } else reject(new Error(res.data?.detail || '请求失败'))
      },
      fail: (err) => reject(new Error('网络错误：' + err.errMsg))
    })
  })
}

export { API_BASE, authHeader, get, post, put, del, upload }