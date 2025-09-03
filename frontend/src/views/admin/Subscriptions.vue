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
      <el-table :data="subscriptions" style="width: 100%" v-loading="loading" row-key="user.id" @selection-change="handleSelectionChange">
        <!-- 选择列 -->
        <el-table-column type="selection" width="55" />
        
        <!-- 用户信息 -->
        <el-table-column label="用户信息" width="200">
          <template #default="scope">
                          <div class="user-info">
                <div class="user-id">ID: {{ scope.row.user?.id || '未知' }}</div>
                <div class="username">{{ scope.row.user?.username || '未知用户' }}</div>
                <div class="email">{{ scope.row.user?.email || '未知邮箱' }}</div>
                <div class="user-actions">
                  <el-button size="small" type="primary" @click="showUserDetails(scope.row.user)">
                    <el-icon><View /></el-icon>
                    详情
                  </el-button>
                </div>
              </div>
          </template>
        </el-table-column>
        
        <!-- V2Ray订阅 -->
        <el-table-column label="V2Ray订阅" min-width="300">
          <template #default="scope">
            <div class="subscription-card v2ray">
              <div class="subscription-header">
                <el-tag type="primary" size="small">V2Ray</el-tag>
                <el-tag :type="getStatusType(scope.row.v2ray_subscription?.status || 'inactive')" size="small">
                  {{ getStatusText(scope.row.v2ray_subscription?.status || 'inactive') }}
                </el-tag>
              </div>
              <div class="subscription-url-section">
                <div v-if="!scope.row.v2ray_subscription || scope.row.v2ray_subscription.is_placeholder" class="placeholder-url">
                  <el-tag type="info" size="small">未配置</el-tag>
                </div>
                <div v-else class="subscription-url-container">
                  <span class="subscription-url-text">{{ scope.row.v2ray_subscription.full_url }}</span>
                  <el-button 
                    type="text" 
                    class="copy-btn" 
                    @click="copyUrl(scope.row.v2ray_subscription.full_url)"
                  >
                    复制
                  </el-button>
                </div>
              </div>
              <div class="subscription-details">
                <div class="detail-item">
                  <span class="label">到期时间:</span>
                  <el-date-picker
                    v-model="scope.row.v2ray_subscription.expires_at"
                    type="datetime"
                    placeholder="选择到期时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    size="small"
                    @change="(value) => updateExpireTime(scope.row.v2ray_subscription.id, value)"
                    style="width: 180px"
                  />
                </div>
                <div class="detail-item">
                  <span class="label">设备限制:</span>
                  <el-input-number
                    v-model="scope.row.v2ray_subscription.device_limit"
                    :min="1"
                    :max="10"
                    size="small"
                    @change="(value) => updateDeviceLimit(scope.row.v2ray_subscription.id, value)"
                    :disabled="!scope.row.v2ray_subscription || scope.row.v2ray_subscription.is_placeholder"
                    style="width: 80px"
                  />
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- Clash订阅 -->
        <el-table-column label="Clash订阅" min-width="300">
          <template #default="scope">
            <div class="subscription-card clash">
              <div class="subscription-header">
                <el-tag type="success" size="small">Clash</el-tag>
                <el-tag :type="getStatusType(scope.row.clash_subscription?.status || 'inactive')" size="small">
                  {{ getStatusText(scope.row.clash_subscription?.status || 'inactive') }}
                </el-tag>
              </div>
              <div class="subscription-url-section">
                <div v-if="!scope.row.clash_subscription || scope.row.clash_subscription.is_placeholder" class="placeholder-url">
                  <el-tag type="info" size="small">未配置</el-tag>
                </div>
                <div v-else class="subscription-url-container">
                  <span class="subscription-url-text">{{ scope.row.clash_subscription.full_url }}</span>
                  <el-button 
                    type="text" 
                    class="copy-btn" 
                    @click="copyUrl(scope.row.clash_subscription.full_url)"
                  >
                    复制
                  </el-button>
                </div>
              </div>
              <div class="subscription-details">
                <div class="detail-item">
                  <span class="label">到期时间:</span>
                  <el-date-picker
                    v-model="scope.row.clash_subscription.expires_at"
                    type="datetime"
                    placeholder="选择到期时间"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                    size="small"
                    @change="(value) => updateExpireTime(scope.row.clash_subscription.id, value)"
                    style="width: 180px"
                  />
                </div>
                <div class="detail-item">
                  <span class="label">设备限制:</span>
                  <el-input-number
                    v-model="scope.row.clash_subscription.device_limit"
                    :min="1"
                    :max="10"
                    size="small"
                    @change="(value) => updateDeviceLimit(scope.row.clash_subscription.id, value)"
                    :disabled="!scope.row.clash_subscription || scope.row.clash_subscription.is_placeholder"
                    style="width: 80px"
                  />
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- 设备管理 -->
        <el-table-column label="设备管理" width="200">
          <template #default="scope">
            <div class="device-management">
              <div class="device-summary">
                <el-tag :type="(scope.row.total_devices || 0) >= (scope.row.max_device_limit || 3) ? 'danger' : 'success'" size="small">
                  {{ scope.row.total_devices || 0 }}/{{ scope.row.max_device_limit || 3 }}
                </el-tag>
                <span class="device-text">设备</span>
              </div>
              <div class="device-actions">
                <el-button 
                  size="small" 
                  type="info" 
                  @click="viewUserDevices(scope.row)"
                  :disabled="(scope.row.total_devices || 0) === 0"
                >
                  <el-icon><Monitor /></el-icon>
                  查看设备
                </el-button>
                <el-button 
                  size="small" 
                  type="warning" 
                  @click="clearUserAllDevices(scope.row)"
                  :disabled="(scope.row.total_devices || 0) === 0"
                >
                  <el-icon><Delete /></el-icon>
                  清空设备
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- 操作 -->
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <div class="action-buttons">
              <el-button 
                size="small" 
                type="warning" 
                @click="resetUserAllSubscriptions(scope.row.user?.id)"
              >
                <el-icon><RefreshLeft /></el-icon>
                重置全部
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteUserAllData(scope.row.user?.id)"
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
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBulkOperationsDialog = false">取消</el-button>
          <el-button type="primary" @click="executeBulkOperation" :loading="bulkLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 用户详情对话框 -->
    <el-dialog v-model="userDetailDialogVisible" title="用户详情" width="600px">
      <div v-if="selectedUser" class="user-detail">
        <div class="detail-row">
          <span class="label">用户ID:</span>
          <span class="value">{{ selectedUser.id }}</span>
        </div>
        <div class="detail-row">
          <span class="label">用户名:</span>
          <span class="value">{{ selectedUser.username }}</span>
        </div>
        <div class="detail-row">
          <span class="label">邮箱:</span>
          <span class="value">{{ selectedUser.email }}</span>
        </div>
        <div class="detail-row">
          <span class="label">注册时间:</span>
          <span class="value">{{ selectedUser.created_at }}</span>
        </div>
        <div class="detail-row">
          <span class="label">最后登录:</span>
          <span class="value">{{ selectedUser.last_login_at || '从未登录' }}</span>
        </div>
      </div>
    </el-dialog>

    <!-- 统计对话框 -->
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
          <el-table-column prop="subscription_type" label="订阅类型" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.subscription_type === 'V2Ray' ? 'primary' : 'success'" size="small">
                {{ scope.row.subscription_type }}
              </el-tag>
            </template>
          </el-table-column>
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
  Refresh, RefreshLeft, Monitor, Delete, View 
} from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminSubscriptions',
  components: {
    Download, Operation, DataAnalysis, Plus, Edit, 
    Refresh, RefreshLeft, Monitor, Delete, View
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
    
    const selectedUsers = ref([])
    const userDetailDialogVisible = ref(false)
    const selectedUser = ref(null)

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

    const viewUserDevices = async (userData) => {
      currentSubscription.value = userData
      showDevicesDialog.value = true
      // 加载用户所有设备的汇总信息
      await loadUserDevices(userData.user.id)
    }

    const loadUserDevices = async (userId) => {
      devicesLoading.value = true
      try {
        // 获取用户的所有订阅设备
        const allDevices = []
        const userSubscriptions = subscriptions.value.find(s => s.user.id === userId)
        
        if (userSubscriptions) {
          // 加载V2Ray订阅的设备
          if (userSubscriptions.v2ray_subscription && !userSubscriptions.v2ray_subscription.is_placeholder) {
            const v2rayResponse = await api.get(`/admin/subscriptions/${userSubscriptions.v2ray_subscription.id}/devices`)
            if (v2rayResponse.data && v2rayResponse.data.success && v2rayResponse.data.data) {
              allDevices.push(...v2rayResponse.data.data.devices.map(d => ({ ...d, subscription_type: 'V2Ray' })))
            }
          }
          
          // 加载Clash订阅的设备
          if (userSubscriptions.clash_subscription && !userSubscriptions.clash_subscription.is_placeholder) {
            const clashResponse = await api.get(`/admin/subscriptions/${userSubscriptions.clash_subscription.id}/devices`)
            if (clashResponse.data && clashResponse.data.success && clashResponse.data.data) {
              allDevices.push(...clashResponse.data.data.devices.map(d => ({ ...d, subscription_type: 'Clash' })))
            }
          }
        }
        
        devices.value = allDevices
      } catch (error) {
        console.error('加载用户设备失败:', error)
        ElMessage.error('加载用户设备失败')
        devices.value = []
      } finally {
        devicesLoading.value = false
      }
    }

    const clearUserAllDevices = async (userData) => {
      try {
        await ElMessageBox.confirm(
          `确定要清空用户 "${userData.user.username}" 的所有设备吗？此操作不可恢复！`,
          '确认清空',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning',
          }
        )
        
        clearingDevices.value = true
        
        // 清空用户所有订阅的设备
        if (userData.v2ray_subscription && !userData.v2ray_subscription.is_placeholder) {
          await api.delete(`/admin/subscriptions/${userData.v2ray_subscription.id}/devices`)
        }
        if (userData.clash_subscription && !userData.clash_subscription.is_placeholder) {
          await api.delete(`/admin/subscriptions/${userData.clash_subscription.id}/devices`)
        }
        
        ElMessage.success('用户所有设备已清空')
        // 重新加载数据
        await loadSubscriptions()
        if (currentSubscription.value && currentSubscription.value.user.id === userData.user.id) {
          await loadUserDevices(userData.user.id)
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('清空用户设备失败:', error)
          ElMessage.error('清空用户设备失败')
        }
      } finally {
        clearingDevices.value = false
      }
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
      viewUserDevices,
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
      showUserDetails(user) {
        ElMessage.info(`用户详情: ${user.username} (${user.email})`);
        // 这里可以打开用户详情对话框
      },
      
      showUserBackend(user) {
        ElMessage.info(`访问用户后台: ${user.username}`);
        // 这里可以跳转到用户后台或打开用户管理对话框
      },
      
      sendUserNotification(user) {
        ElMessage.info(`发送通知给用户: ${user.username}`);
        // 这里可以打开发送通知对话框
      },
      
      editUserSubscription(userData) {
        ElMessage.info(`编辑用户订阅: ${userData.user.username}`);
        // 这里可以打开编辑订阅对话框
      },
      
      updateUserExpireTime(userId, value) {
        if (!value) return;
        ElMessage.info(`更新用户 ${userId} 的到期时间: ${value}`);
        // 这里需要调用API更新用户的到期时间
      },
      
      extendExpireTime(userId, months) {
        ElMessage.info(`延长用户 ${userId} 的到期时间 ${months} 个月`);
        // 这里需要调用API延长用户的到期时间
      },
      
      updateUserMaxDevices(userId, value) {
        ElMessage.info(`更新用户 ${userId} 的最大设备数: ${value}`);
        // 这里需要调用API更新用户的最大设备数
      },
      
      increaseMaxDevices(userId, amount) {
        ElMessage.info(`增加用户 ${userId} 的最大设备数 ${amount} 个`);
        // 这里需要调用API增加用户的最大设备数
      },
      
      // 批量操作相关方法
      handleSelectionChange(selection) {
        bulkForm.selectedIds = selection
      },
      
      // 显示用户详情
      showUserDetails(user) {
        selectedUser.value = user
        userDetailDialogVisible.value = true
      },
      
      // 批量重置订阅
      bulkResetSubscriptions() {
        if (bulkForm.selectedIds.length === 0) {
          ElMessage.warning('请先选择用户');
          return;
        }
        ElMessageBox.confirm('确定要重置选中用户的所有订阅吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          const userIds = bulkForm.selectedIds.map(sub => sub.user.id);
          // 这里需要调用API批量重置订阅
          ElMessage.success(`已重置 ${userIds.length} 个用户的订阅`);
          loadSubscriptions();
        });
      },
      
      // 批量删除用户
      bulkDeleteUsers() {
        if (bulkForm.selectedIds.length === 0) {
          ElMessage.warning('请先选择用户');
          return;
        }
        ElMessageBox.confirm('确定要删除选中的用户吗？此操作不可恢复！', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'danger'
        }).then(() => {
          const userIds = bulkForm.selectedIds.map(sub => sub.user.id);
          // 这里需要调用API批量删除用户
          ElMessage.success(`已删除 ${userIds.length} 个用户`);
          loadSubscriptions();
        });
      },
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
      deleteUserAllData,
      viewUserDevices,
      loadUserDevices,
      clearUserAllDevices
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

