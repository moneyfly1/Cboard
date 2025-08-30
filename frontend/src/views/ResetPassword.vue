<template>
  <div class="reset-password-container">
    <div class="reset-password-card">
      <div class="card-header">
        <h2>重置密码</h2>
        <p>请输入您的新密码</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleSubmit"
        class="reset-password-form"
      >
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            placeholder="请输入新密码"
            type="password"
            size="large"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            placeholder="请确认新密码"
            type="password"
            size="large"
            prefix-icon="Lock"
            show-password
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
            重置密码
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
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/utils/api'

export default {
  name: 'ResetPassword',
  setup() {
    const route = useRoute()
    const router = useRouter()
    const formRef = ref()
    const loading = ref(false)

    const form = reactive({
      password: '',
      confirmPassword: ''
    })

    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请确认密码'))
      } else if (value !== form.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }

    const rules = {
      password: [
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
        { max: 20, message: '密码长度不能超过20位', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }

    const handleSubmit = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        loading.value = true

        const token = route.query.token
        if (!token) {
          ElMessage.error('重置链接无效')
          return
        }

        await authAPI.resetPassword({
          token,
          password: form.password
        })
        
        ElMessage.success('密码重置成功，请使用新密码登录')
        router.push('/login')
      } catch (error) {
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('重置失败，请稍后重试')
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
.reset-password-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.reset-password-card {
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

.reset-password-form {
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
  .reset-password-card {
    padding: 30px 20px;
  }
  
  .card-header h2 {
    font-size: 1.5rem;
  }
}
</style> 