import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  // 方法
  const login = async (credentials) => {
    loading.value = true
    try {
      // 使用表单数据格式发送登录请求
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      })
      
      const { access_token, refresh_token, user: userData } = response.data
      
      // 保存令牌和用户信息
      token.value = access_token
      user.value = userData
      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '登录失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const register = async (userData) => {
    loading.value = true
    try {
      await api.post('/auth/register', userData)
      return { success: true, message: '注册成功，请查收QQ邮箱验证邮件' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '注册失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  const refreshToken = async () => {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) {
      logout()
      return false
    }

    try {
      const response = await api.post('/auth/refresh', { refresh_token })
      const { access_token } = response.data
      
      token.value = access_token
      localStorage.setItem('token', access_token)
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  const forgotPassword = async (email) => {
    loading.value = true
    try {
      await api.post('/auth/forgot-password', { email })
      return { success: true, message: '重置链接已发送到您的QQ邮箱，请查收' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '发送失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const resetPassword = async (token, newPassword) => {
    loading.value = true
    try {
      await api.post('/auth/reset-password', { token, new_password: newPassword })
      return { success: true, message: '密码重置成功' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '重置失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const verifyEmail = async (token) => {
    loading.value = true
    try {
      await api.post('/auth/verify-email', { token })
      return { success: true, message: 'QQ邮箱验证成功' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '验证失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const updateUser = (userData) => {
    user.value = { ...user.value, ...userData }
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  return {
    // 状态
    token,
    user,
    loading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    login,
    register,
    logout,
    refreshToken,
    forgotPassword,
    resetPassword,
    verifyEmail,
    updateUser
  }
}) 