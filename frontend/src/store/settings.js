import { defineStore } from 'pinia'
import { settingsAPI } from '@/utils/api'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    // 基本设置
    siteName: 'XBoard',
    siteDescription: '高性能面板系统',
    siteKeywords: '面板,管理,系统',
    siteLogo: '',
    siteFavicon: '',
    
    // 注册设置
    allowRegistration: true,
    requireEmailVerification: true,
    allowQqEmailOnly: true,
    minPasswordLength: 8,
    
    // 主题设置
    defaultTheme: 'default',
    allowUserTheme: true,
    availableThemes: ['default', 'dark', 'blue', 'green'],
    
    // 支付设置
    enablePayment: true,
    defaultPaymentMethod: '',
    paymentCurrency: 'CNY',
    
    // 公告设置
    enableAnnouncement: true,
    announcementPosition: 'top',
    maxAnnouncements: 5,
    
    // 加载状态
    loading: false,
    error: null
  }),

  getters: {
    // 获取网站标题
    siteTitle: (state) => state.siteName,
    
    // 获取当前主题
    currentTheme: (state) => {
      const userTheme = localStorage.getItem('user-theme')
      if (state.allowUserTheme && userTheme && state.availableThemes.includes(userTheme)) {
        return userTheme
      }
      return state.defaultTheme
    },
    
    // 检查是否允许注册
    canRegister: (state) => state.allowRegistration,
    
    // 检查是否需要邮箱验证
    needsEmailVerification: (state) => state.requireEmailVerification,
    
    // 检查是否仅允许特定邮箱
    emailRestriction: (state) => state.allowQqEmailOnly,
    
    // 检查支付是否启用
    paymentEnabled: (state) => state.enablePayment,
    
    // 检查公告是否启用
    announcementEnabled: (state) => state.enableAnnouncement
  },

  actions: {
    // 加载设置
    async loadSettings() {
      this.loading = true
      this.error = null
      
      try {
        const response = await settingsAPI.getPublicSettings()
        const settings = response.data
        
        // 更新基本设置
        this.siteName = settings.site_name || 'XBoard'
        this.siteDescription = settings.site_description || '高性能面板系统'
        this.siteKeywords = settings.site_keywords || '面板,管理,系统'
        this.siteLogo = settings.site_logo || ''
        this.siteFavicon = settings.site_favicon || ''
        
        // 更新注册设置
        this.allowRegistration = settings.allow_registration !== false
        this.requireEmailVerification = settings.require_email_verification !== false
        this.allowQqEmailOnly = settings.allow_qq_email_only !== false
        this.minPasswordLength = settings.min_password_length || 8
        
        // 更新主题设置
        this.defaultTheme = settings.default_theme || 'default'
        this.allowUserTheme = settings.allow_user_theme !== false
        this.availableThemes = settings.available_themes || ['default', 'dark', 'blue', 'green']
        
        // 更新支付设置
        this.enablePayment = settings.enable_payment !== false
        this.defaultPaymentMethod = settings.default_payment_method || ''
        this.paymentCurrency = settings.payment_currency || 'CNY'
        
        // 更新公告设置
        this.enableAnnouncement = settings.enable_announcement !== false
        this.announcementPosition = settings.announcement_position || 'top'
        this.maxAnnouncements = settings.max_announcements || 5
        
        // 更新页面标题
        document.title = this.siteName
        
        // 更新网站图标
        if (this.siteFavicon) {
          const link = document.querySelector("link[rel*='icon']") || document.createElement('link')
          link.type = 'image/x-icon'
          link.rel = 'shortcut icon'
          link.href = this.siteFavicon
          document.getElementsByTagName('head')[0].appendChild(link)
        }
        
      } catch (error) {
        this.error = error.message || '加载设置失败'
        console.error('加载设置失败:', error)
      } finally {
        this.loading = false
      }
    },

    // 设置用户主题
    setUserTheme(theme) {
      if (this.allowUserTheme && this.availableThemes.includes(theme)) {
        localStorage.setItem('user-theme', theme)
        // 应用主题
        this.applyTheme(theme)
      }
    },

    // 应用主题
    applyTheme(theme) {
      // 移除所有主题类
      document.documentElement.classList.remove('theme-default', 'theme-dark', 'theme-blue', 'theme-green')
      
      // 添加新主题类
      document.documentElement.classList.add(`theme-${theme}`)
      
      // 更新CSS变量
      this.updateThemeVariables(theme)
    },

    // 更新主题CSS变量
    updateThemeVariables(theme) {
      const root = document.documentElement
      
      // 主题颜色配置
      const themeColors = {
        default: {
          '--primary-color': '#409eff',
          '--success-color': '#67c23a',
          '--warning-color': '#e6a23c',
          '--danger-color': '#f56c6c',
          '--info-color': '#909399',
          '--text-color': '#303133',
          '--text-color-secondary': '#606266',
          '--border-color': '#dcdfe6',
          '--background-color': '#ffffff',
          '--background-color-secondary': '#f5f7fa'
        },
        dark: {
          '--primary-color': '#409eff',
          '--success-color': '#67c23a',
          '--warning-color': '#e6a23c',
          '--danger-color': '#f56c6c',
          '--info-color': '#909399',
          '--text-color': '#ffffff',
          '--text-color-secondary': '#c0c4cc',
          '--border-color': '#4c4d4f',
          '--background-color': '#1d1e1f',
          '--background-color-secondary': '#2d2e2f'
        },
        blue: {
          '--primary-color': '#1890ff',
          '--success-color': '#52c41a',
          '--warning-color': '#faad14',
          '--danger-color': '#ff4d4f',
          '--info-color': '#8c8c8c',
          '--text-color': '#262626',
          '--text-color-secondary': '#595959',
          '--border-color': '#d9d9d9',
          '--background-color': '#ffffff',
          '--background-color-secondary': '#f0f2f5'
        },
        green: {
          '--primary-color': '#52c41a',
          '--success-color': '#389e0d',
          '--warning-color': '#d48806',
          '--danger-color': '#cf1322',
          '--info-color': '#8c8c8c',
          '--text-color': '#262626',
          '--text-color-secondary': '#595959',
          '--border-color': '#d9d9d9',
          '--background-color': '#ffffff',
          '--background-color-secondary': '#f6ffed'
        }
      }
      
      const colors = themeColors[theme] || themeColors.default
      
      // 设置CSS变量
      Object.entries(colors).forEach(([key, value]) => {
        root.style.setProperty(key, value)
      })
    },

    // 初始化主题
    initTheme() {
      const theme = this.currentTheme
      this.applyTheme(theme)
    },

    // 验证邮箱格式
    validateEmail(email) {
      if (!email) return false
      
      // 基本邮箱格式验证
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
      if (!emailPattern.test(email)) return false
      
      // 邮箱验证 - 支持所有邮箱格式
      return true
      
      return true
    },

    // 验证密码强度
    validatePassword(password) {
      if (!password) return false
      
      if (password.length < this.minPasswordLength) return false
      
      // 密码复杂度验证
      const hasLetter = /[a-zA-Z]/.test(password)
      const hasDigit = /\d/.test(password)
      const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
      
      return hasLetter && hasDigit && hasSpecial
    },

    // 获取密码验证错误信息
    getPasswordError(password) {
      if (!password) return '请输入密码'
      
      if (password.length < this.minPasswordLength) {
        return `密码长度至少${this.minPasswordLength}位`
      }
      
      const hasLetter = /[a-zA-Z]/.test(password)
      const hasDigit = /\d/.test(password)
      const hasSpecial = /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)
      
      if (!hasLetter) return '密码必须包含字母'
      if (!hasDigit) return '密码必须包含数字'
      if (!hasSpecial) return '密码必须包含特殊字符'
      
      return null
    },

    // 获取邮箱验证错误信息
    getEmailError(email) {
      if (!email) return '请输入邮箱'
      
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
      if (!emailPattern.test(email)) return '邮箱格式不正确'
      
      // 支持所有邮箱格式
      return null
      
      return null
    },

    // 重置设置
    resetSettings() {
      this.siteName = 'XBoard'
      this.siteDescription = '高性能面板系统'
      this.siteKeywords = '面板,管理,系统'
      this.siteLogo = ''
      this.siteFavicon = ''
      this.allowRegistration = true
      this.requireEmailVerification = true
      this.allowQqEmailOnly = false
      this.minPasswordLength = 8
      this.defaultTheme = 'default'
      this.allowUserTheme = true
      this.availableThemes = ['default', 'dark', 'blue', 'green']
      this.enablePayment = true
      this.defaultPaymentMethod = ''
      this.paymentCurrency = 'CNY'
      this.enableAnnouncement = true
      this.announcementPosition = 'top'
      this.maxAnnouncements = 5
    }
  }
}) 