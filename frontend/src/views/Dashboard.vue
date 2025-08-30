<template>
  <div class="dashboard-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>订阅管理</h1>
      <p>管理您的订阅服务和设备</p>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-card">
      <div class="stats-content">
        <h3>剩余时长</h3>
        <div class="stats-number">{{ subscriptionInfo.remainingDays }} 天</div>
        <div class="expiry-date">
          到期时间：<span>{{ subscriptionInfo.expiryDate }}</span>
        </div>
        <div class="expiry-warning" v-if="subscriptionInfo.isExpiring">
          <i class="el-icon-warning"></i> 订阅即将到期，请及时续费
        </div>
        <div class="device-stats">
          当前设备数：<span class="current-devices">{{ subscriptionInfo.currentDevices }}</span> / 
          <span class="max-devices">{{ subscriptionInfo.maxDevices }}</span> 个
          <span class="device-hint">（当前/最大）</span>
        </div>
        <div class="device-warning" v-if="subscriptionInfo.isDeviceLimitReached">
          <i class="el-icon-warning"></i> 设备数量已达上限，建议重置订阅地址
        </div>
      </div>
    </div>

    <!-- 网站公告 -->
    <el-card class="announcement-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-bell"></i>
          网站公告
        </div>
      </template>
      <div class="announcement-content">
        <strong>请遵守节点当地和您所在国家的法律法规，禁止用作违规行为，不要发表不该说的言论，不要认为换了IP就找不到你，出问题后果自负，请谨言慎行才是生存之道！</strong>
        
        <div class="device-management-tip" v-if="subscriptionInfo.isDeviceLimitReached">
          <strong>📱 设备管理提示：</strong>
          <p>当您的设备数量达到上限时，可以点击下方"一键重置订阅地址"按钮来清除所有在线设备记录，然后使用新的订阅地址重新配置您的设备。</p>
        </div>
        
        <div class="action-buttons">
          <el-button type="primary" @click="showResetConfirm">
            <i class="el-icon-refresh"></i>
            一键重置订阅地址
          </el-button>
          <el-button type="primary" @click="sendSubscriptionEmail">
            <i class="el-icon-message"></i>
            发送订阅地址到QQ邮箱
          </el-button>
        </div>
        
        <div class="warning-text">请注意，点击重置订阅之后，你之前所有的链接都会失效。</div>
        
        <div class="renewal-section">
          <strong style="color: red;">续费请点击下方按钮</strong>
          <hr>
          <el-button type="primary" @click="$router.push('/packages')">
            续费请点击我
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 订阅地址 -->
    <el-card class="subscription-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-link"></i>
          订阅地址
        </div>
      </template>
      
      <!-- SSR订阅地址 -->
      <div class="subscription-item">
        <div class="subscription-input">
          <el-input 
            v-model="subscriptionInfo.ssrUrl" 
            readonly 
            placeholder="SSR订阅地址"
          >
            <template #append>
              <el-button @click="copyToClipboard(subscriptionInfo.ssrUrl)">
                复制
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="subscription-tip ssr-tip">
          <i class="el-icon-info"></i>
          适配软件：Shadowrocket、V2Ray、Hiddify
        </div>
      </div>

      <!-- Clash订阅地址 -->
      <div class="subscription-item">
        <div class="subscription-input">
          <el-input 
            v-model="subscriptionInfo.clashUrl" 
            readonly 
            placeholder="Clash订阅地址"
          >
            <template #append>
              <el-button @click="copyToClipboard(subscriptionInfo.clashUrl)">
                复制
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="subscription-tip clash-tip">
          <i class="el-icon-info"></i>
          适配软件：电脑版Clash、安卓版Clash Meta、电脑版Mihomo Part
        </div>
      </div>

      <!-- 快速导入按钮 -->
      <div class="quick-import">
        <el-button type="primary" @click="importToClash">
          <i class="el-icon-download"></i>
          小猫咪软件一键导入
        </el-button>
        <div class="import-tip">此步骤省略复制订阅地址到小猫咪软件下载配置的步骤，方便快捷</div>
        
        <el-button type="primary" @click="importToShadowrocket">
          <i class="el-icon-download"></i>
          小火箭一键导入
        </el-button>
      </div>

      <!-- 二维码 -->
      <div class="qrcode-section">
        <div id="qrcode"></div>
      </div>
    </el-card>

    <!-- 快速配置 -->
    <el-card class="quick-config-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-download"></i>
          快速配置
        </div>
      </template>
      
      <el-form :model="quickConfig" label-width="100px">
        <el-form-item label="选择平台">
          <el-select v-model="quickConfig.platform" @change="updateClientDownloads">
            <el-option label="Windows" value="windows"></el-option>
            <el-option label="Android" value="android"></el-option>
            <el-option label="Mac" value="mac"></el-option>
            <el-option label="iOS" value="ios"></el-option>
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 客户端下载区域 -->
      <div class="client-downloads">
        <div v-for="client in currentClients" :key="client.id" class="client-card">
          <div class="client-info">
            <span class="client-name">{{ client.name }}</span>
            <el-button 
              type="primary" 
              size="small" 
              @click="downloadClient(client.downloadUrl)"
            >
              <i class="el-icon-download"></i>
              下载
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 重置确认对话框 -->
    <el-dialog
      v-model="resetDialogVisible"
      title="确认重置订阅地址"
      width="400px"
    >
      <div class="reset-confirm-content">
        <i class="el-icon-warning" style="color: #e6a23c; font-size: 24px;"></i>
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
import QRCode from 'qrcode'
import { useAuthStore } from '@/store/auth'
import { subscriptionAPI } from '@/utils/api'

