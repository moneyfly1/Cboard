<template>
  <div class="user-settings-container">
    <div class="page-header">
      <h1>用户设置</h1>
      <p>管理您的账户设置和偏好</p>
    </div>

    <el-row :gutter="20">
      <!-- 左侧设置菜单 -->
      <el-col :span="6">
        <el-card class="settings-menu">
          <template #header>
            <div class="card-header">
              <i class="el-icon-setting"></i>
              设置分类
            </div>
          </template>
          
          <el-menu
            :default-active="activeSetting"
            @select="handleSettingSelect"
            class="settings-menu-list"
          >
            <el-menu-item index="profile">
              <i class="el-icon-user"></i>
              <span>个人资料</span>
            </el-menu-item>
            <el-menu-item index="security">
              <i class="el-icon-lock"></i>
              <span>安全设置</span>
            </el-menu-item>
            <el-menu-item index="notifications">
              <i class="el-icon-bell"></i>
              <span>通知设置</span>
            </el-menu-item>
            <el-menu-item index="privacy">
              <i class="el-icon-view"></i>
              <span>隐私设置</span>
            </el-menu-item>
            <el-menu-item index="preferences">
              <i class="el-icon-star-on"></i>
              <span>偏好设置</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右侧设置内容 -->
      <el-col :span="18">
        <!-- 个人资料设置 -->
        <el-card v-if="activeSetting === 'profile'" class="setting-content">
          <template #header>
            <div class="card-header">
              <i class="el-icon-user"></i>
              个人资料
            </div>
          </template>
          
          <el-form :model="profileForm" :rules="profileRules" ref="profileFormRef" label-width="100px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="profileForm.username" placeholder="请输入用户名"></el-input>
            </el-form-item>
            
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" disabled>
                <template #append>
                  <el-button @click="showEmailChangeDialog">修改</el-button>
                </template>
              </el-input>
            </el-form-item>
            
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="profileForm.nickname" placeholder="请输入昵称"></el-input>
            </el-form-item>
            
            <el-form-item label="头像">
              <el-upload
                class="avatar-uploader"
                action="#"
                :show-file-list="false"
                :before-upload="beforeAvatarUpload"
              >
                <img v-if="profileForm.avatar" :src="profileForm.avatar" class="avatar" />
                <i v-else class="el-icon-plus avatar-uploader-icon"></i>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveProfile" :loading="profileSaving">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 安全设置 -->
        <el-card v-if="activeSetting === 'security'" class="setting-content">
          <template #header>
            <div class="card-header">
              <i class="el-icon-lock"></i>
              安全设置
            </div>
          </template>
          
          <el-form :model="securityForm" :rules="securityRules" ref="securityFormRef" label-width="100px">
            <el-form-item label="当前密码" prop="currentPassword">
              <el-input v-model="securityForm.currentPassword" type="password" placeholder="请输入当前密码"></el-input>
            </el-form-item>
            
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="securityForm.newPassword" type="password" placeholder="请输入新密码"></el-input>
            </el-form-item>
            
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input v-model="securityForm.confirmPassword" type="password" placeholder="请再次输入新密码"></el-input>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="passwordChanging">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
          
          <el-divider></el-divider>
          
          <div class="security-options">
            <h4>其他安全选项</h4>
            <el-switch
              v-model="securityForm.twoFactorAuth"
              active-text="启用两步验证"
              inactive-text="禁用两步验证"
            ></el-switch>
            <p class="security-tip">启用两步验证可以提高账户安全性</p>
          </div>
        </el-card>

        <!-- 通知设置 -->
        <el-card v-if="activeSetting === 'notifications'" class="setting-content">
          <template #header>
            <div class="card-header">
              <i class="el-icon-bell"></i>
              通知设置
            </div>
          </template>
          
          <div class="notification-settings">
            <h4>邮件通知</h4>
            <el-switch
              v-model="notificationForm.emailNotifications"
              active-text="启用邮件通知"
              inactive-text="禁用邮件通知"
            ></el-switch>
            
            <el-divider></el-divider>
            
            <h4>通知类型</h4>
            <el-checkbox-group v-model="notificationForm.notificationTypes">
              <el-checkbox label="subscription">订阅相关通知</el-checkbox>
              <el-checkbox label="payment">支付相关通知</el-checkbox>
              <el-checkbox label="system">系统通知</el-checkbox>
              <el-checkbox label="marketing">营销通知</el-checkbox>
            </el-checkbox-group>
            
            <el-divider></el-divider>
            
            <el-button type="primary" @click="saveNotificationSettings" :loading="notificationSaving">
              保存设置
            </el-button>
          </div>
        </el-card>

        <!-- 隐私设置 -->
        <el-card v-if="activeSetting === 'privacy'" class="setting-content">
          <template #header>
            <div class="card-header">
              <i class="el-icon-view"></i>
              隐私设置
            </div>
          </template>
          
          <div class="privacy-settings">
            <h4>数据共享</h4>
            <el-switch
              v-model="privacyForm.dataSharing"
              active-text="允许数据共享"
              inactive-text="禁止数据共享"
            ></el-switch>
            <p class="privacy-tip">数据共享用于改进服务质量，不会泄露个人信息</p>
            
            <el-divider></el-divider>
            
            <h4>分析统计</h4>
            <el-switch
              v-model="privacyForm.analytics"
              active-text="启用使用统计"
              inactive-text="禁用使用统计"
            ></el-switch>
            
            <el-divider></el-divider>
            
            <el-button type="primary" @click="savePrivacySettings" :loading="privacySaving">
              保存设置
            </el-button>
          </div>
        </el-card>

        <!-- 偏好设置 -->
        <el-card v-if="activeSetting === 'preferences'" class="setting-content">
          <template #header>
            <div class="card-header">
              <i class="el-icon-star-on"></i>
              偏好设置
            </div>
          </template>
          
          <div class="preference-settings">
            <h4>界面设置</h4>
            <el-form label-width="120px">
              <el-form-item label="主题模式">
                <el-radio-group v-model="preferenceForm.theme">
                  <el-radio label="light">浅色主题</el-radio>
                  <el-radio label="dark">深色主题</el-radio>
                  <el-radio label="auto">跟随系统</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="语言">
                <el-select v-model="preferenceForm.language" placeholder="选择语言">
                  <el-option label="简体中文" value="zh-CN"></el-option>
                  <el-option label="English" value="en-US"></el-option>
                </el-select>
              </el-form-item>
              
              <el-form-item label="时区">
                <el-select v-model="preferenceForm.timezone" placeholder="选择时区">
                  <el-option label="UTC+8 (北京时间)" value="Asia/Shanghai"></el-option>
                  <el-option label="UTC+0 (格林威治时间)" value="UTC"></el-option>
                </el-select>
              </el-form-item>
            </el-form>
            
            <el-divider></el-divider>
            
            <el-button type="primary" @click="savePreferenceSettings" :loading="preferenceSaving">
              保存设置
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 修改邮箱对话框 -->
    <el-dialog
      v-model="emailChangeDialogVisible"
      title="修改邮箱"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="emailChangeForm" :rules="emailChangeRules" ref="emailChangeFormRef" label-width="100px">
        <el-form-item label="新邮箱" prop="newEmail">
          <el-input v-model="emailChangeForm.newEmail" placeholder="请输入新邮箱"></el-input>
        </el-form-item>
        
        <el-form-item label="验证码" prop="verificationCode">
          <el-input v-model="emailChangeForm.verificationCode" placeholder="请输入验证码">
            <template #append>
              <el-button @click="sendVerificationCode" :disabled="codeSending">
                {{ codeSending ? '发送中...' : '发送验证码' }}
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="emailChangeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmEmailChange" :loading="emailChanging">
            确认修改
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'

