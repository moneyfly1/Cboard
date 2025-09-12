<template>
  <div class="notifications-admin-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>通知管理</h2>
          <el-button type="primary" @click="showAddDialog">
            <i class="el-icon-plus"></i>
            发布通知
          </el-button>
        </div>
      </template>

      <!-- 通知列表 -->
      <el-table
        :data="notifications"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="type" label="类型">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="editNotification(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deleteNotification(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑通知对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑通知' : '发布通知'"
      width="800px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="通知标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入通知标题" />
        </el-form-item>
        
        <el-form-item label="通知类型" prop="type">
          <el-select v-model="form.type" placeholder="选择通知类型">
            <el-option label="系统公告" value="announcement" />
            <el-option label="维护通知" value="maintenance" />
            <el-option label="更新通知" value="update" />
            <el-option label="活动通知" value="activity" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="通知内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="请输入通知内容"
          />
        </el-form-item>
        
        <el-form-item label="发布状态" prop="status">
          <el-select v-model="form.status" placeholder="选择发布状态" disabled>
            <el-option label="发布" value="published" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="发送邮件" prop="send_email">
          <el-switch v-model="form.send_email" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitLoading"
          >
            {{ isEdit ? '更新' : '发布' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { notificationAPI } from '@/utils/api'

export default {
  name: 'AdminNotifications',
  setup() {
    const loading = ref(false)
    const submitLoading = ref(false)
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const formRef = ref()
    const notifications = ref([])

    const pagination = reactive({
      page: 1,
      size: 20,
      total: 0
    })

    const form = reactive({
      title: '',
      type: 'announcement',
      content: '',
      status: 'published',
      send_email: false
    })

    const rules = {
      title: [
        { required: true, message: '请输入通知标题', trigger: 'blur' }
      ],
      type: [
        { required: true, message: '请选择通知类型', trigger: 'change' }
      ],
      content: [
        { required: true, message: '请输入通知内容', trigger: 'blur' }
      ],
      status: [
        { required: true, message: '请选择发布状态', trigger: 'change' }
      ]
    }

    // 获取通知类型颜色
    const getTypeColor = (type) => {
      const colors = {
        announcement: 'primary',
        maintenance: 'warning',
        update: 'success',
        activity: 'info'
      }
      return colors[type] || 'info'
    }

    // 获取通知类型标签
    const getTypeLabel = (type) => {
      const labels = {
        announcement: '系统公告',
        maintenance: '维护通知',
        update: '更新通知',
        activity: '活动通知'
      }
      return labels[type] || type
    }

    // 获取通知列表
    const fetchNotifications = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          size: pagination.size
        }
        const response = await notificationAPI.getNotifications(params)
        console.log('通知API响应:', response)
        console.log('通知响应数据结构:', response.data)
        if (response.data && response.data.success) {
          notifications.value = response.data.data?.announcements || []
          pagination.total = response.data.data?.total || 0
        } else {
          notifications.value = []
          pagination.total = 0
        }
      } catch (error) {
        ElMessage.error('获取通知列表失败')
        console.error('获取通知列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pagination.size = size
      pagination.page = 1
      fetchNotifications()
    }

    const handleCurrentChange = (page) => {
      pagination.page = page
      fetchNotifications()
    }

    // 显示添加对话框
    const showAddDialog = () => {
      isEdit.value = false
      resetForm()
      dialogVisible.value = true
    }

    // 编辑通知
    const editNotification = (notification) => {
      isEdit.value = true
      Object.assign(form, notification)
      dialogVisible.value = true
    }

    // 重置表单
    const resetForm = () => {
      Object.assign(form, {
        title: '',
        type: 'announcement',
        content: '',
        status: 'published',
        send_email: false
      })
      if (formRef.value) {
        formRef.value.resetFields()
      }
    }

    // 提交表单
    const handleSubmit = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        submitLoading.value = true

        if (isEdit.value) {
          await notificationAPI.updateNotification(form.id, form)
          ElMessage.success('通知更新成功')
        } else {
          await notificationAPI.createNotification(form)
          ElMessage.success('通知发布成功')
        }

        dialogVisible.value = false
        fetchNotifications()
      } catch (error) {
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('操作失败')
        }
      } finally {
        submitLoading.value = false
      }
    }

    // 删除通知
    const deleteNotification = async (id) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这个通知吗？',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await notificationAPI.deleteNotification(id)
        ElMessage.success('通知删除成功')
        fetchNotifications()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
          console.error('删除通知失败:', error)
        }
      }
    }

    onMounted(() => {
      fetchNotifications()
    })

    return {
      loading,
      submitLoading,
      dialogVisible,
      isEdit,
      formRef,
      notifications,
      pagination,
      form,
      rules,
      getTypeColor,
      getTypeLabel,
      handleSizeChange,
      handleCurrentChange,
      showAddDialog,
      editNotification,
      handleSubmit,
      deleteNotification
    }
  }
}
</script>

<style scoped>
.notifications-admin-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.pagination-section {
  margin-top: 20px;
  text-align: right;
}

@media (max-width: 768px) {
  .notifications-admin-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
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