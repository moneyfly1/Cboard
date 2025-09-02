<template>
  <div class="admin-subscriptions">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>订阅管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportSubscriptions">
              <el-icon><Download /></el-icon>
              导出订阅
            </el-button>
            <el-button type="warning" @click="showBulkOperationsDialog = true">
              <el-icon><Operation /></el-icon>
              批量操作
            </el-button>
            <el-button type="info" @click="showStatisticsDialog = true">
              <el-icon><DataAnalysis /></el-icon>
              订阅统计
            </el-button>
            <el-button type="primary" @click="showAddSubscriptionDialog = true">
              <el-icon><Plus /></el-icon>
              添加订阅
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户邮箱">
          <el-input v-model="searchForm.user_email" placeholder="搜索用户邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态">
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="过期" value="expired" />
            <el-option label="暂停" value="paused" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchSubscriptions">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 订阅列表 -->
      <el-table :data="subscriptions" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="user.email" label="用户邮箱" />
        <el-table-column prop="subscription_url" label="订阅地址" width="200">
          <template #default="scope">
            <el-input 
              :value="scope.row.subscription_url" 
              readonly 
              size="small"
            >
              <template #append>
                <el-button @click="copyUrl(scope.row.subscription_url)">复制</el-button>
              </template>
            </el-input>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="expires_at" label="到期时间" />
        <el-table-column prop="device_count" label="设备数" width="100" />
        <el-table-column prop="device_limit" label="设备限制" width="100" />
        <el-table-column label="操作" width="300">
          <template #default="scope">
            <el-button size="small" @click="editSubscription(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click="renewSubscription(scope.row)"
              v-if="scope.row.status === 'expired'"
            >
              <el-icon><Refresh /></el-icon>
              续费
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="resetSubscription(scope.row)"
            >
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="viewDevices(scope.row)"
            >
              <el-icon><Monitor /></el-icon>
              设备
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteSubscription(scope.row)"
            >
              <el-icon><Delete /></el-icon>
              删除
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

    <!-- 添加/编辑订阅对话框 -->
    <el-dialog 
      v-model="showAddSubscriptionDialog" 
      :title="editingSubscription ? '编辑订阅' : '添加订阅'"
      width="500px"
    >
      <el-form :model="subscriptionForm" :rules="subscriptionRules" ref="subscriptionFormRef" label-width="100px">
        <el-form-item label="用户" prop="user_id">
          <el-select v-model="subscriptionForm.user_id" placeholder="选择用户" filterable>
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="user.email" 
              :value="user.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="到期时间" prop="expires_at">
          <el-date-picker
            v-model="subscriptionForm.expires_at"
            type="datetime"
            placeholder="选择到期时间"
          />
        </el-form-item>
        <el-form-item label="设备限制" prop="device_limit">
          <el-input-number v-model="subscriptionForm.device_limit" :min="1" :max="10" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="subscriptionForm.status" placeholder="选择状态">
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="过期" value="expired" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddSubscriptionDialog = false">取消</el-button>
          <el-button type="primary" @click="saveSubscription">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 设备列表对话框 -->
    <el-dialog v-model="showDevicesDialog" title="设备列表" width="800px">
      <el-table :data="devices" style="width: 100%">
        <el-table-column prop="device_id" label="设备ID" />
        <el-table-column prop="device_name" label="设备名称" />
        <el-table-column prop="device_type" label="设备类型" />
        <el-table-column prop="ip_address" label="IP地址" />
        <el-table-column prop="last_seen" label="最后访问" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button 
              size="small" 
              type="danger" 
              @click="removeDevice(scope.row)"
            >移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 批量操作对话框 -->
    <el-dialog v-model="showBulkOperationsDialog" title="批量操作" width="500px">
      <el-form :model="bulkForm" label-width="100px">
        <el-form-item label="操作类型">
          <el-select v-model="bulkForm.operation" placeholder="选择操作">
            <el-option label="批量续费" value="renew" />
            <el-option label="批量重置" value="reset" />
            <el-option label="批量删除" value="delete" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="续费天数" v-if="bulkForm.operation === 'renew'">
          <el-input-number v-model="bulkForm.days" :min="1" :max="365" />
        </el-form-item>
        
        <el-form-item label="选择订阅">
          <el-checkbox-group v-model="bulkForm.selectedIds">
            <el-checkbox 
              v-for="sub in subscriptions" 
              :key="sub.id" 
              :label="sub.id"
            >
              {{ sub.user?.email }} - {{ sub.subscription_url?.substring(0, 20) }}...
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

    <!-- 订阅统计对话框 -->
    <el-dialog v-model="showStatisticsDialog" title="订阅统计" width="600px">
      <div class="statistics-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.totalSubscriptions }}</div>
              <div class="stat-label">总订阅数</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.activeSubscriptions }}</div>
              <div class="stat-label">活跃订阅</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.expiredSubscriptions }}</div>
              <div class="stat-label">过期订阅</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.totalDevices }}</div>
              <div class="stat-label">总设备数</div>
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
  Download, Operation, DataAnalysis, Plus, Edit, 
  Refresh, RefreshLeft, Monitor, Delete 
} from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminSubscriptions',
  components: {
    Download, Operation, DataAnalysis, Plus, Edit, 
    Refresh, RefreshLeft, Monitor, Delete
  },
  setup() {
    const api = useApi()
    const loading = ref(false)
    const subscriptions = ref([])
    const users = ref([])
    const devices = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showAddSubscriptionDialog = ref(false)
    const showDevicesDialog = ref(false)
    const showBulkOperationsDialog = ref(false)
    const showStatisticsDialog = ref(false)
    const editingSubscription = ref(null)
    const subscriptionFormRef = ref()
    const bulkLoading = ref(false)

    const searchForm = reactive({
      user_email: '',
      status: ''
    })

    const subscriptionForm = reactive({
      user_id: '',
      expires_at: '',
      device_limit: 3,
      status: 'active'
    })

    const bulkForm = reactive({
      operation: '',
      days: 30,
      selectedIds: []
    })

    const statistics = reactive({
      totalSubscriptions: 0,
      activeSubscriptions: 0,
      expiredSubscriptions: 0,
      totalDevices: 0
    })

    const subscriptionRules = {
      user_id: [
        { required: true, message: '请选择用户', trigger: 'change' }
      ],
      expires_at: [
        { required: true, message: '请选择到期时间', trigger: 'change' }
      ],
      device_limit: [
        { required: true, message: '请设置设备限制', trigger: 'blur' }
      ],
      status: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }

    const loadSubscriptions = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          ...searchForm
        }
        const response = await api.get('/admin/subscriptions', { params })
        subscriptions.value = response.data.items
        total.value = response.data.total
      } catch (error) {
        ElMessage.error('加载订阅列表失败')
      } finally {
        loading.value = false
      }
    }

    const loadUsers = async () => {
      try {
        const response = await api.get('/admin/users')
        users.value = response.data.items
      } catch (error) {
        ElMessage.error('加载用户列表失败')
      }
    }

    const searchSubscriptions = () => {
      currentPage.value = 1
      loadSubscriptions()
    }

    const resetSearch = () => {
      Object.assign(searchForm, { user_email: '', status: '' })
      searchSubscriptions()
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      loadSubscriptions()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadSubscriptions()
    }

    const editSubscription = (subscription) => {
      editingSubscription.value = subscription
      Object.assign(subscriptionForm, {
        user_id: subscription.user_id,
        expires_at: subscription.expires_at,
        device_limit: subscription.device_limit,
        status: subscription.status
      })
      showAddSubscriptionDialog.value = true
    }

    const saveSubscription = async () => {
      try {
        await subscriptionFormRef.value.validate()
        if (editingSubscription.value) {
          await api.put(`/admin/subscriptions/${editingSubscription.value.id}`, subscriptionForm)
          ElMessage.success('订阅更新成功')
        } else {
          await api.post('/admin/subscriptions', subscriptionForm)
          ElMessage.success('订阅创建成功')
        }
        showAddSubscriptionDialog.value = false
        loadSubscriptions()
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }

    const deleteSubscription = async (subscription) => {
      try {
        await ElMessageBox.confirm('确定要删除这个订阅吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.delete(`/admin/subscriptions/${subscription.id}`)
        ElMessage.success('订阅删除成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const resetSubscription = async (subscription) => {
      try {
        await ElMessageBox.confirm('确定要重置这个订阅吗？这将清空所有设备记录', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.post(`/admin/subscriptions/${subscription.id}/reset`)
        ElMessage.success('订阅重置成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重置失败')
        }
      }
    }

    const viewDevices = async (subscription) => {
      try {
        const response = await api.get(`/admin/subscriptions/${subscription.id}/devices`)
        devices.value = response.data
        showDevicesDialog.value = true
      } catch (error) {
        ElMessage.error('加载设备列表失败')
      }
    }

    const removeDevice = async (device) => {
      try {
        await ElMessageBox.confirm('确定要移除这个设备吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await api.delete(`/admin/devices/${device.id}`)
        ElMessage.success('设备移除成功')
        viewDevices({ id: device.subscription_id })
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('移除失败')
        }
      }
    }

    const copyUrl = (url) => {
      navigator.clipboard.writeText(url).then(() => {
        ElMessage.success('订阅地址已复制到剪贴板')
      }).catch(() => {
        ElMessage.error('复制失败')
      })
    }

    const renewSubscription = async (subscription) => {
      try {
        const { value: days } = await ElMessageBox.prompt(
          '请输入续费天数',
          '续费订阅',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            inputType: 'number',
            inputValue: 30,
            inputValidator: (value) => {
              if (value < 1 || value > 365) {
                return '天数必须在1-365之间'
              }
              return true
            }
          }
        )
        
        await api.post(`/admin/subscriptions/${subscription.id}/renew`, { days: parseInt(days) })
        ElMessage.success('订阅续费成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('续费失败')
        }
      }
    }

    const exportSubscriptions = async () => {
      try {
        const response = await api.get('/admin/subscriptions/export', { 
          responseType: 'blob',
          params: searchForm 
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `subscriptions_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('订阅数据导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
      }
    }

    const executeBulkOperation = async () => {
      if (bulkForm.selectedIds.length === 0) {
        ElMessage.warning('请选择要操作的订阅')
        return
      }

      bulkLoading.value = true
      try {
        const { operation, days } = bulkForm
        
        if (operation === 'renew') {
          await api.post('/admin/subscriptions/bulk-renew', {
            subscription_ids: bulkForm.selectedIds,
            days
          })
          ElMessage.success('批量续费成功')
        } else if (operation === 'reset') {
          await api.post('/admin/subscriptions/bulk-reset', {
            subscription_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量重置成功')
        } else if (operation === 'delete') {
          await ElMessageBox.confirm(
            `确定要删除选中的 ${bulkForm.selectedIds.length} 个订阅吗？`,
            '确认删除',
            { type: 'warning' }
          )
          await api.post('/admin/subscriptions/bulk-delete', {
            subscription_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量删除成功')
        }
        
        showBulkOperationsDialog.value = false
        loadSubscriptions()
        bulkForm.selectedIds = []
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量操作失败')
        }
      } finally {
        bulkLoading.value = false
      }
    }

    const loadStatistics = async () => {
      try {
        const response = await api.get('/admin/subscriptions/statistics')
        Object.assign(statistics, response.data)
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }

    const getStatusType = (status) => {
      const statusMap = {
        'active': 'success',
        'expired': 'danger',
        'paused': 'warning'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        'active': '活跃',
        'expired': '过期',
        'paused': '暂停'
      }
      return statusMap[status] || status
    }

    onMounted(() => {
      loadSubscriptions()
      loadUsers()
      loadStatistics()
    })

    return {
      loading,
      subscriptions,
      users,
      devices,
      currentPage,
      pageSize,
      total,
      searchForm,
      showAddSubscriptionDialog,
      showDevicesDialog,
      editingSubscription,
      subscriptionForm,
      subscriptionFormRef,
      subscriptionRules,
      searchSubscriptions,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      editSubscription,
      saveSubscription,
      deleteSubscription,
      resetSubscription,
      viewDevices,
      removeDevice,
      copyUrl,
      renewSubscription,
      exportSubscriptions,
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
.admin-subscriptions {
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
</style> 