export default {
  name: 'UserSettings',
  setup() {
    const authStore = useAuthStore()
    const activeSetting = ref('profile')
    
    // 表单引用
    const profileFormRef = ref()
    const securityFormRef = ref()
    const emailChangeFormRef = ref()
    
    // 加载状态
    const profileSaving = ref(false)
    const passwordChanging = ref(false)
    const notificationSaving = ref(false)
    const privacySaving = ref(false)
    const preferenceSaving = ref(false)
    const emailChanging = ref(false)
    const codeSending = ref(false)
    
    // 对话框状态
    const emailChangeDialogVisible = ref(false)
    
    // 表单数据
    const profileForm = reactive({
      username: '',
      email: '',
      nickname: '',
      avatar: ''
    })
    
    const securityForm = reactive({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
      twoFactorAuth: false
    })
    
    const notificationForm = reactive({
      emailNotifications: true,
      notificationTypes: ['subscription', 'payment', 'system']
    })
    
    const privacyForm = reactive({
      dataSharing: true,
      analytics: true
    })
    
    const preferenceForm = reactive({
      theme: 'light',
      language: 'zh-CN',
      timezone: 'Asia/Shanghai'
    })
    
    const emailChangeForm = reactive({
      newEmail: '',
      verificationCode: ''
    })
    
    // 表单验证规则
    const profileRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      nickname: [
        { max: 50, message: '昵称长度不能超过 50 个字符', trigger: 'blur' }
      ]
    }
    
    const securityRules = {
      currentPassword: [
        { required: true, message: '请输入当前密码', trigger: 'blur' }
      ],
      newPassword: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请再次输入新密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== securityForm.newPassword) {
              callback(new Error('两次输入密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }
    
    const emailChangeRules = {
      newEmail: [
        { required: true, message: '请输入新邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      verificationCode: [
        { required: true, message: '请输入验证码', trigger: 'blur' },
        { len: 6, message: '验证码长度应为 6 位', trigger: 'blur' }
      ]
    }
    
    // 处理设置选择
    const handleSettingSelect = (key) => {
      activeSetting.value = key
    }
    
    // 加载用户信息
    const loadUserInfo = () => {
      const user = authStore.user
      if (user) {
        profileForm.username = user.username || ''
        profileForm.email = user.email || ''
        profileForm.nickname = user.nickname || ''
        profileForm.avatar = user.avatar || ''
      }
    }
    
    // 保存个人资料
    const saveProfile = async () => {
      try {
        await profileFormRef.value.validate()
        profileSaving.value = true
        
        // 调用API保存个人资料
        await api.put('/users/profile', profileForm)
        
        // 更新本地用户信息
        authStore.updateUser(profileForm)
        
        ElMessage.success('个人资料保存成功')
      } catch (error) {
        ElMessage.error('保存失败：' + error.message)
      } finally {
        profileSaving.value = false
      }
    }
    
    // 修改密码
    const changePassword = async () => {
      try {
        await securityFormRef.value.validate()
        passwordChanging.value = true
        
        // 这里调用API修改密码
        await authStore.changePassword(securityForm.currentPassword, securityForm.newPassword)
        
        ElMessage.success('密码修改成功')
        securityForm.currentPassword = ''
        securityForm.newPassword = ''
        securityForm.confirmPassword = ''
      } catch (error) {
        ElMessage.error('密码修改失败：' + error.message)
      } finally {
        passwordChanging.value = false
      }
    }
    
    // 保存通知设置
    const saveNotificationSettings = async () => {
      try {
        notificationSaving.value = true
        
        // 调用API保存通知设置
        await api.put('/users/notification-settings', notificationForm)
        
        ElMessage.success('通知设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败：' + error.message)
      } finally {
        notificationSaving.value = false
      }
    }
    
    // 保存隐私设置
    const savePrivacySettings = async () => {
      try {
        privacySaving.value = true
        
        // 调用API保存隐私设置
        await api.put('/users/privacy-settings', privacyForm)
        
        ElMessage.success('隐私设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败：' + error.message)
      } finally {
        privacySaving.value = false
      }
    }
    
    // 保存偏好设置
    const savePreferenceSettings = async () => {
      try {
        preferenceSaving.value = true
        
        // 调用API保存偏好设置
        await api.put('/users/preference-settings', preferenceForm)
        
        ElMessage.success('偏好设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败：' + error.message)
      } finally {
        preferenceSaving.value = false
      }
    }
    
    // 显示修改邮箱对话框
    const showEmailChangeDialog = () => {
      emailChangeForm.newEmail = ''
      emailChangeForm.verificationCode = ''
      emailChangeDialogVisible.value = true
    }
    
    // 发送验证码
    const sendVerificationCode = async () => {
      try {
        if (!emailChangeForm.newEmail) {
          ElMessage.warning('请先输入新邮箱')
          return
        }
        
        codeSending.value = true
        
        // 这里调用API发送验证码
        // await api.sendEmailVerificationCode(emailChangeForm.newEmail)
        
        ElMessage.success('验证码已发送到您的邮箱')
      } catch (error) {
        ElMessage.error('发送验证码失败：' + error.message)
      } finally {
        codeSending.value = false
      }
    }
    
    // 确认修改邮箱
    const confirmEmailChange = async () => {
      try {
        await emailChangeFormRef.value.validate()
        emailChanging.value = true
        
        // 这里调用API修改邮箱
        // await api.changeEmail(emailChangeForm.newEmail, emailChangeForm.verificationCode)
        
        ElMessage.success('邮箱修改成功')
        emailChangeDialogVisible.value = false
        profileForm.email = emailChangeForm.newEmail
      } catch (error) {
        ElMessage.error('邮箱修改失败：' + error.message)
      } finally {
        emailChanging.value = false
      }
    }
    
    // 头像上传前的处理
    const beforeAvatarUpload = (file) => {
      const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
      const isLt2M = file.size / 1024 / 1024 < 2

      if (!isJPG) {
        ElMessage.error('上传头像图片只能是 JPG/PNG 格式!')
      }
      if (!isLt2M) {
        ElMessage.error('上传头像图片大小不能超过 2MB!')
      }
      return isJPG && isLt2M
    }
    
    onMounted(() => {
      loadUserInfo()
    })
    
    return {
      activeSetting,
      profileFormRef,
      securityFormRef,
      emailChangeFormRef,
      profileSaving,
      passwordChanging,
      notificationSaving,
      privacySaving,
      preferenceSaving,
      emailChanging,
      codeSending,
      emailChangeDialogVisible,
      profileForm,
      securityForm,
      notificationForm,
      privacyForm,
      preferenceForm,
      emailChangeForm,
      profileRules,
      securityRules,
      emailChangeRules,
      handleSettingSelect,
      saveProfile,
      changePassword,
      saveNotificationSettings,
      savePrivacySettings,
      savePreferenceSettings,
      showEmailChangeDialog,
      sendVerificationCode,
      confirmEmailChange,
      beforeAvatarUpload
    }
  }
}
</script>

<style scoped>
.user-settings-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #333;
}

.page-header p {
  margin: 0;
  color: #666;
}

.settings-menu {
  position: sticky;
  top: 20px;
}

.settings-menu-list {
  border-right: none;
}

.setting-content {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  font-weight: bold;
}

.card-header i {
  margin-right: 8px;
  color: #409eff;
}

.avatar-uploader {
  text-align: center;
}

.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.avatar-uploader .el-upload:hover {
  border-color: #409eff;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
}

.avatar {
  width: 100px;
  height: 100px;
  display: block;
}

.security-options,
.notification-settings,
.privacy-settings,
.preference-settings {
  margin-top: 20px;
}

.security-options h4,
.notification-settings h4,
.privacy-settings h4,
.preference-settings h4 {
  margin: 0 0 15px 0;
  color: #333;
}

.security-tip,
.privacy-tip {
  margin: 10px 0 0 0;
  color: #666;
  font-size: 14px;
}

.el-divider {
  margin: 20px 0;
}

.dialog-footer {
  text-align: right;
}
</style>
