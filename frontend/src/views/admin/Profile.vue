<template>
  <div class="admin-profile-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>个人资料</h2>
          <p>管理您的账户信息和密码</p>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form
            ref="basicFormRef"
            :model="basicForm"
            :rules="basicRules"
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="用户名">
              <el-input v-model="basicForm.username" disabled />
              <small class="form-tip">用户名不可修改</small>
            </el-form-item>
            
            <el-form-item label="邮箱地址">
              <el-input v-model="basicForm.email" disabled />
              <small class="form-tip">邮箱地址不可修改</small>
            </el-form-item>
            
            <el-form-item label="显示名称" prop="display_name">
              <el-input v-model="basicForm.display_name" placeholder="请输入显示名称" />
            </el-form-item>
            
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                :action="uploadUrl"
                :show-file-list="false"
                :on-success="handleAvatarSuccess"
                :before-upload="beforeAvatarUpload"
                accept="image/*"
              >
                <img v-if="basicForm.avatar_url" :src="basicForm.avatar_url" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
              <small class="form-tip">支持 JPG、PNG 格式，文件大小不超过 2MB</small>
            </el-form-item>
            
            <el-form-item label="手机号码" prop="phone">
              <el-input v-model="basicForm.phone" placeholder="请输入手机号码" />
            </el-form-item>
            
            <el-form-item label="个人简介" prop="bio">
              <el-input
                v-model="basicForm.bio"
                type="textarea"
                :rows="3"
                placeholder="请输入个人简介"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveBasicInfo" :loading="basicLoading">
                保存基本信息
              </el-button>
              <el-button @click="resetBasicForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 修改密码 -->
        <el-tab-pane label="修改密码" name="password">
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="120px"
            class="profile-form"
          >
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="passwordForm.current_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                placeholder="请输入新密码"
                show-password
              />
              <small class="form-tip">密码长度至少8位，包含字母和数字</small>
            </el-form-item>
            
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="passwordLoading">
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 安全设置 -->
        <el-tab-pane label="安全设置" name="security">
          <div class="security-section">
            <h3>账户安全</h3>
            
            <el-form label-width="120px" class="profile-form">
              <el-form-item label="两步验证">
                <el-switch v-model="securityForm.two_factor_enabled" @change="toggleTwoFactor" />
                <small class="form-tip">启用两步验证可以提高账户安全性</small>
              </el-form-item>
              
              <el-form-item label="登录通知">
                <el-switch v-model="securityForm.login_notification" @change="toggleLoginNotification" />
                <small class="form-tip">在新设备登录时发送邮件通知</small>
              </el-form-item>
              
              <el-form-item label="会话超时">
                <el-select v-model="securityForm.session_timeout" @change="updateSessionTimeout">
                  <el-option label="30分钟" value="30" />
                  <el-option label="1小时" value="60" />
                  <el-option label="2小时" value="120" />
                  <el-option label="4小时" value="240" />
                  <el-option label="永不超时" value="0" />
                </el-select>
                <small class="form-tip">设置登录会话的超时时间</small>
              </el-form-item>
            </el-form>
          </div>

          <div class="security-section">
            <h3>登录历史</h3>
            <el-table :data="loginHistory" style="width: 100%">
              <el-table-column prop="login_time" label="登录时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.login_time) }}
                </template>
              </el-table-column>
              <el-table-column prop="ip_address" label="IP地址" width="140" />
              <el-table-column prop="location" label="登录地点" />
              <el-table-column prop="device" label="设备信息" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                    {{ row.status === 'success' ? '成功' : '失败' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane label="通知设置" name="notifications">
          <el-form label-width="120px" class="profile-form">
            <el-form-item label="邮件通知">
              <el-switch v-model="notificationForm.email_enabled" @change="toggleEmailNotification" />
              <small class="form-tip">接收重要的系统通知邮件</small>
            </el-form-item>
            
            <el-form-item label="系统通知">
              <el-switch v-model="notificationForm.system_notification" @change="toggleSystemNotification" />
              <small class="form-tip">接收系统维护、更新等通知</small>
            </el-form-item>
            
            <el-form-item label="安全通知">
              <el-switch v-model="notificationForm.security_notification" @change="toggleSecurityNotification" />
              <small class="form-tip">接收安全相关的通知</small>
            </el-form-item>
            
            <el-form-item label="通知频率">
              <el-select v-model="notificationForm.frequency" @change="updateNotificationFrequency">
                <el-option label="实时" value="realtime" />
                <el-option label="每小时" value="hourly" />
                <el-option label="每天" value="daily" />
                <el-option label="每周" value="weekly" />
              </el-select>
              <small class="form-tip">设置通知的发送频率</small>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AdminProfile',
  components: {
    Plus
  },
  setup() {
    const activeTab = ref('basic')
    const basicFormRef = ref()
    const passwordFormRef = ref()
    
    const basicLoading = ref(false)
    const passwordLoading = ref(false)
    
    const uploadUrl = '/api/admin/upload'
    
    const authStore = useAuthStore()

    // 基本信息表单
    const basicForm = reactive({
      username: '',
      email: '',
      display_name: '',
      avatar_url: '',
      phone: '',
      bio: ''
    })

    // 密码修改表单
    const passwordForm = reactive({
      current_password: '',
      new_password: '',
      confirm_password: ''
    })

    // 安全设置表单
    const securityForm = reactive({
      two_factor_enabled: false,
      login_notification: true,
      session_timeout: '120'
    })

    // 通知设置表单
    const notificationForm = reactive({
      email_enabled: true,
      system_notification: true,
      security_notification: true,
      frequency: 'realtime'
    })

    // 登录历史
    const loginHistory = ref([])

    // 表单验证规则
    const basicRules = {
      display_name: [
        { required: true, message: '请输入显示名称', trigger: 'blur' },
        { min: 2, max: 20, message: '显示名称长度在 2 到 20 个字符', trigger: 'blur' }
      ],
      phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
      ],
      bio: [
        { max: 200, message: '个人简介不能超过200个字符', trigger: 'blur' }
      ]
    }

    const passwordRules = {
      current_password: [
        { required: true, message: '请输入当前密码', trigger: 'blur' }
      ],
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 8, message: '密码长度至少8位', trigger: 'blur' },
        { pattern: /^(?=.*[A-Za-z])(?=.*\d)/, message: '密码必须包含字母和数字', trigger: 'blur' }
      ],
      confirm_password: [
        { required: true, message: '请确认新密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== passwordForm.new_password) {
              callback(new Error('两次输入的密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }

    // 加载基本信息
    const loadBasicInfo = async () => {
      try {
        const response = await adminAPI.getProfile()
        if (response.success) {
          const data = response.data
          Object.assign(basicForm, {
            username: data.username || '',
            email: data.email || '',
            display_name: data.display_name || '',
            avatar_url: data.avatar_url || '',
            phone: data.phone || '',
            bio: data.bio || ''
          })
        }
      } catch (error) {
        console.error('加载基本信息失败:', error)
        ElMessage.error('加载基本信息失败')
      }
    }

    // 保存基本信息
    const saveBasicInfo = async () => {
      try {
        await basicFormRef.value.validate()
        basicLoading.value = true
        
        const response = await adminAPI.updateProfile(basicForm)
        if (response.success) {
          ElMessage.success('基本信息保存成功')
          // 更新store中的用户信息
          authStore.updateUser(basicForm)
        } else {
          ElMessage.error(response.message || '保存失败')
        }
      } catch (error) {
        console.error('保存基本信息失败:', error)
        ElMessage.error('保存失败')
      } finally {
        basicLoading.value = false
      }
    }

    // 重置基本信息表单
    const resetBasicForm = () => {
      loadBasicInfo()
    }

    // 修改密码
    const changePassword = async () => {
      try {
        await passwordFormRef.value.validate()
        passwordLoading.value = true
        
        const response = await adminAPI.changePassword(passwordForm)
        if (response.success) {
          ElMessage.success('密码修改成功，请重新登录')
          // 清除表单
          Object.assign(passwordForm, {
            current_password: '',
            new_password: '',
            confirm_password: ''
          })
          // 退出登录
          authStore.logout()
        } else {
          ElMessage.error(response.message || '密码修改失败')
        }
      } catch (error) {
        console.error('修改密码失败:', error)
        ElMessage.error('修改密码失败')
      } finally {
        passwordLoading.value = false
      }
    }

    // 重置密码表单
    const resetPasswordForm = () => {
      Object.assign(passwordForm, {
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
      passwordFormRef.value?.clearValidate()
    }

    // 头像上传成功
    const handleAvatarSuccess = (response) => {
      if (response.success) {
        basicForm.avatar_url = response.data.url
        ElMessage.success('头像上传成功')
      } else {
        ElMessage.error('头像上传失败')
      }
    }

    // 头像上传前验证
    const beforeAvatarUpload = (file) => {
      const isJPG = file.type === 'image/jpeg'
      const isPNG = file.type === 'image/png'
      const isLt2M = file.size / 1024 / 1024 < 2

      if (!isJPG && !isPNG) {
        ElMessage.error('头像只能是 JPG 或 PNG 格式!')
        return false
      }
      if (!isLt2M) {
        ElMessage.error('头像大小不能超过 2MB!')
        return false
      }
      return true
    }

    // 切换两步验证
    const toggleTwoFactor = async (value) => {
      try {
        const response = await adminAPI.updateSecuritySettings({
          two_factor_enabled: value
        })
        if (response.success) {
          ElMessage.success(value ? '两步验证已启用' : '两步验证已禁用')
        } else {
          ElMessage.error('设置失败')
          // 恢复原状态
          securityForm.two_factor_enabled = !value
        }
      } catch (error) {
        console.error('设置两步验证失败:', error)
        ElMessage.error('设置失败')
        securityForm.two_factor_enabled = !value
      }
    }

    // 切换登录通知
    const toggleLoginNotification = async (value) => {
      try {
        await adminAPI.updateSecuritySettings({
          login_notification: value
        })
        ElMessage.success('设置已保存')
      } catch (error) {
        console.error('设置登录通知失败:', error)
        ElMessage.error('设置失败')
        securityForm.login_notification = !value
      }
    }

    // 更新会话超时
    const updateSessionTimeout = async (value) => {
      try {
        await adminAPI.updateSecuritySettings({
          session_timeout: value
        })
        ElMessage.success('会话超时设置已保存')
      } catch (error) {
        console.error('设置会话超时失败:', error)
        ElMessage.error('设置失败')
      }
    }

    // 切换邮件通知
    const toggleEmailNotification = async (value) => {
      try {
        await adminAPI.updateNotificationSettings({
          email_enabled: value
        })
        ElMessage.success('设置已保存')
      } catch (error) {
        console.error('设置邮件通知失败:', error)
        ElMessage.error('设置失败')
        notificationForm.email_enabled = !value
      }
    }

    // 切换系统通知
    const toggleSystemNotification = async (value) => {
      try {
        await adminAPI.updateNotificationSettings({
          system_notification: value
        })
        ElMessage.success('设置已保存')
      } catch (error) {
        console.error('设置系统通知失败:', error)
        ElMessage.error('设置失败')
        notificationForm.system_notification = !value
      }
    }

    // 切换安全通知
    const toggleSecurityNotification = async (value) => {
      try {
        await adminAPI.updateNotificationSettings({
          security_notification: value
        })
        ElMessage.success('设置已保存')
      } catch (error) {
        console.error('设置安全通知失败:', error)
        ElMessage.error('设置失败')
        notificationForm.security_notification = !value
      }
    }

    // 更新通知频率
    const updateNotificationFrequency = async (value) => {
      try {
        await adminAPI.updateNotificationSettings({
          frequency: value
        })
        ElMessage.success('通知频率设置已保存')
      } catch (error) {
        console.error('设置通知频率失败:', error)
        ElMessage.error('设置失败')
      }
    }

    // 加载登录历史
    const loadLoginHistory = async () => {
      try {
        const response = await adminAPI.getLoginHistory()
        if (response.success) {
          loginHistory.value = response.data || []
        }
      } catch (error) {
        console.error('加载登录历史失败:', error)
      }
    }

    // 加载安全设置
    const loadSecuritySettings = async () => {
      try {
        const response = await adminAPI.getSecuritySettings()
        if (response.success) {
          const data = response.data
          Object.assign(securityForm, {
            two_factor_enabled: data.two_factor_enabled || false,
            login_notification: data.login_notification || true,
            session_timeout: data.session_timeout || '120'
          })
        }
      } catch (error) {
        console.error('加载安全设置失败:', error)
      }
    }

    // 加载通知设置
    const loadNotificationSettings = async () => {
      try {
        const response = await adminAPI.getNotificationSettings()
        if (response.success) {
          const data = response.data
          Object.assign(notificationForm, {
            email_enabled: data.email_enabled || true,
            system_notification: data.system_notification || true,
            security_notification: data.security_notification || true,
            frequency: data.frequency || 'realtime'
          })
        }
      } catch (error) {
        console.error('加载通知设置失败:', error)
      }
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }

    // 生命周期
    onMounted(() => {
      loadBasicInfo()
      loadSecuritySettings()
      loadNotificationSettings()
      loadLoginHistory()
    })

    return {
      activeTab,
      basicFormRef,
      passwordFormRef,
      basicLoading,
      passwordLoading,
      basicForm,
      passwordForm,
      securityForm,
      notificationForm,
      loginHistory,
      basicRules,
      passwordRules,
      uploadUrl,
      saveBasicInfo,
      resetBasicForm,
      changePassword,
      resetPasswordForm,
      handleAvatarSuccess,
      beforeAvatarUpload,
      toggleTwoFactor,
      toggleLoginNotification,
      updateSessionTimeout,
      toggleEmailNotification,
      toggleSystemNotification,
      toggleSecurityNotification,
      updateNotificationFrequency,
      formatDate
    }
  }
}
</script>

<style scoped>
.admin-profile-container {
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

.card-header p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.profile-form {
  max-width: 600px;
  margin-top: 20px;
}

.form-tip {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.avatar-uploader {
  text-align: center;
}

.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-uploader .avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
  border: 1px dashed #d9d9d9;
  border-radius: 50%;
}

.security-section {
  margin-bottom: 30px;
}

.security-section h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.2rem;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

@media (max-width: 768px) {
  .admin-profile-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .profile-form {
    max-width: 100%;
  }
}
</style>
