<template>
  <div class="profile-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>个人资料</h1>
      <p>管理您的账户信息</p>
    </div>

    <div class="profile-content">
      <!-- 基本信息 -->
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-user"></i>
            基本信息
          </div>
        </template>

        <el-form
          ref="profileForm"
          :model="profileForm"
          :rules="profileRules"
          label-width="120px"
        >
          <el-form-item label="QQ号码" prop="username">
            <el-input 
              v-model="profileForm.username" 
              disabled
              placeholder="QQ号码"
            >
              <template #prepend>
                <i class="el-icon-user"></i>
              </template>
            </el-input>
            <div class="form-tip">QQ号码不可修改</div>
          </el-form-item>

          <el-form-item label="QQ邮箱" prop="email">
            <el-input 
              v-model="profileForm.email" 
              disabled
              placeholder="QQ邮箱"
            >
              <template #prepend>
                <i class="el-icon-message"></i>
              </template>
            </el-input>
            <div class="form-tip">QQ邮箱不可修改</div>
          </el-form-item>

          <el-form-item label="注册时间">
            <el-input 
              :value="formatTime(userInfo.created_at)" 
              disabled
            >
              <template #prepend>
                <i class="el-icon-time"></i>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="最后登录">
            <el-input 
              :value="formatTime(userInfo.last_login)" 
              disabled
            >
              <template #prepend>
                <i class="el-icon-time"></i>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="账户状态">
            <el-tag :type="userInfo.is_active ? 'success' : 'danger'">
              {{ userInfo.is_active ? '正常' : '已禁用' }}
            </el-tag>
            <el-tag 
              :type="userInfo.is_verified ? 'success' : 'warning'"
              style="margin-left: 10px;"
            >
              {{ userInfo.is_verified ? '已验证' : '未验证' }}
            </el-tag>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 修改密码 -->
      <el-card class="password-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-lock"></i>
            修改密码
          </div>
        </template>

        <el-form
          ref="passwordForm"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="120px"
        >
          <el-form-item label="当前密码" prop="oldPassword">
            <el-input 
              v-model="passwordForm.oldPassword" 
              type="password"
              placeholder="请输入当前密码"
              show-password
            >
              <template #prepend>
                <i class="el-icon-lock"></i>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item label="新密码" prop="newPassword">
            <el-input 
              v-model="passwordForm.newPassword" 
              type="password"
              placeholder="请输入新密码"
              show-password
            >
              <template #prepend>
                <i class="el-icon-lock"></i>
              </template>
            </el-input>
            <div class="form-tip">密码长度不能少于6位</div>
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input 
              v-model="passwordForm.confirmPassword" 
              type="password"
              placeholder="请再次输入新密码"
              show-password
            >
              <template #prepend>
                <i class="el-icon-lock"></i>
              </template>
            </el-input>
          </el-form-item>

          <el-form-item>
            <el-button 
              type="primary" 
              @click="changePassword"
              :loading="passwordLoading"
            >
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 账户安全 -->
      <el-card class="security-card">
        <template #header>
          <div class="card-header">
            <i class="el-icon-shield"></i>
            账户安全
          </div>
        </template>

        <div class="security-items">
          <div class="security-item">
            <div class="security-info">
              <div class="security-title">
                <i class="el-icon-message"></i>
                QQ邮箱验证
              </div>
              <div class="security-desc">
                {{ userInfo.is_verified ? '您的QQ邮箱已验证' : '请验证您的QQ邮箱' }}
              </div>
            </div>
            <div class="security-action">
              <el-tag :type="userInfo.is_verified ? 'success' : 'warning'">
                {{ userInfo.is_verified ? '已验证' : '未验证' }}
              </el-tag>
              <el-button 
                v-if="!userInfo.is_verified"
                type="primary" 
                size="small"
                @click="resendVerificationEmail"
                :loading="emailLoading"
              >
                重新发送验证邮件
              </el-button>
            </div>
          </div>

          <div class="security-item">
            <div class="security-info">
              <div class="security-title">
                <i class="el-icon-time"></i>
                登录记录
              </div>
              <div class="security-desc">
                最后登录时间：{{ formatTime(userInfo.last_login) }}
              </div>
            </div>
            <div class="security-action">
              <el-button 
                type="info" 
                size="small"
                @click="viewLoginHistory"
              >
                查看登录历史
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 订阅信息 -->
      <el-card class="subscription-card" v-if="subscriptionInfo">
        <template #header>
          <div class="card-header">
            <i class="el-icon-link"></i>
            订阅信息
          </div>
        </template>

        <div class="subscription-info">
          <div class="info-item">
            <span class="label">剩余时长：</span>
            <span class="value">{{ subscriptionInfo.remainingDays }} 天</span>
          </div>
          <div class="info-item">
            <span class="label">到期时间：</span>
            <span class="value">{{ subscriptionInfo.expiryDate }}</span>
          </div>
          <div class="info-item">
            <span class="label">设备限制：</span>
            <span class="value">{{ subscriptionInfo.currentDevices }}/{{ subscriptionInfo.maxDevices }} 个</span>
          </div>
          <div class="info-item">
            <span class="label">订阅状态：</span>
            <span class="value">
              <el-tag :type="subscriptionInfo.isExpiring ? 'warning' : 'success'">
                {{ subscriptionInfo.isExpiring ? '即将到期' : '正常' }}
              </el-tag>
            </span>
          </div>
        </div>

        <div class="subscription-actions">
          <el-button type="primary" @click="$router.push('/dashboard')">
            管理订阅
          </el-button>
          <el-button type="success" @click="$router.push('/packages')">
            续费订阅
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { userAPI, subscriptionAPI } from '@/utils/api'
import dayjs from 'dayjs'

