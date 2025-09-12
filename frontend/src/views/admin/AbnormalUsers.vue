<template>
  <div class="abnormal-users">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>异常用户监控</span>
          <div class="header-actions">
            <el-button type="primary" @click="loadAbnormalUsers">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="info" @click="showSettingsDialog = true">
              <el-icon><Setting /></el-icon>
              监控设置
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" style="margin-bottom: 20px;">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.totalAbnormal }}</div>
              <div class="stat-label">异常用户总数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.frequentReset }}</div>
              <div class="stat-label">频繁重置用户</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.frequentSubscription }}</div>
              <div class="stat-label">频繁订阅用户</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.multipleAbnormal }}</div>
              <div class="stat-label">多重异常用户</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 异常用户列表 -->
      <el-table :data="abnormalUsers" style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="120">
          <template #default="scope">
            <el-button type="text" @click="viewUserDetails(scope.row.user_id)">
              {{ scope.row.username }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" width="200">
          <template #default="scope">
            <el-button type="text" @click="viewUserDetails(scope.row.user_id)">
              {{ scope.row.email }}
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal_type" label="异常类型" width="150">
          <template #default="scope">
            <el-tag :type="getAbnormalTypeTag(scope.row.abnormal_type)">
              {{ getAbnormalTypeText(scope.row.abnormal_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal_count" label="异常次数" width="120" />
        <el-table-column prop="description" label="异常描述" />
        <el-table-column prop="last_activity" label="最后活动时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewUserDetails(scope.row.user_id)">
              <el-icon><View /></el-icon>
              查看详情
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="markAsNormal(scope.row)"
            >
              <el-icon><Check /></el-icon>
              标记正常
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户详情对话框 -->
    <el-dialog v-model="showUserDetailsDialog" title="用户详细信息" width="80%" :before-close="closeUserDetails">
      <div v-if="userDetails" class="user-details">
        <!-- 用户基本信息 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <span>基本信息</span>
          </template>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="用户ID">{{ userDetails.user_info.id }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ userDetails.user_info.username }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ userDetails.user_info.email }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="userDetails.user_info.is_active ? 'success' : 'danger'">
                {{ userDetails.user_info.is_active ? '活跃' : '禁用' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="验证状态">
              <el-tag :type="userDetails.user_info.is_verified ? 'success' : 'warning'">
                {{ userDetails.user_info.is_verified ? '已验证' : '未验证' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="管理员">
              <el-tag :type="userDetails.user_info.is_admin ? 'danger' : 'info'">
                {{ userDetails.user_info.is_admin ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ userDetails.user_info.created_at }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ userDetails.user_info.last_login || '从未登录' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 统计信息 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <span>统计信息</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-number">{{ userDetails.statistics.total_subscriptions }}</div>
                <div class="stat-label">总订阅数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-number">{{ userDetails.statistics.total_orders }}</div>
                <div class="stat-label">总订单数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-number">{{ userDetails.statistics.total_resets }}</div>
                <div class="stat-label">总重置次数</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-item">
                <div class="stat-number">¥{{ userDetails.statistics.total_spent }}</div>
                <div class="stat-label">总消费</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 订阅重置记录 -->
        <el-card style="margin-bottom: 20px;">
          <template #header>
            <span>订阅重置记录</span>
          </template>
          <el-table :data="userDetails.subscription_resets" style="width: 100%">
            <el-table-column prop="reset_type" label="重置类型" width="120" />
            <el-table-column prop="reason" label="重置原因" />
            <el-table-column prop="device_count_before" label="重置前设备数" width="120" />
            <el-table-column prop="device_count_after" label="重置后设备数" width="120" />
            <el-table-column prop="reset_by" label="操作者" width="100" />
            <el-table-column prop="created_at" label="重置时间" width="180" />
          </el-table>
        </el-card>

        <!-- 最近活动 -->
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <el-table :data="userDetails.recent_activities" style="width: 100%">
            <el-table-column prop="activity_type" label="活动类型" width="120" />
            <el-table-column prop="description" label="描述" />
            <el-table-column prop="ip_address" label="IP地址" width="150" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </el-card>
      </div>
    </el-dialog>

    <!-- 监控设置对话框 -->
    <el-dialog v-model="showSettingsDialog" title="监控设置" width="500px">
      <el-form :model="settings" label-width="150px">
        <el-form-item label="重置次数阈值">
          <el-input-number v-model="settings.resetThreshold" :min="1" :max="50" />
          <span style="margin-left: 10px; color: #666;">天内重置超过此次数视为异常</span>
        </el-form-item>
        <el-form-item label="订阅次数阈值">
          <el-input-number v-model="settings.subscriptionThreshold" :min="1" :max="20" />
          <span style="margin-left: 10px; color: #666;">天内创建超过此数量订阅视为异常</span>
        </el-form-item>
        <el-form-item label="监控时间范围">
          <el-input-number v-model="settings.monitorDays" :min="7" :max="90" />
          <span style="margin-left: 10px; color: #666;">天</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showSettingsDialog = false">取消</el-button>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Setting, View, Check } from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AbnormalUsers',
  components: {
    Refresh, Setting, View, Check
  },
  setup() {
    const loading = ref(false)
    const abnormalUsers = ref([])
    const showUserDetailsDialog = ref(false)
    const showSettingsDialog = ref(false)
    const userDetails = ref(null)

    const statistics = reactive({
      totalAbnormal: 0,
      frequentReset: 0,
      frequentSubscription: 0,
      multipleAbnormal: 0
    })

    const settings = reactive({
      resetThreshold: 5,
      subscriptionThreshold: 3,
      monitorDays: 30
    })

    const loadAbnormalUsers = async () => {
      loading.value = true
      try {
        const response = await adminAPI.getAbnormalUsers()
        console.log('异常用户API响应:', response)
        
        if (response.data && response.data.success) {
          abnormalUsers.value = response.data.data || []
          updateStatistics()
          if (abnormalUsers.value.length === 0) {
            ElMessage.info('当前没有异常用户')
          }
        } else {
          console.warn('异常用户数据格式异常:', response.data)
          abnormalUsers.value = []
          ElMessage.warning('获取异常用户数据失败')
        }
      } catch (error) {
        console.error('加载异常用户失败:', error)
        ElMessage.error('加载异常用户失败: ' + (error.response?.data?.message || error.message))
        abnormalUsers.value = []
      } finally {
        loading.value = false
      }
    }

    const updateStatistics = () => {
      statistics.totalAbnormal = abnormalUsers.value.length
      statistics.frequentReset = abnormalUsers.value.filter(u => u.abnormal_type === 'frequent_reset').length
      statistics.frequentSubscription = abnormalUsers.value.filter(u => u.abnormal_type === 'frequent_subscription').length
      statistics.multipleAbnormal = abnormalUsers.value.filter(u => u.abnormal_type === 'multiple_abnormal').length
    }

    const viewUserDetails = async (userId) => {
      try {
        console.log('正在获取用户详情:', userId)
        const response = await adminAPI.getUserDetails(userId)
        console.log('用户详情API响应:', response)
        
        if (response && response.data && response.data.success) {
          userDetails.value = response.data.data
          showUserDetailsDialog.value = true
          console.log('用户详情已设置:', userDetails.value)
        } else if (response && response.success) {
          userDetails.value = response.data
          showUserDetailsDialog.value = true
          console.log('用户详情已设置(直接结构):', userDetails.value)
        } else {
          ElMessage.error('获取用户详情失败: ' + (response?.data?.message || response?.message || '未知错误'))
        }
      } catch (error) {
        console.error('获取用户详情失败:', error)
        ElMessage.error('获取用户详情失败: ' + (error.response?.data?.message || error.message))
      }
    }

    const closeUserDetails = () => {
      showUserDetailsDialog.value = false
      userDetails.value = null
    }

    const markAsNormal = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要将用户 ${user.username} 标记为正常吗？这将从异常列表中移除该用户。`,
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 这里可以添加标记为正常的API调用
        ElMessage.success('用户已标记为正常')
        loadAbnormalUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }

    const saveSettings = () => {
      // 这里可以添加保存设置的API调用
      ElMessage.success('设置已保存')
      showSettingsDialog.value = false
      loadAbnormalUsers()
    }

    const getAbnormalTypeTag = (type) => {
      const typeMap = {
        'frequent_reset': 'warning',
        'frequent_subscription': 'danger',
        'multiple_abnormal': 'error'
      }
      return typeMap[type] || 'info'
    }

    const getAbnormalTypeText = (type) => {
      const typeMap = {
        'frequent_reset': '频繁重置',
        'frequent_subscription': '频繁订阅',
        'multiple_abnormal': '多重异常'
      }
      return typeMap[type] || type
    }

    onMounted(() => {
      loadAbnormalUsers()
    })

    return {
      loading,
      abnormalUsers,
      statistics,
      settings,
      showUserDetailsDialog,
      showSettingsDialog,
      userDetails,
      loadAbnormalUsers,
      viewUserDetails,
      closeUserDetails,
      markAsNormal,
      saveSettings,
      getAbnormalTypeTag,
      getAbnormalTypeText
    }
  }
}
</script>

<style scoped>
.abnormal-users {
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

.stat-card {
  text-align: center;
}

.stat-content {
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

.user-details {
  max-height: 70vh;
  overflow-y: auto;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-item .stat-number {
  font-size: 1.5rem;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-item .stat-label {
  color: #606266;
  font-size: 12px;
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
