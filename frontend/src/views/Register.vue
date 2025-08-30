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
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱地址"
            prefix-icon="Message"
            size="large"
          />
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
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/utils/api'
import { useSettingsStore } from '@/store/settings'

const router = useRouter()
const settingsStore = useSettingsStore()

// 响应式数据
const loading = ref(false)
const registerFormRef = ref()

const registerForm = reactive({
  email: '',
  username: '',
  password: '',
  confirmPassword: ''
})

// 计算属性
const settings = computed(() => settingsStore)

// 表单验证规则
const registerRules = computed(() => ({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        const error = settingsStore.getEmailError(value)
        if (error) {
          callback(new Error(error))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        const error = settingsStore.getPasswordError(value)
        if (error) {
          callback(new Error(error))
        } else {
          callback()
        }
      }, 
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
    
    ElMessage.success('注册成功！')
    
    // 如果需要邮箱验证，跳转到验证页面
    if (settingsStore.needsEmailVerification) {
      router.push('/verify-email')
    } else {
      // 直接跳转到登录页面
      router.push('/login')
    }
    
  } catch (error) {
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