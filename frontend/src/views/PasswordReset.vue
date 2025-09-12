<template>
  <div class="reset-container">
    <div class="reset-card">
      <div class="reset-header">
        <img v-if="settings.siteLogo" :src="settings.siteLogo" :alt="settings.siteName" class="logo" />
        <h1>重置密码</h1>
        <p>设置您的新密码</p>
      </div>

      <el-form
        ref="resetFormRef"
        :model="resetForm"
        :rules="resetRules"
        label-width="0"
        class="reset-form"
      >
        <el-form-item prop="newPassword">
          <el-input
            v-model="resetForm.newPassword"
            type="password"
            placeholder="新密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="resetForm.confirmPassword"
            type="password"
            placeholder="确认新密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="reset-button"
            :loading="loading"
            @click="handleReset"
          >
            重置密码
          </el-button>
        </el-form-item>
      </el-form>

      <div class="reset-footer">
        <p>
          <router-link to="/login">返回登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useSettingsStore } from '@/store/settings'
import { api } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const settingsStore = useSettingsStore()

// 响应式数据
const loading = ref(false)
const resetFormRef = ref()

const resetForm = reactive({
  newPassword: '',
  confirmPassword: ''
})

// 计算属性
const settings = computed(() => settingsStore)

// 表单验证规则
const resetRules = computed(() => ({
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 50, message: '密码长度在 8 到 50 个字符', trigger: 'blur' },
    { 
      pattern: /^(?=.*[A-Za-z])(?=.*\d)/, 
      message: '密码必须包含字母和数字', 
      trigger: 'blur' 
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== resetForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}))

// 重置密码
const handleReset = async () => {
  try {
    await resetFormRef.value.validate()
    
    loading.value = true
    
    const token = route.query.token
    if (!token) {
      ElMessage.error('缺少重置令牌')
      return
    }
    
    const response = await api.post('/auth/reset-password-new', {
      token: token,
      new_password: resetForm.newPassword
    })
    
    ElMessage.success('密码重置成功！')
    
    // 延迟跳转到登录页面
    setTimeout(() => {
      router.push('/login')
    }, 1500)
    
  } catch (error) {
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('重置失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

// 检查重置令牌
onMounted(() => {
  const token = route.query.token
  if (!token) {
    ElMessage.error('无效的重置链接')
    router.push('/login')
  }
})
</script>

<style lang="scss" scoped>
.reset-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.reset-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.reset-header {
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

.reset-form {
  .reset-button {
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

.reset-footer {
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
  .reset-card {
    padding: 24px;
    margin: 10px;
  }
  
  .reset-header h1 {
    font-size: 20px;
  }
}
</style>
