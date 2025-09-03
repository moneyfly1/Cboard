<template>
  <div class="dashboard-container">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="banner-content">
        <div class="welcome-text">
          <h1>欢迎回来，{{ userInfo.username }}！</h1>
          <p>管理您的订阅服务和设备</p>
        </div>
        <div class="banner-avatar">
          <el-avatar :size="80" :src="userInfo.avatar">
            {{ userInfo.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
        </div>
      </div>
    </div>

    <!-- 统计卡片区域 -->
    <div class="stats-grid">
      <div class="stat-card primary">
        <div class="stat-icon">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ subscriptionInfo.remainingDays }}</div>
          <div class="stat-label">剩余天数</div>
          <div class="stat-detail">到期时间：{{ subscriptionInfo.expiryDate }}</div>
        </div>
        <div class="stat-status" :class="{ 'expiring': subscriptionInfo.isExpiring }">
          <el-tag :type="subscriptionInfo.isExpiring ? 'warning' : 'success'" size="small">
            {{ subscriptionInfo.isExpiring ? '即将到期' : '正常' }}
          </el-tag>
        </div>
      </div>

      <div class="stat-card secondary">
        <div class="stat-icon">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ subscriptionInfo.currentDevices }}</div>
          <div class="stat-label">当前设备</div>
          <div class="stat-detail">上限：{{ subscriptionInfo.maxDevices }} 个</div>
        </div>
        <div class="stat-status" :class="{ 'limit-reached': subscriptionInfo.isDeviceLimitReached }">
          <el-tag :type="subscriptionInfo.isDeviceLimitReached ? 'danger' : 'info'" size="small">
            {{ subscriptionInfo.isDeviceLimitReached ? '已达上限' : '正常' }}
          </el-tag>
        </div>
      </div>

      <div class="stat-card success">
        <div class="stat-icon">
          <el-icon><Download /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ subscriptionInfo.trafficUsed || 0 }}</div>
          <div class="stat-label">已用流量</div>
          <div class="stat-detail">总流量：{{ subscriptionInfo.trafficLimit || '无限制' }} GB</div>
        </div>
        <div class="stat-status">
          <el-progress 
            :percentage="subscriptionInfo.trafficPercentage || 0" 
            :stroke-width="8"
            :show-text="false"
          />
        </div>
      </div>

      <div class="stat-card warning">
        <div class="stat-icon">
          <el-icon><Star /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ subscriptionInfo.packageName || '基础套餐' }}</div>
          <div class="stat-label">当前套餐</div>
          <div class="stat-detail">价格：¥{{ subscriptionInfo.packagePrice || '0.00' }}/月</div>
        </div>
        <div class="stat-status">
          <el-button type="primary" size="small" @click="$router.push('/packages')">
            升级套餐
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要功能区域 -->
    <div class="main-content">
      <!-- 订阅地址管理 -->
      <el-card class="feature-card subscription-card">
        <template #header>
          <div class="card-header">
            <el-icon><Link /></el-icon>
            <span>订阅地址管理</span>
          </div>
        </template>
        
        <div class="subscription-content">
          <!-- SSR订阅地址 -->
          <div class="subscription-item">
            <div class="subscription-label">
              <el-icon><Monitor /></el-icon>
              <span>SSR订阅地址</span>
            </div>
            <div class="subscription-input-group">
              <el-input 
                v-model="subscriptionInfo.ssrUrl" 
                readonly 
                placeholder="SSR订阅地址"
                size="large"
              >
                <template #prepend>
                  <el-icon><CopyDocument /></el-icon>
                </template>
                <template #append>
                  <el-button type="primary" @click="copyToClipboard(subscriptionInfo.ssrUrl)">
                    复制
                  </el-button>
                </template>
              </el-input>
              <div class="subscription-tip">
                <el-icon><InfoFilled /></el-icon>
                适配软件：Shadowrocket、V2Ray、Hiddify
              </div>
            </div>
          </div>

          <!-- Clash订阅地址 -->
          <div class="subscription-item">
            <div class="subscription-label">
              <el-icon><Grid /></el-icon>
              <span>Clash订阅地址</span>
            </div>
            <div class="subscription-input-group">
              <el-input 
                v-model="subscriptionInfo.clashUrl" 
                readonly 
                placeholder="Clash订阅地址"
                size="large"
              >
                <template #prepend>
                  <el-icon><CopyDocument /></el-icon>
                </template>
                <template #append>
                  <el-button type="primary" @click="copyToClipboard(subscriptionInfo.clashUrl)">
                    复制
                  </el-button>
                </template>
              </el-input>
              <div class="subscription-tip">
                <el-icon><InfoFilled /></el-icon>
                适配软件：电脑版Clash、安卓版Clash Meta、电脑版Mihomo Part
              </div>
            </div>
          </div>

          <!-- 快速导入按钮 -->
          <div class="quick-import-section">
            <h4>快速导入</h4>
            <div class="import-buttons">
              <el-button type="primary" size="large" @click="importToClash">
                <el-icon><Download /></el-icon>
                小猫咪软件一键导入
              </el-button>
              <el-button type="success" size="large" @click="importToShadowrocket">
                <el-icon><Download /></el-icon>
                小火箭一键导入
              </el-button>
            </div>
            <div class="import-tip">
              <el-icon><Lightbulb /></el-icon>
              此步骤省略复制订阅地址到软件下载配置的步骤，方便快捷
            </div>
          </div>

          <!-- 二维码 -->
          <div class="qrcode-section" v-if="subscriptionInfo.qrcodeUrl">
            <h4>订阅二维码</h4>
            <div class="qrcode-container">
              <div id="qrcode"></div>
              <p>扫描二维码快速导入</p>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 设备管理 -->
      <el-card class="feature-card device-card">
        <template #header>
          <div class="card-header">
            <el-icon><Connection /></el-icon>
            <span>设备管理</span>
            <el-button type="primary" size="small" @click="refreshDevices">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>
        
        <div class="device-content">
          <div class="device-stats">
            <div class="device-stat">
              <span class="stat-label">在线设备</span>
              <span class="stat-value">{{ deviceStats.onlineCount }}</span>
            </div>
            <div class="device-stat">
              <span class="stat-label">总设备数</span>
              <span class="stat-value">{{ deviceStats.totalCount }}</span>
            </div>
            <div class="device-stat">
              <span class="stat-label">设备上限</span>
              <span class="stat-value">{{ deviceStats.limit }}</span>
            </div>
          </div>

          <div class="device-list" v-if="devices.length > 0">
            <div class="device-item" v-for="device in devices" :key="device.id">
              <div class="device-info">
                <el-icon class="device-icon"><Monitor /></el-icon>
                <div class="device-details">
                  <div class="device-name">{{ device.name || '未知设备' }}</div>
                  <div class="device-meta">
                    {{ device.device_type }} • {{ device.ip_address }}
                  </div>
                </div>
              </div>
              <div class="device-actions">
                <el-tag :type="device.is_online ? 'success' : 'info'" size="small">
                  {{ device.is_online ? '在线' : '离线' }}
                </el-tag>
                <el-button 
                  type="danger" 
                  size="small" 
                  @click="removeDevice(device.id)"
                  :disabled="!device.is_online"
                >
                  移除
                </el-button>
              </div>
            </div>
          </div>

          <div class="no-devices" v-else>
            <el-empty description="暂无设备连接" />
          </div>

          <div class="device-actions-footer">
            <el-button type="warning" @click="showResetConfirm">
              <el-icon><Refresh /></el-icon>
              重置订阅地址
            </el-button>
            <el-button type="info" @click="sendSubscriptionEmail">
              <el-icon><Message /></el-icon>
              发送到邮箱
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 快速配置 -->
      <el-card class="feature-card config-card">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>快速配置</span>
          </div>
        </template>
        
        <div class="config-content">
          <el-form :model="quickConfig" label-width="100px">
            <el-form-item label="选择平台">
              <el-select v-model="quickConfig.platform" @change="updateClientDownloads">
                <el-option label="Windows" value="windows" />
                <el-option label="Android" value="android" />
                <el-option label="Mac" value="mac" />
                <el-option label="iOS" value="ios" />
              </el-select>
            </el-form-item>
          </el-form>

          <div class="client-downloads">
            <h4>推荐客户端</h4>
            <div class="client-grid">
              <div v-for="client in currentClients" :key="client.id" class="client-card">
                <div class="client-icon">
                  <el-icon><Monitor /></el-icon>
                </div>
                <div class="client-info">
                  <div class="client-name">{{ client.name }}</div>
                  <div class="client-desc">{{ client.description }}</div>
                </div>
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="downloadClient(client.downloadUrl)"
                >
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 网站公告 -->
      <el-card class="feature-card announcement-card">
        <template #header>
          <div class="card-header">
            <el-icon><Bell /></el-icon>
            <span>网站公告</span>
          </div>
        </template>
        
        <div class="announcement-content">
          <div class="announcement-text">
            <el-alert
              title="重要提醒"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                请遵守节点当地和您所在国家的法律法规，禁止用作违规行为，不要发表不该说的言论，不要认为换了IP就找不到你，出问题后果自负，请谨言慎行才是生存之道！
              </template>
            </el-alert>
          </div>
          
          <div class="renewal-section">
            <el-alert
              title="续费提醒"
              type="info"
              :closable="false"
              show-icon
            >
              <template #default>
                如需续费或升级套餐，请点击下方按钮
              </template>
            </el-alert>
            <div class="renewal-actions">
              <el-button type="primary" size="large" @click="$router.push('/packages')">
                <el-icon><ShoppingCart /></el-icon>
                查看套餐
              </el-button>
              <el-button type="success" size="large" @click="$router.push('/orders')">
                <el-icon><Document /></el-icon>
                我的订单
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 重置确认对话框 -->
    <el-dialog
      v-model="resetDialogVisible"
      title="确认重置订阅地址"
      width="400px"
      center
    >
      <div class="reset-confirm-content">
        <el-icon class="warning-icon"><Warning /></el-icon>
        <p>此操作不可逆，旧的订阅链接将立即失效。确定要继续吗？</p>
      </div>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmReset">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Clock, Connection, Download, Star, Link, Monitor, Grid, 
  CopyDocument, InfoFilled, Lightbulb, Refresh, Message, 
  Setting, Bell, Warning, ShoppingCart, Document
} from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import { useAuthStore } from '@/store/auth'
import { subscriptionAPI } from '@/utils/api'

