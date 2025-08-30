<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>XBoard Modern</h1>
        <p>现代化订阅管理系统</p>
      </div>
      
      <el-form
        ref="loginForm"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="QQ号码或QQ邮箱"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-button"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
        
        <div class="login-actions">
          <el-link type="primary" @click="$router.push('/register')">
            注册账户
          </el-link>
          <el-link type="primary" @click="showForgotPassword = true">
            忘记密码？
          </el-link>
        </div>
      </el-form>
    </div>
    
    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="showForgotPassword"
      title="忘记密码"
      width="400px"
    >
      <el-form
        ref="forgotForm"
        :model="forgotForm"
        :rules="forgotRules"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            placeholder="请输入QQ邮箱地址"
            type="email"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showForgotPassword = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="forgotLoading"
          @click="handleForgotPassword"
        >
          发送重置邮件
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    
    const loginForm = reactive({
      username: '',
      password: ''
    })
    
    const forgotForm = reactive({
      email: ''
    })
    
    const loading = ref(false)
    const forgotLoading = ref(false)
    const showForgotPassword = ref(false)
    
    const loginRules = {
      username: [
        { required: true, message: '请输入QQ号码或QQ邮箱', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ]
    }
    
    const forgotRules = {
      email: [
        { required: true, message: '请输入QQ邮箱地址', trigger: 'blur' },
        { type: 'email', message: '请输入正确的QQ邮箱格式', trigger: 'blur' },
        { 
          pattern: /^\d+@qq\.com$/,
          message: '请输入正确的QQ邮箱地址',
          trigger: 'blur'
        }
      ]
    }
    
    const handleLogin = async () => {
      loading.value = true
      
      try {
        const result = await authStore.login(loginForm)
        if (result.success) {
          ElMessage.success('登录成功')
          router.push('/dashboard')
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        ElMessage.error('登录失败，请重试')
      } finally {
        loading.value = false
      }
    }
    
    const handleForgotPassword = async () => {
      forgotLoading.value = true
      
      try {
        const result = await authStore.forgotPassword(forgotForm.email)
        if (result.success) {
          ElMessage.success(result.message)
          showForgotPassword.value = false
          forgotForm.email = ''
        } else {
          ElMessage.error(result.message)
        }
      } catch (error) {
        ElMessage.error('发送失败，请重试')
      } finally {
        forgotLoading.value = false
      }
    }
    
    return {
      loginForm,
      forgotForm,
      loading,
      forgotLoading,
      showForgotPassword,
      loginRules,
      forgotRules,
      handleLogin,
      handleForgotPassword
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  color: #1677ff;
  font-size: 28px;
  margin-bottom: 8px;
  font-weight: 600;
}

.login-header p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-top: 20px;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.login-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  font-size: 14px;
}

@media (max-width: 480px) {
  .login-box {
    padding: 30px 20px;
  }
  
  .login-header h1 {
    font-size: 24px;
  }
}
</style> 