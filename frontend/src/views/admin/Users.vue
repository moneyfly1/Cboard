<template>
  <div class="admin-users">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>用户管理</span>
          <el-button type="primary" @click="showAddUserDialog = true">
            添加用户
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="邮箱">
          <el-input v-model="searchForm.email" placeholder="搜索邮箱" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态">
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="待激活" value="inactive" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchUsers">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 用户列表 -->
      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" />
        <el-table-column prop="last_login" label="最后登录" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteUser(scope.row)"
            >删除</el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="toggleUserStatus(scope.row)"
            >
              {{ scope.row.status === 'active' ? '禁用' : '启用' }}
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
      width="500px"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="userForm.status" placeholder="选择状态">
            <el-option label="活跃" value="active" />
            <el-option label="待激活" value="inactive" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddUserDialog = false">取消</el-button>
          <el-button type="primary" @click="saveUser">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminUsers',
  setup() {
    const api = useApi()
    const loading = ref(false)
    const users = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showAddUserDialog = ref(false)
    const editingUser = ref(null)
    const userFormRef = ref()

    const searchForm = reactive({
      email: '',
      status: ''
    })

    const userForm = reactive({
      email: '',
      username: '',
      password: '',
      status: 'active'
    })

    const userRules = {
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' }
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
          ...searchForm
        }
        const response = await api.get('/admin/users', { params })
        users.value = response.data.items
        total.value = response.data.total
      } catch (error) {
        ElMessage.error('加载用户列表失败')
      } finally {
        loading.value = false
      }
    }

    const searchUsers = () => {
      currentPage.value = 1
      loadUsers()
    }

    const resetSearch = () => {
      Object.assign(searchForm, { email: '', status: '' })
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

    const editUser = (user) => {
      editingUser.value = user
      Object.assign(userForm, {
        email: user.email,
        username: user.username,
        status: user.status
      })
      showAddUserDialog.value = true
    }

    const saveUser = async () => {
      try {
        await userFormRef.value.validate()
        if (editingUser.value) {
          await api.put(`/admin/users/${editingUser.value.id}`, userForm)
          ElMessage.success('用户更新成功')
        } else {
          await api.post('/admin/users', userForm)
          ElMessage.success('用户创建成功')
        }
        showAddUserDialog.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error('操作失败')
      }
    }

    const deleteUser = async (user) => {
      try {
        await ElMessageBox.confirm('确定要删除这个用户吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
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
        await api.put(`/admin/users/${user.id}/status`, { status: newStatus })
        ElMessage.success('状态更新成功')
        loadUsers()
      } catch (error) {
        ElMessage.error('状态更新失败')
      }
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

    onMounted(() => {
      loadUsers()
    })

    return {
      loading,
      users,
      currentPage,
      pageSize,
      total,
      searchForm,
      showAddUserDialog,
      editingUser,
      userForm,
      userFormRef,
      userRules,
      searchUsers,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      editUser,
      saveUser,
      deleteUser,
      toggleUserStatus,
      getStatusType,
      getStatusText
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

.search-form {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style> 