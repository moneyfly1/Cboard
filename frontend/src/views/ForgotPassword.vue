<template>
  <div class="forgot-password-container">
    <div class="forgot-password-card">
      <div class="card-header">
        <h2>忘记密码</h2>
        <p>请输入您的QQ邮箱，我们将发送重置密码的链接</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
        class="forgot-password-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="form.email"
            placeholder="请输入QQ邮箱"
            type="email"
            size="large"
            prefix-icon="Message"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleSubmit"
            class="submit-btn"
          >
            发送重置邮件
          </el-button>
        </el-form-item>

        <div class="form-footer">
          <el-link type="primary" @click="$router.push('/login')">
            返回登录
          </el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/utils/api'

export default {
  name: 'ForgotPassword',
  setup() {
    const formRef = ref()
    const loading = ref(false)

    const form = reactive({
      email: ''
    })

    const rules = {
      email: [
        { required: true, message: '请输入邮箱地址', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
        { 
          pattern: /^[1-9][0-9]{4,}@qq\.com$/,
          message: '请输入正确的QQ邮箱格式',
          trigger: 'blur'
        }
      ]
    }

    const handleSubmit = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        loading.value = true

        await authAPI.forgotPassword({ email: form.email })
        
        ElMessage.success('重置邮件已发送，请检查您的QQ邮箱')
        form.email = ''
      } catch (error) {
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('发送失败，请稍后重试')
        }
      } finally {
        loading.value = false
      }
    }

    return {
      formRef,
      form,
      rules,
      loading,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.forgot-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forgot-password-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
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

.forgot-password-form {
  width: 100%;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 1rem;
  font-weight: 600;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
}

@media (max-width: 480px) {
  .forgot-password-card {
    padding: 30px 20px;
  }
  
  .card-header h2 {
    font-size: 1.5rem;
  }
}
</style> 