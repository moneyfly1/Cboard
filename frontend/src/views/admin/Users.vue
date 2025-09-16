<template>
  <div class="admin-users">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>用户管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="showAddUserDialog = true">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="搜索">
          <el-input 
            v-model="searchForm.keyword" 
            placeholder="输入用户邮箱或用户名进行搜索"
            style="width: 300px;"
            clearable
            @keyup.enter="searchUsers"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="待激活" value="inactive" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="注册时间">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchUsers">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>


      <!-- 批量操作工具栏 -->
      <div class="batch-actions" v-if="selectedUsers.length > 0">
        <div class="batch-info">
          <span>已选择 {{ selectedUsers.length }} 个用户</span>
        </div>
        <div class="batch-buttons">
          <el-button type="danger" @click="batchDeleteUsers" :loading="batchDeleting">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
          <el-button @click="clearSelection">
            <el-icon><Close /></el-icon>
            取消选择
          </el-button>
        </div>
      </div>

      <!-- 用户列表 -->
      <el-table 
        :data="users" 
        style="width: 100%" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="email" label="邮箱" min-width="200">
          <template #default="scope">
            <div class="user-email">
              <el-avatar :size="32" :src="scope.row.avatar">
                {{ scope.row.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <div class="email-info">
                <div class="email">
                  <el-button type="text" @click="viewUserDetails(scope.row.id)" class="clickable-text">
                    {{ scope.row.email }}
                  </el-button>
                </div>
                <div class="username">
                  <el-button type="text" @click="viewUserDetails(scope.row.id)" class="clickable-text">
                    {{ scope.row.username }}
                  </el-button>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备信息" width="140" align="center">
          <template #default="scope">
            <div class="device-info">
              <div class="device-stats">
                <div class="device-item online">
                  <el-icon class="device-icon online-icon"><Monitor /></el-icon>
                  <span class="device-count">{{ scope.row.online_devices || 0 }}</span>
                  <span class="device-label">在线</span>
                </div>
                <div class="device-separator">/</div>
                <div class="device-item total">
                  <el-icon class="device-icon total-icon"><Connection /></el-icon>
                  <span class="device-count">{{ scope.row.device_count || 0 }}</span>
                  <span class="device-label">总计</span>
                </div>
              </div>
              <div class="device-limit" v-if="scope.row.subscription">
                <el-text size="small" type="info">
                  限制: {{ scope.row.subscription.device_limit || 0 }}
                </el-text>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="订阅状态" width="140" align="center">
          <template #default="scope">
            <div v-if="scope.row.subscription" class="subscription-info">
              <div class="subscription-status">
                <el-tag 
                  :type="getSubscriptionStatusType(scope.row.subscription.status)" 
                  size="small"
                  effect="dark"
                >
                  {{ getSubscriptionStatusText(scope.row.subscription.status) }}
                </el-tag>
              </div>
              <div v-if="scope.row.subscription.days_until_expire !== null" class="expire-info">
                <el-text 
                  size="small" 
                  :type="scope.row.subscription.is_expired ? 'danger' : (scope.row.subscription.days_until_expire <= 7 ? 'warning' : 'success')"
                >
                  {{ scope.row.subscription.is_expired ? '已过期' : `${scope.row.subscription.days_until_expire}天后到期` }}
                </el-text>
              </div>
            </div>
            <div v-else class="no-subscription">
              <el-tag type="info" size="small" effect="plain">无订阅</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.last_login) || '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="180">
          <template #default="scope">
            <div v-if="scope.row.subscription && scope.row.subscription.expire_time" class="expire-time-info">
              <div class="expire-date">{{ formatDate(scope.row.subscription.expire_time) }}</div>
              <div class="expire-countdown">
                <el-text 
                  size="small" 
                  :type="scope.row.subscription.is_expired ? 'danger' : (scope.row.subscription.days_until_expire <= 7 ? 'warning' : 'success')"
                >
                  {{ scope.row.subscription.is_expired ? '已过期' : `${scope.row.subscription.days_until_expire}天后到期` }}
                </el-text>
              </div>
            </div>
            <div v-else class="no-expire">
              <el-text type="info" size="small">无订阅</el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <div class="button-row">
                <el-button size="small" type="primary" @click="editUser(scope.row)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  :type="scope.row.status === 'active' ? 'warning' : 'success'"
                  @click="toggleUserStatus(scope.row)"
                >
                  <el-icon><Switch /></el-icon>
                  {{ scope.row.status === 'active' ? '禁用' : '启用' }}
                </el-button>
              </div>
              <div class="button-row">
                <el-button 
                  size="small" 
                  type="info" 
                  @click="resetUserPassword(scope.row)"
                >
                  <el-icon><Key /></el-icon>
                  重置密码
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteUser(scope.row)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
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

    <!-- 添加/编辑用户对话框 -->
    <el-dialog 
      v-model="showAddUserDialog" 
      :title="editingUser ? '编辑用户' : '添加用户'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="userForm.status" placeholder="选择状态">
            <el-option label="活跃" value="active" />
            <el-option label="待激活" value="inactive" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item label="管理员权限" v-if="editingUser">
          <el-switch 
            v-model="userForm.is_admin" 
            active-text="是管理员"
            inactive-text="普通用户"
          />
        </el-form-item>
        <el-form-item label="邮箱验证" v-if="editingUser">
          <el-switch 
            v-model="userForm.is_verified" 
            active-text="已验证"
            inactive-text="未验证"
          />
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input 
            v-model="userForm.note" 
            type="textarea" 
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddUserDialog = false">取消</el-button>
          <el-button type="primary" @click="saveUser" :loading="saving">
            {{ editingUser ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 用户详情对话框 -->
    <el-dialog v-model="showUserDialog" title="用户详情" width="900px">
      <div v-if="selectedUser">
        <!-- 用户基本信息 -->
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户ID">{{ selectedUser.user_info?.id || selectedUser.id }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ selectedUser.user_info?.email || selectedUser.email }}</el-descriptions-item>
          <el-descriptions-item label="用户名">{{ selectedUser.user_info?.username || selectedUser.username }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedUser.user_info?.is_active !== false ? 'active' : 'inactive')">
              {{ getStatusText(selectedUser.user_info?.is_active !== false ? 'active' : 'inactive') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDate(selectedUser.user_info?.created_at || selectedUser.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="最后登录">{{ formatDate(selectedUser.user_info?.last_login || selectedUser.last_login) || '从未登录' }}</el-descriptions-item>
          <el-descriptions-item label="订阅数量">{{ selectedUser.statistics?.total_subscriptions || selectedUser.subscription_count || 0 }}</el-descriptions-item>
          <el-descriptions-item label="订单数量">{{ selectedUser.statistics?.total_orders || 0 }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 统计信息 -->
        <div class="user-stats" v-if="selectedUser.statistics">
          <h4>统计信息</h4>
          <el-row :gutter="20">
            <el-col :span="6">
              <el-statistic title="总消费" :value="selectedUser.statistics.total_spent" prefix="¥" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="重置次数" :value="selectedUser.statistics.total_resets" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="近30天重置" :value="selectedUser.statistics.recent_resets_30d" />
            </el-col>
            <el-col :span="6">
              <el-statistic title="订阅数量" :value="selectedUser.statistics.total_subscriptions" />
            </el-col>
          </el-row>
        </div>
        
        <!-- 用户订阅列表 -->
        <div class="user-subscriptions" v-if="selectedUser.subscriptions && selectedUser.subscriptions.length">
          <h4>订阅列表</h4>
          <el-table :data="selectedUser.subscriptions" size="small">
            <el-table-column prop="id" label="订阅ID" width="80" />
            <el-table-column prop="subscription_url" label="订阅地址" min-width="200" />
            <el-table-column prop="device_limit" label="设备限制" width="100" />
            <el-table-column prop="current_devices" label="当前设备" width="100" />
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                  {{ scope.row.is_active ? '活跃' : '未激活' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="expire_time" label="到期时间" width="180" />
          </el-table>
        </div>
        
        <!-- 用户订单列表 -->
        <div class="user-orders" v-if="selectedUser.orders && selectedUser.orders.length">
          <h4>订单列表</h4>
          <el-table :data="selectedUser.orders" size="small">
            <el-table-column prop="order_no" label="订单号" min-width="150" />
            <el-table-column prop="amount" label="金额" width="100">
              <template #default="scope">
                ¥{{ scope.row.amount }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'paid' ? 'success' : (scope.row.status === 'pending' ? 'warning' : 'danger')" size="small">
                  {{ scope.row.status === 'paid' ? '已支付' : (scope.row.status === 'pending' ? '待支付' : '已取消') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="payment_method" label="支付方式" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180" />
          </el-table>
        </div>
        
        <!-- 最近活动 -->
        <div class="user-activities" v-if="selectedUser.recent_activities && selectedUser.recent_activities.length">
          <h4>最近活动</h4>
          <el-table :data="selectedUser.recent_activities" size="small">
            <el-table-column prop="activity_type" label="活动类型" width="120" />
            <el-table-column prop="description" label="描述" min-width="200" />
            <el-table-column prop="ip_address" label="IP地址" width="120" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </div>
      </div>
    </el-dialog>




  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Edit, Delete, View, Search, Refresh, 
  Switch, Key, Close
} from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AdminUsers',
  components: {
    Plus, Edit, Delete, View, Search, Refresh, 
    Switch, Key, Close
  },
  setup() {
    const api = adminAPI
    const loading = ref(false)
    const saving = ref(false)
    const batchDeleting = ref(false)
    const users = ref([])
    const selectedUsers = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showAddUserDialog = ref(false)
    const showUserDialog = ref(false)
    const editingUser = ref(null)
    const selectedUser = ref(null)
    const userFormRef = ref()


    const searchForm = reactive({
      keyword: '',
      status: '',
      date_range: ''
    })

    const userForm = reactive({
      email: '',
      username: '',
      password: '',
      status: 'active',
      is_admin: false,
      is_verified: false,
      note: ''
    })



    const userRules = {
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 2, max: 20, message: '用户名长度在2到20个字符', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ],
      status: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }


    const loadUsers = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          keyword: searchForm.keyword,
          status: searchForm.status,
          date_range: searchForm.date_range
        }
        
        const response = await api.getUsers(params)
        
        // 检查响应是否成功
        if (response.data && response.data.success && response.data.data) {
          const responseData = response.data.data
          users.value = responseData.users || []
          total.value = responseData.total || 0
        } else {
          users.value = []
          total.value = 0
          
          // 如果有错误消息，显示给用户
          if (response.data?.message) {
            ElMessage.error(`加载用户列表失败: ${response.data.message}`)
          }
        }
      } catch (error) {
        ElMessage.error(`加载用户列表失败: ${error.response?.data?.message || error.message}`)
        users.value = []
        total.value = 0
      } finally {
        loading.value = false
      }
    }

    const searchUsers = () => {
      currentPage.value = 1
      loadUsers()
    }

    const resetSearch = () => {
      Object.assign(searchForm, { 
        keyword: '', 
        status: '', 
        date_range: '' 
      })
      searchUsers()
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      loadUsers()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadUsers()
    }



    const viewUserDetails = async (userId) => {
      try {
        const response = await adminAPI.getUserDetails(userId)
        
        if (response && response.data && response.data.success) {
          selectedUser.value = response.data.data
          showUserDialog.value = true
        } else if (response && response.success) {
          selectedUser.value = response.data
          showUserDialog.value = true
        } else {
          ElMessage.error('获取用户详情失败: ' + (response?.data?.message || response?.message || '未知错误'))
        }
      } catch (error) {
        ElMessage.error('获取用户详情失败: ' + (error.response?.data?.message || error.message))
      }
    }

    const editUser = (user) => {
      editingUser.value = user
      Object.assign(userForm, {
        email: user.email,
        username: user.username,
        status: user.status,
        is_admin: user.is_admin || false,
        is_verified: user.is_verified || false,
        note: user.note || ''
      })
      showAddUserDialog.value = true
    }

    const saveUser = async () => {
      try {
        await userFormRef.value.validate()
        saving.value = true
        
        if (editingUser.value) {
          // 转换数据格式以匹配后端API期望
          const userData = {
            username: userForm.username,
            email: userForm.email,
            is_active: userForm.status === 'active',
            is_verified: userForm.is_verified,
            is_admin: userForm.is_admin
          }
          await api.updateUser(editingUser.value.id, userData)
          ElMessage.success('用户更新成功')
        } else {
          // 转换数据格式以匹配后端API期望
          const userData = {
            username: userForm.username,
            email: userForm.email,
            password: userForm.password,
            is_active: userForm.status === 'active',
            is_admin: false,
            is_verified: false
          }
          await api.createUser(userData)
          ElMessage.success('用户创建成功')
        }
        
        showAddUserDialog.value = false
        editingUser.value = null
        resetUserForm()
        loadUsers()
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        saving.value = false
      }
    }

    const deleteUser = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`, 
          '确认删除', 
          { type: 'warning' }
        )
        await adminAPI.deleteUser(user.id)
        ElMessage.success('用户删除成功')
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`删除失败: ${error.response?.data?.message || error.message}`)
        }
      }
    }

    const toggleUserStatus = async (user) => {
      try {
        const newStatus = user.status === 'active' ? 'disabled' : 'active'
        const action = newStatus === 'active' ? '启用' : '禁用'
        
        await ElMessageBox.confirm(
          `确定要${action}用户 "${user.username}" 吗？`, 
          `确认${action}`, 
          { type: 'warning' }
        )
        
        await adminAPI.updateUserStatus(user.id, newStatus)
        ElMessage.success(`用户${action}成功`)
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`状态更新失败: ${error.response?.data?.message || error.message}`)
        }
      }
    }




    const resetUserForm = () => {
      Object.assign(userForm, {
        email: '',
        username: '',
        password: '',
        status: 'active',
        note: ''
      })
      userFormRef.value?.resetFields()
    }

    const getStatusType = (status) => {
      const statusMap = {
        'active': 'success',
        'inactive': 'warning',
        'disabled': 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getStatusText = (status) => {
      const statusMap = {
        'active': '活跃',
        'inactive': '待激活',
        'disabled': '禁用'
      }
      return statusMap[status] || status
    }

    const formatDate = (date) => {
      if (!date) return ''
      return new Date(date).toLocaleString('zh-CN')
    }



    const loginAsUser = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要以用户 ${user.username} 的身份登录吗？`,
          '确认登录',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )
        
        const response = await api.post(`/admin/users/${user.id}/login-as`)
        
        ElMessage.success('登录成功，正在跳转...')
        
        // 跳转到用户后台
        setTimeout(() => {
          // 在新标签页中打开用户后台，并传递认证信息
          const newWindow = window.open('/dashboard', '_blank')
          
          // 等待新窗口加载完成后设置认证信息
          newWindow.addEventListener('load', () => {
            newWindow.postMessage({
              type: 'SET_AUTH',
              token: response.data.token,
              user: response.data.user,
              adminToken: localStorage.getItem('token'),
              adminUser: localStorage.getItem('user')
            }, '*')
          })
        }, 1000)
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('登录失败')
          console.error('登录失败:', error)
        }
      }
    }


    // 重置用户密码
    const resetUserPassword = async (user) => {
      try {
        const { value: newPassword } = await ElMessageBox.prompt(
          `为用户 ${user.username} 设置新密码`,
          '重置密码',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            inputType: 'password',
            inputPlaceholder: '请输入新密码（至少6位）',
            inputValidator: (value) => {
              if (!value) {
                return '密码不能为空'
              }
              if (value.length < 6) {
                return '密码长度不能少于6位'
              }
              return true
            }
          }
        )

        await adminAPI.resetUserPassword(user.id, newPassword)
        
        ElMessage.success('密码重置成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`密码重置失败: ${error.response?.data?.message || error.message}`)
        }
      }
    }

    // 获取订阅状态类型
    const getSubscriptionStatusType = (status) => {
      const statusMap = {
        'active': 'success',
        'inactive': 'info',
        'expired': 'danger'
      }
      return statusMap[status] || 'info'
    }

    // 获取订阅状态文本
    const getSubscriptionStatusText = (status) => {
      const statusMap = {
        'active': '活跃',
        'inactive': '未激活',
        'expired': '已过期'
      }
      return statusMap[status] || '未知'
    }

    // 批量操作相关函数
    const handleSelectionChange = (selection) => {
      selectedUsers.value = selection
    }

    const clearSelection = () => {
      selectedUsers.value = []
      // 清除表格选择
      const table = document.querySelector('.el-table')
      if (table) {
        const checkboxes = table.querySelectorAll('input[type="checkbox"]')
        checkboxes.forEach(checkbox => {
          checkbox.checked = false
        })
      }
    }

    const batchDeleteUsers = async () => {
      if (selectedUsers.value.length === 0) {
        ElMessage.warning('请先选择要删除的用户')
        return
      }

      // 检查是否包含管理员用户
      const adminUsers = selectedUsers.value.filter(user => user.is_admin)
      if (adminUsers.length > 0) {
        ElMessage.error('不能删除管理员用户')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作将清空这些用户的所有数据（订阅、设备、日志等），且不可恢复。`, 
          '确认批量删除', 
          { 
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )

        batchDeleting.value = true
        
        // 获取要删除的用户ID列表
        const userIds = selectedUsers.value.map(user => user.id)
        
        // 调用批量删除API
        await adminAPI.batchDeleteUsers(userIds)
        
        ElMessage.success(`成功删除 ${selectedUsers.value.length} 个用户`)
        
        // 清空选择并重新加载数据
        clearSelection()
        loadUsers()
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error(`批量删除失败: ${error.response?.data?.message || error.message}`)
        }
      } finally {
        batchDeleting.value = false
      }
    }

    onMounted(() => {
      loadUsers()
    })

    return {
      loading,
      saving,
      batchDeleting,
      users,
      selectedUsers,
      currentPage,
      pageSize,
      total,
      searchForm,
      showAddUserDialog,
      showUserDialog,
      editingUser,
      selectedUser,
      userForm,
      userFormRef,
      userRules,
      searchUsers,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      viewUserDetails,
      editUser,
      saveUser,
      deleteUser,
      toggleUserStatus,
      getStatusType,
      getStatusText,
      formatDate,
      resetUserPassword,
      getSubscriptionStatusType,
      getSubscriptionStatusText,
      handleSelectionChange,
      clearSelection,
      batchDeleteUsers
    }
  }
}
</script>

<style scoped>
.admin-users {
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

.batch-actions {
  margin: 20px 0;
  padding: 15px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.batch-buttons {
  display: flex;
  gap: 10px;
}

.user-email {
  display: flex;
  align-items: center;
  gap: 12px;
}

.email-info {
  display: flex;
  flex-direction: column;
}

.email {
  font-weight: 500;
  color: #303133;
}

.username {
  font-size: 12px;
  color: #909399;
}

.device-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.device-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.device-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  min-width: 40px;
}

.device-icon {
  font-size: 16px;
  margin-bottom: 2px;
}

.online-icon {
  color: #67c23a;
}

.total-icon {
  color: #409eff;
}

.device-count {
  font-weight: bold;
  font-size: 14px;
  line-height: 1;
}

.device-label {
  font-size: 10px;
  color: #909399;
  line-height: 1;
}

.device-separator {
  font-size: 14px;
  color: #c0c4cc;
  font-weight: bold;
}

.device-limit {
  margin-top: 2px;
  padding: 2px 6px;
  background: #ecf5ff;
  border-radius: 4px;
  border: 1px solid #d9ecff;
}

.subscription-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.subscription-status {
  display: flex;
  justify-content: center;
}

.no-subscription {
  display: flex;
  justify-content: center;
}

.expire-info {
  margin-top: 2px;
  text-align: center;
  padding: 2px 6px;
  background: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #e1f5fe;
}

.expire-time-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.expire-date {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.expire-countdown {
  padding: 2px 6px;
  border-radius: 4px;
  background: #f0f9ff;
  border: 1px solid #e1f5fe;
}

.no-expire {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .device-stats {
    flex-direction: column;
    gap: 4px;
  }
  
  .device-separator {
    display: none;
  }
  
  .device-item {
    min-width: 35px;
  }
}

@media (max-width: 768px) {
  .device-info {
    gap: 4px;
  }
  
  .device-stats {
    padding: 2px 4px;
  }
  
  .device-icon {
    font-size: 14px;
  }
  
  .device-count {
    font-size: 12px;
  }
  
  .device-label {
    font-size: 9px;
  }
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.user-stats {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.user-stats h4 {
  margin-bottom: 15px;
  color: #606266;
}

.user-subscriptions,
.user-orders,
.user-activities {
  margin-top: 20px;
}

.user-subscriptions h4,
.user-orders h4,
.user-activities h4 {
  margin-bottom: 15px;
  color: #606266;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.button-row {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.action-buttons .el-button {
  margin: 0;
  padding: 6px 12px;
  font-size: 12px;
  min-width: 60px;
  flex: 1;
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

.subscription-management {
  padding: 20px 0;
}

.subscription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.subscription-header h4 {
  margin: 0;
  color: #303133;
}

.chart-container {
  margin-top: 30px;
}

.chart-container h4 {
  margin-bottom: 15px;
  color: #606266;
}

/* 设备管理样式 */
.device-management {
  padding: 0;
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-name i {
  font-size: 16px;
  color: #409eff;
}

.ip-address {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
}

.user-agent {
  font-size: 12px;
  color: #909399;
  cursor: help;
}

/* 设备管理页面样式 - 复制自普通用户设备管理页面 */
.devices-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h3 {
  color: #1677ff;
  font-size: 1.5rem;
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

.devices-card,
.chart-card {
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

.device-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.device-name i {
  font-size: 1.2rem;
  color: #1677ff;
}

.ip-address {
  font-family: 'Courier New', monospace;
  color: #666;
}

.user-agent {
  color: #666;
  font-size: 0.9rem;
}

.chart-container {
  padding: 1rem 0;
}

.chart-item {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
}

.chart-label {
  width: 100px;
  font-weight: 500;
  color: #333;
}

.chart-bar {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.chart-count {
  width: 60px;
  text-align: right;
  font-weight: 600;
  color: #1677ff;
}

@media (max-width: 768px) {
  .devices-container {
    padding: 10px;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .chart-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .chart-label {
    width: auto;
  }
  
  .chart-bar {
    width: 100%;
  }
  
  .chart-count {
    width: auto;
  }
}

.device-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.device-actions {
  display: flex;
  gap: 10px;
}

.no-devices {
  text-align: center;
  padding: 40px 0;
}

.clickable-text {
  color: #409eff !important;
  text-decoration: none;
  padding: 0 !important;
  font-size: inherit !important;
}

.clickable-text:hover {
  color: #66b1ff !important;
  text-decoration: underline;
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