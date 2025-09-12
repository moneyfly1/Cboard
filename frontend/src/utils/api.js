import axios from 'axios'
import router from '@/router'

// 创建axios实例
export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// useApi函数 - 用于在Vue组件中获取API实例
export const useApi = () => {
  return api
}

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从localStorage获取token，避免循环导入
    const token = localStorage.getItem('token')
    console.log('=== 请求拦截器 ===')
    console.log('请求URL:', config.url)
    console.log('请求方法:', config.method)
    console.log('Token:', token)
    console.log('请求头:', config.headers)
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log('已添加Authorization头')
    } else {
      console.log('未找到token')
    }
    
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
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
      // 清除token并跳转到登录页
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      router.push('/login')
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
  getLoginHistory: () => api.get('/users/login-history'),
  getUserActivities: () => api.get('/users/activities'),
  getSubscriptionResets: () => api.get('/users/subscription-resets'),
  getUserInfo: () => api.get('/users/dashboard-info'),
  getAnnouncements: () => api.get('/announcements/'),
  getUserDevices: () => api.get('/users/devices'),
  sendVerificationEmail: () => api.post('/users/send-verification-email')
}

// 订阅相关API
export const subscriptionAPI = {
  getCurrentSubscription: () => api.get('/subscriptions/user-subscription'),
  getUserSubscription: () => api.get('/subscriptions/user-subscription'),
  resetSubscription: () => api.post('/subscriptions/reset-subscription'),
  sendSubscriptionEmail: () => api.post('/subscriptions/send-subscription-email'),
  sendSubscriptionToEmail: () => api.post('/subscriptions/send-subscription-email'),
  getDevices: () => api.get('/subscriptions/devices'),
  getUserDevices: () => api.get('/subscriptions/devices'),
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
  batchTestNodes: (nodeIds) => api.post('/nodes/batch-test', nodeIds),
  importFromClash: (clashConfig) => api.post('/nodes/import-from-clash', { clash_config: clashConfig }),
  getNodesStats: () => api.get('/admin/nodes/stats'),
  getSpeedMonitorStatus: () => api.get('/admin/node-speed-monitor/status')
}

// 管理端API
export const adminAPI = {
  // 管理端首页
  getDashboard: () => api.get('/admin/dashboard'),
  getStats: () => api.get('/admin/stats'),
  getUsers: (params) => {
    console.log('adminAPI.getUsers 被调用，参数:', params)
    return api.get('/admin/users', { params })
  },
  getUserStatistics: () => {
    console.log('adminAPI.getUserStatistics 被调用')
    return api.get('/admin/users/statistics')
  },
  getOrders: (params) => api.get('/admin/orders', { params }),
  
  // 用户管理
  createUser: (data) => api.post('/admin/users', data),
  getUser: (userId) => api.get(`/admin/users/${userId}`),
  updateUser: (userId, data) => api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  loginAsUser: (userId) => api.post(`/admin/users/${userId}/login-as`),
  getAbnormalUsers: () => api.get('/admin/users/abnormal'),
  getUserDetails: (userId) => api.get(`/admin/users/${userId}/details`),
  
  // 用户状态管理
  updateUserStatus: (userId, status) => api.put(`/admin/users/${userId}/status`, { status }),
  resetUserPassword: (userId, password) => api.post(`/admin/users/${userId}/reset-password`, { password }),
  
  // 用户批量操作
  batchDeleteUsers: (userIds) => api.post('/admin/users/batch-delete', { user_ids: userIds }),
  
  // 节点测速监控
  getNodeSpeedMonitorStatus: () => api.get('/admin/node-speed-monitor/status'),
  startNodeSpeedMonitor: () => api.post('/admin/node-speed-monitor/start'),
  stopNodeSpeedMonitor: () => api.post('/admin/node-speed-monitor/stop'),
  forceTestAllNodes: () => api.post('/admin/node-speed-monitor/force-test'),
  getNodesStats: () => api.get('/admin/nodes/stats'),
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
  resetUserSubscription: (userId) => api.post(`/admin/subscriptions/user/${userId}/reset-all`),
  sendSubscriptionEmail: (userId) => api.post(`/admin/subscriptions/user/${userId}/send-email`),
  batchClearDevices: () => api.post('/admin/subscriptions/batch-clear-devices'),
  exportSubscriptions: () => api.get('/admin/subscriptions/export'),
  getAppleStats: () => api.get('/admin/subscriptions/apple-stats'),
  getOnlineStats: () => api.get('/admin/subscriptions/online-stats'),
  clearUserDevices: (userId) => api.delete(`/admin/subscriptions/user/${userId}/delete-all`),
  
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
  resendEmail: (emailId) => api.post(`/admin/email-queue/${emailId}/resend`),
  getEmailDetail: (emailId) => api.get(`/admin/email-queue/${emailId}`),
  retryEmail: (emailId) => api.post(`/admin/email-queue/${emailId}/retry`),
  deleteEmailFromQueue: (emailId) => api.delete(`/admin/email-queue/${emailId}`),
  clearEmailQueue: (status) => api.post('/admin/email-queue/clear', { status }),
  getEmailQueueStatistics: () => api.get('/admin/email-queue/statistics'),
  
  // 个人资料管理
  getProfile: () => api.get('/admin/profile'),
  updateProfile: (data) => api.put('/admin/profile', data),
  changePassword: (data) => api.post('/admin/change-password', data),
  getLoginHistory: () => api.get('/admin/login-history'),
  getSecuritySettings: () => api.get('/admin/security-settings'),
  updateSecuritySettings: (data) => api.put('/admin/security-settings', data),
  getNotificationSettings: () => api.get('/admin/notification-settings'),
  updateNotificationSettings: (data) => api.put('/admin/notification-settings', data),
  
  // 系统日志管理
  getSystemLogs: (params) => api.get('/admin/system-logs', { params }),
  getLogsStats: () => api.get('/admin/logs-stats'),
  exportLogs: (params) => api.get('/admin/export-logs', { params }),
  clearLogs: () => api.post('/admin/clear-logs'),
  
  // 设备管理
  getUserDevices: (userId) => api.get(`/admin/users/${userId}/devices`),
  getSubscriptionDevices: (subscriptionId) => api.get(`/admin/subscriptions/${subscriptionId}/devices`),
  getDeviceDetail: (deviceId) => api.get(`/admin/devices/devices/${deviceId}`),
  updateDeviceStatus: (deviceId, data) => api.put(`/admin/devices/devices/${deviceId}`, data),
  removeDevice: (deviceId) => api.delete(`/admin/devices/${deviceId}`),
  deleteUserDevice: (userId, deviceId) => api.delete(`/admin/users/${userId}/devices/${deviceId}`),
  clearUserDevices: (userId) => api.post(`/admin/users/${userId}/clear-devices`)
}

