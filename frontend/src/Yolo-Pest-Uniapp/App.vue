<script>
	let authChecked = false

	export default {
		onLaunch: function() {
			console.log('App Launch')
			// 延迟执行认证检查，确保页面栈已初始化完成
			setTimeout(() => {
				this.checkAuth()
			}, 300)
		},
		onShow: function() {
			// 如果 onLaunch 已检查过，不再重复执行
			if (!authChecked) return
			const token = uni.getStorageSync('token')
			if (!token) {
				this.redirectToLogin()
			}
		},
		onHide: function() {
			console.log('App Hide')
		},
		methods: {
			checkAuth() {
				authChecked = true
				const token = uni.getStorageSync('token')
				const pages = getCurrentPages()
				const currentPage = pages.length > 0 ? pages[pages.length - 1].route : ''
				const noAuthPages = ['pages/login/index', 'pages/register/index']
				if (!token && !noAuthPages.includes(currentPage)) {
					this.redirectToLogin()
				}
			},
			redirectToLogin() {
				uni.reLaunch({
					url: '/pages/login/index',
					fail: (err) => {
						console.error('reLaunch 失败，使用 navigateTo 降级:', err)
						uni.navigateTo({ url: '/pages/login/index' })
					}
				})
			}
		}
	}
</script>

<style>
	/*每个页面公共css */
</style>