export default {
  name: 'Profile',
  setup() {
    const authStore = useAuthStore()
    const passwordLoading = ref(false)
    const emailLoading = ref(false)
    
    const userInfo = ref({})
    const subscriptionInfo = ref(null)

    const profileForm = reactive({
      username: '',
      email: ''
    })

    const passwordForm = reactive({
      oldPassword: '',
      newPassword: '',
      confirmPassword: ''
    })

    // 表单验证规则
    const profileRules = {
      username: [
        { required: true, message: '请输入QQ号码', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入QQ邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的QQ邮箱格式', trigger: 'blur' }
      ]
    }

    const passwordRules = {
      oldPassword: [
        { required: true, message: '请输入当前密码', trigger: 'blur' }
      ],
      newPassword: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请确认新密码', trigger: 'blur' },
        {
          validator: (rule, value, callback) => {
            if (value !== passwordForm.newPassword) {
              callback(new Error('两次输入的密码不一致'))
            } else {
              callback()
            }
          },
          trigger: 'blur'
        }
      ]
    }

    // 获取用户信息
    const fetchUserInfo = async () => {
      try {
        const response = await userAPI.getProfile()
        userInfo.value = response.data
        
        // 更新表单数据
        profileForm.username = userInfo.value.username
        profileForm.email = userInfo.value.email
      } catch (error) {
        ElMessage.error('获取用户信息失败')
      }
    }

    // 获取订阅信息
    const fetchSubscriptionInfo = async () => {
      try {
        const response = await subscriptionAPI.getUserSubscription()
        subscriptionInfo.value = response.data
      } catch (error) {
        // 用户可能没有订阅，忽略错误
      }
    }

    // 修改密码
    const changePassword = async () => {
      passwordLoading.value = true
      try {
        await userAPI.changePassword({
          old_password: passwordForm.oldPassword,
          new_password: passwordForm.newPassword
        })
        
        ElMessage.success('密码修改成功')
        
        // 清空表单
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
        
      } catch (error) {
        ElMessage.error('密码修改失败')
      } finally {
        passwordLoading.value = false
      }
    }

    // 重新发送验证邮件
    const resendVerificationEmail = async () => {
      emailLoading.value = true
      try {
        await authStore.sendVerificationEmail()
        ElMessage.success('验证邮件已发送，请查收QQ邮箱')
      } catch (error) {
        ElMessage.error('发送验证邮件失败')
      } finally {
        emailLoading.value = false
      }
    }

    // 查看登录历史
    const viewLoginHistory = () => {
      ElMessage.info('登录历史功能开发中')
    }

    // 格式化时间
    const formatTime = (time) => {
      if (!time) return '未知'
      return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }

    onMounted(() => {
      fetchUserInfo()
      fetchSubscriptionInfo()
    })

    return {
      userInfo,
      subscriptionInfo,
      profileForm,
      passwordForm,
      profileRules,
      passwordRules,
      passwordLoading,
      emailLoading,
      changePassword,
      resendVerificationEmail,
      viewLoginHistory,
      formatTime
    }
  }
}
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h1 {
  color: #1677ff;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
  font-size: 1rem;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.profile-card,
.password-card,
.security-card,
.subscription-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.form-tip {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.5rem;
}

.security-items {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.security-info {
  flex: 1;
}

.security-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.security-desc {
  color: #666;
  font-size: 0.9rem;
}

.security-action {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.subscription-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
}

.info-item .label {
  color: #666;
  font-weight: 500;
}

.info-item .value {
  color: #333;
  font-weight: 600;
}

.subscription-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

@media (max-width: 768px) {
  .profile-container {
    padding: 10px;
  }
  
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .security-action {
    width: 100%;
    justify-content: flex-end;
  }
  
  .subscription-info {
    grid-template-columns: 1fr;
  }
  
  .subscription-actions {
    flex-direction: column;
  }
}
</style> 