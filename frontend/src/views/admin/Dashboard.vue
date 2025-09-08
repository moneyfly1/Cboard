<template>
  <div class="admin-dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalUsers }}</div>
            <div class="stat-label">总用户数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.activeSubscriptions }}</div>
            <div class="stat-label">活跃订阅</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalOrders }}</div>
            <div class="stat-label">总订单数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalRevenue }}</div>
            <div class="stat-label">总收入(元)</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近注册用户</span>
              <el-badge :value="recentUsers.length" class="item-count" />
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="recentUsers.slice(0, 10)" 
              style="width: 100%"
              :show-header="false"
              size="small"
            >
              <el-table-column width="40">
                <template #default="scope">
                  <el-avatar :size="24" class="user-avatar">
                    {{ scope.row.username?.charAt(0)?.toUpperCase() || 'U' }}
                  </el-avatar>
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="scope">
                  <div class="user-info">
                    <div class="user-name">{{ scope.row.username }}</div>
                    <div class="user-email">{{ scope.row.email }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="80" align="right">
                <template #default="scope">
                  <el-tag 
                    :type="scope.row.status === 'active' ? 'success' : 'warning'" 
                    size="small"
                    effect="plain"
                  >
                    {{ scope.row.status === 'active' ? '活跃' : '待激活' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近订单</span>
              <el-badge :value="recentOrders.length" class="item-count" />
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="recentOrders.slice(0, 10)" 
              style="width: 100%"
              :show-header="false"
              size="small"
            >
              <el-table-column width="40">
                <template #default="scope">
                  <div class="order-icon">
                    <el-icon><ShoppingCart /></el-icon>
                  </div>
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="scope">
                  <div class="order-info">
                    <div class="order-no">{{ scope.row.order_no }}</div>
                    <div class="order-amount">¥{{ scope.row.amount }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="80" align="right">
                <template #default="scope">
                  <el-tag 
                    :type="getOrderStatusType(scope.row.status)" 
                    size="small"
                    effect="plain"
                  >
                    {{ getOrderStatusText(scope.row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">异常客户</span>
              <div class="header-actions">
                <el-badge :value="abnormalUsers.length" class="item-count" />
                <el-button type="text" @click="goToAbnormalUsers" class="view-all-btn">
                  查看全部
                  <el-icon><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          <div class="table-container">
            <el-table 
              :data="abnormalUsers.slice(0, 10)" 
              style="width: 100%"
              :show-header="false"
              size="small"
            >
              <el-table-column width="40">
                <template #default="scope">
                  <div class="abnormal-icon">
                    <el-icon><Warning /></el-icon>
                  </div>
                </template>
              </el-table-column>
              <el-table-column>
                <template #default="scope">
                  <div class="abnormal-info">
                    <div class="abnormal-user">{{ scope.row.username }}</div>
                    <div class="abnormal-email">{{ scope.row.email }}</div>
                  </div>
                </template>
              </el-table-column>
              <el-table-column width="80" align="right">
                <template #default="scope">
                  <el-tag 
                    :type="getAbnormalTypeTag(scope.row.abnormal_type)" 
                    size="small"
                    effect="plain"
                  >
                    {{ scope.row.abnormal_count }}次
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApi } from '@/utils/api'
import { ArrowRight, ShoppingCart, Warning } from '@element-plus/icons-vue'

export default {
  name: 'AdminDashboard',
  components: {
    ArrowRight,
    ShoppingCart,
    Warning
  },
  setup() {
    const api = useApi()
    const router = useRouter()
    const stats = ref({
      totalUsers: 0,
      activeSubscriptions: 0,
      totalOrders: 0,
      totalRevenue: 0
    })
    const recentUsers = ref([])
    const recentOrders = ref([])
    const abnormalUsers = ref([])

    const loadStats = async () => {
      try {
        const response = await api.get('/admin/stats')
        console.log('统计API响应:', response)
        console.log('统计响应数据结构:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          const data = response.data.data
          stats.value = {
            totalUsers: data.totalUsers || 0,
            activeSubscriptions: data.activeSubscriptions || 0,
            totalOrders: data.totalOrders || 0,
            totalRevenue: data.totalRevenue || 0
          }
        } else {
          console.warn('统计数据格式异常:', response.data)
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    const loadRecentUsers = async () => {
      try {
        const response = await api.get('/admin/users/recent')
        console.log('最近用户API响应:', response)
        console.log('最近用户响应数据结构:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          recentUsers.value = response.data.data
        } else {
          console.warn('最近用户数据格式异常:', response.data)
          recentUsers.value = []
        }
      } catch (error) {
        console.error('加载最近用户失败:', error)
        recentUsers.value = []
      }
    }

    const loadRecentOrders = async () => {
      try {
        const response = await api.get('/admin/orders/recent')
        console.log('最近订单API响应:', response)
        console.log('最近订单响应数据结构:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          recentOrders.value = response.data.data
        } else {
          console.warn('最近订单数据格式异常:', response.data)
          recentOrders.value = []
        }
      } catch (error) {
        console.error('加载最近订单失败:', error)
        recentOrders.value = []
      }
    }

    const loadAbnormalUsers = async () => {
      try {
        const response = await api.get('/admin/users/abnormal')
        console.log('异常用户API响应:', response)
        
        if (response.data && response.data.success && response.data.data) {
          // 只显示前5个异常用户
          abnormalUsers.value = response.data.data.slice(0, 5)
        } else {
          console.warn('异常用户数据格式异常:', response.data)
          abnormalUsers.value = []
        }
      } catch (error) {
        console.error('加载异常用户失败:', error)
        abnormalUsers.value = []
      }
    }

    const getOrderStatusType = (status) => {
      const statusMap = {
        'pending': 'warning',
        'paid': 'success',
        'cancelled': 'danger',
        'refunded': 'info'
      }
      return statusMap[status] || 'info'
    }

    const getOrderStatusText = (status) => {
      const statusMap = {
        'pending': '待支付',
        'paid': '已支付',
        'cancelled': '已取消',
        'refunded': '已退款'
      }
      return statusMap[status] || status
    }

    const getAbnormalTypeTag = (type) => {
      const typeMap = {
        'frequent_reset': 'warning',
        'frequent_subscription': 'danger',
        'multiple_abnormal': 'error'
      }
      return typeMap[type] || 'info'
    }

    const getAbnormalTypeText = (type) => {
      const typeMap = {
        'frequent_reset': '频繁重置',
        'frequent_subscription': '频繁订阅',
        'multiple_abnormal': '多重异常'
      }
      return typeMap[type] || type
    }

    const goToAbnormalUsers = () => {
      router.push('/admin/abnormal-users')
    }

    onMounted(() => {
      loadStats()
      loadRecentUsers()
      loadRecentOrders()
      loadAbnormalUsers()
    })

    return {
      stats,
      recentUsers,
      recentOrders,
      abnormalUsers,
      getOrderStatusType,
      getOrderStatusText,
      getAbnormalTypeTag,
      getAbnormalTypeText,
      goToAbnormalUsers
    }
  }
}
</script>

<style scoped>
.admin-dashboard {
  padding: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 2em;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  margin-top: 10px;
  color: #666;
}

/* 仪表盘卡片样式 */
.dashboard-card {
  height: 400px;
  display: flex;
  flex-direction: column;
}

.dashboard-card .el-card__body {
  flex: 1;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.card-title {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-count {
  margin-right: 8px;
}

.view-all-btn {
  padding: 4px 8px;
  font-size: 12px;
  color: #409eff;
}

.view-all-btn:hover {
  color: #66b1ff;
}

/* 表格容器 */
.table-container {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.table-container .el-table {
  height: 100%;
}

.table-container .el-table__body-wrapper {
  max-height: 300px;
  overflow-y: auto;
}

/* 用户信息样式 */
.user-avatar {
  background-color: #409eff;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.user-info {
  padding-left: 8px;
}

.user-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  line-height: 1.2;
}

.user-email {
  color: #909399;
  font-size: 12px;
  line-height: 1.2;
  margin-top: 2px;
}

/* 订单信息样式 */
.order-icon {
  width: 24px;
  height: 24px;
  background-color: #67c23a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
}

.order-info {
  padding-left: 8px;
}

.order-no {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  line-height: 1.2;
}

.order-amount {
  color: #e6a23c;
  font-size: 12px;
  line-height: 1.2;
  margin-top: 2px;
  font-weight: 600;
}

/* 异常用户信息样式 */
.abnormal-icon {
  width: 24px;
  height: 24px;
  background-color: #f56c6c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
}

.abnormal-info {
  padding-left: 8px;
}

.abnormal-user {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  line-height: 1.2;
}

.abnormal-email {
  color: #909399;
  font-size: 12px;
  line-height: 1.2;
  margin-top: 2px;
}

/* 表格行样式 */
.table-container .el-table__row {
  height: 48px;
}

.table-container .el-table__row:hover {
  background-color: #f5f7fa;
}

/* 标签样式优化 */
.table-container .el-tag {
  border-radius: 12px;
  font-size: 11px;
  padding: 2px 8px;
  height: 20px;
  line-height: 16px;
}

/* 滚动条样式 */
.table-container .el-table__body-wrapper::-webkit-scrollbar {
  width: 4px;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 2px;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 2px;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 