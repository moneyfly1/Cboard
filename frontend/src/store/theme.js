import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'

export const useThemeStore = defineStore('theme', () => {
  // 状态
  const currentTheme = ref(localStorage.getItem('user-theme') || 'light')
  const availableThemes = ref([
    { value: 'light', label: '浅色主题', icon: 'sunny' },
    { value: 'dark', label: '深色主题', icon: 'moon' },
    { value: 'auto', label: '跟随系统', icon: 'monitor' }
  ])
  const loading = ref(false)

  // 计算属性
  const isDarkMode = computed(() => {
    if (currentTheme.value === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }
    return currentTheme.value === 'dark'
  })

  // 方法
  const setTheme = async (theme) => {
    try {
      loading.value = true
      
      // 保存到后端
      await api.put('/users/theme', { theme })
      
      // 更新本地状态
      currentTheme.value = theme
      localStorage.setItem('user-theme', theme)
      
      // 应用主题
      applyTheme(theme)
      
      return { success: true }
    } catch (error) {
      console.error('设置主题失败:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '设置主题失败' 
      }
    } finally {
      loading.value = false
    }
  }

  const applyTheme = (theme) => {
    const root = document.documentElement
    
    // 移除所有主题类
    root.classList.remove('theme-light', 'theme-dark', 'theme-auto')
    
    // 添加新主题类
    root.classList.add(`theme-${theme}`)
    
    // 设置CSS变量
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      root.style.setProperty('--el-bg-color', '#f5f5f5')
      root.style.setProperty('--el-bg-color-page', '#e8e8e8')
      root.style.setProperty('--el-text-color-primary', '#2c2c2c')
      root.style.setProperty('--el-text-color-regular', '#4a4a4a')
      root.style.setProperty('--el-text-color-secondary', '#666666')
      root.style.setProperty('--el-border-color', '#d0d0d0')
      root.style.setProperty('--el-border-color-light', '#e0e0e0')
      root.style.setProperty('--el-border-color-lighter', '#e8e8e8')
      root.style.setProperty('--el-border-color-extra-light', '#f0f0f0')
      root.style.setProperty('--el-fill-color', '#f8f8f8')
      root.style.setProperty('--el-fill-color-light', '#fafafa')
      root.style.setProperty('--el-fill-color-lighter', '#f8f8f8')
      root.style.setProperty('--el-fill-color-extra-light', '#fafafa')
      root.style.setProperty('--el-fill-color-blank', '#f5f5f5')
      
      // 自定义主题变量
      root.style.setProperty('--primary-color', '#409eff')
      root.style.setProperty('--success-color', '#67c23a')
      root.style.setProperty('--warning-color', '#e6a23c')
      root.style.setProperty('--danger-color', '#f56c6c')
      root.style.setProperty('--info-color', '#909399')
      root.style.setProperty('--background-color', '#f5f5f5')
      root.style.setProperty('--text-color', '#2c2c2c')
      root.style.setProperty('--text-color-secondary', '#666666')
      
      // 侧边栏专用颜色
      root.style.setProperty('--sidebar-bg-color', '#f0f0f0')
      root.style.setProperty('--sidebar-text-color', '#2c2c2c')
      root.style.setProperty('--sidebar-hover-bg', '#e8e8e8')
      root.style.setProperty('--sidebar-active-bg', '#409eff')
    } else {
      // 浅色主题
      root.style.setProperty('--el-bg-color', '#ffffff')
      root.style.setProperty('--el-bg-color-page', '#f2f3f5')
      root.style.setProperty('--el-text-color-primary', '#303133')
      root.style.setProperty('--el-text-color-regular', '#606266')
      root.style.setProperty('--el-text-color-secondary', '#909399')
      root.style.setProperty('--el-border-color', '#dcdfe6')
      root.style.setProperty('--el-border-color-light', '#e4e7ed')
      root.style.setProperty('--el-border-color-lighter', '#ebeef5')
      root.style.setProperty('--el-border-color-extra-light', '#f2f6fc')
      root.style.setProperty('--el-fill-color', '#f0f2f5')
      root.style.setProperty('--el-fill-color-light', '#f5f7fa')
      root.style.setProperty('--el-fill-color-lighter', '#fafafa')
      root.style.setProperty('--el-fill-color-extra-light', '#fafcff')
      root.style.setProperty('--el-fill-color-blank', '#ffffff')
      
      // 自定义主题变量
      root.style.setProperty('--primary-color', '#409eff')
      root.style.setProperty('--success-color', '#67c23a')
      root.style.setProperty('--warning-color', '#e6a23c')
      root.style.setProperty('--danger-color', '#f56c6c')
      root.style.setProperty('--info-color', '#909399')
      root.style.setProperty('--background-color', '#ffffff')
      root.style.setProperty('--text-color', '#303133')
      root.style.setProperty('--text-color-secondary', '#909399')
      
      // 侧边栏专用颜色
      root.style.setProperty('--sidebar-bg-color', '#f8f9fa')
      root.style.setProperty('--sidebar-text-color', '#303133')
      root.style.setProperty('--sidebar-hover-bg', '#e9ecef')
      root.style.setProperty('--sidebar-active-bg', '#409eff')
    }
  }

  const loadUserTheme = async () => {
    try {
      const response = await api.get('/users/theme')
      if (response.data && response.data.theme) {
        currentTheme.value = response.data.theme
        localStorage.setItem('user-theme', response.data.theme)
        applyTheme(response.data.theme)
      }
    } catch (error) {
      console.error('加载用户主题失败:', error)
      // 使用本地存储的主题
      applyTheme(currentTheme.value)
    }
  }

  const initTheme = () => {
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', () => {
      if (currentTheme.value === 'auto') {
        applyTheme('auto')
      }
    })
    
    // 应用初始主题
    applyTheme(currentTheme.value)
  }

  return {
    // 状态
    currentTheme,
    availableThemes,
    loading,
    
    // 计算属性
    isDarkMode,
    
    // 方法
    setTheme,
    applyTheme,
    loadUserTheme,
    initTheme
  }
})