export default {
  name: 'Dashboard',
  components: {
    Clock, Connection, Download, Star, Link, Monitor, Grid, 
    CopyDocument, InfoFilled, Lightbulb, Refresh, Message, 
    Setting, Bell, Warning, ShoppingCart, Document
  },
  setup() {
    const authStore = useAuthStore()
    const resetDialogVisible = ref(false)
    
    const userInfo = computed(() => authStore.user || {})
    
    const subscriptionInfo = reactive({
      remainingDays: 0,
      expiryDate: '',
      isExpiring: false,
      currentDevices: 0,
      maxDevices: 0,
      isDeviceLimitReached: false,
      ssrUrl: '',
      clashUrl: '',
      qrcodeUrl: '',
      trafficUsed: 0,
      trafficLimit: null,
      trafficPercentage: 0,
      packageName: '',
      packagePrice: ''
    })

    const deviceStats = reactive({
      onlineCount: 0,
      totalCount: 0,
      limit: 0
    })

    const devices = ref([])

    const quickConfig = reactive({
      platform: 'windows'
    })

    const clientDownloads = {
      windows: [
        { 
          id: 1, 
          name: 'Clash for Windows', 
          description: 'Windows平台最佳代理客户端',
          downloadUrl: 'https://github.com/Fndroid/clash_for_windows_pkg/releases' 
        },
        { 
          id: 2, 
          name: 'V2RayN', 
          description: '轻量级V2Ray客户端',
          downloadUrl: 'https://github.com/2dust/v2rayN/releases' 
        }
      ],
      android: [
        { 
          id: 3, 
          name: 'Clash Meta for Android', 
          description: 'Android平台最佳选择',
          downloadUrl: 'https://github.com/MetaCubeX/ClashMetaForAndroid/releases' 
        },
        { 
          id: 4, 
          name: 'V2RayNG', 
          description: '轻量级V2Ray客户端',
          downloadUrl: 'https://github.com/2dust/v2rayNG/releases' 
        }
      ],
      mac: [
        { 
          id: 5, 
          name: 'ClashX Pro', 
          description: 'macOS平台最佳选择',
          downloadUrl: 'https://clashx.pro/' 
        },
        { 
          id: 6, 
          name: 'V2RayX', 
          description: '轻量级V2Ray客户端',
          downloadUrl: 'https://github.com/Cenmrev/V2RayX/releases' 
        }
      ],
      ios: [
        { 
          id: 7, 
          name: 'Shadowrocket', 
          description: 'iOS平台最佳选择',
          downloadUrl: 'https://apps.apple.com/app/shadowrocket/id932747118' 
        },
        { 
          id: 8, 
          name: 'Quantumult X', 
          description: '功能强大的iOS客户端',
          downloadUrl: 'https://apps.apple.com/app/quantumult-x/id1443988620' 
        }
      ]
    }

    const currentClients = computed(() => {
      return clientDownloads[quickConfig.platform] || []
    })

    // 获取订阅信息
    const fetchSubscriptionInfo = async () => {
      try {
        const response = await subscriptionAPI.getUserSubscription()
        const data = response.data
        
        subscriptionInfo.remainingDays = data.remaining_days || 0
        subscriptionInfo.expiryDate = data.expiry_date || ''
        subscriptionInfo.isExpiring = (data.remaining_days || 0) <= 7
        subscriptionInfo.currentDevices = data.current_devices || 0
        subscriptionInfo.maxDevices = data.max_devices || 0
        subscriptionInfo.isDeviceLimitReached = (data.current_devices || 0) >= (data.max_devices || 0)
        subscriptionInfo.ssrUrl = data.ssr_url || ''
        subscriptionInfo.clashUrl = data.clash_url || ''
        subscriptionInfo.qrcodeUrl = data.qrcode_url || ''
        subscriptionInfo.trafficUsed = data.traffic_used_gb || 0
        subscriptionInfo.trafficLimit = data.traffic_limit_gb
        subscriptionInfo.packageName = data.package_name || '基础套餐'
        subscriptionInfo.packagePrice = data.package_price || '0.00'
        
        // 计算流量百分比
        if (data.traffic_limit_gb && data.traffic_used_gb) {
          subscriptionInfo.trafficPercentage = Math.round((data.traffic_used_gb / data.traffic_limit_gb) * 100)
        }
        
        // 生成二维码
        if (data.qrcode_url) {
          generateQRCode(data.qrcode_url)
        }
      } catch (error) {
        ElMessage.error('获取订阅信息失败')
      }
    }

    // 获取设备信息
    const fetchDevices = async () => {
      try {
        const response = await subscriptionAPI.getDevices()
        devices.value = response.data || []
        
        // 更新设备统计
        deviceStats.onlineCount = devices.value.filter(d => d.is_online).length
        deviceStats.totalCount = devices.value.length
        deviceStats.limit = subscriptionInfo.maxDevices
      } catch (error) {
        ElMessage.error('获取设备信息失败')
      }
    }

    // 生成二维码
    const generateQRCode = async (url) => {
      try {
        const qrcodeElement = document.getElementById('qrcode')
        if (qrcodeElement) {
          await QRCode.toCanvas(qrcodeElement, url, {
            width: 200,
            margin: 2
          })
        }
      } catch (error) {
        console.error('生成二维码失败:', error)
      }
    }

    // 复制到剪贴板
    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('复制成功')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }

    // 发送订阅邮件
    const sendSubscriptionEmail = async () => {
      try {
        await subscriptionAPI.sendSubscriptionEmail()
        ElMessage.success('订阅地址已发送到您的邮箱，请注意查收')
      } catch (error) {
        ElMessage.error('发送失败')
      }
    }

    // 显示重置确认对话框
    const showResetConfirm = () => {
      resetDialogVisible.value = true
    }

    // 确认重置
    const confirmReset = async () => {
      try {
        await subscriptionAPI.resetSubscription()
        ElMessage.success('订阅地址重置成功')
        resetDialogVisible.value = false
        // 重新获取订阅信息
        await fetchSubscriptionInfo()
        await fetchDevices()
      } catch (error) {
        ElMessage.error('重置失败')
      }
    }

    // 导入到Clash
    const importToClash = () => {
      const clashUrl = encodeURIComponent(subscriptionInfo.clashUrl)
      const name = encodeURIComponent(subscriptionInfo.expiryDate)
      const importUrl = `clash://install-config?url=${clashUrl}&name=${name}_到期`
      window.open(importUrl)
    }

    // 导入到Shadowrocket
    const importToShadowrocket = () => {
      const ssrUrl = encodeURIComponent(subscriptionInfo.ssrUrl)
      const name = encodeURIComponent(subscriptionInfo.expiryDate)
      const importUrl = `shadowrocket://add/sub://${ssrUrl}#${name}`
      window.open(importUrl)
    }

    // 下载客户端
    const downloadClient = (url) => {
      window.open(url, '_blank')
    }

    // 更新客户端下载列表
    const updateClientDownloads = () => {
      // 这里可以根据平台更新下载列表
    }

    // 刷新设备
    const refreshDevices = () => {
      fetchDevices()
    }

    // 移除设备
    const removeDevice = async (deviceId) => {
      try {
        await subscriptionAPI.removeDevice(deviceId)
        ElMessage.success('设备移除成功')
        await fetchDevices()
      } catch (error) {
        ElMessage.error('移除设备失败')
      }
    }

    onMounted(() => {
      fetchSubscriptionInfo()
      fetchDevices()
    })

    return {
      userInfo,
      subscriptionInfo,
      deviceStats,
      devices,
      quickConfig,
      currentClients,
      resetDialogVisible,
      copyToClipboard,
      sendSubscriptionEmail,
      showResetConfirm,
      confirmReset,
      importToClash,
      importToShadowrocket,
      downloadClient,
      updateClientDownloads,
      refreshDevices,
      removeDevice
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
}

/* 欢迎横幅 */
.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text h1 {
  margin: 0 0 8px 0;
  font-size: 2.5rem;
  font-weight: 700;
}

.welcome-text p {
  margin: 0;
  font-size: 1.1rem;
  opacity: 0.9;
}

.banner-avatar {
  display: flex;
  align-items: center;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.stat-card.primary {
  border-left: 4px solid #409eff;
}

.stat-card.secondary {
  border-left: 4px solid #67c23a;
}

.stat-card.success {
  border-left: 4px solid #52c41a;
}

.stat-card.warning {
  border-left: 4px solid #faad14;
}

.stat-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.primary {
  background: linear-gradient(135deg, #409eff, #36a3f7);
}

.stat-icon.secondary {
  background: linear-gradient(135deg, #67c23a, #5daf32);
}

.stat-icon.success {
  background: linear-gradient(135deg, #52c41a, #389e0d);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #faad14, #d48806);
}

.stat-content {
  margin-right: 60px;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 1.1rem;
  color: #606266;
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-detail {
  font-size: 0.9rem;
  color: #909399;
  line-height: 1.4;
}

.stat-status {
  position: absolute;
  bottom: 20px;
  right: 20px;
}

/* 主要内容区域 */
.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.feature-card {
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #303133;
}

.card-header .el-icon {
  color: #409eff;
}

/* 订阅地址区域 */
.subscription-content {
  padding: 0;
}

.subscription-item {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.subscription-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.subscription-label .el-icon {
  color: #409eff;
}

.subscription-input-group {
  margin-bottom: 16px;
}

.subscription-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #606266;
  padding: 12px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 3px solid #1976d2;
  margin-top: 12px;
}

.quick-import-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e9ecef;
}

.quick-import-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 1.1rem;
}

.import-buttons {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.import-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  color: #606266;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 3px solid #0ea5e9;
}

.qrcode-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e9ecef;
  text-align: center;
}

.qrcode-section h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.qrcode-container {
  display: inline-block;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.qrcode-container p {
  margin: 16px 0 0 0;
  color: #606266;
  font-size: 0.9rem;
}

/* 设备管理区域 */
.device-content {
  padding: 0;
}

.device-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 24px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.device-stat {
  text-align: center;
}

.device-stat .stat-label {
  display: block;
  font-size: 0.9rem;
  color: #606266;
  margin-bottom: 8px;
}

.device-stat .stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #303133;
}

.device-list {
  margin-bottom: 24px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 12px;
  border: 1px solid #e9ecef;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.device-details .device-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.device-details .device-meta {
  font-size: 0.9rem;
  color: #606266;
}

.device-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.no-devices {
  text-align: center;
  padding: 40px 20px;
}

.device-actions-footer {
  display: flex;
  gap: 16px;
  justify-content: center;
}

/* 快速配置区域 */
.config-content {
  padding: 0;
}

.client-downloads h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 1.1rem;
}

.client-grid {
  display: grid;
  gap: 16px;
}

.client-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.client-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.client-info {
  flex: 1;
}

.client-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.client-desc {
  font-size: 0.9rem;
  color: #606266;
}

/* 公告区域 */
.announcement-content {
  padding: 0;
}

.announcement-text {
  margin-bottom: 24px;
}

.renewal-section {
  padding-top: 24px;
  border-top: 1px solid #e9ecef;
}

.renewal-actions {
  display: flex;
  gap: 16px;
  margin-top: 16px;
  justify-content: center;
}

/* 重置确认对话框 */
.reset-confirm-content {
  text-align: center;
  padding: 20px 0;
}

.warning-icon {
  font-size: 48px;
  color: #faad14;
  margin-bottom: 16px;
}

.reset-confirm-content p {
  margin: 0;
  line-height: 1.6;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 16px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .welcome-text h1 {
    font-size: 2rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .banner-content {
    flex-direction: column;
    text-align: center;
    gap: 20px;
  }
  
  .import-buttons {
    flex-direction: column;
  }
  
  .device-stats {
    flex-direction: column;
    gap: 16px;
  }
  
  .device-actions-footer {
    flex-direction: column;
  }
  
  .renewal-actions {
    flex-direction: column;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card,
.feature-card {
  animation: fadeInUp 0.6s ease-out;
}

.stat-card:nth-child(2) {
  animation-delay: 0.1s;
}

.stat-card:nth-child(3) {
  animation-delay: 0.2s;
}

.stat-card:nth-child(4) {
  animation-delay: 0.3s;
}

.feature-card:nth-child(2) {
  animation-delay: 0.4s;
}

.feature-card:nth-child(3) {
  animation-delay: 0.5s;
}

.feature-card:nth-child(4) {
  animation-delay: 0.6s;
}
</style>
