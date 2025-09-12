import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

import App from './App.vue'
import router from './router'
import { useSettingsStore } from './store/settings'
import { useAuthStore } from './store/auth'

// 导入全局样式
import './styles/global.scss'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
})

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  // 只在开发环境输出详细错误信息
  if (import.meta.env.DEV) {
    console.error('全局错误:', err, info)
  }
}

// 全局属性
app.config.globalProperties.$settings = null
app.config.globalProperties.$auth = null

// 初始化应用
async function initializeApp() {
  try {
    // 设置全局属性
    app.config.globalProperties.$auth = useAuthStore()
    
    // 先挂载应用
    app.mount('#app')
    
    // 异步加载设置（不阻塞应用启动）
    try {
      const settingsStore = useSettingsStore()
      await settingsStore.loadSettings()
      settingsStore.initTheme()
      app.config.globalProperties.$settings = settingsStore
      if (import.meta.env.DEV) {
        console.log('设置加载完成')
      }
    } catch (settingsError) {
      if (import.meta.env.DEV) {
        console.warn('设置加载失败，使用默认设置:', settingsError)
      }
    }
    
    if (import.meta.env.DEV) {
      console.log('应用初始化完成')
    }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('应用初始化失败:', error)
    }
    // 最后的兜底方案
    app.mount('#app')
  }
}

// 启动应用
initializeApp() 