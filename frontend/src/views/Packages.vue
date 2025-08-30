<template>
  <div class="packages-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>套餐订阅</h1>
      <p>选择适合您的套餐进行续费</p>
    </div>

    <!-- 当前订阅状态 -->
    <el-card class="current-subscription-card" v-if="currentSubscription">
      <template #header>
        <div class="card-header">
          <i class="el-icon-info"></i>
          当前订阅状态
        </div>
      </template>
      <div class="subscription-info">
        <div class="info-item">
          <span class="label">剩余时长：</span>
          <span class="value">{{ currentSubscription.remainingDays }} 天</span>
        </div>
        <div class="info-item">
          <span class="label">到期时间：</span>
          <span class="value">{{ currentSubscription.expiryDate }}</span>
        </div>
        <div class="info-item">
          <span class="label">设备限制：</span>
          <span class="value">{{ currentSubscription.currentDevices }}/{{ currentSubscription.maxDevices }} 个</span>
        </div>
      </div>
    </el-card>

    <!-- 套餐列表 -->
    <div class="packages-grid">
      <el-card 
        v-for="pkg in packages" 
        :key="pkg.id" 
        class="package-card"
        :class="{ 'recommended': pkg.is_recommended }"
      >
        <div class="package-header">
          <h3>{{ pkg.name }}</h3>
          <div class="price">
            <span class="currency">¥</span>
            <span class="amount">{{ pkg.price }}</span>
            <span class="period">/{{ pkg.duration }}天</span>
          </div>
          <div class="recommended-badge" v-if="pkg.is_recommended">
            推荐
          </div>
        </div>

        <div class="package-features">
          <div class="feature-item">
            <i class="el-icon-check"></i>
            <span>时长：{{ pkg.duration }} 天</span>
          </div>
          <div class="feature-item">
            <i class="el-icon-check"></i>
            <span>设备限制：{{ pkg.device_limit }} 个</span>
          </div>
          <div class="feature-item">
            <i class="el-icon-check"></i>
            <span>支持所有节点</span>
          </div>
          <div class="feature-item">
            <i class="el-icon-check"></i>
            <span>7×24小时技术支持</span>
          </div>
        </div>

        <div class="package-actions">
          <el-button 
            type="primary" 
            size="large" 
            @click="selectPackage(pkg)"
            :loading="loading"
          >
            立即购买
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 支付对话框 -->
    <el-dialog
      v-model="paymentDialogVisible"
      title="确认购买"
      width="500px"
    >
      <div class="payment-content">
        <div class="selected-package">
          <h4>选择的套餐：{{ selectedPackage?.name }}</h4>
          <div class="package-details">
            <p>时长：{{ selectedPackage?.duration }} 天</p>
            <p>设备限制：{{ selectedPackage?.device_limit }} 个</p>
            <p class="price">价格：¥{{ selectedPackage?.price }}</p>
          </div>
        </div>

        <div class="payment-method">
          <h4>选择支付方式</h4>
          <el-radio-group v-model="paymentMethod">
            <el-radio label="alipay">支付宝</el-radio>
            <el-radio label="wechat">微信支付</el-radio>
          </el-radio-group>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="paymentDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmPayment"
            :loading="paymentLoading"
          >
            确认支付
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 支付二维码对话框 -->
    <el-dialog
      v-model="qrCodeDialogVisible"
      title="扫码支付"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="qr-code-content">
        <div class="qr-code-container">
          <canvas id="payment-qrcode"></canvas>
        </div>
        <div class="payment-info">
          <p>订单金额：¥{{ selectedPackage?.price }}</p>
          <p>剩余时间：{{ paymentTimer }} 秒</p>
        </div>
        <div class="payment-tips">
          <p>请使用支付宝扫描二维码完成支付</p>
          <p>支付完成后页面将自动跳转</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import { orderAPI } from '@/utils/api'

