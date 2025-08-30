<template>
  <div class="admin-orders">
    <el-card>
      <template #header>
        <span>订单管理</span>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="订单号">
          <el-input v-model="searchForm.order_no" placeholder="搜索订单号" />
        </el-form-item>
        <el-form-item label="用户邮箱">
          <el-input v-model="searchForm.user_email" placeholder="搜索用户邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态">
            <el-option label="全部" value="" />
            <el-option label="待支付" value="pending" />
            <el-option label="已支付" value="paid" />
            <el-option label="已取消" value="cancelled" />
            <el-option label="已退款" value="refunded" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchOrders">搜索</el-button>
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
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewOrder(scope.row)">查看</el-button>
            <el-button 
              size="small" 
              type="success" 
              @click="markAsPaid(scope.row)"
              v-if="scope.row.status === 'pending'"
            >标记已付</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="cancelOrder(scope.row)"
              v-if="scope.row.status === 'pending'"
            >取消</el-button>
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
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminOrders',
  setup() {
    const api = useApi()
    const loading = ref(false)
    const orders = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showOrderDialog = ref(false)
    const selectedOrder = ref({})

    const searchForm = reactive({
      order_no: '',
      user_email: '',
      status: '',
      date_range: []
    })

    const loadOrders = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          ...searchForm
        }
        
        // 处理日期范围
        if (searchForm.date_range && searchForm.date_range.length === 2) {
          params.start_date = searchForm.date_range[0]
          params.end_date = searchForm.date_range[1]
        }
        
        const response = await api.get('/admin/orders', { params })
        orders.value = response.data.items
        total.value = response.data.total
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
        order_no: '', 
        user_email: '', 
        status: '', 
        date_range: [] 
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
        await api.put(`/admin/orders/${order.id}/status`, { status: 'paid' })
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
        await api.put(`/admin/orders/${order.id}/status`, { status: 'cancelled' })
        ElMessage.success('订单已取消')
        loadOrders()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
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
      getStatusType,
      getStatusText
    }
  }
}
</script>

<style scoped>
.admin-orders {
  padding: 20px;
}

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 