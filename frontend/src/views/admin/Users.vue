<template>
  <div class="admin-users">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>用户管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportUsers">
              <el-icon><Download /></el-icon>
              导出用户
            </el-button>
            <el-button type="warning" @click="showBulkImportDialog = true">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
            <el-button type="info" @click="showStatisticsDialog = true">
              <el-icon><DataAnalysis /></el-icon>
              用户统计
            </el-button>
            <el-button type="primary" @click="showAddUserDialog = true">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>
            <el-button type="warning" @click="testAPI">
              测试API
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="邮箱">
          <el-input v-model="searchForm.email" placeholder="搜索邮箱" clearable />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="搜索用户名" clearable />
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

      <!-- 批量操作栏 -->
      <div class="batch-actions" v-if="selectedUsers.length > 0">
        <el-alert
          :title="`已选择 ${selectedUsers.length} 个用户`"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="batch-buttons">
          <el-button type="success" @click="batchActivateUsers" :disabled="!hasInactiveUsers">
            批量激活
          </el-button>
          <el-button type="warning" @click="batchDisableUsers" :disabled="!hasActiveUsers">
            批量禁用
          </el-button>
          <el-button type="danger" @click="batchDeleteUsers">
            批量删除
          </el-button>
          <el-button @click="clearSelection">
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
                <div class="email">{{ scope.row.email }}</div>
                <div class="username">{{ scope.row.username }}</div>
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
        <el-table-column prop="subscription_count" label="订阅数" width="100" align="center">
          <template #default="scope">
            <el-badge :value="scope.row.subscription_count || 0" :max="99">
              <el-icon><Connection /></el-icon>
            </el-badge>
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
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewUser(scope.row)">
              <el-icon><View /></el-icon>
              查看
            </el-button>
            <el-button size="small" @click="editUser(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              @click="sendSubscriptionEmail(scope.row)"
              v-if="scope.row.status === 'active'"
            >
              <el-icon><Message /></el-icon>
              订阅邮件
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="manageUserSubscriptions(scope.row)"
            >
              <el-icon><Connection /></el-icon>
              管理订阅
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="resetUserSubscription(scope.row)"
            >
              <el-icon><Refresh /></el-icon>
              重置订阅
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="clearUserDevices(scope.row)"
            >
              <el-icon><Connection /></el-icon>
              清理设备
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="toggleUserStatus(scope.row)"
            >
              <el-icon><Switch /></el-icon>
              {{ scope.row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteUser(scope.row)"
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
    <el-dialog v-model="showUserDialog" title="用户详情" width="800px">
      <el-descriptions :column="2" border v-if="selectedUser">
        <el-descriptions-item label="用户ID">{{ selectedUser.id }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ selectedUser.email }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ selectedUser.username }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(selectedUser.status)">
            {{ getStatusText(selectedUser.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">{{ formatDate(selectedUser.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="最后登录">{{ formatDate(selectedUser.last_login) || '从未登录' }}</el-descriptions-item>
        <el-descriptions-item label="订阅数量">{{ selectedUser.subscription_count || 0 }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ selectedUser.note || '无' }}</el-descriptions-item>
      </el-descriptions>
      
      <!-- 用户订阅列表 -->
      <div class="user-subscriptions" v-if="selectedUser?.subscriptions?.length">
        <h4>订阅列表</h4>
        <el-table :data="selectedUser.subscriptions" size="small">
          <el-table-column prop="id" label="订阅ID" width="80" />
          <el-table-column prop="subscription_url" label="订阅地址" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="expires_at" label="到期时间" width="180" />
        </el-table>
      </div>
    </el-dialog>

    <!-- 批量导入用户对话框 -->
    <el-dialog v-model="showBulkImportDialog" title="批量导入用户" width="500px">
      <el-form :model="bulkImportForm" label-width="100px">
        <el-form-item label="导入方式">
          <el-radio-group v-model="bulkImportForm.method">
            <el-radio label="file">文件上传</el-radio>
            <el-radio label="manual">手动输入</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="文件上传" v-if="bulkImportForm.method === 'file'">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".xlsx,.xls,.csv"
          >
            <el-button type="primary">选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 .xlsx, .xls, .csv 格式</div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="手动输入" v-if="bulkImportForm.method === 'manual'">
          <el-input
            v-model="bulkImportForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入用户信息，格式：邮箱,用户名,密码 (每行一个用户)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBulkImportDialog = false">取消</el-button>
          <el-button type="primary" @click="handleBulkImport" :loading="bulkImportLoading">
            开始导入
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 用户统计对话框 -->
    <el-dialog v-model="showStatisticsDialog" title="用户统计" width="600px">
      <div class="statistics-content">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.totalUsers }}</div>
              <div class="stat-label">总用户数</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.activeUsers }}</div>
              <div class="stat-label">活跃用户</div>
            </el-card>
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.newUsersToday }}</div>
              <div class="stat-label">今日新增</div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="stat-card">
              <div class="stat-number">{{ statistics.subscriptionRate }}%</div>
              <div class="stat-label">订阅率</div>
            </el-card>
          </el-col>
        </el-row>
        
        <div class="chart-container" style="margin-top: 20px;">
          <h4>用户增长趋势</h4>
          <div ref="userGrowthChart" style="height: 300px;"></div>
        </div>
      </div>
    </el-dialog>

    <!-- 用户订阅管理对话框 -->
    <el-dialog v-model="showSubscriptionDialog" title="用户订阅管理" width="800px">
      <div class="subscription-management">
        <div class="subscription-header">
          <h4>用户：{{ selectedUser?.username }}</h4>
          <el-button type="primary" size="small" @click="addUserSubscription">
            <el-icon><Plus /></el-icon>
            添加订阅
          </el-button>
        </div>
        
        <el-table :data="userSubscriptions" size="small">
          <el-table-column prop="id" label="订阅ID" width="80" />
          <el-table-column prop="subscription_url" label="订阅地址" min-width="200" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)" size="small">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="expires_at" label="到期时间" width="180" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button size="small" @click="editUserSubscription(scope.row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteUserSubscription(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Edit, Delete, View, Search, Refresh, Download, 
  Message, Switch, Connection, Upload, DataAnalysis
} from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AdminUsers',
  components: {
    Plus, Edit, Delete, View, Search, Refresh, Download, 
    Message, Switch, Connection
  },
  setup() {
    const api = adminAPI
    const loading = ref(false)
    const saving = ref(false)
    const users = ref([])
    const selectedUsers = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showAddUserDialog = ref(false)
    const showUserDialog = ref(false)
    const showBulkImportDialog = ref(false)
    const showStatisticsDialog = ref(false)
    const showSubscriptionDialog = ref(false)
    const editingUser = ref(null)
    const selectedUser = ref(null)
    const userFormRef = ref()
    const bulkImportLoading = ref(false)
    const fileList = ref([])
    const userSubscriptions = ref([])

    const searchForm = reactive({
      email: '',
      username: '',
      status: '',
      date_range: ''
    })

    const userForm = reactive({
      email: '',
      username: '',
      password: '',
      status: 'active',
      note: ''
    })

    const bulkImportForm = reactive({
      method: 'file',
      content: ''
    })

    const statistics = reactive({
      totalUsers: 0,
      activeUsers: 0,
      newUsersToday: 0,
      subscriptionRate: 0
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

    // 计算属性
    const hasInactiveUsers = computed(() => 
      selectedUsers.value.some(user => user.status === 'inactive')
    )
    
    const hasActiveUsers = computed(() => 
      selectedUsers.value.some(user => user.status === 'active')
    )

    const loadUsers = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          ...searchForm
        }
        
        console.log('=== 开始加载用户列表 ===')
        console.log('请求用户列表参数:', params)
        console.log('当前token:', localStorage.getItem('token'))
        console.log('使用的API:', api)
        console.log('API方法:', api.getUsers)
        
        const response = await api.getUsers(params)
        console.log('=== API响应详情 ===')
        console.log('响应状态:', response.status)
        console.log('响应状态文本:', response.statusText)
        console.log('响应头:', response.headers)
        console.log('响应数据:', response.data)
        console.log('响应数据类型:', typeof response.data)
        console.log('response.data.success:', response.data?.success)
        console.log('response.data.data:', response.data?.data)
        console.log('response.data.data.users:', response.data?.data?.users)
        console.log('response.data.data.total:', response.data?.data?.total)
        
        // 检查响应是否成功
        if (response.data && response.data.success && response.data.data) {
          const responseData = response.data.data
          users.value = responseData.users || []
          total.value = responseData.total || 0
          console.log('=== 数据绑定成功 ===')
          console.log('用户列表加载成功，共', users.value.length, '个用户')
          console.log('users.value:', users.value)
          console.log('total.value:', total.value)
          console.log('users.value类型:', Array.isArray(users.value))
          console.log('users.value长度:', users.value.length)
          
          // 强制触发响应式更新
          nextTick(() => {
            console.log('nextTick后users.value:', users.value)
            console.log('nextTick后users.value长度:', users.value.length)
          })
        } else {
          console.warn('=== 响应数据格式异常 ===')
          console.warn('response.data:', response.data)
          console.warn('response.data.success:', response.data?.success)
          console.warn('response.data.data:', response.data?.data)
          console.warn('response.data.data.users:', response.data?.data?.users)
          console.warn('response.data.data.total:', response.data?.data?.total)
          console.warn('response.data.message:', response.data?.message)
          users.value = []
          total.value = 0
          
          // 如果有错误消息，显示给用户
          if (response.data?.message) {
            ElMessage.error(`加载用户列表失败: ${response.data.message}`)
          }
        }
      } catch (error) {
        console.error('=== 加载用户列表失败 ===')
        console.error('错误对象:', error)
        console.error('错误消息:', error.message)
        console.error('错误响应:', error.response)
        console.error('错误响应数据:', error.response?.data)
        console.error('错误响应状态:', error.response?.status)
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
        email: '', 
        username: '', 
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

    const handleSelectionChange = (selection) => {
      selectedUsers.value = selection
    }

    const clearSelection = () => {
      selectedUsers.value = []
    }

    const viewUser = async (user) => {
      try {
        const response = await api.get(`/admin/users/${user.id}`)
        selectedUser.value = response.data
        showUserDialog.value = true
      } catch (error) {
        ElMessage.error('加载用户详情失败')
        console.error('加载用户详情失败:', error)
      }
    }

    const editUser = (user) => {
      editingUser.value = user
      Object.assign(userForm, {
        email: user.email,
        username: user.username,
        status: user.status,
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
            is_verified: false
          }
          console.log('发送更新用户数据:', userData)
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
          console.log('发送创建用户数据:', userData)
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
        await api.delete(`/admin/users/${user.id}`)
        ElMessage.success('用户删除成功')
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
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
        
        await api.put(`/admin/users/${user.id}/status`, { status: newStatus })
        ElMessage.success(`用户${action}成功`)
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('状态更新失败')
        }
      }
    }

    const sendSubscriptionEmail = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要发送订阅邮件给用户 "${user.username}" 吗？`, 
          '确认发送', 
          { type: 'info' }
        )
        
        await api.post(`/admin/users/${user.id}/send-subscription-email`)
        ElMessage.success('订阅邮件发送成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('发送失败')
        }
      }
    }

    const manageUserSubscriptions = async (user) => {
      try {
        const response = await api.get(`/admin/users/${user.id}/subscriptions`)
        userSubscriptions.value = response.data
        selectedUser.value = user
        showSubscriptionDialog.value = true
      } catch (error) {
        ElMessage.error('加载用户订阅失败')
      }
    }

    const addUserSubscription = () => {
      // 跳转到订阅管理页面或打开添加订阅对话框
      ElMessage.info('请在订阅管理页面添加订阅')
    }

    const editUserSubscription = (subscription) => {
      // 编辑用户订阅
      ElMessage.info('编辑订阅功能开发中')
    }

    const deleteUserSubscription = async (subscription) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除这个订阅吗？`, 
          '确认删除', 
          { type: 'warning' }
        )
        await api.delete(`/admin/subscriptions/${subscription.id}`)
        ElMessage.success('订阅删除成功')
        manageUserSubscriptions(selectedUser.value)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const handleFileChange = (file) => {
      fileList.value = [file]
    }

    const handleBulkImport = async () => {
      if (bulkImportForm.method === 'file' && fileList.value.length === 0) {
        ElMessage.warning('请选择要导入的文件')
        return
      }
      if (bulkImportForm.method === 'manual' && !bulkImportForm.content.trim()) {
        ElMessage.warning('请输入要导入的用户信息')
        return
      }

      bulkImportLoading.value = true
      try {
        if (bulkImportForm.method === 'file') {
          const formData = new FormData()
          formData.append('file', fileList.value[0].raw)
          await api.post('/admin/users/bulk-import', formData)
        } else {
          await api.post('/admin/users/bulk-import', {
            content: bulkImportForm.content
          })
        }
        ElMessage.success('批量导入成功')
        showBulkImportDialog.value = false
        loadUsers()
        resetBulkImportForm()
      } catch (error) {
        ElMessage.error('批量导入失败')
      } finally {
        bulkImportLoading.value = false
      }
    }

    const resetBulkImportForm = () => {
      bulkImportForm.method = 'file'
      bulkImportForm.content = ''
      fileList.value = []
    }

    const loadStatistics = async () => {
      try {
        const response = await api.getUserStatistics()
        console.log('用户统计响应:', response)
        if (response.data) {
          Object.assign(statistics, response.data)
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
        console.error('错误详情:', error.response?.data)
      }
    }

    // 批量操作
    const batchActivateUsers = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要激活选中的 ${selectedUsers.value.length} 个用户吗？`, 
          '确认批量激活', 
          { type: 'warning' }
        )
        
        const userIds = selectedUsers.value
          .filter(user => user.status === 'inactive')
          .map(user => user.id)
        
        await api.post('/admin/users/batch-activate', { user_ids: userIds })
        ElMessage.success('批量激活成功')
        clearSelection()
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量激活失败')
        }
      }
    }

    const batchDisableUsers = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要禁用选中的 ${selectedUsers.value.length} 个用户吗？`, 
          '确认批量禁用', 
          { type: 'warning' }
        )
        
        const userIds = selectedUsers.value
          .filter(user => user.status === 'active')
          .map(user => user.id)
        
        await api.post('/admin/users/batch-disable', { user_ids: userIds })
        ElMessage.success('批量禁用成功')
        clearSelection()
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量禁用失败')
        }
      }
    }

    const batchDeleteUsers = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedUsers.value.length} 个用户吗？此操作不可恢复。`, 
          '确认批量删除', 
          { type: 'warning' }
        )
        
        const userIds = selectedUsers.value.map(user => user.id)
        await api.post('/admin/users/batch-delete', { user_ids: userIds })
        ElMessage.success('批量删除成功')
        clearSelection()
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量删除失败')
        }
      }
    }

    const exportUsers = async () => {
      try {
        const response = await api.get('/admin/users/export', { 
          responseType: 'blob',
          params: searchForm 
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `users_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('用户数据导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
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

    const resetUserSubscription = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要重置用户 ${user.username} 的订阅地址吗？这将清空所有设备记录。`,
          '确认重置',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        const response = await api.post(`/admin/users/${user.id}/reset-subscription`)
        ElMessage.success('订阅重置成功')
        
        // 重新加载用户列表
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重置订阅失败')
          console.error('重置订阅失败:', error)
        }
      }
    }

    const clearUserDevices = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要清理用户 ${user.username} 的所有设备吗？`,
          '确认清理',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        const response = await api.post(`/admin/users/${user.id}/clear-devices`)
        ElMessage.success('设备清理成功')
        
        // 重新加载用户列表
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清理设备失败')
          console.error('清理设备失败:', error)
        }
      }
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
        
        // 保存用户token并跳转
        localStorage.setItem('user_token', response.data.token)
        localStorage.setItem('user_info', JSON.stringify(response.data.user))
        
        ElMessage.success('登录成功，正在跳转...')
        
        // 跳转到用户后台
        setTimeout(() => {
          window.open('/dashboard', '_blank')
        }, 1000)
        
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('登录失败')
          console.error('登录失败:', error)
        }
      }
    }

    const testAPI = async () => {
      try {
        console.log('=== 开始API测试 ===')
        console.log('Token:', localStorage.getItem('token'))
        console.log('API对象:', api)
        console.log('API方法:', api.getUsers)
        
        ElMessage.info('开始测试API...')
        
        // 直接使用fetch调用，绕过adminAPI
        const token = localStorage.getItem('token')
        console.log('使用的token:', token)
        
        const response = await fetch('/api/v1/admin/users?page=1&size=10', {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })
        
        const data = await response.json()
        console.log('直接fetch调用结果:', data)
        
        // 同时测试adminAPI
        const adminResponse = await api.getUsers({ page: 1, size: 10 })
        console.log('adminAPI调用结果:', adminResponse)
        
        ElMessage.success(`API测试成功，直接调用: ${data.data?.users?.length || 0}个用户, adminAPI: ${adminResponse.data?.users?.length || 0}个用户`)
      } catch (error) {
        console.error('API测试失败:', error)
        console.error('错误详情:', error.response?.data)
        ElMessage.error(`API测试失败: ${error.response?.data?.message || error.message}`)
      }
    }

    onMounted(() => {
      console.log('Users.vue 组件已挂载，开始加载数据...')
      console.log('当前token:', localStorage.getItem('token'))
      console.log('API对象:', api)
      
      // 延迟加载，确保组件完全挂载
      setTimeout(() => {
        console.log('开始加载用户数据...')
        loadUsers()
        loadStatistics()
      }, 100)
    })

    return {
      loading,
      saving,
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
      hasInactiveUsers,
      hasActiveUsers,
      searchUsers,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      handleSelectionChange,
      clearSelection,
      viewUser,
      editUser,
      saveUser,
      deleteUser,
      toggleUserStatus,
      sendSubscriptionEmail,
      manageUserSubscriptions,
      addUserSubscription,
      editUserSubscription,
      deleteUserSubscription,
      handleFileChange,
      handleBulkImport,
      loadStatistics,
      batchActivateUsers,
      batchDisableUsers,
      batchDeleteUsers,
      exportUsers,
      testAPI,
      getStatusType,
      getStatusText,
      formatDate,
      resetUserSubscription,
      clearUserDevices,
      loginAsUser,
      // 新增的响应式变量
      showBulkImportDialog,
      showStatisticsDialog,
      showSubscriptionDialog,
      bulkImportForm,
      bulkImportLoading,
      fileList,
      userSubscriptions,
      statistics
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

.pagination {
  margin-top: 20px;
  text-align: right;
}

.user-subscriptions {
  margin-top: 20px;
}

.user-subscriptions h4 {
  margin-bottom: 15px;
  color: #606266;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
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
</style> 