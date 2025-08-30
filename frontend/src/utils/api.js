import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  async error => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      
      // 尝试刷新token
      try {
        await authStore.refreshToken()
        // 重新发送原请求
        const originalRequest = error.config
        originalRequest.headers.Authorization = `Bearer ${authStore.token}`
        return api(originalRequest)
      } catch (refreshError) {
        // 刷新失败，跳转到登录页
        authStore.logout()
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

// 认证相关API
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  verifyEmail: (token) => api.post('/auth/verify-email', { token }),
  resendVerificationEmail: (data) => api.post('/auth/resend-verification', data),
  refreshToken: () => api.post('/auth/refresh-token')
}

// 用户相关API
export const userAPI = {
  getProfile: () => api.get('/users/profile'),
  updateProfile: (data) => api.put('/users/profile', data),
  changePassword: (data) => api.post('/users/change-password', data),
  getLoginHistory: () => api.get('/users/login-history')
}

// 订阅相关API
export const subscriptionAPI = {
  getCurrentSubscription: () => api.get('/subscriptions/current'),
  resetSubscription: () => api.post('/subscriptions/reset'),
  sendSubscriptionEmail: () => api.post('/subscriptions/send-email'),
  getDevices: () => api.get('/subscriptions/devices'),
  removeDevice: (deviceId) => api.delete(`/subscriptions/devices/${deviceId}`),
  getSSRSubscription: (key) => api.get(`/subscriptions/ssr/${key}`),
  getClashSubscription: (key) => api.get(`/subscriptions/clash/${key}`)
}

// 套餐相关API
export const packageAPI = {
  getPackages: (params) => api.get('/packages/', { params }),
  getPackage: (packageId) => api.get(`/packages/${packageId}`),
  createPackage: (data) => api.post('/packages/', data),
  updatePackage: (packageId, data) => api.put(`/packages/${packageId}`, data),
  deletePackage: (packageId) => api.delete(`/packages/${packageId}`)
}

// 订单相关API
export const orderAPI = {
  createOrder: (data) => api.post('/orders/', data),
  getUserOrders: (params) => api.get('/orders/user-orders', { params }),
  getOrderStatus: (orderNo) => api.get(`/orders/${orderNo}/status`),
  cancelOrder: (orderNo) => api.post(`/orders/${orderNo}/cancel`),
  getCurrentSubscription: () => api.get('/subscriptions/current'),
  getPackages: () => api.get('/packages/')
}

// 节点相关API
export const nodeAPI = {
  getNodes: () => api.get('/nodes/'),
  getNode: (nodeId) => api.get(`/nodes/${nodeId}`),
  testNode: (nodeId) => api.post(`/nodes/${nodeId}/test`),
  getNodesStats: () => api.get('/nodes/stats/overview')
}

