<template>
  <div class="user-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- 顶部导航栏 -->
    <header class="header">
      <div class="header-left">
        <div class="logo" @click="$router.push('/dashboard')">
          <img src="/vite.svg" alt="Logo" class="logo-img">
          <span class="logo-text" v-show="!sidebarCollapsed">XBoard</span>
        </div>
        <div class="menu-toggle" @click="toggleSidebar">
          <i class="el-icon-menu"></i>
        </div>
      </div>
      
      <div class="header-center">
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索功能..."
            prefix-icon="el-icon-search"
            clearable
            @keyup.enter="handleSearch"
          />
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
        
        <!-- 通知 -->
        <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notification-badge">
          <el-button type="text" @click="showNotifications = true">
            <i class="el-icon-bell"></i>
          </el-button>
        </el-badge>
        
        <!-- 用户菜单 -->
        <el-dropdown @command="handleUserCommand" class="user-dropdown">
          <div class="user-info">
            <el-avatar :size="32" :src="userAvatar">
              {{ userInitials }}
            </el-avatar>
            <span class="username" v-show="!isMobile">{{ user.username }}</span>
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
                设置
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
        <router-link 
          v-for="item in menuItems" 
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <i :class="item.icon"></i>
          <span class="nav-text" v-show="!sidebarCollapsed">{{ item.title }}</span>
          <el-badge 
            v-if="item.badge" 
            :value="item.badge" 
            class="nav-badge"
            v-show="!sidebarCollapsed"
          />
        </router-link>
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

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="showNotifications"
      title="通知中心"
      direction="rtl"
      size="400px"
    >
      <div class="notifications-container">
        <div v-if="notifications.length === 0" class="empty-notifications">
          <i class="el-icon-bell"></i>
          <p>暂无通知</p>
        </div>
        <div v-else class="notification-list">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.is_read }"
            @click="markAsRead(notification.id)"
          >
            <div class="notification-icon">
              <i :class="getNotificationIcon(notification.type)"></i>
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-text">{{ notification.content }}</div>
              <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>

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
import { notificationAPI } from '@/utils/api'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 响应式数据
const sidebarCollapsed = ref(false)
const searchKeyword = ref('')
const showNotifications = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const isMobile = ref(false)

// 计算属性
const currentTheme = computed(() => themeManager.getCurrentTheme())
const themes = computed(() => themeManager.getAllThemes())
const user = computed(() => authStore.user)
const userAvatar = computed(() => user.value?.avatar || '')
const userInitials = computed(() => {
  if (!user.value?.username) return ''
  return user.value.username.substring(0, 2).toUpperCase()
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

// 菜单项
const menuItems = computed(() => [
  {
    path: '/dashboard',
    title: '仪表盘',
    icon: 'el-icon-s-home',
    badge: null
  },
  {
    path: '/subscription',
    title: '订阅管理',
    icon: 'el-icon-connection',
    badge: null
  },
  {
    path: '/devices',
    title: '设备管理',
    icon: 'el-icon-mobile-phone',
    badge: null
  },
  {
    path: '/packages',
    title: '套餐购买',
    icon: 'el-icon-shopping-cart-2',
    badge: null
  },
  {
    path: '/orders',
    title: '订单记录',
    icon: 'el-icon-document',
    badge: null
  },
  {
    path: '/nodes',
    title: '节点列表',
    icon: 'el-icon-location',
    badge: null
  },
  {
    path: '/help',
    title: '帮助中心',
    icon: 'el-icon-question',
    badge: null
  }
])

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleThemeChange = (themeName) => {
  themeManager.applyTheme(themeName)
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    // 实现搜索功能
    console.log('搜索:', searchKeyword.value)
  }
}

const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      break
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    system: 'el-icon-info',
    order: 'el-icon-shopping-cart-2',
    subscription: 'el-icon-connection'
  }
  return icons[type] || 'el-icon-bell'
}

const formatTime = (time) => {
  return new Date(time).toLocaleString()
}

const markAsRead = async (notificationId) => {
  try {
    await notificationAPI.markAsRead(notificationId)
    await loadNotifications()
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const loadNotifications = async () => {
  try {
    const response = await notificationAPI.getUserNotifications({ limit: 10 })
    notifications.value = response.data.notifications
    unreadCount.value = response.data.total
  } catch (error) {
    console.error('加载通知失败:', error)
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
  loadNotifications()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped lang="scss">
.user-layout {
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
    max-width: 400px;
    margin: 0 20px;
    
    @include respond-to(sm) {
      display: none;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    
    .theme-dropdown, .notification-badge {
      .el-button {
        padding: 8px;
        border-radius: 4px;
        
        &:hover {
          background-color: #f5f7fa;
        }
      }
    }
    
    .user-dropdown {
      .user-info {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        .username {
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
      
      .nav-badge {
        margin-left: auto;
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

.notifications-container {
  .empty-notifications {
    text-align: center;
    padding: 40px 20px;
    color: #909399;
    
    i {
      font-size: 48px;
      margin-bottom: 16px;
    }
  }
  
  .notification-list {
    .notification-item {
      display: flex;
      padding: 16px;
      border-bottom: 1px solid var(--theme-border);
      cursor: pointer;
      transition: background-color 0.3s ease;
      
      &:hover {
        background-color: #f5f7fa;
      }
      
      &.unread {
        background-color: #f0f9ff;
      }
      
      .notification-icon {
        margin-right: 12px;
        
        i {
          font-size: 20px;
          color: var(--theme-primary);
        }
      }
      
      .notification-content {
        flex: 1;
        
        .notification-title {
          font-weight: 500;
          margin-bottom: 4px;
        }
        
        .notification-text {
          color: #666;
          font-size: 14px;
          margin-bottom: 4px;
        }
        
        .notification-time {
          color: #999;
          font-size: 12px;
        }
      }
    }
  }
}
</style> 