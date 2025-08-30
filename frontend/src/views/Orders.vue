<template>
  <div class="orders-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>订单管理</h1>
      <p>查看您的订单历史</p>
    </div>

    <!-- 订单统计 -->
    <el-card class="stats-card">
      <div class="stats-content">
        <div class="stat-item">
          <div class="stat-number">{{ orderStats.total }}</div>
          <div class="stat-label">总订单数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ orderStats.paid }}</div>
          <div class="stat-label">已支付</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ orderStats.pending }}</div>
          <div class="stat-label">待支付</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ orderStats.cancelled }}</div>
          <div class="stat-label">已取消</div>
        </div>
      </div>
    </el-card>

    <!-- 订单列表 -->
    <el-card class="orders-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-document"></i>
          订单列表
          <el-button 
            type="primary" 
            size="small" 
            @click="refreshOrders"
            :loading="loading"
          >
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </template>

      <el-table 
        :data="orders" 
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="order_no" label="订单号" width="180">
          <template #default="{ row }">
            <span class="order-no">{{ row.order_no }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="package_name" label="套餐名称" min-width="150">
          <template #default="{ row }">
            <div class="package-info">
              <span class="package-name">{{ row.package_name }}</span>
              <span class="package-duration">{{ row.package_duration }}天</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="amount" label="金额" width="120">
          <template #default="{ row }">
            <span class="amount">¥{{ row.amount }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="payment_method" label="支付方式" width="120">
          <template #default="{ row }">
            <span class="payment-method">{{ getPaymentMethodName(row.payment_method) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            <span>{{ formatTime(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="payment_time" label="支付时间" width="180">
          <template #default="{ row }">
            <span>{{ row.payment_time ? formatTime(row.payment_time) : '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="viewOrderDetail(row)"
            >
              详情
            </el-button>
            <el-button 
              v-if="row.status === 'pending'"
              type="warning" 
              size="small" 
              @click="cancelOrder(row.id)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && orders.length === 0" 
        description="暂无订单记录"
      >
        <el-button type="primary" @click="$router.push('/packages')">
          去购买套餐
        </el-button>
      </el-empty>
    </el-card>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="600px"
    >
      <div class="order-detail" v-if="selectedOrder">
        <div class="detail-item">
          <span class="label">订单号：</span>
          <span class="value">{{ selectedOrder.order_no }}</span>
        </div>
        <div class="detail-item">
          <span class="label">套餐名称：</span>
          <span class="value">{{ selectedOrder.package_name }}</span>
        </div>
        <div class="detail-item">
          <span class="label">套餐时长：</span>
          <span class="value">{{ selectedOrder.package_duration }} 天</span>
        </div>
        <div class="detail-item">
          <span class="label">设备限制：</span>
          <span class="value">{{ selectedOrder.package_device_limit }} 个</span>
        </div>
        <div class="detail-item">
          <span class="label">订单金额：</span>
          <span class="value amount">¥{{ selectedOrder.amount }}</span>
        </div>
        <div class="detail-item">
          <span class="label">支付方式：</span>
          <span class="value">{{ getPaymentMethodName(selectedOrder.payment_method) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">订单状态：</span>
          <span class="value">
            <el-tag :type="getStatusType(selectedOrder.status)">
              {{ getStatusName(selectedOrder.status) }}
            </el-tag>
          </span>
        </div>
        <div class="detail-item">
          <span class="label">创建时间：</span>
          <span class="value">{{ formatTime(selectedOrder.created_at) }}</span>
        </div>
        <div class="detail-item" v-if="selectedOrder.payment_time">
          <span class="label">支付时间：</span>
          <span class="value">{{ formatTime(selectedOrder.payment_time) }}</span>
        </div>
        <div class="detail-item" v-if="selectedOrder.expire_time">
          <span class="label">到期时间：</span>
          <span class="value">{{ formatTime(selectedOrder.expire_time) }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderAPI } from '@/utils/api'
import dayjs from 'dayjs'

export default {
  name: 'Orders',
  setup() {
    const loading = ref(false)
    const orders = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const detailDialogVisible = ref(false)
    const selectedOrder = ref(null)

    const orderStats = reactive({
      total: 0,
      paid: 0,
      pending: 0,
      cancelled: 0
    })

    // 获取订单列表
    const fetchOrders = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value
        }
        const response = await orderAPI.getUserOrders(params)
        orders.value = response.data.orders || []
        total.value = response.data.total || 0
        
        // 计算统计数据
        updateOrderStats()
      } catch (error) {
        ElMessage.error('获取订单列表失败')
      } finally {
        loading.value = false
      }
    }

    // 更新订单统计
    const updateOrderStats = () => {
      orderStats.total = orders.value.length
      orderStats.paid = orders.value.filter(o => o.status === 'paid').length
      orderStats.pending = orders.value.filter(o => o.status === 'pending').length
      orderStats.cancelled = orders.value.filter(o => o.status === 'cancelled').length
    }

    // 刷新订单列表
    const refreshOrders = () => {
      fetchOrders()
    }

    // 查看订单详情
    const viewOrderDetail = (order) => {
      selectedOrder.value = order
      detailDialogVisible.value = true
    }

    // 取消订单
    const cancelOrder = async (orderId) => {
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

        await orderAPI.cancelOrder(orderId)
        ElMessage.success('订单取消成功')
        
        // 重新获取订单列表
        await fetchOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('取消订单失败')
        }
      }
    }

    // 分页处理
    const handleSizeChange = (val) => {
      pageSize.value = val
      currentPage.value = 1
      fetchOrders()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      fetchOrders()
    }

    // 获取状态类型
    const getStatusType = (status) => {
      const types = {
        pending: 'warning',
        paid: 'success',
        cancelled: 'info',
        expired: 'danger'
      }
      return types[status] || 'info'
    }

    // 获取状态名称
    const getStatusName = (status) => {
      const names = {
        pending: '待支付',
        paid: '已支付',
        cancelled: '已取消',
        expired: '已过期'
      }
      return names[status] || '未知'
    }

    // 获取支付方式名称
    const getPaymentMethodName = (method) => {
      const names = {
        alipay: '支付宝',
        wechat: '微信支付',
        bank: '银行转账'
      }
      return names[method] || '未知'
    }

    // 格式化时间
    const formatTime = (time) => {
      if (!time) return '-'
      return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }

    onMounted(() => {
      fetchOrders()
    })

    return {
      loading,
      orders,
      currentPage,
      pageSize,
      total,
      detailDialogVisible,
      selectedOrder,
      orderStats,
      fetchOrders,
      refreshOrders,
      viewOrderDetail,
      cancelOrder,
      handleSizeChange,
      handleCurrentChange,
      getStatusType,
      getStatusName,
      getPaymentMethodName,
      formatTime
    }
  }
}
</script>

<style scoped>
.orders-container {
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

.stats-card {
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stats-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  padding: 1rem 0;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #1677ff;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.orders-card {
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-weight: 600;
}

.order-no {
  font-family: 'Courier New', monospace;
  color: #1677ff;
  font-weight: 500;
}

.package-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.package-name {
  font-weight: 500;
  color: #333;
}

.package-duration {
  font-size: 0.9rem;
  color: #666;
}

.amount {
  font-weight: 600;
  color: #1677ff;
}

.payment-method {
  color: #666;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

.order-detail {
  padding: 1rem 0;
}

.detail-item {
  display: flex;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-item .value {
  flex: 1;
  color: #333;
}

.detail-item .value.amount {
  color: #1677ff;
  font-weight: 600;
}

@media (max-width: 768px) {
  .orders-container {
    padding: 10px;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .detail-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .detail-item .label {
    width: auto;
  }
}
</style> 