// 通知相关API
export const notificationAPI = {
  // 用户通知
  getUserNotifications: (params) => api.get('/notifications/user-notifications', { params }),
  getUnreadCount: () => api.get('/notifications/unread-count'),
  markAsRead: (notificationId) => api.post(`/notifications/${notificationId}/read`),
  markAllAsRead: () => api.post('/notifications/mark-all-read'),
  
  // 管理端通知
  getNotifications: (params) => api.get('/announcements/admin/list', { params }),
  createNotification: (data) => api.post('/announcements/admin/publish', data),
  updateNotification: (notificationId, data) => api.put(`/announcements/admin/${notificationId}`, data),
  deleteNotification: (notificationId) => api.delete(`/announcements/admin/${notificationId}`),
  broadcastNotification: (data) => api.post('/announcements/admin/broadcast', data),
  
  // 邮件模板
  getEmailTemplates: () => api.get('/admin/email-templates'),
  createEmailTemplate: (data) => api.post('/admin/email-templates', data),
  updateEmailTemplate: (templateId, data) => api.put(`/admin/email-templates/${templateId}`, data),
  deleteEmailTemplate: (templateId) => api.delete(`/admin/email-templates/${templateId}`),
  previewEmailTemplate: (templateName, variables) => api.post(`/admin/email-templates/${templateName}/preview`, variables)
}