export default {
  name: 'Dashboard',
  setup() {
    const authStore = useAuthStore()
    const resetDialogVisible = ref(false)
    
    const subscriptionInfo = reactive({
      remainingDays: 0,
      expiryDate: '',
      isExpiring: false,
      currentDevices: 0,
      maxDevices: 0,
      isDeviceLimitReached: false,
      ssrUrl: '',
      clashUrl: '',
      qrcodeUrl: ''
    })

    const quickConfig = reactive({
      platform: 'windows'
    })

    const clientDownloads = {
      windows: [
        { id: 1, name: 'Clash for Windows', downloadUrl: 'https://github.com/Fndroid/clash_for_windows_pkg/releases' },
        { id: 2, name: 'V2RayN', downloadUrl: 'https://github.com/2dust/v2rayN/releases' }
      ],
      android: [
        { id: 3, name: 'Clash Meta for Android', downloadUrl: 'https://github.com/MetaCubeX/ClashMetaForAndroid/releases' },
        { id: 4, name: 'V2RayNG', downloadUrl: 'https://github.com/2dust/v2rayNG/releases' }
      ],
      mac: [
        { id: 5, name: 'ClashX Pro', downloadUrl: 'https://clashx.pro/' },
        { id: 6, name: 'V2RayX', downloadUrl: 'https://github.com/Cenmrev/V2RayX/releases' }
      ],
      ios: [
        { id: 7, name: 'Shadowrocket', downloadUrl: 'https://apps.apple.com/app/shadowrocket/id932747118' },
        { id: 8, name: 'Quantumult X', downloadUrl: 'https://apps.apple.com/app/quantumult-x/id1443988620' }
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
        
        subscriptionInfo.remainingDays = data.remaining_days
        subscriptionInfo.expiryDate = data.expiry_date
        subscriptionInfo.isExpiring = data.remaining_days <= 7
        subscriptionInfo.currentDevices = data.current_devices
        subscriptionInfo.maxDevices = data.max_devices
        subscriptionInfo.isDeviceLimitReached = data.current_devices >= data.max_devices
        subscriptionInfo.ssrUrl = data.ssr_url
        subscriptionInfo.clashUrl = data.clash_url
        subscriptionInfo.qrcodeUrl = data.qrcode_url
        
        // 生成二维码
        if (data.qrcode_url) {
          generateQRCode(data.qrcode_url)
        }
      } catch (error) {
        ElMessage.error('获取订阅信息失败')
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
        ElMessage.success('订阅地址已发送到您的QQ邮箱，请注意查收')
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

    onMounted(() => {
      fetchSubscriptionInfo()
    })

    return {
      subscriptionInfo,
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
      updateClientDownloads
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-header h1 {
  color: #1677ff;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.page-header p {
  color: #666;
  font-size: 1rem;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stats-content h3 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

.stats-number {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.expiry-date {
  font-size: 1rem;
  opacity: 0.9;
  margin-bottom: 1rem;
}

.expiry-warning {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.device-stats {
  font-size: 1.2rem;
  margin-top: 1rem;
}

.current-devices {
  color: #ffd700;
  font-weight: bold;
}

.max-devices {
  color: #42a5f5;
  font-weight: bold;
}

.device-hint {
  font-size: 0.95rem;
  opacity: 0.8;
  margin-left: 8px;
}

.device-warning {
  background: rgba(255, 107, 107, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.announcement-card,
.subscription-card,
.quick-config-card {
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.announcement-content {
  line-height: 1.6;
}

.device-management-tip {
  padding: 12px;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  margin: 15px 0;
}

.device-management-tip strong {
  color: #856404;
}

.device-management-tip p {
  margin: 8px 0 0 0;
  color: #856404;
  font-size: 14px;
}

.action-buttons {
  margin: 1rem 0;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.warning-text {
  color: #666;
  font-size: 0.9rem;
  margin: 1rem 0;
}

.renewal-section {
  margin-top: 1rem;
  text-align: center;
}

.renewal-section hr {
  margin: 1rem 0;
}

.subscription-item {
  margin-bottom: 1.5rem;
}

.subscription-input {
  margin-bottom: 0.5rem;
}

.subscription-tip {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
}

.ssr-tip {
  background: #e3f2fd;
  color: #1976d2;
}

.clash-tip {
  background: #e8f5e9;
  color: #2e7d32;
}

.quick-import {
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.import-tip {
  font-size: 0.9rem;
  color: #666;
  margin-top: 0.5rem;
}

.qrcode-section {
  text-align: center;
  margin: 1.5rem 0;
}

.client-downloads {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.client-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.client-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.client-name {
  font-weight: 500;
}

.reset-confirm-content {
  text-align: center;
  padding: 1rem 0;
}

.reset-confirm-content p {
  margin: 1rem 0 0 0;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .stats-number {
    font-size: 2rem;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .client-downloads {
    grid-template-columns: 1fr;
  }
}
</style> 