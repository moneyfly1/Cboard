<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <img v-if="settings.siteLogo" :src="settings.siteLogo" :alt="settings.siteName" class="logo" />
        <h1>{{ settings.siteName }}</h1>
        <p>创建您的账户</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="0"
        class="register-form"
      >
        <el-form-item prop="email">
          <div class="email-input-group">
            <el-input
              v-model="registerForm.emailPrefix"
              placeholder="邮箱前缀"
              prefix-icon="Message"
              size="large"
              class="email-prefix"
            />
            <span class="email-separator">@</span>
            <el-select
              v-model="registerForm.emailDomain"
              placeholder="选择邮箱类型"
              size="large"
              class="email-domain"
            >
              <el-option
                v-for="domain in allowedEmailDomains"
                :key="domain"
                :label="domain"
                :value="domain"
              />
            </el-select>
          </div>
        </el-form-item>

        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="register-button"
            :loading="loading"
            @click="handleRegister"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        <p>已有账户？ <router-link to="/login">立即登录</router-link></p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/utils/api'
import { useSettingsStore } from '@/store/settings'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const settingsStore = useSettingsStore()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const registerFormRef = ref()

const registerForm = reactive({
  emailPrefix: '',
  emailDomain: 'qq.com', // 默认选择qq.com
  email: '', // 计算属性，由前缀和域名组成
  username: '',
  password: '',
  confirmPassword: ''
})

// 允许的邮箱域名
const allowedEmailDomains = [
  'qq.com',
  'gmail.com', 
  '126.com',
  '163.com',
  'hotmail.com',
  'foxmail.com'
]

// 监听邮箱前缀和域名的变化，自动组合完整邮箱
watch([() => registerForm.emailPrefix, () => registerForm.emailDomain], ([prefix, domain]) => {
  if (prefix && domain) {
    registerForm.email = `${prefix}@${domain}`
  } else {
    registerForm.email = ''
  }
})

// 计算属性
const settings = computed(() => settingsStore)

// 表单验证规则
const registerRules = computed(() => ({
  email: [
    { required: true, message: '请选择邮箱类型', trigger: 'change' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' },
    { 
      pattern: /^[a-zA-Z0-9_]+$/, 
      message: '用户名只能包含字母、数字和下划线', 
      trigger: 'blur' 
    }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 50, message: '密码长度在 8 到 50 个字符', trigger: 'blur' },
    { 
      pattern: /^(?=.*[A-Za-z])(?=.*\d)/, 
      message: '密码必须包含字母和数字', 
      trigger: 'blur' 
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}))

// 方法
const handleRegister = async () => {
  try {
    await registerFormRef.value.validate()
    
    loading.value = true
    
    const response = await authAPI.register({
      email: registerForm.email,
      username: registerForm.username,
      password: registerForm.password
    })
    
    console.log('注册响应:', response.data)
    
    // 注册成功，自动登录
    if (response.data && response.data.access_token) {
      // 检查用户数据是否存在
      if (!response.data.user) {
        console.error('响应中缺少用户数据:', response.data)
        ElMessage.error('注册成功但用户数据异常，请重新登录')
        return
      }
      
      // 保存token到localStorage
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('user', JSON.stringify({
        id: response.data.user.id,
        username: response.data.user.username,
        email: response.data.user.email,
        is_admin: response.data.user.is_admin
      }))
      
      // 更新store状态
      authStore.setToken(response.data.access_token)
      authStore.setUser({
        id: response.data.user.id,
        username: response.data.user.username,
        email: response.data.user.email,
        is_admin: response.data.user.is_admin
      })
      
      ElMessage.success('注册成功！正在为您登录...')
      
      // 跳转到首页
      router.push('/')
    } else {
      console.error('注册响应格式异常:', response.data)
      ElMessage.error('注册失败，请重试')
    }
    
  } catch (error) {
    console.error('注册错误:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('注册失败，请重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--success-color) 100%);
  padding: 20px;
}

.register-card {
  background: var(--background-color);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
  
  .logo {
    width: 60px;
    height: 60px;
    margin-bottom: 16px;
  }
  
  h1 {
    margin: 0 0 8px 0;
    color: var(--text-color);
    font-size: 24px;
    font-weight: 600;
  }
  
  p {
    margin: 0;
    color: var(--text-color-secondary);
    font-size: 14px;
  }
}

.register-form {
  .register-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
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
}

.email-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .email-prefix {
    flex: 2; /* 邮箱前缀输入框占更多空间 */
  }
  
  .email-separator {
    font-size: 16px;
    font-weight: 500;
    color: var(--text-color-secondary);
    min-width: 20px;
    text-align: center;
  }
  
  .email-domain {
    flex: 1; /* 域名选择框占较少空间 */
    min-width: 100px;
  }
}

.register-footer {
  text-align: center;
  margin-top: 24px;
  
  p {
    margin: 0;
    color: var(--text-color-secondary);
    font-size: 14px;
    
    a {
      color: var(--primary-color);
      text-decoration: none;
      
      &:hover {
        text-decoration: underline;
      }
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .register-card {
    padding: 24px;
    margin: 10px;
  }
  
  .register-header h1 {
    font-size: 20px;
  }
}
</style> 