// 配置相关API
export const configAPI = {
  getConfigFiles: () => api.get('/config/admin/config-files'),
  getConfigFileContent: (fileName) => api.get(`/config/admin/config-files/${fileName}`),
  saveConfigFile: (fileName, content) => api.post(`/config/admin/config-files/${fileName}`, { content }),
  backupConfigFile: (fileName) => api.post(`/config/admin/config-files/${fileName}/backup`),
  restoreConfigFile: (fileName) => api.post(`/config/admin/config-files/${fileName}/restore`),
  getSystemConfig: () => api.get('/admin/system-config'),
  saveSystemConfig: (data) => api.post('/admin/system-config', data),
  getEmailConfig: () => api.get('/admin/email-config'),
  saveEmailConfig: (data) => api.post('/admin/email-config', data),
  testEmail: () => api.post('/admin/test-email'),
  testEmailToUser: (email) => api.post('/admin/test-email-to-user', { email }),
  getClashConfig: () => api.get('/admin/clash-config'),
  saveClashConfig: (content) => api.post('/admin/clash-config', { content }),
  getClashConfigInvalid: () => api.get('/admin/clash-config-invalid'),
  saveClashConfigInvalid: (content) => api.post('/admin/clash-config-invalid', { content }),
  getV2rayConfig: () => api.get('/admin/v2ray-config'),
  saveV2rayConfig: (content) => api.post('/admin/v2ray-config', { content }),
  getV2rayConfigInvalid: () => api.get('/admin/v2ray-config-invalid'),
  saveV2rayConfigInvalid: (content) => api.post('/admin/v2ray-config-invalid', { content }),
  exportConfig: () => api.get('/admin/export-config'),
  
  // 支付设置管理
  getPaymentSettings: () => api.get('/admin/payment-configs'),
  savePaymentSettings: (data) => api.put('/admin/payment-configs', data),
  testPaymentConfig: (data) => api.post('/admin/payment-configs/test', data)
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
  getPaymentMethods: () => api.get('/payment-methods/active'),
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
  getPaymentStats: () => api.get('/admin/payment-stats'),
  
  // 配置更新
  getConfigUpdateStatus: () => api.get('/admin/config-update/status'),
  startConfigUpdate: () => api.post('/admin/config-update/start'),
  stopConfigUpdate: () => api.post('/admin/config-update/stop'),
  testConfigUpdate: () => api.post('/admin/config-update/test'),
  getConfigUpdateLogs: (params) => api.get('/admin/config-update/logs', { params }),
  getConfigUpdateConfig: () => api.get('/admin/config-update/config'),
  updateConfigUpdateConfig: (data) => api.put('/admin/config-update/config', data),
  getConfigUpdateFiles: () => api.get('/admin/config-update/files'),
  getConfigUpdateSchedule: () => api.get('/admin/config-update/schedule'),
  updateConfigUpdateSchedule: (data) => api.put('/admin/config-update/schedule', data),
  startConfigUpdateSchedule: () => api.post('/admin/config-update/schedule/start'),
  stopConfigUpdateSchedule: () => api.post('/admin/config-update/schedule/stop'),
  clearConfigUpdateLogs: () => api.post('/admin/config-update/logs/clear'),
}

// 系统设置相关API
export const settingsAPI = {
  // 用户端设置API
  getPublicSettings: () => api.get('/settings/public-settings'),
  getAnnouncements: (params) => api.get('/settings/announcements', { params }),
  
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
  
  // 发布公告API
  publishAnnouncement: (data) => api.post('/announcements/admin/publish', data),
  getAdminAnnouncements: (page = 1, size = 20) => api.get(`/announcements/admin/list?page=${page}&size=${size}`),
  
  // 主题配置API
  getThemeConfigs: () => api.get('/admin/themes'),
  createThemeConfig: (data) => api.post('/admin/themes', data),
  updateThemeConfig: (themeId, data) => api.put(`/admin/themes/${themeId}`, data),
  deleteThemeConfig: (themeId) => api.delete(`/admin/themes/${themeId}`),
  
  // 邮件测试API
  testEmailSettings: (data) => api.post('/admin/test-email', data)
}

// 软件配置API (softwareConfigAPI) - NEW
export const softwareConfigAPI = {
  getSoftwareConfig: () => api.get('/software-config/'),
  updateSoftwareConfig: (data) => api.put('/software-config/', data)
}

// 配置更新API (configUpdateAPI) - NEW
export const configUpdateAPI = {
  // 状态管理
  getStatus: () => api.get('/admin/config-update/status'),
  startUpdate: () => api.post('/admin/config-update/start'),
  stopUpdate: () => api.post('/admin/config-update/stop'),
  testUpdate: () => api.post('/admin/config-update/test'),
  
  // 配置管理
  getConfig: () => api.get('/admin/config-update/config'),
  updateConfig: (data) => api.put('/admin/config-update/config', data),
  
  // 文件管理
  getFiles: () => api.get('/admin/config-update/files'),
  
  // 日志管理
  getLogs: (params) => api.get('/admin/config-update/logs', { params }),
  clearLogs: () => api.post('/admin/config-update/logs/clear'),
  
  
  // 节点源管理
  getNodeSources: () => api.get('/admin/config-update/node-sources'),
  updateNodeSources: (data) => api.put('/admin/config-update/node-sources', data),
  
  // 过滤关键词管理
  getFilterKeywords: () => api.get('/admin/config-update/filter-keywords'),
  updateFilterKeywords: (data) => api.put('/admin/config-update/filter-keywords', data)
}

export default api 