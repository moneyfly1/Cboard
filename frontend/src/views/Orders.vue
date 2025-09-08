<template>
  <div class="orders-container">
    <div class="page-header">
      <h1>订单记录</h1>
      <p>查看您的所有订单记录</p>
    </div>

    <!-- 订单统计 -->
    <el-row :gutter="20" class="order-stats">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ orderStats.total }}</div>
            <div class="stat-label">总订单数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ orderStats.pending }}</div>
            <div class="stat-label">待支付</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ orderStats.paid }}</div>
            <div class="stat-label">已支付</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ orderStats.totalAmount }}</div>
            <div class="stat-label">总金额(元)</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-select v-model="filters.status" placeholder="订单状态" clearable>
            <el-option label="全部状态" value="" />
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已退款" value="refunded" />
            <el-option label="支付失败" value="failed" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filters.payment_method" placeholder="支付方式" clearable>
            <el-option label="全部方式" value="" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-date-picker
            v-model="filters.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="applyFilters">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 订单列表 -->
    <el-card class="orders-list">
      <template #header>
        <div class="card-header">
          <span>订单列表</span>
          <el-button type="primary" @click="refreshOrders">
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </template>

      <el-table 
        :data="orders" 
        style="width: 100%"
        v-loading="isLoading"
        :empty-text="emptyText"
      >
        <el-table-column prop="order_no" label="订单号" width="180">
          <template #default="scope">
            <el-tag size="small" type="info">{{ scope.row.order_no }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="package_name" label="套餐名称" />
        
        <el-table-column prop="amount" label="金额" width="120">
          <template #default="scope">
            <span class="amount">¥{{ scope.row.amount }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="payment_method" label="支付方式" width="120">
          <template #default="scope">
            <el-tag 
              :type="getPaymentMethodType(scope.row.payment_method)"
              size="small"
            >
              {{ getPaymentMethodText(scope.row.payment_method) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag 
              :type="getOrderStatusType(scope.row.status)"
              size="small"
            >
              {{ getOrderStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="paid_at" label="支付时间" width="180">
          <template #default="scope">
            {{ scope.row.paid_at ? formatDateTime(scope.row.paid_at) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button 
              v-if="scope.row.status === 'pending'"
              size="small" 
              type="primary"
              @click="payOrder(scope.row)"
            >
              立即支付
            </el-button>
            
            <el-button 
              v-if="scope.row.status === 'pending'"
              size="small" 
              @click="cancelOrder(scope.row)"
            >
              取消订单
            </el-button>
            
            <el-button 
              v-if="scope.row.status === 'paid'"
              size="small" 
              type="success"
              @click="viewOrderDetail(scope.row)"
            >
              查看详情
            </el-button>
            
            <el-button 
              v-if="scope.row.status === 'paid'"
              size="small" 
              type="warning"
              @click="applyRefund(scope.row)"
            >
              申请退款
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="600px"
    >
      <div v-if="selectedOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">{{ selectedOrder.order_no }}</el-descriptions-item>
          <el-descriptions-item label="套餐名称">{{ selectedOrder.package_name }}</el-descriptions-item>
          <el-descriptions-item label="订单金额">¥{{ selectedOrder.amount }}</el-descriptions-item>
          <el-descriptions-item label="支付方式">{{ getPaymentMethodText(selectedOrder.payment_method) }}</el-descriptions-item>
          <el-descriptions-item label="订单状态">
            <el-tag :type="getOrderStatusType(selectedOrder.status)">
              {{ getOrderStatusText(selectedOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedOrder.created_at) }}</el-descriptions-item>
          <el-descriptions-item v-if="selectedOrder.paid_at" label="支付时间" :span="2">
            {{ formatDateTime(selectedOrder.paid_at) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedOrder.payment_id" label="支付ID" :span="2">
            {{ selectedOrder.payment_id }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 支付二维码对话框 -->
    <el-dialog
      v-model="paymentQRVisible"
      title="扫码支付"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="payment-qr-container">
        <div class="order-info">
          <h3>订单信息</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单号">{{ selectedOrder?.order_no }}</el-descriptions-item>
            <el-descriptions-item label="套餐名称">{{ selectedOrder?.package_name }}</el-descriptions-item>
            <el-descriptions-item label="支付金额">
              <span class="amount">¥{{ selectedOrder?.amount }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="支付方式">
              <el-tag type="primary">{{ selectedOrder?.payment_method === 'alipay' ? '支付宝' : '微信支付' }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="qr-code-wrapper">
          <div v-if="paymentQRCode" class="qr-code">
            <img :src="paymentQRCode" alt="支付二维码" />
          </div>
          <div v-else class="qr-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <p>正在生成二维码...</p>
          </div>
        </div>
        
        <div class="payment-tips">
          <el-alert
            title="支付提示"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>1. 请使用{{ selectedOrder?.payment_method === 'alipay' ? '支付宝' : '微信' }}扫描上方二维码</p>
              <p>2. 确认订单信息无误后完成支付</p>
              <p>3. 支付完成后请勿关闭此窗口，系统将自动检测支付状态</p>
            </template>
          </el-alert>
        </div>
        
        <div class="payment-actions">
          <el-button 
            @click="checkPaymentStatus" 
            :loading="isCheckingPayment"
            type="primary"
          >
            检查支付状态
          </el-button>
          <el-button @click="paymentQRVisible = false">
            关闭
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 退款申请对话框 -->
    <el-dialog
      v-model="refundDialogVisible"
      title="申请退款"
      width="500px"
    >
      <el-form :model="refundForm" :rules="refundRules" ref="refundFormRef" label-width="100px">
        <el-form-item label="退款金额" prop="amount">
          <el-input 
            v-model="refundForm.amount" 
            type="number" 
            :min="0" 
            :max="selectedOrder?.amount"
            step="0.01"
          >
            <template #prepend>¥</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="退款原因" prop="reason">
          <el-select v-model="refundForm.reason" placeholder="请选择退款原因">
            <el-option label="商品质量问题" value="quality_issue" />
            <el-option label="服务不满意" value="service_unsatisfactory" />
            <el-option label="重复购买" value="duplicate_purchase" />
            <el-option label="其他原因" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="详细说明" prop="description">
          <el-input 
            v-model="refundForm.description" 
            type="textarea" 
            :rows="4"
            placeholder="请详细描述退款原因"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="refundDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRefund" :loading="isSubmitting">
            提交申请
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'
import { formatDateTime } from '@/utils/date'

export default {
  name: 'Orders',
  components: {
    Loading
  },
  setup() {
    const api = useApi()
    
    // 响应式数据
    const orders = ref([])
    const isLoading = ref(false)
    const orderStats = ref({
      total: 0,
      pending: 0,
      paid: 0,
      totalAmount: 0
    })
    
    // 筛选条件
    const filters = reactive({
      status: '',
      payment_method: '',
      date_range: []
    })
    
    // 分页
    const pagination = reactive({
      current: 1,
      size: 20,
      total: 0
    })
    
    // 对话框状态
    const detailDialogVisible = ref(false)
    const refundDialogVisible = ref(false)
    const paymentQRVisible = ref(false)
    const selectedOrder = ref(null)
    const paymentQRCode = ref('')
    const isCheckingPayment = ref(false)
    
    // 退款表单
    const refundForm = reactive({
      amount: 0,
      reason: '',
      description: ''
    })
    const refundRules = {
      amount: [
        { required: true, message: '请输入退款金额', trigger: 'blur' },
        { type: 'number', min: 0, message: '退款金额不能小于0', trigger: 'blur' }
      ],
      reason: [
        { required: true, message: '请选择退款原因', trigger: 'change' }
      ],
      description: [
        { required: true, message: '请输入详细说明', trigger: 'blur' },
        { min: 10, message: '详细说明至少10个字符', trigger: 'blur' }
      ]
    }
    const refundFormRef = ref()
    const isSubmitting = ref(false)
    
    // 计算属性
    const emptyText = computed(() => {
      if (isLoading.value) return '加载中...'
      if (filters.status || filters.payment_method || filters.date_range.length > 0) {
        return '没有找到符合条件的订单'
      }
      return '暂无订单记录'
    })
    
    // 方法
    const loadOrders = async () => {
      try {
        isLoading.value = true
        
        const params = {
          page: pagination.current,
          size: pagination.size,
          ...filters
        }
        
        if (filters.date_range && filters.date_range.length === 2) {
          params.start_date = filters.date_range[0]
          params.end_date = filters.date_range[1]
        }
        
        const response = await api.get('/orders/', { params })
        orders.value = response.data.data?.orders || response.data.items || []
        pagination.total = response.data.data?.total || response.data.total || 0
        
        // 更新统计信息
        await loadOrderStats()
        
      } catch (error) {
        ElMessage.error('加载订单列表失败')
        console.error('加载订单失败:', error)
      } finally {
        isLoading.value = false
      }
    }
    
    const loadOrderStats = async () => {
      try {
        const response = await api.get('/orders/stats')
        orderStats.value = response.data
      } catch (error) {
        console.error('加载订单统计失败:', error)
      }
    }
    
    const applyFilters = () => {
      pagination.current = 1
      loadOrders()
    }
    
    const resetFilters = () => {
      filters.status = ''
      filters.payment_method = ''
      filters.date_range = []
      pagination.current = 1
      loadOrders()
    }
    
    const refreshOrders = () => {
      loadOrders()
    }
    
    const handleSizeChange = (size) => {
      pagination.size = size
      pagination.current = 1
      loadOrders()
    }
    
    const handleCurrentChange = (page) => {
      pagination.current = page
      loadOrders()
    }
    
    const payOrder = async (order) => {
      try {
        console.log('=== 订单支付流程 ===')
        console.log('订单信息:', order)
        
        // 创建支付订单
        const paymentData = {
          order_no: order.order_no,
          amount: order.amount,
          currency: 'CNY',
          payment_method: order.payment_method || 'alipay',
          subject: `订阅套餐 - ${order.package_name}`,
          body: `购买${order.package_duration}天订阅套餐`,
          return_url: window.location.origin + '/payment/return',
          notify_url: window.location.origin + '/api/v1/payment/notify'
        }
        
        console.log('支付数据:', paymentData)
        
        const response = await api.post('/payment/create', paymentData)
        console.log('支付API响应:', response.data)
        
        if (response.data && response.data.payment_url) {
          console.log('支付URL:', response.data.payment_url)
          // 显示支付二维码
          showPaymentQR(order, response.data.payment_url)
        } else {
          console.error('支付响应格式错误:', response.data)
          ElMessage.error('创建支付订单失败')
        }
        
      } catch (error) {
        ElMessage.error('创建支付订单失败，请重试')
        console.error('支付失败:', error)
      }
    }
    
    const showPaymentQR = (order, paymentUrl) => {
      console.log('显示支付二维码:', { order, paymentUrl })
      
      selectedOrder.value = order
      paymentQRCode.value = paymentUrl
      paymentQRVisible.value = true
      
      console.log('二维码对话框状态:', paymentQRVisible.value)
      
      // 开始检查支付状态
      startPaymentStatusCheck()
    }
    
    const startPaymentStatusCheck = () => {
      // 每3秒检查一次支付状态
      const checkInterval = setInterval(async () => {
        await checkPaymentStatus()
      }, 3000)
      
      // 30分钟后停止检查
      setTimeout(() => {
        clearInterval(checkInterval)
      }, 30 * 60 * 1000)
    }
    
    const checkPaymentStatus = async () => {
      if (!selectedOrder.value) return
      
      try {
        isCheckingPayment.value = true
        
        const response = await api.get(`/payment/transactions?order_no=${selectedOrder.value.order_no}`)
        const payments = response.data
        
        if (payments.length > 0) {
          const latestPayment = payments[0]
          
          if (latestPayment.status === 'success') {
            // 支付成功
            paymentQRVisible.value = false
            ElMessage.success('支付成功！')
            loadOrders() // 刷新订单列表
          } else if (latestPayment.status === 'failed') {
            // 支付失败
            paymentQRVisible.value = false
            ElMessage.error('支付失败，请重试')
          }
        }
        
      } catch (error) {
        console.error('检查支付状态失败:', error)
      } finally {
        isCheckingPayment.value = false
      }
    }
    
    const cancelOrder = async (order) => {
      try {
        await ElMessageBox.confirm(
          '确定要取消这个订单吗？取消后无法恢复。',
          '确认取消',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await api.post(`/orders/${order.id}/cancel`)
        ElMessage.success('订单已取消')
        loadOrders()
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('取消订单失败')
          console.error('取消订单失败:', error)
        }
      }
    }
    
    const viewOrderDetail = (order) => {
      selectedOrder.value = order
      detailDialogVisible.value = true
    }
    
    const applyRefund = (order) => {
      selectedOrder.value = order
      refundForm.amount = order.amount
      refundForm.reason = ''
      refundForm.description = ''
      refundDialogVisible.value = true
    }
    
    const submitRefund = async () => {
      try {
        await refundFormRef.value.validate()
        
        isSubmitting.value = true
        
        const refundData = {
          order_id: selectedOrder.value.id,
          amount: refundForm.amount,
          reason: refundForm.reason,
          description: refundForm.description
        }
        
        await api.post('/orders/refund', refundData)
        
        ElMessage.success('退款申请已提交，请等待审核')
        refundDialogVisible.value = false
        loadOrders()
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('提交退款申请失败')
          console.error('提交退款申请失败:', error)
        }
      } finally {
        isSubmitting.value = false
      }
    }
    
    // 工具方法
    const getOrderStatusType = (status) => {
      const statusMap = {
        pending: 'warning',
        paid: 'success',
        cancelled: 'info',
        refunded: 'danger',
        failed: 'danger'
      }
      return statusMap[status] || 'info'
    }
    
    const getOrderStatusText = (status) => {
      const statusMap = {
        pending: '待支付',
        paid: '已支付',
        cancelled: '已取消',
        refunded: '已退款',
        failed: '支付失败'
      }
      return statusMap[status] || status
    }
    
    const getPaymentMethodType = (method) => {
      const methodMap = {
        alipay: 'primary',
        wechat: 'success'
      }
      return methodMap[method] || 'info'
    }
    
    const getPaymentMethodText = (method) => {
      const methodMap = {
        alipay: '支付宝',
        wechat: '微信支付'
      }
      return methodMap[method] || method
    }
    
    // 生命周期
    onMounted(() => {
      loadOrders()
    })
    
    return {
      orders,
      isLoading,
      orderStats,
      filters,
      pagination,
      detailDialogVisible,
      refundDialogVisible,
      selectedOrder,
      refundForm,
      refundRules,
      refundFormRef,
      isSubmitting,
      emptyText,
      loadOrders,
      loadOrderStats,
      applyFilters,
      resetFilters,
      refreshOrders,
      handleSizeChange,
      handleCurrentChange,
      payOrder,
      cancelOrder,
      viewOrderDetail,
      applyRefund,
      submitRefund,
      getOrderStatusType,
      getOrderStatusText,
      getPaymentMethodType,
      getPaymentMethodText,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.orders-container {
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
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

.order-stats {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.orders-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.amount {
  color: #f56c6c;
  font-weight: bold;
}

.pagination-wrapper {
  text-align: center;
  margin-top: 20px;
}

.order-detail {
  padding: 20px 0;
}

.dialog-footer {
  text-align: right;
}

.dialog-footer .el-button {
  margin-left: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .order-stats .el-col {
    margin-bottom: 10px;
  }
  
  .filter-card .el-col {
    margin-bottom: 10px;
  }
  
  .page-header h1 {
    font-size: 24px;
  }
}

/* 支付二维码样式 */
.payment-qr-container {
  text-align: center;
}

.payment-qr-container .order-info {
  margin-bottom: 20px;
}

.payment-qr-container .order-info h3 {
  margin-bottom: 15px;
  color: #303133;
  font-size: 16px;
}

.payment-qr-container .amount {
  color: #f56c6c;
  font-size: 18px;
  font-weight: bold;
}

.qr-code-wrapper {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.qr-code img {
  max-width: 200px;
  max-height: 200px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}

.qr-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #909399;
}

.qr-loading .el-icon {
  font-size: 24px;
  margin-bottom: 10px;
}

.payment-tips {
  margin: 20px 0;
}

.payment-actions {
  margin-top: 20px;
}

.payment-actions .el-button {
  margin: 0 10px;
}
</style> 