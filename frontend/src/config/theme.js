// 主题配置
export const themeConfig = {
  // 默认主题
  default: {
    name: 'default',
    primary: '#409EFF',
    success: '#67C23A',
    warning: '#E6A23C',
    danger: '#F56C6C',
    info: '#909399',
    background: '#f5f7fa',
    text: '#303133',
    border: '#DCDFE6'
  },
  
  // 深色主题
  dark: {
    name: 'dark',
    primary: '#409EFF',
    success: '#67C23A',
    warning: '#E6A23C',
    danger: '#F56C6C',
    info: '#909399',
    background: '#1a1a1a',
    text: '#ffffff',
    border: '#4c4c4c'
  },
  
  // 蓝色主题
  blue: {
    name: 'blue',
    primary: '#1890ff',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#8c8c8c',
    background: '#f0f2f5',
    text: '#262626',
    border: '#d9d9d9'
  },
  
  // 绿色主题
  green: {
    name: 'green',
    primary: '#52c41a',
    success: '#52c41a',
    warning: '#faad14',
    danger: '#ff4d4f',
    info: '#8c8c8c',
    background: '#f6ffed',
    text: '#262626',
    border: '#b7eb8f'
  }
}

// 主题管理类
export class ThemeManager {
  constructor() {
    this.currentTheme = localStorage.getItem('theme') || 'default'
    this.applyTheme(this.currentTheme)
  }
  
  // 获取当前主题
  getCurrentTheme() {
    return this.currentTheme
  }
  
  // 获取主题配置
  getThemeConfig(themeName = null) {
    const theme = themeName || this.currentTheme
    return themeConfig[theme] || themeConfig.default
  }
  
  // 应用主题
  applyTheme(themeName) {
    const config = this.getThemeConfig(themeName)
    if (!config) return
    
    this.currentTheme = themeName
    localStorage.setItem('theme', themeName)
    
    // 设置CSS变量
    const root = document.documentElement
    Object.keys(config).forEach(key => {
      if (key !== 'name') {
        root.style.setProperty(`--el-color-${key}`, config[key])
        root.style.setProperty(`--theme-${key}`, config[key])
      }
    })
    
    // 设置主题类名
    root.className = root.className.replace(/theme-\w+/g, '')
    root.classList.add(`theme-${themeName}`)
  }
  
  // 切换主题
  toggleTheme() {
    const themes = Object.keys(themeConfig)
    const currentIndex = themes.indexOf(this.currentTheme)
    const nextIndex = (currentIndex + 1) % themes.length
    this.applyTheme(themes[nextIndex])
  }
  
  // 获取所有主题
  getAllThemes() {
    return Object.keys(themeConfig).map(key => ({
      name: key,
      label: this.getThemeLabel(key),
      config: themeConfig[key]
    }))
  }
  
  // 获取主题标签
  getThemeLabel(themeName) {
    const labels = {
      default: '默认主题',
      dark: '深色主题',
      blue: '蓝色主题',
      green: '绿色主题'
    }
    return labels[themeName] || themeName
  }
}

// 创建全局主题管理器实例
export const themeManager = new ThemeManager() 