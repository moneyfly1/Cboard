<template>
  <div class="settings-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>系统设置</h1>
      <el-button type="primary" @click="saveAllSettings" :loading="saving">
        <i class="el-icon-check"></i>
        保存所有设置
      </el-button>
    </div>

    <!-- 设置分类标签页 -->
    <el-tabs v-model="activeTab" type="card" class="settings-tabs">
      <!-- 基本设置 -->
      <el-tab-pane label="基本设置" name="general">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>网站基本设置</span>
            </div>
          </template>
          
          <el-form :model="settings.general" label-width="120px">
            <el-form-item label="网站名称">
              <el-input v-model="settings.general.site_name" placeholder="请输入网站名称" />
            </el-form-item>
            
            <el-form-item label="网站描述">
              <el-input 
                v-model="settings.general.site_description" 
                type="textarea"
                placeholder="请输入网站描述"
                :rows="3"
              />
            </el-form-item>
            
            <el-form-item label="网站关键词">
              <el-input v-model="settings.general.site_keywords" placeholder="请输入网站关键词，用逗号分隔" />
            </el-form-item>
            
            <el-form-item label="网站Logo">
              <el-input v-model="settings.general.site_logo" placeholder="请输入Logo图片URL" />
            </el-form-item>
            
            <el-form-item label="网站图标">
              <el-input v-model="settings.general.site_favicon" placeholder="请输入Favicon图标URL" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 注册设置 -->
      <el-tab-pane label="注册设置" name="registration">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>用户注册设置</span>
            </div>
          </template>
          
          <el-form :model="settings.registration" label-width="120px">
            <el-form-item label="允许注册">
              <el-switch 
                v-model="settings.registration.allow_registration"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="邮箱验证">
              <el-switch 
                v-model="settings.registration.require_email_verification"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="仅允许QQ邮箱">
              <el-switch 
                v-model="settings.registration.allow_qq_email_only"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="最小密码长度">
              <el-input-number 
                v-model="settings.registration.min_password_length"
                :min="6"
                :max="20"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 邮件设置 -->
      <el-tab-pane label="邮件设置" name="email">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>邮件服务器设置</span>
            </div>
          </template>
          
          <el-form :model="settings.email" label-width="120px">
            <el-form-item label="SMTP服务器">
              <el-input v-model="settings.email.smtp_host" placeholder="请输入SMTP服务器地址" />
            </el-form-item>
            
            <el-form-item label="SMTP端口">
              <el-input-number v-model="settings.email.smtp_port" :min="1" :max="65535" />
            </el-form-item>
            
            <el-form-item label="SMTP用户名">
              <el-input v-model="settings.email.smtp_username" placeholder="请输入SMTP用户名" />
            </el-form-item>
            
            <el-form-item label="SMTP密码">
              <el-input 
                v-model="settings.email.smtp_password" 
                type="password"
                placeholder="请输入SMTP密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="加密方式">
              <el-select v-model="settings.email.smtp_encryption">
                <el-option label="无" value="" />
                <el-option label="TLS" value="tls" />
                <el-option label="SSL" value="ssl" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="发件人邮箱">
              <el-input v-model="settings.email.from_email" placeholder="请输入发件人邮箱" />
            </el-form-item>
            
            <el-form-item label="发件人名称">
              <el-input v-model="settings.email.from_name" placeholder="请输入发件人名称" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="testEmailSettings">
                测试邮件设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 通知设置 -->
      <el-tab-pane label="通知设置" name="notification">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>通知方式设置</span>
            </div>
          </template>
          
          <el-form :model="settings.notification" label-width="120px">
            <el-form-item label="邮件通知">
              <el-switch 
                v-model="settings.notification.enable_email_notification"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <el-form-item label="短信通知">
              <el-switch 
                v-model="settings.notification.enable_sms_notification"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <el-form-item label="Webhook通知">
              <el-switch 
                v-model="settings.notification.enable_webhook_notification"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
            
            <el-form-item label="Webhook地址" v-if="settings.notification.enable_webhook_notification">
              <el-input v-model="settings.notification.webhook_url" placeholder="请输入Webhook地址" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 主题设置 -->
      <el-tab-pane label="主题设置" name="theme">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>主题配置</span>
            </div>
          </template>
          
          <el-form :model="settings.theme" label-width="120px">
            <el-form-item label="默认主题">
              <el-select v-model="settings.theme.default_theme">
                <el-option label="默认主题" value="default" />
                <el-option label="暗色主题" value="dark" />
                <el-option label="蓝色主题" value="blue" />
                <el-option label="绿色主题" value="green" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="允许用户选择主题">
              <el-switch 
                v-model="settings.theme.allow_user_theme"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="可用主题">
              <el-checkbox-group v-model="settings.theme.available_themes">
                <el-checkbox label="default">默认主题</el-checkbox>
                <el-checkbox label="dark">暗色主题</el-checkbox>
                <el-checkbox label="blue">蓝色主题</el-checkbox>
                <el-checkbox label="green">绿色主题</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 支付设置 -->
      <el-tab-pane label="支付设置" name="payment">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>支付配置</span>
            </div>
          </template>
          
          <el-form :model="settings.payment" label-width="120px">
            <el-form-item label="启用支付">
              <el-switch 
                v-model="settings.payment.enable_payment"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="默认支付方式">
              <el-select v-model="settings.payment.default_payment_method" placeholder="请选择默认支付方式">
                <el-option label="支付宝" value="alipay" />
                <el-option label="微信支付" value="wechat" />
                <el-option label="PayPal" value="paypal" />
                <el-option label="Stripe" value="stripe" />
                <el-option label="加密货币" value="crypto" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="支付货币">
              <el-select v-model="settings.payment.payment_currency">
                <el-option label="人民币 (CNY)" value="CNY" />
                <el-option label="美元 (USD)" value="USD" />
                <el-option label="欧元 (EUR)" value="EUR" />
                <el-option label="日元 (JPY)" value="JPY" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 公告设置 -->
      <el-tab-pane label="公告设置" name="announcement">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>公告管理</span>
              <el-button type="primary" size="small" @click="showAnnouncementDialog = true">
                <i class="el-icon-plus"></i>
                添加公告
              </el-button>
            </div>
          </template>
          
          <el-form :model="settings.announcement" label-width="120px">
            <el-form-item label="启用公告">
              <el-switch 
                v-model="settings.announcement.enable_announcement"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="公告位置">
              <el-select v-model="settings.announcement.announcement_position">
                <el-option label="顶部" value="top" />
                <el-option label="侧边栏" value="sidebar" />
                <el-option label="弹窗" value="popup" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="最大公告数">
              <el-input-number 
                v-model="settings.announcement.max_announcements"
                :min="1"
                :max="20"
              />
            </el-form-item>
          </el-form>
          
          <!-- 公告列表 -->
          <div class="announcement-list">
            <h4>公告列表</h4>
            <el-table :data="announcements" style="width: 100%">
              <el-table-column prop="title" label="标题" />
              <el-table-column prop="type" label="类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getAnnouncementTypeColor(row.type)">
                    {{ getAnnouncementTypeLabel(row.type) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'danger'">
                    {{ row.is_active ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="is_pinned" label="置顶" width="100">
                <template #default="{ row }">
                  <el-tag v-if="row.is_pinned" type="warning">置顶</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200">
                <template #default="{ row }">
                  <el-button type="text" size="small" @click="editAnnouncement(row)">
                    编辑
                  </el-button>
                  <el-button type="text" size="small" @click="toggleAnnouncementStatus(row)">
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-button>
                  <el-button type="text" size="small" @click="toggleAnnouncementPin(row)">
                    {{ row.is_pinned ? '取消置顶' : '置顶' }}
                  </el-button>
                  <el-button type="text" size="small" class="danger-text" @click="deleteAnnouncement(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 安全设置 -->
      <el-tab-pane label="安全设置" name="security">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>安全配置</span>
            </div>
          </template>
          
          <el-form :model="settings.security" label-width="120px">
            <el-form-item label="启用验证码">
              <el-switch 
                v-model="settings.security.enable_captcha"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="最大登录尝试">
              <el-input-number 
                v-model="settings.security.max_login_attempts"
                :min="3"
                :max="10"
              />
            </el-form-item>
            
            <el-form-item label="锁定时间（分钟）">
              <el-input-number 
                v-model="settings.security.lockout_duration"
                :min="5"
                :max="1440"
              />
            </el-form-item>
            
            <el-form-item label="会话超时（分钟）">
              <el-input-number 
                v-model="settings.security.session_timeout"
                :min="30"
                :max="10080"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 性能设置 -->
      <el-tab-pane label="性能设置" name="performance">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>性能优化</span>
            </div>
          </template>
          
          <el-form :model="settings.performance" label-width="120px">
            <el-form-item label="启用缓存">
              <el-switch 
                v-model="settings.performance.enable_cache"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="缓存时间（秒）">
              <el-input-number 
                v-model="settings.performance.cache_duration"
                :min="60"
                :max="86400"
              />
            </el-form-item>
            
            <el-form-item label="启用压缩">
              <el-switch 
                v-model="settings.performance.enable_compression"
                active-text="是"
                inactive-text="否"
              />
            </el-form-item>
            
            <el-form-item label="最大上传大小（MB）">
              <el-input-number 
                v-model="settings.performance.max_upload_size"
                :min="1"
                :max="100"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 公告编辑对话框 -->
    <el-dialog
      v-model="showAnnouncementDialog"
      :title="editingAnnouncement ? '编辑公告' : '添加公告'"
      width="600px"
    >
      <el-form
        ref="announcementFormRef"
        :model="announcementForm"
        :rules="announcementRules"
        label-width="100px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="announcementForm.title" placeholder="请输入公告标题" />
        </el-form-item>
        
        <el-form-item label="内容" prop="content">
          <el-input 
            v-model="announcementForm.content" 
            type="textarea"
            placeholder="请输入公告内容"
            :rows="6"
          />
        </el-form-item>
        
        <el-form-item label="类型" prop="type">
          <el-select v-model="announcementForm.type">
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="成功" value="success" />
            <el-option label="错误" value="error" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标用户" prop="target_users">
          <el-select v-model="announcementForm.target_users">
            <el-option label="所有用户" value="all" />
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch 
            v-model="announcementForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
        
        <el-form-item label="置顶">
          <el-switch 
            v-model="announcementForm.is_pinned"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="announcementForm.start_time"
            type="datetime"
            placeholder="选择开始时间"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="announcementForm.end_time"
            type="datetime"
            placeholder="选择结束时间"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAnnouncementDialog = false">取消</el-button>
          <el-button type="primary" @click="saveAnnouncement" :loading="saving">
            {{ editingAnnouncement ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '@/utils/api'

// 响应式数据
const activeTab = ref('general')
const saving = ref(false)
const showAnnouncementDialog = ref(false)
const editingAnnouncement = ref(null)
const announcements = ref([])

// 设置数据
const settings = reactive({
  general: {
    site_name: '',
    site_description: '',
    site_keywords: '',
    site_logo: '',
    site_favicon: ''
  },
  registration: {
    allow_registration: true,
    require_email_verification: true,
    allow_qq_email_only: true,
    min_password_length: 8
  },
  email: {
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    smtp_encryption: 'tls',
    from_email: '',
    from_name: ''
  },
  notification: {
    enable_email_notification: true,
    enable_sms_notification: false,
    enable_webhook_notification: false,
    webhook_url: ''
  },
  theme: {
    default_theme: 'default',
    allow_user_theme: true,
    available_themes: ['default', 'dark', 'blue', 'green']
  },
  payment: {
    enable_payment: true,
    default_payment_method: '',
    payment_currency: 'CNY'
  },
  announcement: {
    enable_announcement: true,
    announcement_position: 'top',
    max_announcements: 5
  },
  security: {
    enable_captcha: false,
    max_login_attempts: 5,
    lockout_duration: 30,
    session_timeout: 1440
  },
  performance: {
    enable_cache: true,
    cache_duration: 3600,
    enable_compression: true,
    max_upload_size: 10
  }
})

// 公告表单
const announcementForm = reactive({
  title: '',
  content: '',
  type: 'info',
  target_users: 'all',
  is_active: true,
  is_pinned: false,
  start_time: null,
  end_time: null
})

// 表单验证规则
const announcementRules = {
  title: [
    { required: true, message: '请输入公告标题', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' }
  ]
}

// 方法
const loadSettings = async () => {
  try {
    const response = await adminAPI.getSystemSettings()
    const data = response.data
    
    // 更新设置数据
    Object.keys(settings).forEach(category => {
      if (data[category]) {
        Object.assign(settings[category], data[category])
      }
    })
  } catch (error) {
    ElMessage.error('加载设置失败')
  }
}

const loadAnnouncements = async () => {
  try {
    const response = await adminAPI.getAnnouncementsAdmin()
    announcements.value = response.data.announcements
  } catch (error) {
    ElMessage.error('加载公告失败')
  }
}

const saveAllSettings = async () => {
  saving.value = true
  try {
    // 合并所有设置
    const allSettings = {}
    Object.keys(settings).forEach(category => {
      Object.keys(settings[category]).forEach(key => {
        allSettings[`${category}_${key}`] = settings[category][key]
      })
    })
    
    await adminAPI.updateSystemSettings(allSettings)
    ElMessage.success('设置保存成功')
  } catch (error) {
    ElMessage.error('设置保存失败')
  } finally {
    saving.value = false
  }
}

const testEmailSettings = async () => {
  try {
    await adminAPI.testEmailSettings(settings.email)
    ElMessage.success('邮件设置测试成功')
  } catch (error) {
    ElMessage.error('邮件设置测试失败')
  }
}

const editAnnouncement = (announcement) => {
  editingAnnouncement.value = announcement
  Object.assign(announcementForm, {
    title: announcement.title,
    content: announcement.content,
    type: announcement.type,
    target_users: announcement.target_users,
    is_active: announcement.is_active,
    is_pinned: announcement.is_pinned,
    start_time: announcement.start_time ? new Date(announcement.start_time) : null,
    end_time: announcement.end_time ? new Date(announcement.end_time) : null
  })
  showAnnouncementDialog.value = true
}

const saveAnnouncement = async () => {
  saving.value = true
  try {
    if (editingAnnouncement.value) {
      await adminAPI.updateAnnouncement(editingAnnouncement.value.id, announcementForm)
      ElMessage.success('公告更新成功')
    } else {
      await adminAPI.createAnnouncement(announcementForm)
      ElMessage.success('公告创建成功')
    }
    showAnnouncementDialog.value = false
    loadAnnouncements()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const toggleAnnouncementStatus = async (announcement) => {
  try {
    await adminAPI.toggleAnnouncementStatus(announcement.id)
    ElMessage.success('状态切换成功')
    loadAnnouncements()
  } catch (error) {
    ElMessage.error('状态切换失败')
  }
}

const toggleAnnouncementPin = async (announcement) => {
  try {
    await adminAPI.toggleAnnouncementPin(announcement.id)
    ElMessage.success('置顶状态切换成功')
    loadAnnouncements()
  } catch (error) {
    ElMessage.error('置顶状态切换失败')
  }
}

const deleteAnnouncement = async (announcement) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除公告"${announcement.title}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await adminAPI.deleteAnnouncement(announcement.id)
    ElMessage.success('删除成功')
    loadAnnouncements()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getAnnouncementTypeLabel = (type) => {
  const labels = {
    info: '信息',
    warning: '警告',
    success: '成功',
    error: '错误'
  }
  return labels[type] || type
}

const getAnnouncementTypeColor = (type) => {
  const colors = {
    info: '',
    warning: 'warning',
    success: 'success',
    error: 'danger'
  }
  return colors[type] || ''
}

// 生命周期
onMounted(() => {
  loadSettings()
  loadAnnouncements()
})
</script>

<style scoped lang="scss">
.settings-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
  }
  
  .settings-tabs {
    .settings-card {
      margin-bottom: 20px;
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
  }
  
  .announcement-list {
    margin-top: 20px;
    
    h4 {
      margin: 0 0 16px 0;
      color: #303133;
    }
  }
  
  .danger-text {
    color: #f56c6c;
  }
}
</style> 