// 管理端API
export const adminAPI = {
  // 管理端首页
  getDashboard: () => api.get('/admin/dashboard'),
  getStats: () => api.get('/admin/stats'),
  getUsers: (params) => api.get('/admin/users', { params }),
  getOrders: (params) => api.get('/admin/orders', { params }),
  
  // 用户管理
  createUser: (data) => api.post('/admin/users', data),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  loginAsUser: (userId) => api.post(`/admin/users/${userId}/login-as`),
  
  // 用户批量操作
  batchDeleteUsers: (userIds) => api.post('/admin/users/batch-delete', { user_ids: userIds }),
  batchEnableUsers: (userIds) => api.post('/admin/users/batch-enable', { user_ids: userIds }),
  batchDisableUsers: (userIds) => api.post('/admin/users/batch-disable', { user_ids: userIds }),
  batchVerifyUsers: (userIds) => api.post('/admin/users/batch-verify', { user_ids: userIds }),
  
  // 用户邮件操作
  sendSubscriptionEmail: (userId) => api.post(`/admin/users/${userId}/send-subscription-email`),
  batchSendSubscriptionEmail: (userIds) => api.post('/admin/users/batch-send-subscription-email', { user_ids: userIds }),
  
  // 即将过期用户
  getExpiringUsers: (params) => api.get('/admin/users/expiring', { params }),
  batchSendExpireReminder: (userIds) => api.post('/admin/users/batch-expire-reminder', { user_ids: userIds }),
  
  // 订阅管理
  getSubscriptions: (params) => api.get('/admin/subscriptions', { params }),
  createSubscription: (data) => api.post('/admin/subscriptions', data),
  updateSubscription: (subscriptionId, data) => api.put(`/admin/subscriptions/${subscriptionId}`, data),
  resetSubscription: (subscriptionId) => api.post(`/admin/subscriptions/${subscriptionId}/reset`),
  extendSubscription: (subscriptionId, days) => api.post(`/admin/subscriptions/${subscriptionId}/extend`, { days }),
  
  // 订阅批量操作
  batchDeleteSubscriptions: (subscriptionIds) => api.post('/admin/subscriptions/batch-delete', { subscription_ids: subscriptionIds }),
  batchEnableSubscriptions: (subscriptionIds) => api.post('/admin/subscriptions/batch-enable', { subscription_ids: subscriptionIds }),
  batchDisableSubscriptions: (subscriptionIds) => api.post('/admin/subscriptions/batch-disable', { subscription_ids: subscriptionIds }),
  batchResetSubscriptions: (subscriptionIds) => api.post('/admin/subscriptions/batch-reset', { subscription_ids: subscriptionIds }),
  batchSendSubscriptionEmail: (subscriptionIds) => api.post('/admin/subscriptions/batch-send-email', { subscription_ids: subscriptionIds }),
  
  // 订单管理
  updateOrder: (orderId, data) => api.put(`/admin/orders/${orderId}`, data),
  
  // 套餐管理
  getPackages: () => api.get('/admin/packages'),
  createPackage: (data) => api.post('/admin/packages', data),
  updatePackage: (packageId, data) => api.put(`/admin/packages/${packageId}`, data),
  deletePackage: (packageId) => api.delete(`/admin/packages/${packageId}`),
  
  // 邮件队列管理
  getEmailQueue: (params) => api.get('/admin/email-queue', { params }),
  resendEmail: (emailId) => api.post(`/admin/email-queue/${emailId}/resend`)
}

