<template>
  <div class="verify-email-container">
    <div class="verify-email-card">
      <div class="card-header">
        <div class="icon-wrapper">
          <i class="el-icon-message"></i>
        </div>
        <h2>邮箱验证</h2>
        <p>请检查您的QQ邮箱并点击验证链接</p>
      </div>

      <div class="verify-content">
        <div class="email-info">
          <p>验证邮件已发送至：</p>
          <p class="email">{{ email }}</p>
        </div>

        <div class="verify-tips">
          <h4>验证步骤：</h4>
          <ol>
            <li>打开您的QQ邮箱</li>
            <li>查找来自我们的验证邮件</li>
            <li>点击邮件中的验证链接</li>
            <li>验证成功后即可登录</li>
          </ol>
        </div>

        <div class="action-buttons">
          <el-button
            type="primary"
            size="large"
            :loading="resendLoading"
            @click="resendEmail"
            class="resend-btn"
          >
            重新发送验证邮件
          </el-button>
          
          <el-button
            size="large"
            @click="goToLogin"
            class="login-btn"
          >
            返回登录
          </el-button>
        </div>

        <div class="countdown" v-if="countdown > 0">
          <p>{{ countdown }}秒后可重新发送</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/utils/api'

export default {
  name: 'VerifyEmail',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const email = ref('')
    const resendLoading = ref(false)
    const countdown = ref(0)
    let countdownTimer = null

    const startCountdown = () => {
      countdown.value = 60
      countdownTimer = setInterval(() => {
        countdown.value--
        if (countdown.value <= 0) {
          clearInterval(countdownTimer)
        }
      }, 1000)
    }

    const resendEmail = async () => {
      if (countdown.value > 0) return

      try {
        resendLoading.value = true
        await authAPI.resendVerificationEmail({ email: email.value })
        ElMessage.success('验证邮件已重新发送')
        startCountdown()
      } catch (error) {
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('发送失败，请稍后重试')
        }
      } finally {
        resendLoading.value = false
      }
    }

    const goToLogin = () => {
      router.push('/login')
    }

    onMounted(() => {
      email.value = route.query.email || ''
      if (!email.value) {
        ElMessage.error('邮箱参数缺失')
        router.push('/login')
        return
      }
      startCountdown()
    })

    onUnmounted(() => {
      if (countdownTimer) {
        clearInterval(countdownTimer)
      }
    })

    return {
      email,
      resendLoading,
      countdown,
      resendEmail,
      goToLogin
    }
  }
}
</script>

<style scoped>
.verify-email-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.verify-email-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 500px;
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.icon-wrapper {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.icon-wrapper i {
  font-size: 2rem;
  color: white;
}

.card-header h2 {
  color: #333;
  font-size: 1.8rem;
  margin-bottom: 10px;
  font-weight: 600;
}

.card-header p {
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
}

.verify-content {
  text-align: center;
}

.email-info {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.email-info p {
  margin: 5px 0;
  color: #333;
}

.email-info .email {
  font-weight: 600;
  color: #1677ff;
  font-size: 1.1rem;
}

.verify-tips {
  margin-bottom: 30px;
  text-align: left;
}

.verify-tips h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 1rem;
}

.verify-tips ol {
  color: #666;
  line-height: 1.8;
  padding-left: 20px;
}

.verify-tips li {
  margin-bottom: 8px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.resend-btn {
  height: 44px;
  font-size: 1rem;
  font-weight: 600;
}

.login-btn {
  height: 44px;
  font-size: 1rem;
}

.countdown {
  color: #999;
  font-size: 0.9rem;
}

.countdown p {
  margin: 0;
}

@media (max-width: 480px) {
  .verify-email-card {
    padding: 30px 20px;
  }
  
  .card-header h2 {
    font-size: 1.5rem;
  }
  
  .action-buttons {
    gap: 10px;
  }
}
</style> 