export default {
  name: 'Packages',
  setup() {
    const loading = ref(false)
    const paymentLoading = ref(false)
    const paymentDialogVisible = ref(false)
    const qrCodeDialogVisible = ref(false)
    const paymentMethod = ref('alipay')
    const paymentTimer = ref(300)
    const currentSubscription = ref(null)
    const packages = ref([])
    const selectedPackage = ref(null)
    let timerInterval = null

    // 获取当前订阅信息
    const fetchCurrentSubscription = async () => {
      try {
        const response = await orderAPI.getCurrentSubscription()
        currentSubscription.value = response.data
      } catch (error) {
        console.error('获取当前订阅失败:', error)
      }
    }

    // 获取套餐列表
    const fetchPackages = async () => {
      loading.value = true
      try {
        const response = await orderAPI.getPackages()
        packages.value = response.data
      } catch (error) {
        ElMessage.error('获取套餐列表失败')
        console.error('获取套餐列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 选择套餐
    const selectPackage = (pkg) => {
      selectedPackage.value = pkg
      paymentDialogVisible.value = true
    }

    // 确认支付
    const confirmPayment = async () => {
      if (!selectedPackage.value) {
        ElMessage.error('请选择套餐')
        return
      }

      paymentLoading.value = true
      try {
        const response = await orderAPI.createOrder({
          package_id: selectedPackage.value.id,
          payment_method: paymentMethod.value
        })

        const order = response.data
        selectedPackage.value = order

        // 生成支付二维码
        await generatePaymentQRCode(order.payment_url)

        // 关闭支付对话框，显示二维码对话框
        paymentDialogVisible.value = false
        qrCodeDialogVisible.value = true

        // 开始倒计时和轮询
        startPaymentTimer()
        startPaymentPolling()

      } catch (error) {
        ElMessage.error('创建订单失败')
        console.error('创建订单失败:', error)
      } finally {
        paymentLoading.value = false
      }
    }

    // 生成支付二维码
    const generatePaymentQRCode = async (paymentUrl) => {
      try {
        const qrcodeElement = document.getElementById('payment-qrcode')
        if (qrcodeElement) {
          await QRCode.toCanvas(qrcodeElement, paymentUrl, {
            width: 200,
            margin: 2
          })
        }
      } catch (error) {
        console.error('生成支付二维码失败:', error)
      }
    }

    // 开始支付倒计时
    const startPaymentTimer = () => {
      paymentTimer.value = 300
      timerInterval = setInterval(() => {
        paymentTimer.value--
        if (paymentTimer.value <= 0) {
          clearInterval(timerInterval)
          qrCodeDialogVisible.value = false
          ElMessage.warning('支付超时，请重新下单')
        }
      }, 1000)
    }

    // 开始轮询支付状态
    const startPaymentPolling = () => {
      const pollInterval = setInterval(async () => {
        try {
          const response = await orderAPI.getOrderStatus(selectedPackage.value.order_no)
          if (response.data.status === 'paid') {
            clearInterval(pollInterval)
            clearInterval(timerInterval)
            qrCodeDialogVisible.value = false
            ElMessage.success('支付成功！')
            
            // 刷新当前订阅信息
            await fetchCurrentSubscription()
          }
        } catch (error) {
          console.error('查询支付状态失败:', error)
        }
      }, 3000) // 每3秒查询一次

      // 5分钟后停止轮询
      setTimeout(() => {
        clearInterval(pollInterval)
      }, 300000)
    }

    // 清理定时器
    const clearTimers = () => {
      if (timerInterval) {
        clearInterval(timerInterval)
      }
    }

    onMounted(() => {
      fetchCurrentSubscription()
      fetchPackages()
    })

    onUnmounted(() => {
      clearTimers()
    })

    return {
      loading,
      paymentLoading,
      paymentDialogVisible,
      qrCodeDialogVisible,
      paymentMethod,
      paymentTimer,
      currentSubscription,
      packages,
      selectedPackage,
      selectPackage,
      confirmPayment
    }
  }
}
</script>

<style scoped>
.packages-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h1 {
  color: #1677ff;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
  font-size: 1rem;
}

.current-subscription-card {
  margin-bottom: 2rem;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.subscription-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  color: #666;
  font-weight: 500;
}

.value {
  color: #1677ff;
  font-weight: 600;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.package-card {
  position: relative;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.package-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.package-card.recommended {
  border-color: #1677ff;
}

.recommended-badge {
  position: absolute;
  top: -10px;
  right: 20px;
  background: #1677ff;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.package-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.package-header h3 {
  color: #333;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.price {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
}

.currency {
  color: #1677ff;
  font-size: 1.2rem;
  font-weight: 600;
}

.amount {
  color: #1677ff;
  font-size: 2.5rem;
  font-weight: 700;
}

.period {
  color: #666;
  font-size: 1rem;
}

.package-features {
  margin-bottom: 2rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0.5rem 0;
  color: #333;
}

.feature-item i {
  color: #52c41a;
  font-size: 1rem;
}

.package-actions {
  text-align: center;
}

.payment-content {
  padding: 1rem 0;
}

.selected-package {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.selected-package h4 {
  color: #333;
  margin-bottom: 1rem;
}

.package-details p {
  margin: 0.5rem 0;
  color: #666;
}

.package-details .price {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1677ff;
}

.payment-method {
  margin-top: 1.5rem;
}

.payment-method h4 {
  margin-bottom: 1rem;
  color: #333;
}

.qr-code-content {
  text-align: center;
}

.qr-code-container {
  margin-bottom: 1.5rem;
}

.payment-info {
  margin-bottom: 1rem;
}

.payment-info p {
  margin: 0.5rem 0;
  color: #333;
}

.payment-tips {
  color: #666;
  font-size: 0.9rem;
}

.payment-tips p {
  margin: 0.25rem 0;
}

@media (max-width: 768px) {
  .packages-grid {
    grid-template-columns: 1fr;
  }
  
  .subscription-info {
    grid-template-columns: 1fr;
  }
  
  .package-card {
    margin-bottom: 1rem;
  }
}
</style> 