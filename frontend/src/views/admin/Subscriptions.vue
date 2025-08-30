<template>
  <div class="admin-subscriptions">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>订阅管理</span>
          <el-button type="primary" @click="showAddSubscriptionDialog = true">
            添加订阅
          </el-button>
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
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button size="small" @click="editSubscription(scope.row)">编辑</el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="resetSubscription(scope.row)"
            >重置</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteSubscription(scope.row)"
            >删除</el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="viewDevices(scope.row)"
            >设备</el-button>
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
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminSubscriptions',
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
    const editingSubscription = ref(null)
    const subscriptionFormRef = ref()

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
      getStatusType,
      getStatusText
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

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 