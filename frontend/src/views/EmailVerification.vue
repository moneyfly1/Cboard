<template>
  <div class="verification-container">
    <div class="verification-card">
      <div class="verification-header">
        <img v-if="settings.siteLogo" :src="settings.siteLogo" :alt="settings.siteName" class="logo" />
        <h1>邮箱验证</h1>
        <p>请验证您的邮箱地址</p>
      </div>

      <div v-if="loading" class="loading-section">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在验证邮箱...</p>
      </div>

      <div v-else-if="verificationResult.success" class="success-section">
        <el-icon class="success-icon"><Check /></el-icon>
        <h2>验证成功！</h2>
        <p>{{ verificationResult.message }}</p>
        <el-button type="primary" @click="goToLogin" class="action-button">
          立即登录
        </el-button>
      </div>

      <div v-else class="error-section">
        <el-icon class="error-icon"><Close /></el-icon>
        <h2>验证失败</h2>
        <p>{{ verificationResult.message }}</p>
        <div class="action-buttons">
          <el-button @click="resendVerification" :loading="resendLoading">
            重新发送验证邮件
          </el-button>
          <el-button type="primary" @click="goToLogin">
            返回登录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Check, Close } from '@element-plus/icons-vue'
import { useSettingsStore } from '@/store/settings'
import { api } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()

// 响应式数据
const loading = ref(true)
const resendLoading = ref(false)
const verificationResult = reactive({
  success: false,
  message: ''
})

// 计算属性
const settings = computed(() => settingsStore)

// 验证邮箱
const verifyEmail = async (token) => {
  try {
    const response = await api.post('/auth/verify-email', { token })
    verificationResult.success = true
    verificationResult.message = response.data.message
    ElMessage.success('邮箱验证成功！')
  } catch (error) {
    verificationResult.success = false
    verificationResult.message = error.response?.data?.detail || '验证失败，请重试'
    ElMessage.error(verificationResult.message)
  } finally {
    loading.value = false
  }
}

// 重新发送验证邮件
const resendVerification = async () => {
  resendLoading.value = true
  try {
    // 这里需要用户输入邮箱地址
    const email = prompt('请输入您的邮箱地址：')
    if (email) {
      await api.post('/auth/resend-verification', { email })
      ElMessage.success('验证邮件已重新发送，请查收')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '发送失败，请重试')
  } finally {
    resendLoading.value = false
  }
}

// 跳转到登录页面
const goToLogin = () => {
  router.push('/login')
}

// 组件挂载时验证邮箱
onMounted(() => {
  const token = route.query.token
  if (token) {
    verifyEmail(token)
  } else {
    verificationResult.success = false
    verificationResult.message = '缺少验证令牌'
    loading.value = false
  }
})
</script>

<style lang="scss" scoped>
.verification-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.verification-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.verification-header {
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

.loading-section {
  .el-icon {
    font-size: 48px;
    color: var(--primary-color);
    margin-bottom: 16px;
  }
  
  p {
    color: var(--text-color-secondary);
    font-size: 16px;
  }
}

.success-section {
  .success-icon {
    font-size: 48px;
    color: #67c23a;
    margin-bottom: 16px;
  }
  
  h2 {
    margin: 0 0 16px 0;
    color: var(--text-color-primary);
    font-size: 20px;
    font-weight: 600;
  }
  
  p {
    margin: 0 0 24px 0;
    color: var(--text-color-secondary);
    font-size: 14px;
  }
  
  .action-button {
    width: 100%;
    height: 48px;
    font-size: 16px;
    font-weight: 500;
  }
}

.error-section {
  .error-icon {
    font-size: 48px;
    color: #f56c6c;
    margin-bottom: 16px;
  }
  
  h2 {
    margin: 0 0 16px 0;
    color: var(--text-color-primary);
    font-size: 20px;
    font-weight: 600;
  }
  
  p {
    margin: 0 0 24px 0;
    color: var(--text-color-secondary);
    font-size: 14px;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: 12px;
    
    .el-button {
      width: 100%;
      height: 48px;
      font-size: 16px;
      font-weight: 500;
    }
  }
}

// 响应式设计
@media (max-width: 480px) {
  .verification-card {
    padding: 24px;
    margin: 10px;
  }
  
  .verification-header h1 {
    font-size: 20px;
  }
}
</style>
