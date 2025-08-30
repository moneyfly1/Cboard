import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import UserLayout from '@/components/layout/UserLayout.vue'
import AdminLayout from '@/components/layout/AdminLayout.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: () => import('@/views/VerifyEmail.vue'),
    meta: { requiresGuest: true }
  },
  
  // 用户端路由
  {
    path: '/',
    component: UserLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { 
          title: '仪表盘',
          breadcrumb: [
            { title: '首页', path: '/dashboard' }
          ]
        }
      },
      {
        path: 'subscription',
        name: 'Subscription',
        component: () => import('@/views/Subscription.vue'),
        meta: { 
          title: '订阅管理',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '订阅管理', path: '/subscription' }
          ]
        }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/Devices.vue'),
        meta: { 
          title: '设备管理',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '设备管理', path: '/devices' }
          ]
        }
      },
      {
        path: 'packages',
        name: 'Packages',
        component: () => import('@/views/Packages.vue'),
        meta: { 
          title: '套餐购买',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '套餐购买', path: '/packages' }
          ]
        }
      },
      {
        path: 'orders',
        name: 'Orders',
        component: () => import('@/views/Orders.vue'),
        meta: { 
          title: '订单记录',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '订单记录', path: '/orders' }
          ]
        }
      },
      {
        path: 'nodes',
        name: 'Nodes',
        component: () => import('@/views/Nodes.vue'),
        meta: { 
          title: '节点列表',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '节点列表', path: '/nodes' }
          ]
        }
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('@/views/Help.vue'),
        meta: { 
          title: '帮助中心',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '帮助中心', path: '/help' }
          ]
        }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { 
          title: '个人资料',
          breadcrumb: [
            { title: '首页', path: '/dashboard' },
            { title: '个人资料', path: '/profile' }
          ]
        }
      }
    ]
  },
  
  // 管理端路由
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { title: '管理仪表盘', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }] } },
      { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/Users.vue'), meta: { title: '用户管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '用户管理', path: '/admin/users' }] } },
      { path: 'subscriptions', name: 'AdminSubscriptions', component: () => import('@/views/admin/Subscriptions.vue'), meta: { title: '订阅管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '订阅管理', path: '/admin/subscriptions' }] } },
      { path: 'orders', name: 'AdminOrders', component: () => import('@/views/admin/Orders.vue'), meta: { title: '订单管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '订单管理', path: '/admin/orders' }] } },
      { path: 'packages', name: 'AdminPackages', component: () => import('@/views/admin/Packages.vue'), meta: { title: '套餐管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '套餐管理', path: '/admin/packages' }] } },
      { path: 'payment-config', name: 'AdminPaymentConfig', component: () => import('@/views/admin/PaymentConfig.vue'), meta: { title: '支付配置', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '支付配置', path: '/admin/payment-config' }] } },
      { path: 'settings', name: 'AdminSettings', component: () => import('@/views/admin/Settings.vue'), meta: { title: '系统设置', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '系统设置', path: '/admin/settings' }] } },
      { path: 'notifications', name: 'AdminNotifications', component: () => import('@/views/admin/Notifications.vue'), meta: { title: '通知管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '通知管理', path: '/admin/notifications' }] } },
      { path: 'config', name: 'AdminConfig', component: () => import('@/views/admin/Config.vue'), meta: { title: '配置管理', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '配置管理', path: '/admin/config' }] } },
      { path: 'statistics', name: 'AdminStatistics', component: () => import('@/views/admin/Statistics.vue'), meta: { title: '数据统计', breadcrumb: [{ title: '管理后台', path: '/admin/dashboard' }, { title: '数据统计', path: '/admin/statistics' }] } }
    ]
  },
  
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - XBoard`
  }
  
  // 需要认证的页面
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }
  
  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/dashboard')
    return
  }
  
  // 已登录用户不能访问登录/注册页面
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next('/dashboard')
    return
  }
  
  next()
})

export default router 