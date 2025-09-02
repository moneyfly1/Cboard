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
      console.log('认证存储：开始登录请求')
      console.log('认证存储：用户名:', credentials.username)
      
      // 使用新的JSON登录端点
      const response = await api.post('/auth/login-json', {
        username: credentials.username,
        password: credentials.password
      })
      
      console.log('认证存储：收到响应:', response.data)
      
      const { access_token, refresh_token, user: userData } = response.data
      
      console.log('认证存储：解析的用户数据:', userData)
      console.log('认证存储：is_admin字段:', userData?.is_admin)
      
      // 保存令牌和用户信息
      token.value = access_token
      user.value = userData
      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      console.log('认证存储：保存后的用户状态:', user.value)
      console.log('认证存储：保存后的isAdmin状态:', isAdmin.value)
      
      return { success: true }
    } catch (error) {
      console.error('认证存储：登录错误:', error)
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
      return { success: true, message: '注册成功，请查收邮箱验证邮件' }
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
      return { success: true, message: '重置链接已发送到您的邮箱，请查收' }
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
      return { success: true, message: '邮箱验证成功' }
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

  const changePassword = async (oldPassword, newPassword) => {
    loading.value = true
    try {
      await api.post('/users/change-password', {
        old_password: oldPassword,
        new_password: newPassword
      })
      return { success: true, message: '密码修改成功' }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.detail || '密码修改失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const getCurrentState = () => {
    return {
      token: token.value,
      user: user.value,
      isAuthenticated: isAuthenticated.value,
      isAdmin: isAdmin.value,
      localStorageUser: localStorage.getItem('user'),
      localStorageToken: localStorage.getItem('token')
    }
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
    updateUser,
    changePassword,
    getCurrentState
  }
}) 