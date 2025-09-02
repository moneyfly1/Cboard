<template>
  <div class="email-queue-admin">
    <div class="page-header">
      <h1>邮件队列管理</h1>
      <div class="header-actions">
        <el-button @click="refreshQueue" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="warning" @click="clearFailedEmails">
          <el-icon><Delete /></el-icon>
          清空失败邮件
        </el-button>
        <el-button type="danger" @click="clearAllEmails">
          <el-icon><Delete /></el-icon>
          清空所有邮件
        </el-button>
      </div>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ statistics.total || 0 }}</div>
            <div class="stat-label">总邮件数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number success">{{ statistics.pending || 0 }}</div>
            <div class="stat-label">待发送</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number warning">{{ statistics.sent || 0 }}</div>
            <div class="stat-label">已发送</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number danger">{{ statistics.failed || 0 }}</div>
            <div class="stat-label">发送失败</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和搜索 -->
    <el-card class="filter-section">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="选择状态" clearable>
            <el-option label="待发送" value="pending" />
            <el-option label="发送中" value="sending" />
            <el-option label="已发送" value="sent" />
            <el-option label="发送失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="filterForm.priority" placeholder="选择优先级" clearable>
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="filterForm.email" placeholder="搜索邮箱地址" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="applyFilter">
            <el-icon><Search /></el-icon>
            筛选
          </el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 邮件队列列表 -->
    <el-card class="queue-list">
      <template #header>
        <div class="card-header">
          <span>邮件队列列表</span>
          <div class="header-info">
            共 {{ pagination.total }} 条记录，第 {{ pagination.page }}/{{ pagination.pages }} 页
          </div>
        </div>
      </template>

      <el-table :data="emailList" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="to_email" label="收件人" min-width="200" />
        <el-table-column prop="subject" label="主题" min-width="250" />
        <el-table-column prop="template_name" label="模板" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityTagType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="retry_count" label="重试次数" width="100">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.retry_count > 0 }">
              {{ row.retry_count }}/{{ row.max_retries || 3 }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewEmailDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button 
              v-if="row.status === 'failed'" 
              size="small" 
              type="warning" 
              @click="retryEmail(row)"
            >
              <el-icon><Refresh /></el-icon>
              重试
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteEmail(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 邮件详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      title="邮件详情" 
      width="70%"
      :close-on-click-modal="false"
    >
      <div v-if="emailDetail" class="email-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="邮件ID">{{ emailDetail.id }}</el-descriptions-item>
          <el-descriptions-item label="收件人">{{ emailDetail.to_email }}</el-descriptions-item>
          <el-descriptions-item label="主题">{{ emailDetail.subject }}</el-descriptions-item>
          <el-descriptions-item label="模板">{{ emailDetail.template_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(emailDetail.status)">
              {{ getStatusText(emailDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityTagType(emailDetail.priority)">
              {{ getPriorityText(emailDetail.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="重试次数">{{ emailDetail.retry_count }}/{{ emailDetail.max_retries }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(emailDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="发送时间" v-if="emailDetail.sent_at">
            {{ formatDate(emailDetail.sent_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="处理时间" v-if="emailDetail.processing_time">
            {{ emailDetail.processing_time }}ms
          </el-descriptions-item>
        </el-descriptions>

        <!-- 模板数据 -->
        <div class="detail-section" v-if="emailDetail.template_data">
          <h4>模板数据</h4>
          <el-input
            v-model="emailDetail.template_data"
            type="textarea"
            :rows="6"
            readonly
          />
        </div>

        <!-- 错误信息 -->
        <div class="detail-section" v-if="emailDetail.error_message">
          <h4>错误信息</h4>
          <el-alert
            :title="emailDetail.error_message"
            type="error"
            :description="emailDetail.error_details || '无详细错误信息'"
            show-icon
            :closable="false"
          />
        </div>

        <!-- SMTP响应 -->
        <div class="detail-section" v-if="emailDetail.smtp_response">
          <h4>SMTP响应</h4>
          <el-input
            v-model="emailDetail.smtp_response"
            type="textarea"
            :rows="3"
            readonly
          />
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button 
            v-if="emailDetail && emailDetail.status === 'failed'" 
            type="warning" 
            @click="retryEmailFromDetail"
          >
            重试发送
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, View, Delete } from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'

export default {
  name: 'EmailQueue',
  components: {
    Refresh, Search, View, Delete
  },
  setup() {
    const loading = ref(false)
    const detailDialogVisible = ref(false)
    const emailDetail = ref(null)
    
    const filterForm = reactive({
      status: '',
      priority: '',
      email: ''
    })
    
    const pagination = reactive({
      page: 1,
      size: 20,
      total: 0,
      pages: 0
    })
    
    const emailList = ref([])
    const statistics = reactive({
      total: 0,
      pending: 0,
      sent: 0,
      failed: 0
    })

    // 获取邮件队列列表
    const fetchEmailQueue = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          size: pagination.size,
          ...filterForm
        }
        
        const response = await adminAPI.getEmailQueue(params)
        if (response.success) {
          emailList.value = response.data.emails
          pagination.total = response.data.total
          pagination.pages = response.data.pages
        }
      } catch (error) {
        ElMessage.error('获取邮件队列失败')
      } finally {
        loading.value = false
      }
    }

    // 获取统计信息
    const fetchStatistics = async () => {
      try {
        const response = await adminAPI.getEmailQueueStatistics()
        if (response.success) {
          Object.assign(statistics, response.data)
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      }
    }

    // 刷新队列
    const refreshQueue = () => {
      fetchEmailQueue()
      fetchStatistics()
    }

    // 应用筛选
    const applyFilter = () => {
      pagination.page = 1
      fetchEmailQueue()
    }

    // 重置筛选
    const resetFilter = () => {
      Object.assign(filterForm, {
        status: '',
        priority: '',
        email: ''
      })
      pagination.page = 1
      fetchEmailQueue()
    }

    // 查看邮件详情
    const viewEmailDetail = async (row) => {
      try {
        const response = await adminAPI.getEmailDetail(row.id)
        if (response.success) {
          emailDetail.value = response.data
          detailDialogVisible.value = true
        }
      } catch (error) {
        ElMessage.error('获取邮件详情失败')
      }
    }

    // 重试邮件
    const retryEmail = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要重试发送邮件到 ${row.to_email} 吗？`,
          '确认重试',
          { type: 'warning' }
        )
        
        const response = await adminAPI.retryEmail(row.id)
        if (response.success) {
          ElMessage.success('邮件重试成功')
          refreshQueue()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('邮件重试失败')
        }
      }
    }

    // 从详情对话框重试
    const retryEmailFromDetail = async () => {
      if (emailDetail.value) {
        await retryEmail(emailDetail.value)
        detailDialogVisible.value = false
      }
    }

    // 删除邮件
    const deleteEmail = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除发送到 ${row.to_email} 的邮件吗？`,
          '确认删除',
          { type: 'warning' }
        )
        
        const response = await adminAPI.deleteEmailFromQueue(row.id)
        if (response.success) {
          ElMessage.success('邮件删除成功')
          refreshQueue()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('邮件删除失败')
        }
      }
    }

    // 清空失败邮件
    const clearFailedEmails = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有失败的邮件吗？',
          '确认清空',
          { type: 'warning' }
        )
        
        const response = await adminAPI.clearEmailQueue('failed')
        if (response.success) {
          ElMessage.success('失败邮件清空成功')
          refreshQueue()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清空失败邮件失败')
        }
      }
    }

    // 清空所有邮件
    const clearAllEmails = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要清空所有邮件吗？此操作不可恢复！',
          '确认清空',
          { type: 'error' }
        )
        
        const response = await adminAPI.clearEmailQueue()
        if (response.success) {
          ElMessage.success('所有邮件清空成功')
          refreshQueue()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清空所有邮件失败')
        }
      }
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pagination.size = size
      pagination.page = 1
      fetchEmailQueue()
    }

    const handleCurrentChange = (page) => {
      pagination.page = page
      fetchEmailQueue()
    }

    // 状态标签类型
    const getStatusTagType = (status) => {
      const statusMap = {
        pending: 'warning',
        sending: 'info',
        sent: 'success',
        failed: 'danger',
        cancelled: 'info'
      }
      return statusMap[status] || 'info'
    }

    // 状态文本
    const getStatusText = (status) => {
      const statusMap = {
        pending: '待发送',
        sending: '发送中',
        sent: '已发送',
        failed: '发送失败',
        cancelled: '已取消'
      }
      return statusMap[status] || status
    }

    // 优先级标签类型
    const getPriorityTagType = (priority) => {
      const priorityMap = {
        high: 'danger',
        medium: 'warning',
        low: 'info'
      }
      return priorityMap[priority] || 'info'
    }

    // 优先级文本
    const getPriorityText = (priority) => {
      const priorityMap = {
        high: '高',
        medium: '中',
        low: '低'
      }
      return priorityMap[priority] || priority
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }

    onMounted(() => {
      fetchEmailQueue()
      fetchStatistics()
    })

    return {
      loading,
      detailDialogVisible,
      emailDetail,
      filterForm,
      pagination,
      emailList,
      statistics,
      fetchEmailQueue,
      fetchStatistics,
      refreshQueue,
      applyFilter,
      resetFilter,
      viewEmailDetail,
      retryEmail,
      retryEmailFromDetail,
      deleteEmail,
      clearFailedEmails,
      clearAllEmails,
      handleSizeChange,
      handleCurrentChange,
      getStatusTagType,
      getStatusText,
      getPriorityTagType,
      getPriorityText,
      formatDate
    }
  }
}
</script>

<style scoped>
.email-queue-admin {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #333;
  font-size: 1.8rem;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-overview {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.stat-number.success {
  color: #67c23a;
}

.stat-number.warning {
  color: #e6a23c;
}

.stat-number.danger {
  color: #f56c6c;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.queue-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  color: #666;
  font-size: 0.9rem;
}

.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

.email-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.detail-section {
  margin-top: 20px;
}

.detail-section h4 {
  margin-bottom: 10px;
  color: #333;
  font-size: 1rem;
}

.text-danger {
  color: #f56c6c;
}

.dialog-footer {
  text-align: right;
}

@media (max-width: 768px) {
  .email-queue-admin {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .filter-form {
    flex-direction: column;
  }
  
  .filter-form .el-form-item {
    margin-bottom: 10px;
  }
}
</style>
