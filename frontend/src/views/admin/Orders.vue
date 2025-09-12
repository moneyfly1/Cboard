<template>
  <div class="admin-orders">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>订单管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportOrders">
              <el-icon><Download /></el-icon>
              导出订单
            </el-button>
            <el-button type="warning" @click="showBulkOperationsDialog = true">
              <el-icon><Operation /></el-icon>
              批量操作
            </el-button>
            <el-button type="info" @click="showStatisticsDialog = true">
              <el-icon><DataAnalysis /></el-icon>
              订单统计
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="searchForm.keyword" 
            placeholder="输入订单号、用户邮箱或用户名进行搜索"
            style="width: 300px;"
            clearable
            @keyup.enter="searchOrders"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchOrders">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 订单列表 -->
      <el-table :data="orders" style="width: 100%" v-loading="loading">
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="user.email" label="用户邮箱" />
        <el-table-column prop="package_name" label="套餐名称" />
        <el-table-column prop="amount" label="金额">
          <template #default="scope">
            ¥{{ scope.row.amount }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="支付方式" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column prop="paid_at" label="支付时间" />
        <el-table-column label="操作" width="280">
          <template #default="scope">
            <el-button size="small" @click="viewOrder(scope.row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click="markAsPaid(scope.row)"
              v-if="scope.row.status === 'pending'"
            >
              <el-icon><Check /></el-icon>
              标记已付
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="refundOrder(scope.row)"
              v-if="scope.row.status === 'paid'"
            >
              <el-icon><Money /></el-icon>
              退款
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="cancelOrder(scope.row)"
              v-if="scope.row.status === 'pending'"
            >
              <el-icon><Close /></el-icon>
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
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
    </el-card>

    <!-- 订单详情对话框 -->
    <el-dialog v-model="showOrderDialog" title="订单详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单号">{{ selectedOrder.order_no }}</el-descriptions-item>
        <el-descriptions-item label="用户邮箱">{{ selectedOrder.user?.email }}</el-descriptions-item>
        <el-descriptions-item label="套餐名称">{{ selectedOrder.package_name }}</el-descriptions-item>
        <el-descriptions-item label="金额">¥{{ selectedOrder.amount }}</el-descriptions-item>
        <el-descriptions-item label="支付方式">{{ selectedOrder.payment_method }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedOrder.status)">
            {{ getStatusText(selectedOrder.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ selectedOrder.created_at }}</el-descriptions-item>
        <el-descriptions-item label="支付时间">{{ selectedOrder.paid_at || '-' }}</el-descriptions-item>
      </el-descriptions>
      
      <div v-if="selectedOrder.payment_proof" style="margin-top: 20px;">
        <h4>支付凭证</h4>
        <img :src="selectedOrder.payment_proof" style="max-width: 100%;" />
      </div>
    </el-dialog>

    <!-- 批量操作对话框 -->
    <el-dialog v-model="showBulkOperationsDialog" title="批量操作" width="500px">
      <el-form :model="bulkForm" label-width="100px">
        <el-form-item label="操作类型">
          <el-select v-model="bulkForm.operation" placeholder="选择操作">
            <el-option label="批量标记已付" value="mark_paid" />
            <el-option label="批量取消" value="cancel" />
            <el-option label="批量退款" value="refund" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择订单">
          <el-checkbox-group v-model="bulkForm.selectedIds">
            <el-checkbox 
              v-for="order in orders" 
              :key="order.id" 
              :label="order.id"
            >
              {{ order.order_no }} - {{ order.user?.email }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBulkOperationsDialog = false">取消</el-button>
          <el-button type="primary" @click="executeBulkOperation" :loading="bulkLoading">
            执行操作
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 订单统计对话框 -->
    <el-dialog v-model="showStatisticsDialog" title="订单统计" width="600px">
      <div class="statistics-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.totalOrders }}</div>
              <div class="stat-label">总订单数</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.pendingOrders }}</div>
              <div class="stat-label">待支付</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.paidOrders }}</div>
              <div class="stat-label">已支付</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">¥{{ statistics.totalRevenue }}</div>
              <div class="stat-label">总收入</div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, Operation, DataAnalysis, View, Check, Money, Close, Search 
} from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminOrders',
  components: {
    Download, Operation, DataAnalysis, View, Check, Money, Close, Search
  },
  setup() {
    const api = useApi()
    const loading = ref(false)
    const orders = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showOrderDialog = ref(false)
    const showBulkOperationsDialog = ref(false)
    const showStatisticsDialog = ref(false)
    const selectedOrder = ref({})
    const bulkLoading = ref(false)

    const searchForm = reactive({
      keyword: '',
      status: ''
    })

    const bulkForm = reactive({
      operation: '',
      selectedIds: []
    })

    const statistics = reactive({
      totalOrders: 0,
      pendingOrders: 0,
      paidOrders: 0,
      totalRevenue: 0
    })

    const loadOrders = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        
        // 添加搜索参数
        if (searchForm.keyword) {
          params.search = searchForm.keyword
        }
        if (searchForm.status) {
          params.status = searchForm.status
        }
        
        const response = await api.get('/admin/orders', { params })
        console.log('订单API响应:', response)
        console.log('订单响应数据结构:', response.data)
        orders.value = response.data.data?.orders || response.data.items || []
        total.value = response.data.data?.total || response.data.total || 0
      } catch (error) {
        ElMessage.error('加载订单列表失败')
      } finally {
        loading.value = false
      }
    }

    const searchOrders = () => {
      currentPage.value = 1
      loadOrders()
    }

    const resetSearch = () => {
      Object.assign(searchForm, { 
        keyword: '', 
        status: '' 
      })
      searchOrders()
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      loadOrders()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadOrders()
    }

    const viewOrder = (order) => {
      selectedOrder.value = order
      showOrderDialog.value = true
    }

    const markAsPaid = async (order) => {
      try {
        await ElMessageBox.confirm('确定要将此订单标记为已支付吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.put(`/admin/orders/${order.id}`, { status: 'paid' })
        ElMessage.success('订单状态更新成功')
        loadOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }

    const cancelOrder = async (order) => {
      try {
        await ElMessageBox.confirm('确定要取消此订单吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.put(`/admin/orders/${order.id}`, { status: 'cancelled' })
        ElMessage.success('订单已取消')
        loadOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }

    const refundOrder = async (order) => {
      try {
        await ElMessageBox.confirm('确定要退款此订单吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.put(`/admin/orders/${order.id}`, { status: 'refunded' })
        ElMessage.success('订单已退款')
        loadOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }

    const exportOrders = async () => {
      try {
        const response = await api.get('/admin/orders/export', { 
          responseType: 'blob',
          params: searchForm 
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `orders_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('订单数据导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
      }
    }

    const executeBulkOperation = async () => {
      if (bulkForm.selectedIds.length === 0) {
        ElMessage.warning('请选择要操作的订单')
        return
      }

      bulkLoading.value = true
      try {
        const { operation } = bulkForm
        
        if (operation === 'mark_paid') {
          await api.post('/admin/orders/bulk-mark-paid', {
            order_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量标记已付成功')
        } else if (operation === 'cancel') {
          await api.post('/admin/orders/bulk-cancel', {
            order_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量取消成功')
        } else if (operation === 'refund') {
          await api.post('/admin/orders/bulk-refund', {
            order_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量退款成功')
        }
        
        showBulkOperationsDialog.value = false
        loadOrders()
        bulkForm.selectedIds = []
      } catch (error) {
        ElMessage.error('批量操作失败')
      } finally {
        bulkLoading.value = false
      }
    }

    const loadStatistics = async () => {
      try {
        const response = await api.get('/admin/orders/statistics')
        console.log('订单统计API响应:', response)
        console.log('订单统计数据:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          const statsData = response.data.data
          statistics.totalOrders = statsData.total_orders || 0
          statistics.pendingOrders = statsData.pending_orders || 0
          statistics.paidOrders = statsData.paid_orders || 0
          statistics.totalRevenue = statsData.total_revenue || 0
          console.log('更新后的统计数据:', statistics)
        } else {
          console.warn('订单统计API返回数据格式异常:', response.data)
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
        ElMessage.error('加载统计数据失败')
      }
    }

    const getStatusType = (status) => {
      const statusMap = {
        'pending': 'warning',
        'paid': 'success',
        'cancelled': 'danger',
        'refunded': 'info'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        'pending': '待支付',
        'paid': '已支付',
        'cancelled': '已取消',
        'refunded': '已退款'
      }
      return statusMap[status] || status
    }

    onMounted(() => {
      loadOrders()
      loadStatistics()
    })

    return {
      loading,
      orders,
      currentPage,
      pageSize,
      total,
      searchForm,
      showOrderDialog,
      selectedOrder,
      searchOrders,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      viewOrder,
      markAsPaid,
      cancelOrder,
      refundOrder,
      exportOrders,
      executeBulkOperation,
      loadStatistics,
      getStatusType,
      getStatusText,
      // 新增的响应式变量
      showBulkOperationsDialog,
      showStatisticsDialog,
      bulkForm,
      bulkLoading,
      statistics
    }
  }
}
</script>

<style scoped>
.admin-orders {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.statistics-content {
  padding: 20px 0;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

/* 移除所有输入框的圆角和阴影效果，设置为简单长方形 */
:deep(.el-input__wrapper) {
  border-radius: 0 !important;
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
  background-color: #ffffff !important;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 0 !important;
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
  background-color: #ffffff !important;
}

:deep(.el-input__inner) {
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  background-color: transparent !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc !important;
  box-shadow: none !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #1677ff !important;
  box-shadow: none !important;
}
</style> 