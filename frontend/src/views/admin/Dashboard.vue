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
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近注册用户</span>
          </template>
          <el-table :data="recentUsers" style="width: 100%">
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="created_at" label="注册时间" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : 'warning'">
                  {{ scope.row.status === 'active' ? '活跃' : '待激活' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近订单</span>
          </template>
          <el-table :data="recentOrders" style="width: 100%">
            <el-table-column prop="order_no" label="订单号" />
            <el-table-column prop="amount" label="金额" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="getOrderStatusType(scope.row.status)">
                  {{ getOrderStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminDashboard',
  setup() {
    const api = useApi()
    const stats = ref({
      totalUsers: 0,
      activeSubscriptions: 0,
      totalOrders: 0,
      totalRevenue: 0
    })
    const recentUsers = ref([])
    const recentOrders = ref([])

    const loadStats = async () => {
      try {
        const response = await api.get('/admin/stats')
        console.log('统计API响应:', response)
        console.log('统计响应数据结构:', response.data)
        stats.value = response.data.data || response.data
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    const loadRecentUsers = async () => {
      try {
        const response = await api.get('/admin/users/recent')
        console.log('最近用户API响应:', response)
        console.log('最近用户响应数据结构:', response.data)
        recentUsers.value = response.data.data?.users || response.data.users || response.data
      } catch (error) {
        console.error('加载最近用户失败:', error)
      }
    }

    const loadRecentOrders = async () => {
      try {
        const response = await api.get('/admin/orders/recent')
        console.log('最近订单API响应:', response)
        console.log('最近订单响应数据结构:', response.data)
        recentOrders.value = response.data.data?.orders || response.data.orders || response.data
      } catch (error) {
        console.error('加载最近订单失败:', error)
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

    onMounted(() => {
      loadStats()
      loadRecentUsers()
      loadRecentOrders()
    })

    return {
      stats,
      recentUsers,
      recentOrders,
      getOrderStatusType,
      getOrderStatusText
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
</style> 