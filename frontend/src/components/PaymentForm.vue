<template>
  <div class="payment-form">
    <el-card class="payment-card">
      <template #header>
        <div class="card-header">
          <span>选择支付方式</span>
        </div>
      </template>

      <!-- 订单信息 -->
      <div class="order-info">
        <h3>订单信息</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ orderInfo.orderNo }}</el-descriptions-item>
          <el-descriptions-item label="套餐名称">{{ orderInfo.packageName }}</el-descriptions-item>
          <el-descriptions-item label="支付金额">
            <span class="amount">¥{{ orderInfo.amount }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="有效期">{{ orderInfo.duration }}天</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 支付方式选择 -->
      <div class="payment-methods">
        <h3>支付方式</h3>
        <el-radio-group v-model="selectedPaymentMethod" @change="onPaymentMethodChange">
          <el-radio-button value="alipay">
            <i class="payment-icon alipay-icon"></i>
            支付宝
          </el-radio-button>
          <el-radio-button value="wechat">
            <i class="payment-icon wechat-icon"></i>
            微信支付
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 支付按钮 -->
      <div class="payment-actions">
        <el-button 
          type="primary" 
          size="large" 
          :loading="isProcessing"
          @click="handlePayment"
          :disabled="!selectedPaymentMethod"
        >
          {{ getPaymentButtonText() }}
        </el-button>
        
        <el-button 
          size="large" 
          @click="$emit('cancel')"
          :disabled="isProcessing"
        >
          取消支付
        </el-button>
      </div>

      <!-- 支付提示 -->
      <div class="payment-tips">
        <el-alert
          v-if="selectedPaymentMethod === 'alipay'"
          title="支付宝支付提示"
          type="info"
          :closable="false"
          show-icon
        >
          <p>1. 点击支付按钮后将跳转到支付宝</p>
          <p>2. 请在支付宝中完成支付</p>
          <p>3. 支付完成后将自动返回</p>
        </el-alert>
        
        <el-alert
          v-if="selectedPaymentMethod === 'wechat'"
          title="微信支付提示"
          type="info"
          :closable="false"
          show-icon
        >
          <p>1. 点击支付按钮后将显示二维码</p>
          <p>2. 请使用微信扫描二维码完成支付</p>
          <p>3. 支付完成后将自动刷新状态</p>
        </el-alert>
      </div>
    </el-card>

    <!-- 微信支付二维码弹窗 -->
    <el-dialog
      v-model="wechatQRVisible"
      title="微信支付"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="wechat-qr-container">
        <div class="qr-code-wrapper">
          <div v-if="wechatQRCode" class="qr-code">
            <img :src="wechatQRCode" alt="微信支付二维码" />
          </div>
          <div v-else class="qr-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <p>正在生成二维码...</p>
          </div>
        </div>
        
        <div class="qr-tips">
          <p>请使用微信扫描二维码完成支付</p>
          <p>支付完成后请勿关闭此窗口</p>
        </div>
        
        <div class="qr-actions">
          <el-button @click="checkPaymentStatus" :loading="isCheckingStatus">
            检查支付状态
          </el-button>
          <el-button type="primary" @click="wechatQRVisible = false">
            支付完成
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 支付结果弹窗 -->
    <el-dialog
      v-model="resultVisible"
      :title="paymentResult.success ? '支付成功' : '支付失败'"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="payment-result">
        <div v-if="paymentResult.success" class="success-result">
          <el-icon class="result-icon success"><CircleCheckFilled /></el-icon>
          <h3>支付成功！</h3>
          <p>您的订阅已激活，可以正常使用了。</p>
          <div class="result-details">
            <p><strong>订单号：</strong>{{ paymentResult.data?.order_no }}</p>
            <p><strong>支付金额：</strong>¥{{ paymentResult.data?.amount }}</p>
            <p><strong>支付时间：</strong>{{ formatDateTime(paymentResult.data?.paid_at) }}</p>
          </div>
        </div>
        
        <div v-else class="failed-result">
          <el-icon class="result-icon failed"><CircleCloseFilled /></el-icon>
          <h3>支付失败</h3>
          <p>{{ paymentResult.message }}</p>
          <div class="error-details">
            <p><strong>错误代码：</strong>{{ paymentResult.error_code }}</p>
            <p><strong>错误信息：</strong>{{ paymentResult.error_message }}</p>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button v-if="!paymentResult.success" @click="retryPayment">
            重试支付
          </el-button>
          <el-button type="primary" @click="handleResultClose">
            {{ paymentResult.success ? '完成' : '关闭' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled, Loading } from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'
import { formatDateTime } from '@/utils/date'

export default {
  name: 'PaymentForm',
  components: {
    CircleCheckFilled,
    CircleCloseFilled,
    Loading
  },
  props: {
    orderInfo: {
      type: Object,
      required: true
    }
  },
  emits: ['success', 'cancel', 'error'],
  setup(props, { emit }) {
    const api = useApi()
    
    // 响应式数据
    const selectedPaymentMethod = ref('')
    const isProcessing = ref(false)
    const isCheckingStatus = ref(false)
    const wechatQRVisible = ref(false)
    const wechatQRCode = ref('')
    const resultVisible = ref(false)
    const paymentResult = reactive({
      success: false,
      message: '',
      data: null,
      error_code: '',
      error_message: ''
    })
    
    // 支付状态检查定时器
    let statusCheckTimer = null
    
    // 计算属性
    const canProceed = computed(() => {
      return selectedPaymentMethod.value && !isProcessing.value
    })
    
    // 方法
    const onPaymentMethodChange = (method) => {
      selectedPaymentMethod.value = method
    }
    
    const getPaymentButtonText = () => {
      if (isProcessing.value) {
        return '处理中...'
      }
      return `立即支付 ¥${props.orderInfo.amount}`
    }
    
    const handlePayment = async () => {
      if (!selectedPaymentMethod.value) {
        ElMessage.warning('请选择支付方式')
        return
      }
      
      try {
        isProcessing.value = true
        
        // 创建支付订单
        const paymentData = {
          order_no: props.orderInfo.orderNo,
          amount: props.orderInfo.amount,
          currency: 'CNY',
          payment_method: selectedPaymentMethod.value,
          subject: `订阅套餐 - ${props.orderInfo.packageName}`,
          body: `购买${props.orderInfo.duration}天订阅套餐`,
          return_url: window.location.origin + '/payment/return',
          notify_url: window.location.origin + '/api/v1/payment/notify'
        }
        
        const response = await api.post('/payment/create', paymentData)
        
        if (response.data.payment_url) {
          if (selectedPaymentMethod.value === 'alipay') {
            // 支付宝支付 - 跳转支付页面
            window.open(response.data.payment_url, '_blank')
            ElMessage.success('正在跳转到支付宝...')
          } else if (selectedPaymentMethod.value === 'wechat') {
            // 微信支付 - 显示二维码
            wechatQRCode.value = response.data.payment_url
            wechatQRVisible.value = true
            startStatusCheck()
          }
        } else {
          throw new Error('获取支付链接失败')
        }
        
      } catch (error) {
        console.error('支付失败:', error)
        ElMessage.error(error.response?.data?.detail || '支付失败，请重试')
        emit('error', error)
      } finally {
        isProcessing.value = false
      }
    }
    
    const startStatusCheck = () => {
      // 每3秒检查一次支付状态
      statusCheckTimer = setInterval(async () => {
        await checkPaymentStatus()
      }, 3000)
    }
    
    const checkPaymentStatus = async () => {
      try {
        isCheckingStatus.value = true
        
        const response = await api.get(`/payment/transactions?order_no=${props.orderInfo.orderNo}`)
        const payments = response.data
        
        if (payments.length > 0) {
          const latestPayment = payments[0]
          
          if (latestPayment.status === 'success') {
            // 支付成功
            clearInterval(statusCheckTimer)
            wechatQRVisible.value = false
            
            paymentResult.success = true
            paymentResult.message = '支付成功'
            paymentResult.data = latestPayment
            
            resultVisible.value = true
            emit('success', latestPayment)
          } else if (latestPayment.status === 'failed') {
            // 支付失败
            clearInterval(statusCheckTimer)
            wechatQRVisible.value = false
            
            paymentResult.success = false
            paymentResult.message = '支付失败'
            paymentResult.error_code = 'PAYMENT_FAILED'
            paymentResult.error_message = '支付处理失败，请重试'
            
            resultVisible.value = true
            emit('error', new Error('支付失败'))
          }
        }
        
      } catch (error) {
        console.error('检查支付状态失败:', error)
        ElMessage.error('检查支付状态失败')
      } finally {
        isCheckingStatus.value = false
      }
    }
    
    const retryPayment = () => {
      resultVisible.value = false
      // 重新开始支付流程
      handlePayment()
    }
    
    const handleResultClose = () => {
      resultVisible.value = false
      if (paymentResult.success) {
        // 支付成功，可以跳转到其他页面
        emit('success', paymentResult.data)
      }
    }
    
    // 生命周期
    onMounted(() => {
      // 默认选择支付宝
      selectedPaymentMethod.value = 'alipay'
    })
    
    onUnmounted(() => {
      if (statusCheckTimer) {
        clearInterval(statusCheckTimer)
      }
    })
    
    return {
      selectedPaymentMethod,
      isProcessing,
      isCheckingStatus,
      wechatQRVisible,
      wechatQRCode,
      resultVisible,
      paymentResult,
      canProceed,
      onPaymentMethodChange,
      getPaymentButtonText,
      handlePayment,
      checkPaymentStatus,
      retryPayment,
      handleResultClose,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.payment-form {
  max-width: 800px;
  margin: 0 auto;
}

.payment-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 18px;
  font-weight: bold;
}

.order-info {
  margin-bottom: 30px;
}

.order-info h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
}

.amount {
  color: #f56c6c;
  font-size: 18px;
  font-weight: bold;
}

.payment-methods {
  margin-bottom: 30px;
}

.payment-methods h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
}

.payment-icon {
  display: inline-block;
  width: 20px;
  height: 20px;
  margin-right: 8px;
  vertical-align: middle;
}

.alipay-icon {
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="%2300a0e9" d="M22.319 4.609c-.977.377-2.04.777-3.18 1.196-1.14.419-2.38.839-3.72 1.259-1.34.42-2.78.84-4.32 1.26-1.54.42-3.18.84-4.92 1.26-1.74.42-3.58.84-5.52 1.26-1.94.42-3.98.84-6.12 1.26v1.5c2.14.42 4.18.84 6.12 1.26 1.94.42 3.78.84 5.52 1.26 1.74.42 3.38.84 4.92 1.26 1.54.42 2.98.84 4.32 1.26 1.34.42 2.58.84 3.72 1.259 1.14.419 2.203.819 3.18 1.196.977.377 1.84.754 2.58 1.131.74.377 1.36.754 1.86 1.131.5.377.88.754 1.14 1.131.26.377.4.754.4 1.131 0 .377-.14.754-.4 1.131-.26.377-.64.754-1.14 1.131-.5.377-1.12.754-1.86 1.131-.74.377-1.603.754-2.58 1.131-.977.377-2.04.777-3.18 1.196-1.14.419-2.38.839-3.72 1.259-1.34.42-2.78.84-4.32 1.26-1.54.42-3.18.84-4.92 1.26-1.74.42-3.58.84-5.52 1.26-1.94.42-3.98.84-6.12 1.26v1.5c2.14.42 4.18.84 6.12 1.26 1.94.42 3.78.84 5.52 1.26 1.74.42 3.38.84 4.92 1.26 1.54.42 2.98.84 4.32 1.26 1.34.42 2.58.84 3.72 1.259 1.14.419 2.203.819 3.18 1.196.977.377 1.84.754 2.58 1.131.74.377 1.36.754 1.86 1.131.5.377.88.754 1.14 1.131.26.377.4.754.4 1.131 0 .377-.14.754-.4 1.131-.26.377-.64.754-1.14 1.131-.5.377-1.12.754-1.86 1.131-.74.377-1.603.754-2.58 1.131z"/></svg>') no-repeat center;
  background-size: contain;
}

.wechat-icon {
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="%2307c160" d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.212 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 4.882-1.932 6.109-.207 1.227 1.725.792 4.82-.207 6.109-1.932 1.703-4.972 1.703-6.109.207-1.227-1.725-.792-4.82.207-6.109 1.932-1.703 4.972-1.703 6.109-.207z"/></svg>') no-repeat center;
  background-size: contain;
}

.payment-actions {
  text-align: center;
  margin-bottom: 20px;
}

.payment-actions .el-button {
  margin: 0 10px;
  min-width: 120px;
}

.payment-tips {
  margin-top: 20px;
}

.payment-tips .el-alert {
  margin-bottom: 10px;
}

.payment-tips p {
  margin: 5px 0;
  font-size: 14px;
}

/* 微信支付二维码弹窗 */
.wechat-qr-container {
  text-align: center;
}

.qr-code-wrapper {
  margin-bottom: 20px;
}

.qr-code img {
  max-width: 200px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.qr-loading {
  padding: 40px;
  color: #909399;
}

.qr-loading .el-icon {
  font-size: 24px;
  margin-bottom: 10px;
}

.qr-tips {
  margin-bottom: 20px;
  color: #606266;
}

.qr-tips p {
  margin: 5px 0;
}

.qr-actions .el-button {
  margin: 0 10px;
}

/* 支付结果弹窗 */
.payment-result {
  text-align: center;
  padding: 20px 0;
}

.result-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.result-icon.success {
  color: #67c23a;
}

.result-icon.failed {
  color: #f56c6c;
}

.payment-result h3 {
  margin-bottom: 10px;
  color: #303133;
}

.payment-result p {
  margin-bottom: 15px;
  color: #606266;
}

.result-details,
.error-details {
  text-align: left;
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-top: 15px;
}

.result-details p,
.error-details p {
  margin: 5px 0;
  font-size: 14px;
}

.dialog-footer {
  text-align: right;
}

.dialog-footer .el-button {
  margin-left: 10px;
}
</style>
