<template>
  <div class="packages-container">
    <div class="page-header">
      <h1>套餐购买</h1>
      <p>选择适合您的订阅套餐</p>
    </div>

    <!-- 套餐列表 -->
    <div class="packages-grid">
      <el-card 
        v-for="package in packages" 
        :key="package.id" 
        class="package-card"
        :class="{ 'popular': package.is_popular, 'recommended': package.is_recommended }"
      >
        <div class="package-header">
          <h3 class="package-name">{{ package.name }}</h3>
          <div v-if="package.is_popular" class="popular-badge">热门</div>
          <div v-if="package.is_recommended" class="recommended-badge">推荐</div>
        </div>
        
        <div class="package-price">
          <span class="currency">¥</span>
          <span class="amount">{{ package.price }}</span>
          <span class="period">/{{ package.duration_days }}天</span>
        </div>
        
        <div class="package-features">
          <ul>
            <li v-for="feature in package.features" :key="feature">
              <i class="el-icon-check"></i>
              {{ feature }}
            </li>
          </ul>
        </div>
        
        <div class="package-actions">
          <el-button 
            type="primary" 
            size="large" 
            @click="selectPackage(package)"
            :loading="isProcessing"
            style="width: 100%"
          >
            立即购买
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 购买确认对话框 -->
    <el-dialog
      v-model="purchaseDialogVisible"
      title="确认购买"
      width="500px"
      :close-on-click-modal="false"
    >
      <div class="purchase-confirm">
        <div class="package-summary">
          <h4>套餐信息</h4>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="套餐名称">{{ selectedPackage?.name }}</el-descriptions-item>
            <el-descriptions-item label="有效期">{{ selectedPackage?.duration_days }}天</el-descriptions-item>
            <el-descriptions-item label="设备限制">{{ selectedPackage?.device_limit }}个</el-descriptions-item>
            <el-descriptions-item label="支付金额">
              <span class="amount">¥{{ selectedPackage?.price }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="purchase-actions">
          <el-button @click="purchaseDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmPurchase">确认购买</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 支付表单 -->
    <el-dialog
      v-model="paymentDialogVisible"
      title="选择支付方式"
      width="600px"
      :close-on-click-modal="false"
    >
      <PaymentForm 
        :order-info="orderInfo"
        @success="onPaymentSuccess"
        @cancel="onPaymentCancel"
        @error="onPaymentError"
      />
    </el-dialog>

    <!-- 购买成功提示 -->
    <el-dialog
      v-model="successDialogVisible"
      title="购买成功"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="success-message">
        <el-icon class="success-icon"><CircleCheckFilled /></el-icon>
        <h3>恭喜！购买成功</h3>
        <p>您的订阅已激活，可以正常使用了。</p>
        <div class="success-actions">
          <el-button type="primary" @click="goToSubscription">查看订阅</el-button>
          <el-button @click="successDialogVisible = false">关闭</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'
import PaymentForm from '@/components/PaymentForm.vue'

export default {
  name: 'Packages',
  components: {
    PaymentForm,
    CircleCheckFilled
  },
  setup() {
    const router = useRouter()
    const api = useApi()
    
    // 响应式数据
    const packages = ref([])
    const isProcessing = ref(false)
    const purchaseDialogVisible = ref(false)
    const paymentDialogVisible = ref(false)
    const successDialogVisible = ref(false)
    const selectedPackage = ref(null)
    const orderInfo = reactive({
      orderNo: '',
      packageName: '',
      amount: 0,
      duration: 0
    })
    
    // 获取套餐列表
    const loadPackages = async () => {
      try {
        const response = await api.get('/packages/')
        packages.value = response.data.map(pkg => ({
          ...pkg,
          features: [
            `有效期 ${pkg.duration_days} 天`,
            `支持 ${pkg.device_limit} 个设备`,
            pkg.bandwidth_limit ? `流量限制 ${pkg.bandwidth_limit}GB` : '无流量限制',
            '7×24小时技术支持',
            '高速稳定节点'
          ],
          is_popular: pkg.sort_order === 2,
          is_recommended: pkg.sort_order === 3
        }))
      } catch (error) {
        ElMessage.error('加载套餐列表失败')
        console.error('加载套餐失败:', error)
      }
    }
    
    // 选择套餐
    const selectPackage = (pkg) => {
      selectedPackage.value = pkg
      purchaseDialogVisible.value = true
    }
    
    // 确认购买
    const confirmPurchase = async () => {
      try {
        isProcessing.value = true
        
        // 创建订单
        const orderData = {
          package_id: selectedPackage.value.id,
          amount: selectedPackage.value.price,
          currency: 'CNY'
        }
        
        const response = await api.post('/orders/create', orderData)
        const order = response.data
        
        // 设置订单信息
        orderInfo.orderNo = order.order_no
        orderInfo.packageName = selectedPackage.value.name
        orderInfo.amount = selectedPackage.value.price
        orderInfo.duration = selectedPackage.value.duration_days
        
        // 关闭购买确认对话框，显示支付对话框
        purchaseDialogVisible.value = false
        paymentDialogVisible.value = true
        
      } catch (error) {
        ElMessage.error('创建订单失败，请重试')
        console.error('创建订单失败:', error)
      } finally {
        isProcessing.value = false
      }
    }
    
    // 支付成功回调
    const onPaymentSuccess = (paymentData) => {
      paymentDialogVisible.value = false
      successDialogVisible.value = true
      
      ElMessage.success('支付成功！')
      
      // 可以在这里更新用户信息或跳转页面
    }
    
    // 支付取消回调
    const onPaymentCancel = () => {
      paymentDialogVisible.value = false
      ElMessage.info('已取消支付')
    }
    
    // 支付失败回调
    const onPaymentError = (error) => {
      paymentDialogVisible.value = false
      ElMessage.error('支付失败，请重试')
      console.error('支付失败:', error)
    }
    
    // 跳转到订阅页面
    const goToSubscription = () => {
      successDialogVisible.value = false
      router.push('/subscription')
    }
    
    // 生命周期
    onMounted(() => {
      loadPackages()
    })
    
    return {
      packages,
      isProcessing,
      purchaseDialogVisible,
      paymentDialogVisible,
      successDialogVisible,
      selectedPackage,
      orderInfo,
      selectPackage,
      confirmPurchase,
      onPaymentSuccess,
      onPaymentCancel,
      onPaymentError,
      goToSubscription
    }
  }
}
</script>

<style scoped>
.packages-container {
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 28px;
}

.page-header p {
  margin: 0;
  color: #909399;
  font-size: 16px;
}

.packages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.package-card {
  position: relative;
  text-align: center;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.package-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.package-card.popular {
  border-color: #409EFF;
}

.package-card.recommended {
  border-color: #67C23A;
}

.package-header {
  position: relative;
  margin-bottom: 20px;
}

.package-name {
  margin: 0;
  color: #303133;
  font-size: 20px;
  font-weight: bold;
}

.popular-badge,
.recommended-badge {
  position: absolute;
  top: -10px;
  right: -10px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: white;
}

.popular-badge {
  background: #409EFF;
}

.recommended-badge {
  background: #67C23A;
}

.package-price {
  margin-bottom: 30px;
}

.currency {
  font-size: 18px;
  color: #909399;
  vertical-align: top;
}

.amount {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
  margin: 0 5px;
}

.period {
  font-size: 16px;
  color: #909399;
}

.package-features {
  margin-bottom: 30px;
  text-align: left;
}

.package-features ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.package-features li {
  padding: 8px 0;
  color: #606266;
  display: flex;
  align-items: center;
}

.package-features li i {
  color: #67C23A;
  margin-right: 10px;
  font-size: 16px;
}

.package-actions {
  margin-bottom: 20px;
}

/* 购买确认对话框 */
.purchase-confirm {
  padding: 20px 0;
}

.package-summary h4 {
  margin-bottom: 15px;
  color: #303133;
}

.amount {
  color: #f56c6c;
  font-weight: bold;
}

.purchase-actions {
  text-align: center;
  margin-top: 20px;
}

.purchase-actions .el-button {
  margin: 0 10px;
}

/* 成功提示对话框 */
.success-message {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  font-size: 48px;
  color: #67C23A;
  margin-bottom: 15px;
}

.success-message h3 {
  margin: 15px 0;
  color: #303133;
}

.success-message p {
  margin-bottom: 20px;
  color: #606266;
}

.success-actions {
  margin-top: 20px;
}

.success-actions .el-button {
  margin: 0 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .packages-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .package-card {
    margin: 0 10px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
  
  .amount {
    font-size: 28px;
  }
}
</style> 