.user-id {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.username {
  font-weight: bold;
  color: #303133;
}

.email {
  color: #606266;
  font-size: 13px;
}

.user-actions {
  margin-top: 8px;
}

.user-detail {
  padding: 20px 0;
}

.detail-row {
  display: flex;
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  font-weight: bold;
  color: #606266;
  min-width: 100px;
  margin-right: 15px;
}

.detail-row .value {
  color: #303133;
  flex: 1;
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

.subscription-url-container {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.subscription-url-text {
  flex: 1;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: #495057;
  word-break: break-all;
  line-height: 1.4;
  padding: 4px 0;
}

.copy-btn {
  flex-shrink: 0;
  font-size: 12px;
  padding: 4px 8px;
  height: auto;
  min-width: 50px;
}

.subscription-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background: #fafafa;
  margin: 8px 0;
  transition: all 0.3s ease;
}

.subscription-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.subscription-card.v2ray {
  border-left: 4px solid #409eff;
  background: linear-gradient(135deg, #f0f8ff 0%, #fafafa 100%);
}

.subscription-card.clash {
  border-left: 4px solid #67c23a;
  background: linear-gradient(135deg, #f0fff0 0%, #fafafa 100%);
}

.subscription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.subscription-url-section {
  margin-bottom: 12px;
}

.subscription-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-item .label {
  font-size: 12px;
  color: #606266;
  min-width: 60px;
}

.device-management {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.device-summary {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-text {
  font-size: 12px;
  color: #606266;
}

.device-actions {
  display: flex;
  gap: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}

.subscription-url {
  width: 100%;
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