// 通知相关API
export const notificationAPI = {
  // 用户通知
  getUserNotifications: (params) => api.get('/notifications/user-notifications', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (notificationId) => api.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/notifications/mark-all-read'),
  
  // 管理端通知
  getNotifications: (params) => api.get('/admin/notifications', { params }),
  createNotification: (data) => api.post('/admin/notifications', data),
  updateNotification: (notificationId, data) => api.put(`/admin/notifications/${notificationId}`, data),
  deleteNotification: (notificationId) => api.delete(`/admin/notifications/${notificationId}`),
  broadcastNotification: (data) => api.post('/admin/notifications/broadcast', data),
  
  // 邮件模板
  getEmailTemplates: () => api.get('/admin/email-templates'),
  createEmailTemplate: (data) => api.post('/admin/email-templates', data),
  updateEmailTemplate: (templateId, data) => api.put(`/admin/email-templates/${templateId}`, data),
  deleteEmailTemplate: (templateId) => api.delete(`/admin/email-templates/${templateId}`),
  previewEmailTemplate: (templateName, variables) => api.post(`/admin/email-templates/${templateName}/preview`, variables)
}

// 配置相关API
export const configAPI = {
  getConfigFiles: () => api.get('/admin/config-files'),
  getConfigFileContent: (fileName) => api.get(`/admin/config-files/${fileName}`),
  saveConfigFile: (fileName, content) => api.post(`/admin/config-files/${fileName}`, { content }),
  backupConfigFile: (fileName) => api.post(`/admin/config-files/${fileName}/backup`),
  restoreConfigFile: (fileName) => api.post(`/admin/config-files/${fileName}/restore`),
  getSystemConfig: () => api.get('/admin/system-config'),
  saveSystemConfig: (data) => api.post('/admin/system-config', data),
  getEmailConfig: () => api.get('/admin/email-config'),
  saveEmailConfig: (data) => api.post('/admin/email-config', data),
  testEmail: () => api.post('/admin/test-email'),
  getClashConfig: () => api.get('/admin/clash-config'),
  saveClashConfig: (content) => api.post('/admin/clash-config', { content }),
  getV2rayConfig: () => api.get('/admin/v2ray-config'),
  saveV2rayConfig: (content) => api.post('/admin/v2ray-config', { content }),
  exportConfig: () => api.get('/admin/export-config')
}

// 统计相关API
export const statisticsAPI = {
  getStatistics: () => api.get('/admin/statistics'),
  getUserTrend: () => api.get('/admin/statistics/user-trend'),
  getRevenueTrend: () => api.get('/admin/statistics/revenue-trend'),
  getUserStatistics: (params) => api.get('/admin/statistics/users', { params }),
  getSubscriptionStatistics: () => api.get('/admin/statistics/subscriptions'),
  getOrderStatistics: (params) => api.get('/admin/statistics/orders', { params }),
  getStatisticsOverview: () => api.get('/admin/statistics/overview'),
  exportStatistics: (type, format) => api.get('/admin/statistics/export', { params: { type, format } })
}

// 支付相关API
export const paymentAPI = {
  // 用户端支付API
  getPaymentMethods: () => api.get('/payment-methods'),
  createPayment: (data) => api.post('/create-payment', data),
  getPaymentStatus: (transactionId) => api.get(`/payment-status/${transactionId}`),
  
  // 管理端支付API
  getPaymentConfigs: (params) => api.get('/admin/payment-configs', { params }),
  createPaymentConfig: (data) => api.post('/admin/payment-configs', data),
  updatePaymentConfig: (configId, data) => api.put(`/admin/payment-configs/${configId}`, data),
  deletePaymentConfig: (configId) => api.delete(`/admin/payment-configs/${configId}`),
  
  // 支付交易管理
  getPaymentTransactions: (params) => api.get('/admin/payment-transactions', { params }),
  getPaymentTransactionDetail: (transactionId) => api.get(`/admin/payment-transactions/${transactionId}`),
  
  // 支付统计
  getPaymentStats: () => api.get('/admin/payment-stats')
}

// 系统设置相关API
export const settingsAPI = {
  // 用户端设置API
  getPublicSettings: () => api.get('/public-settings'),
  getAnnouncements: (params) => api.get('/announcements', { params }),
  
  // 管理端设置API
  getSystemSettings: () => api.get('/admin/settings'),
  updateSystemSettings: (data) => api.put('/admin/settings', data),
  getConfigsByCategory: (params) => api.get('/admin/configs', { params }),
  createConfig: (data) => api.post('/admin/configs', data),
  updateConfig: (configKey, data) => api.put(`/admin/configs/${configKey}`, data),
  deleteConfig: (configKey) => api.delete(`/admin/configs/${configKey}`),
  initializeConfigs: () => api.post('/admin/configs/initialize'),
  
  // 公告管理API
  getAnnouncementsAdmin: (params) => api.get('/admin/announcements', { params }),
  getAnnouncementDetail: (announcementId) => api.get(`/admin/announcements/${announcementId}`),
  createAnnouncement: (data) => api.post('/admin/announcements', data),
  updateAnnouncement: (announcementId, data) => api.put(`/admin/announcements/${announcementId}`, data),
  deleteAnnouncement: (announcementId) => api.delete(`/admin/announcements/${announcementId}`),
  toggleAnnouncementStatus: (announcementId) => api.post(`/admin/announcements/${announcementId}/toggle-status`),
  toggleAnnouncementPin: (announcementId) => api.post(`/admin/announcements/${announcementId}/toggle-pin`),
  
  // 主题配置API
  getThemeConfigs: () => api.get('/admin/themes'),
  createThemeConfig: (data) => api.post('/admin/themes', data),
  updateThemeConfig: (themeId, data) => api.put(`/admin/themes/${themeId}`, data),
  deleteThemeConfig: (themeId) => api.delete(`/admin/themes/${themeId}`),
  
  // 邮件测试API
  testEmailSettings: (data) => api.post('/admin/test-email', data)
}

export default api 