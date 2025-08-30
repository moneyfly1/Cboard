<template>
  <div class="admin-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <div class="logo" @click="$router.push('/admin/dashboard')">
          <img src="/vite.svg" alt="Logo" class="logo-img">
          <span class="logo-text" v-show="!sidebarCollapsed">XBoard 管理后台</span>
        </div>
        <div class="menu-toggle" @click="toggleSidebar">
          <i class="el-icon-menu"></i>
        </div>
      </div>
      
      <div class="header-center">
        <div class="quick-stats">
          <div class="stat-item">
            <i class="el-icon-user"></i>
            <span>{{ stats.users || 0 }}</span>
            <small>用户</small>
          </div>
          <div class="stat-item">
            <i class="el-icon-connection"></i>
            <span>{{ stats.subscriptions || 0 }}</span>
            <small>订阅</small>
          </div>
          <div class="stat-item">
            <i class="el-icon-money"></i>
            <span>¥{{ stats.revenue || 0 }}</span>
            <small>收入</small>
          </div>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 主题切换 -->
        <el-dropdown @command="handleThemeChange" class="theme-dropdown">
          <el-button type="text" class="theme-btn">
            <i class="el-icon-brush"></i>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-for="theme in themes" 
                :key="theme.name"
                :command="theme.name"
                :class="{ active: currentTheme === theme.name }"
              >
                <i class="el-icon-check" v-if="currentTheme === theme.name"></i>
                {{ theme.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 系统状态 -->
        <el-tooltip content="系统状态" placement="bottom">
          <div class="system-status" :class="systemStatus">
            <i class="el-icon-success"></i>
          </div>
        </el-tooltip>
        
        <!-- 管理员菜单 -->
        <el-dropdown @command="handleAdminCommand" class="admin-dropdown">
          <div class="admin-info">
            <el-avatar :size="32" :src="adminAvatar">
              {{ adminInitials }}
            </el-avatar>
            <span class="admin-name" v-show="!isMobile">{{ admin.username }}</span>
            <i class="el-icon-arrow-down"></i>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <i class="el-icon-user"></i>
                个人资料
              </el-dropdown-item>
              <el-dropdown-item command="settings">
                <i class="el-icon-setting"></i>
                系统设置
              </el-dropdown-item>
              <el-dropdown-item command="logs">
                <i class="el-icon-document"></i>
                系统日志
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <i class="el-icon-switch-button"></i>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section-title" v-show="!sidebarCollapsed">概览</div>
          <router-link 
            to="/admin/dashboard"
            class="nav-item"
            :class="{ active: $route.path === '/admin/dashboard' }"
          >
            <i class="el-icon-s-home"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">仪表盘</span>
          </router-link>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title" v-show="!sidebarCollapsed">用户管理</div>
          <router-link 
            to="/admin/users"
            class="nav-item"
            :class="{ active: $route.path === '/admin/users' }"
          >
            <i class="el-icon-user"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">用户列表</span>
          </router-link>
          <router-link 
            to="/admin/subscriptions"
            class="nav-item"
            :class="{ active: $route.path === '/admin/subscriptions' }"
          >
            <i class="el-icon-connection"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">订阅管理</span>
          </router-link>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title" v-show="!sidebarCollapsed">订单管理</div>
          <router-link 
            to="/admin/orders"
            class="nav-item"
            :class="{ active: $route.path === '/admin/orders' }"
          >
            <i class="el-icon-shopping-cart-2"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">订单列表</span>
          </router-link>
          <router-link 
            to="/admin/packages"
            class="nav-item"
            :class="{ active: $route.path === '/admin/packages' }"
          >
            <i class="el-icon-goods"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">套餐管理</span>
          </router-link>
        </div>
        
        <div class="nav-section">
          <div class="nav-section-title" v-show="!sidebarCollapsed">系统管理</div>
          <router-link 
            to="/admin/notifications"
            class="nav-item"
            :class="{ active: $route.path === '/admin/notifications' }"
          >
            <i class="el-icon-bell"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">通知管理</span>
          </router-link>
          <router-link 
            to="/admin/config"
            class="nav-item"
            :class="{ active: $route.path === '/admin/config' }"
          >
            <i class="el-icon-setting"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">配置管理</span>
          </router-link>
          <router-link 
            to="/admin/statistics"
            class="nav-item"
            :class="{ active: $route.path === '/admin/statistics' }"
          >
            <i class="el-icon-data-analysis"></i>
            <span class="nav-text" v-show="!sidebarCollapsed">数据统计</span>
          </router-link>
        </div>
      </nav>
    </aside>

    <!-- 主内容区域 -->
    <main class="main-content">
      <div class="content-wrapper">
        <!-- 面包屑导航 -->
        <div class="breadcrumb" v-if="showBreadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item 
              v-for="item in breadcrumbItems" 
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <!-- 页面内容 -->
        <div class="page-content">
          <router-view />
        </div>
      </div>
    </main>

    <!-- 移动端遮罩 -->
    <div 
      v-if="isMobile && !sidebarCollapsed" 
      class="mobile-overlay"
      @click="sidebarCollapsed = true"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { themeManager } from '@/config/theme'
import { adminAPI } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 响应式数据
const sidebarCollapsed = ref(false)
const stats = ref({})
const isMobile = ref(false)

// 计算属性
const currentTheme = computed(() => themeManager.getCurrentTheme())
const themes = computed(() => themeManager.getAllThemes())
const admin = computed(() => authStore.user)
const adminAvatar = computed(() => admin.value?.avatar || '')
const adminInitials = computed(() => {
  if (!admin.value?.username) return ''
  return admin.value.username.substring(0, 2).toUpperCase()
})

const showBreadcrumb = computed(() => {
  return route.meta.showBreadcrumb !== false
})

const breadcrumbItems = computed(() => {
  const items = []
  if (route.meta.breadcrumb) {
    items.push(...route.meta.breadcrumb)
  }
  return items
})

const systemStatus = computed(() => {
  // 这里可以根据实际系统状态返回不同的类名
  return 'online'
})

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleThemeChange = (themeName) => {
  themeManager.applyTheme(themeName)
}

const handleAdminCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/admin/profile')
      break
    case 'settings':
      router.push('/admin/settings')
      break
    case 'logs':
      router.push('/admin/logs')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}

const loadStats = async () => {
  try {
    const response = await adminAPI.getDashboard()
    stats.value = response.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const checkMobile = () => {
  isMobile.value = window.innerWidth <= 768
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

// 生命周期
onMounted(() => {
  checkMobile()
  loadStats()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped lang="scss">
@import '@/styles/global.scss';
.admin-layout {
  display: flex;
  height: 100vh;
  background-color: var(--theme-background);
}

.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: var(--header-height);
  background: white;
  border-bottom: 1px solid var(--theme-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      
      .logo-img {
        width: 32px;
        height: 32px;
      }
      
      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--theme-primary);
      }
    }
    
    .menu-toggle {
      display: none;
      cursor: pointer;
      padding: 8px;
      border-radius: 4px;
      
      &:hover {
        background-color: #f5f7fa;
      }
      
      @include respond-to(sm) {
        display: block;
      }
    }
  }
  
  .header-center {
    flex: 1;
    display: flex;
    justify-content: center;
    
    .quick-stats {
      display: flex;
      gap: 24px;
      
      @include respond-to(sm) {
        display: none;
      }
      
      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        
        i {
          font-size: 20px;
          color: var(--theme-primary);
        }
        
        span {
          font-size: 18px;
          font-weight: 600;
          color: var(--theme-text);
        }
        
        small {
          font-size: 12px;
          color: #666;
        }
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .theme-dropdown {
      .el-button {
        padding: 8px;
        border-radius: 4px;
        
        &:hover {
          background-color: #f5f7fa;
        }
      }
    }
    
    .system-status {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      
      &.online {
        background-color: #f0f9ff;
        color: #52c41a;
      }
      
      &.warning {
        background-color: #fff7e6;
        color: #faad14;
      }
      
      &.error {
        background-color: #fff2f0;
        color: #ff4d4f;
      }
    }
    
    .admin-dropdown {
      .admin-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        .admin-name {
          font-weight: 500;
        }
      }
    }
  }
}

.sidebar {
  position: fixed;
  top: var(--header-height);
  left: 0;
  width: var(--sidebar-width);
  height: calc(100vh - var(--header-height));
  background: white;
  border-right: 1px solid var(--theme-border);
  transition: all 0.3s ease;
  z-index: 999;
  overflow-y: auto;
  
  &.collapsed {
    width: var(--sidebar-collapsed-width);
  }
  
  @include respond-to(sm) {
    transform: translateX(-100%);
    
    &.collapsed {
      transform: translateX(0);
    }
  }
  
  .sidebar-nav {
    padding: 20px 0;
    
    .nav-section {
      margin-bottom: 24px;
      
      .nav-section-title {
        padding: 0 20px 8px;
        font-size: 12px;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      
      .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 20px;
        color: var(--theme-text);
        text-decoration: none;
        transition: all 0.3s ease;
        position: relative;
        
        &:hover {
          background-color: #f5f7fa;
          color: var(--theme-primary);
        }
        
        &.active {
          background-color: var(--theme-primary);
          color: white;
          
          &::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
            background-color: var(--theme-primary);
          }
        }
        
        i {
          font-size: 18px;
          margin-right: 12px;
          width: 20px;
          text-align: center;
        }
        
        .nav-text {
          font-weight: 500;
        }
      }
    }
  }
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  margin-top: var(--header-height);
  transition: all 0.3s ease;
  
  .sidebar-collapsed & {
    margin-left: var(--sidebar-collapsed-width);
  }
  
  @include respond-to(sm) {
    margin-left: 0;
  }
  
  .content-wrapper {
    padding: var(--content-padding);
    
    .breadcrumb {
      margin-bottom: 20px;
      padding: 12px 16px;
      background: white;
      border-radius: var(--border-radius);
      box-shadow: var(--box-shadow);
    }
    
    .page-content {
      min-height: calc(100vh - var(--header-height) - 80px);
    }
  }
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 998;
}
</style> 