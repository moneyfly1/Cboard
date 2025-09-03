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

      <!-- 搜索和排序栏 -->
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
            <el-option label="未配置" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item label="订阅类型">
          <el-select v-model="searchForm.subscription_type" placeholder="选择类型">
            <el-option label="全部" value="" />
            <el-option label="V2Ray" value="v2ray" />
            <el-option label="Clash" value="clash" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="searchForm.sort_by" placeholder="选择排序">
            <el-option label="默认" value="" />
            <el-option label="用户名" value="username" />
            <el-option label="到期时间" value="expires_at" />
            <el-option label="设备数量" value="device_count" />
            <el-option label="创建时间" value="created_at" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchSubscriptions">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 订阅列表 -->
      <el-table :data="subscriptions" style="width: 100%" v-loading="loading" row-key="id">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="用户信息" width="200">
          <template #default="scope">
            <div class="user-info">
              <div class="username">{{ scope.row.user.username }}</div>
              <div class="email">{{ scope.row.user.email }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订阅类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.subscription_type === 'v2ray' ? 'primary' : 'success'" size="small">
              {{ scope.row.subscription_type === 'v2ray' ? 'V2Ray' : 'Clash' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订阅地址" min-width="300">
          <template #default="scope">
            <div v-if="scope.row.is_placeholder" class="placeholder-url">
              <el-tag type="info" size="small">未配置</el-tag>
            </div>
            <el-input 
              v-else
              :value="scope.row.full_url" 
              readonly 
              size="small"
              class="subscription-url"
            >
              <template #append>
                <el-button @click="copyUrl(scope.row.full_url)" size="small">复制</el-button>
              </template>
            </el-input>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="180">
          <template #default="scope">
            <el-date-picker
              v-model="scope.row.expires_at"
              type="datetime"
              placeholder="选择到期时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              size="small"
              @change="(value) => updateExpireTime(scope.row.id, value)"
              style="width: 100%"
            />
          </template>
        </el-table-column>
        <el-table-column label="设备管理" width="220">
          <template #default="scope">
            <div class="device-info">
              <div class="device-count">
                <el-tag :type="scope.row.device_count >= scope.row.device_limit ? 'danger' : 'success'" size="small">
                  {{ scope.row.device_count }}/{{ scope.row.device_limit }}
                </el-tag>
              </div>
              <div class="device-limit-edit">
                <el-input-number
                  v-model="scope.row.device_limit"
                  :min="1"
                  :max="10"
                  size="small"
                  @change="(value) => updateDeviceLimit(scope.row.id, value)"
                  :disabled="scope.row.is_placeholder"
                  style="width: 80px"
                />
              </div>
              <div class="device-actions">
                <el-button 
                  size="small" 
                  type="info" 
                  @click="viewDevices(scope.row)"
                  :disabled="scope.row.device_count === 0 || scope.row.is_placeholder"
                >
                  <el-icon><Monitor /></el-icon>
                  设备
                </el-button>
                <el-button 
                  size="small" 
                  type="warning" 
                  @click="clearAllDevices(scope.row)"
                  :disabled="scope.row.device_count === 0 || scope.row.is_placeholder"
                >
                  <el-icon><Delete /></el-icon>
                  清空
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="scope">
            <div class="action-buttons">
              <el-button 
                size="small" 
                type="success" 
                @click="renewSubscription(scope.row)"
                v-if="scope.row.status === 'expired'"
                :disabled="scope.row.is_placeholder"
              >
                <el-icon><Refresh /></el-icon>
                续费
              </el-button>
              <el-button 
                size="small" 
                type="warning" 
                @click="resetSubscription(scope.row)"
                :disabled="scope.row.is_placeholder"
              >
                <el-icon><RefreshLeft /></el-icon>
                重置
              </el-button>
              <el-button 
                size="small" 
                type="info" 
                @click="resetUserAllSubscriptions(scope.row.user.id)"
                v-if="!scope.row.is_placeholder"
              >
                <el-icon><RefreshLeft /></el-icon>
                重置全部
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteUserAllData(scope.row.user.id)"
                v-if="!scope.row.is_placeholder"
              >
                <el-icon><Delete /></el-icon>
                删除用户
              </el-button>
            </div>
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

    <!-- 设备管理对话框 -->
    <el-dialog 
      v-model="showDevicesDialog" 
      title="设备管理" 
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="currentSubscription" class="devices-dialog-content">
        <div class="subscription-info">
          <h4>订阅信息</h4>
          <p><strong>用户:</strong> {{ currentSubscription.user.username }} ({{ currentSubscription.user.email }})</p>
          <p><strong>订阅类型:</strong> {{ currentSubscription.subscription_type === 'v2ray' ? 'V2Ray' : 'Clash' }}</p>
          <p><strong>设备限制:</strong> {{ currentSubscription.device_count }}/{{ currentSubscription.device_limit }}</p>
        </div>
        
        <div class="devices-actions">
          <el-button type="warning" @click="clearAllDevices(currentSubscription)" :loading="clearingDevices">
            <el-icon><Delete /></el-icon>
            清空所有设备
          </el-button>
          <el-button type="info" @click="refreshDevices">
            <el-icon><Refresh /></el-icon>
            刷新设备列表
          </el-button>
        </div>
        
        <el-table :data="devices" style="width: 100%" v-loading="devicesLoading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="设备名称" width="150" />
          <el-table-column prop="type" label="设备类型" width="100">
            <template #default="scope">
              <el-tag :type="getDeviceTypeColor(scope.row.type)" size="small">
                {{ scope.row.type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ip" label="IP地址" width="120" />
          <el-table-column prop="last_access" label="最后访问" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.last_access) }}
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                {{ scope.row.is_active ? '活跃' : '离线' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button 
                size="small" 
                type="danger" 
                @click="removeDevice(scope.row)"
                :loading="removingDevice === scope.row.id"
              >
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="devices-footer">
          <p>共 {{ devices.length }} 个设备</p>
        </div>
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
    const currentSubscription = ref(null)
    const devicesLoading = ref(false)
    const removingDevice = ref(null)
    const clearingDevices = ref(false)

    const searchForm = reactive({
      user_email: '',
      status: '',
      subscription_type: '',
      sort_by: ''
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
        
        console.log('=== 开始加载订阅列表 ===')
        console.log('请求参数:', params)
        
        const response = await api.get('/admin/subscriptions', { params })
        console.log('订阅列表响应:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          const responseData = response.data.data
          subscriptions.value = responseData.subscriptions || []
          total.value = responseData.total || 0
          console.log('订阅列表加载成功，共', subscriptions.value.length, '个订阅')
          console.log('前3个订阅示例:', subscriptions.value.slice(0, 3))
        } else {
          console.warn('订阅列表响应格式异常:', response.data)
          subscriptions.value = []
          total.value = 0
          if (response.data?.message) {
            ElMessage.error(`加载订阅列表失败: ${response.data.message}`)
          }
        }
      } catch (error) {
        console.error('加载订阅列表失败:', error)
        ElMessage.error('加载订阅列表失败')
        subscriptions.value = []
        total.value = 0
      } finally {
        loading.value = false
      }
    }

    const loadUsers = async () => {
      try {
        const response = await api.get('/admin/users')
        console.log('订阅管理页面 - 加载用户列表响应:', response.data)
        
        if (response.data && response.data.success && response.data.data) {
          const responseData = response.data.data
          users.value = responseData.users || []
          console.log('订阅管理页面 - 用户列表加载成功，共', users.value.length, '个用户')
        } else {
          console.warn('订阅管理页面 - 用户列表响应格式异常:', response.data)
          users.value = []
          if (response.data?.message) {
            ElMessage.error(`加载用户列表失败: ${response.data.message}`)
          }
        }
      } catch (error) {
        console.error('订阅管理页面 - 加载用户列表失败:', error)
        ElMessage.error('加载用户列表失败')
        users.value = []
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
      currentSubscription.value = subscription
      showDevicesDialog.value = true
      await loadSubscriptionDevices(subscription.id)
    }

    const loadSubscriptionDevices = async (subscriptionId) => {
      devicesLoading.value = true
      try {
        const response = await api.get(`/admin/subscriptions/${subscriptionId}/devices`)
        if (response.data && response.data.success && response.data.data) {
          devices.value = response.data.data.devices || []
        } else {
          devices.value = []
          ElMessage.error('加载设备列表失败')
        }
      } catch (error) {
        console.error('加载设备列表失败:', error)
        ElMessage.error('加载设备列表失败')
        devices.value = []
      } finally {
        devicesLoading.value = false
      }
    }

    const removeDevice = async (device) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除设备 "${device.name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        removingDevice.value = device.id
        const response = await api.delete(`/admin/subscriptions/${currentSubscription.value.id}/devices/${device.id}`)
        
        if (response.data && response.data.success) {
          ElMessage.success('设备删除成功')
          // 重新加载设备列表和订阅列表
          await loadSubscriptionDevices(currentSubscription.value.id)
          await loadSubscriptions()
        } else {
          ElMessage.error('设备删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除设备失败:', error)
          ElMessage.error('删除设备失败')
        }
      } finally {
        removingDevice.value = null
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

    const clearAllDevices = async (subscription) => {
      try {
        await ElMessageBox.confirm(
          `确定要清空用户 "${subscription.user.username}" 的所有设备吗？此操作不可恢复！`,
          '确认清空',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        clearingDevices.value = true
        const response = await api.delete(`/admin/subscriptions/${subscription.id}/devices`)
        
        if (response.data && response.data.success) {
          ElMessage.success('所有设备已清空')
          // 重新加载设备列表和订阅列表
          if (currentSubscription.value && currentSubscription.value.id === subscription.id) {
            await loadSubscriptionDevices(subscription.id)
          }
          await loadSubscriptions()
        } else {
          ElMessage.error('清空设备失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('清空设备失败:', error)
          ElMessage.error('清空设备失败')
        }
      } finally {
        clearingDevices.value = false
      }
    }

    const refreshDevices = async () => {
      if (currentSubscription.value) {
        await loadSubscriptionDevices(currentSubscription.value.id)
      }
    }

    const updateExpireTime = async (subscriptionId, newExpireTime) => {
      try {
        const response = await api.put(`/admin/subscriptions/${subscriptionId}`, {
          expires_at: newExpireTime
        })
        
        if (response.data && response.data.success) {
          ElMessage.success('到期时间更新成功')
          // 重新加载订阅列表
          await loadSubscriptions()
        } else {
          ElMessage.error('到期时间更新失败')
        }
      } catch (error) {
        console.error('更新到期时间失败:', error)
        ElMessage.error('更新到期时间失败')
      }
    }

    const getDeviceTypeColor = (type) => {
      const typeColors = {
        'mobile': 'success',
        'desktop': 'primary',
        'tablet': 'warning',
        'unknown': 'info'
      }
      return typeColors[type] || 'info'
    }

    const formatDateTime = (dateTimeStr) => {
      if (!dateTimeStr) return '未知'
      try {
        const date = new Date(dateTimeStr)
        return date.toLocaleString('zh-CN')
      } catch (error) {
        return dateTimeStr
      }
    }

    const updateDeviceLimit = async (subscriptionId, newLimit) => {
      try {
        const response = await api.put(`/admin/subscriptions/${subscriptionId}`, {
          device_limit: newLimit
        })
        
        if (response.data && response.data.success) {
          ElMessage.success('设备限制更新成功')
          // 重新加载订阅列表
          await loadSubscriptions()
        } else {
          ElMessage.error('设备限制更新失败')
        }
      } catch (error) {
        console.error('更新设备限制失败:', error)
        ElMessage.error('更新设备限制失败')
      }
    }

    const resetUserAllSubscriptions = async (userId) => {
      try {
        await ElMessageBox.confirm(
          '确定要重置该用户的所有订阅吗？这将重新生成V2Ray和Clash的订阅地址。',
          '确认重置',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        const response = await api.post(`/admin/subscriptions/user/${userId}/reset-all`)
        
        if (response.data && response.data.success) {
          ElMessage.success('用户所有订阅重置成功')
          await loadSubscriptions()
        } else {
          ElMessage.error('重置订阅失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('重置用户订阅失败:', error)
          ElMessage.error('重置订阅失败')
        }
      }
    }

    const deleteUserAllData = async (userId) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除该用户及其所有数据吗？此操作不可恢复！',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'danger',
          }
        )
        
        const response = await api.delete(`/admin/subscriptions/user/${userId}/delete-all`)
        
        if (response.data && response.data.success) {
          ElMessage.success('用户及其所有数据删除成功')
          await loadSubscriptions()
        } else {
          ElMessage.error('删除用户失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除用户失败:', error)
          ElMessage.error('删除用户失败')
        }
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
      statistics,
      // 新增的方法
      clearAllDevices,
      refreshDevices,
      updateExpireTime,
      getDeviceTypeColor,
      formatDateTime,
      loadSubscriptionDevices,
      updateDeviceLimit,
      resetUserAllSubscriptions,
      deleteUserAllData
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

.user-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.username {
  font-weight: bold;
  color: #303133;
}

.email {
  font-size: 12px;
  color: #909399;
}

.subscription-url {
  width: 100%;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.device-count {
  margin-bottom: 4px;
}

.device-actions {
  display: flex;
  gap: 4px;
}

.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.devices-dialog-content {
  padding: 0;
}

.subscription-info {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.subscription-info h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.subscription-info p {
  margin: 8px 0;
  color: #606266;
}

.devices-actions {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.devices-footer {
  margin-top: 16px;
  text-align: center;
  color: #909399;
  font-size: 14px;
}

.placeholder-url {
  text-align: center;
  padding: 8px;
}

.device-limit-edit {
  margin: 8px 0;
}

.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.search-form .el-form-item {
  margin-bottom: 0;
  margin-right: 0;
}
</style> 