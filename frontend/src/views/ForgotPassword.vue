<template>
  <div class="forgot-container">
    <div class="forgot-card">
      <div class="forgot-header">
        <img v-if="settings.siteLogo" :src="settings.siteLogo" :alt="settings.siteName" class="logo" />
        <h1>忘记密码</h1>
        <p>输入您的邮箱地址，我们将发送重置链接</p>
      </div>

      <el-form
        ref="forgotFormRef"
        :model="forgotForm"
        :rules="forgotRules"
        label-width="0"
        class="forgot-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="forgotForm.email"
            placeholder="邮箱地址"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="forgot-button"
            :loading="loading"
            @click="handleForgotPassword"
          >
            发送重置链接
          </el-button>
        </el-form-item>
      </el-form>

      <div class="forgot-footer">
        <p>
          <router-link to="/login">返回登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useSettingsStore } from '@/store/settings'
import { api } from '@/utils/api'

const router = useRouter()
const settingsStore = useSettingsStore()

// 响应式数据
const loading = ref(false)
const forgotFormRef = ref()

const forgotForm = reactive({
  email: ''
})

// 计算属性
const settings = computed(() => settingsStore)

// 表单验证规则
const forgotRules = computed(() => ({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}))

// 发送重置邮件
const handleForgotPassword = async () => {
  try {
    await forgotFormRef.value.validate()
    
    loading.value = true
    
    const response = await api.post('/auth/forgot-password-new', {
      email: forgotForm.email
    })
    
    ElMessage.success('如果该邮箱已注册，重置链接已发送到您的邮箱')
    
    // 延迟跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 2000)
    
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('发送失败，请重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.forgot-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forgot-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.forgot-header {
  text-align: center;
  margin-bottom: 32px;
  
  .logo {
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
  }
  
  h1 {
    margin: 0 0 8px 0;
    color: var(--text-color-primary);
    font-size: 24px;
    font-weight: 600;
  }
  
  p {
    margin: 0;
    color: var(--text-color-secondary);
    font-size: 14px;
  }
}

.forgot-form {
  .forgot-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
  }
}

.forgot-footer {
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
  .forgot-card {
    padding: 24px;
    margin: 10px;
  }
  
  .forgot-header h1 {
    font-size: 20px;
  }
}
</style>