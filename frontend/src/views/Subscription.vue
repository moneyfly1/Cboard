<template>
  <div class="subscription-container">
    <el-card class="subscription-card">
      <template #header>
        <div class="card-header">
          <h2>订阅管理</h2>
          <p>管理您的订阅信息和设备连接</p>
        </div>
      </template>

      <!-- 订阅状态 -->
      <div class="subscription-status" v-if="subscription">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">订阅状态</div>
              <div class="status-value">
                <el-tag :type="subscription.status === 'active' ? 'success' : 'danger'">
                  {{ subscription.status === 'active' ? '活跃' : '已过期' }}
                </el-tag>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">剩余时长</div>
              <div class="status-value">{{ subscription.remainingDays }} 天</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">到期时间</div>
              <div class="status-value">{{ subscription.expiryDate }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="status-item">
              <div class="status-label">设备使用</div>
              <div class="status-value">{{ subscription.currentDevices }}/{{ subscription.maxDevices }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 订阅地址 -->
      <div class="subscription-urls" v-if="subscription && subscription.subscription_id">
        <h3>订阅地址</h3>
        <div class="url-list">
          <div class="url-item">
            <div class="url-label">移动端地址：</div>
            <div class="url-content">
              <el-input
                v-model="subscription.mobileUrl"
                readonly
                size="large"
              >
                <template #append>
                  <el-button @click="copyUrl(subscription.mobileUrl)">
                    <i class="el-icon-document-copy"></i>
                  </el-button>
                </template>
              </el-input>
            </div>
          </div>
          
          <div class="url-item">
            <div class="url-label">Clash地址：</div>
            <div class="url-content">
              <el-input
                v-model="subscription.clashUrl"
                readonly
                size="large"
              >
                <template #append>
                  <el-button @click="copyUrl(subscription.clashUrl)">
                    <i class="el-icon-document-copy"></i>
                  </el-button>
                </template>
              </el-input>
            </div>
          </div>
        </div>

        <div class="qr-code-section">
          <h4>二维码</h4>
          <div class="qr-codes">
            <div class="qr-item">
              <canvas id="mobile-qrcode"></canvas>
              <p>移动端</p>
            </div>
            <div class="qr-item">
              <canvas id="clash-qrcode"></canvas>
              <p>Clash</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 无订阅状态提示 -->
      <div class="no-subscription" v-else>
        <el-empty description="您还没有订阅">
          <el-button type="primary" @click="$router.push('/packages')">
            立即订阅
          </el-button>
        </el-empty>
      </div>

      <!-- 订阅设置对话框 -->
      <el-dialog v-model="showSettingsDialog" title="订阅设置" width="500px">
        <el-form :model="subscriptionForm" label-width="120px">
          <el-form-item label="设备数量限制">
            <el-input-number 
              v-model="subscriptionForm.device_limit" 
              :min="1" 
              :max="20"
              :disabled="subscriptionForm.device_limit < subscription.currentDevices"
            />
            <div class="form-tip">
              当前已使用 {{ subscription.currentDevices }} 个设备
            </div>
          </el-form-item>
          
          <el-form-item label="到期时间">
            <el-date-picker
              v-model="subscriptionForm.expire_time"
              type="datetime"
              placeholder="选择到期时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
            />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showSettingsDialog = false">取消</el-button>
            <el-button type="primary" @click="saveSubscriptionSettings" :loading="savingSettings">
              保存设置
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 操作按钮 -->
      <div class="subscription-actions" v-if="subscription && subscription.subscription_id">
        <el-button
          type="primary"
          size="large"
          @click="resetSubscription"
          :loading="resetLoading"
        >
          重置订阅地址
        </el-button>
        
        <el-button
          type="warning"
          size="large"
          @click="showSettingsDialog = true"
        >
          订阅设置
        </el-button>
        
        <el-button
          type="success"
          size="large"
          @click="$router.push('/packages')"
        >
          续费订阅
        </el-button>
      </div>
    </el-card>

    <!-- 设备管理 -->
    <el-card class="devices-card">
      <template #header>
        <div class="card-header">
          <h3>设备管理</h3>
          <p>管理已连接的设备</p>
        </div>
      </template>

      <el-table
        :data="devices"
        v-loading="devicesLoading"
        style="width: 100%"
      >
        <el-table-column prop="name" label="设备名称" />
        <el-table-column prop="type" label="设备类型" />
        <el-table-column prop="ip" label="IP地址" />
        <el-table-column prop="lastSeen" label="最后访问" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              @click="removeDevice(row.id)"
              :loading="row.removing"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import QRCode from 'qrcode'
import { subscriptionAPI } from '@/utils/api'

export default {
  name: 'Subscription',
  setup() {
    const subscription = ref(null)
    const devices = ref([])
    const resetLoading = ref(false)
    const devicesLoading = ref(false)
    const showSettingsDialog = ref(false)
    const savingSettings = ref(false)
    const subscriptionForm = ref({
      device_limit: 3,
      expire_time: ''
    })

    // 获取订阅信息
    const fetchSubscription = async () => {
      try {
        const response = await subscriptionAPI.getCurrentSubscription()
        subscription.value = response.data
        
        // 初始化订阅表单
        if (subscription.value && subscription.value.subscription_id) {
          subscriptionForm.value.device_limit = subscription.value.maxDevices || 3
          subscriptionForm.value.expire_time = subscription.value.expiryDate || ''
        }
        
        generateQRCodes()
      } catch (error) {
        ElMessage.error('获取订阅信息失败')
        console.error('获取订阅信息失败:', error)
      }
    }

    // 获取设备列表
    const fetchDevices = async () => {
      devicesLoading.value = true
      try {
        const response = await subscriptionAPI.getDevices()
        devices.value = response.data
      } catch (error) {
        ElMessage.error('获取设备列表失败')
        console.error('获取设备列表失败:', error)
      } finally {
        devicesLoading.value = false
      }
    }

    // 生成二维码
    const generateQRCodes = async () => {
      if (!subscription.value) return

      try {
        // 生成移动端二维码
        const mobileElement = document.getElementById('mobile-qrcode')
        if (mobileElement) {
          await QRCode.toCanvas(mobileElement, subscription.value.mobileUrl, {
            width: 150,
            margin: 2
          })
        }

        // 生成Clash二维码
        const clashElement = document.getElementById('clash-qrcode')
        if (clashElement) {
          await QRCode.toCanvas(clashElement, subscription.value.clashUrl, {
            width: 150,
            margin: 2
          })
        }
      } catch (error) {
        console.error('生成二维码失败:', error)
      }
    }

    // 复制链接
    const copyUrl = async (url) => {
      try {
        await navigator.clipboard.writeText(url)
        ElMessage.success('链接已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }

    // 保存订阅设置
    const saveSubscriptionSettings = async () => {
      try {
        savingSettings.value = true
        
        await api.put('/subscriptions/user-subscription', subscriptionForm.value)
        
        ElMessage.success('订阅设置保存成功')
        showSettingsDialog.value = false
        
        // 重新获取订阅信息
        await fetchSubscription()
      } catch (error) {
        ElMessage.error('保存设置失败')
        console.error('保存订阅设置失败:', error)
      } finally {
        savingSettings.value = false
      }
    }

    // 重置订阅地址
    const resetSubscription = async () => {
      try {
        await ElMessageBox.confirm(
          '重置订阅地址将清空所有设备记录，确定要继续吗？',
          '确认重置',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        resetLoading.value = true
        await subscriptionAPI.resetSubscription()
        
        ElMessage.success('订阅地址已重置')
        await fetchSubscription()
        await fetchDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重置失败')
          console.error('重置订阅失败:', error)
        }
      } finally {
        resetLoading.value = false
      }
    }

    // 移除设备
    const removeDevice = async (deviceId) => {
      try {
        await ElMessageBox.confirm(
          '确定要移除这个设备吗？',
          '确认移除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        const device = devices.value.find(d => d.id === deviceId)
        if (device) {
          device.removing = true
        }

        await subscriptionAPI.removeDevice(deviceId)
        
        ElMessage.success('设备已移除')
        await fetchDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('移除失败')
          console.error('移除设备失败:', error)
        }
      } finally {
        const device = devices.value.find(d => d.id === deviceId)
        if (device) {
          device.removing = false
        }
      }
    }

    onMounted(() => {
      fetchSubscription()
      fetchDevices()
    })

    return {
      subscription,
      devices,
      resetLoading,
      devicesLoading,
      copyUrl,
      resetSubscription,
      removeDevice
    }
  }
}
</script>

<style scoped>
.subscription-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.subscription-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 15px;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.card-header p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.subscription-status {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-item {
  text-align: center;
}

.status-label {
  color: #666;
  font-size: 0.9rem;
  margin-bottom: 8px;
}

.status-value {
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
}

.subscription-urls {
  margin-bottom: 30px;
}

.subscription-urls h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.url-list {
  margin-bottom: 30px;
}

.url-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  gap: 15px;
}

.url-label {
  min-width: 100px;
  color: #666;
  font-weight: 500;
}

.url-content {
  flex: 1;
}

.qr-code-section {
  text-align: center;
}

.qr-code-section h4 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.1rem;
}

.qr-codes {
  display: flex;
  justify-content: center;
  gap: 40px;
}

.qr-item {
  text-align: center;
}

.qr-item p {
  margin-top: 10px;
  color: #666;
  font-size: 0.9rem;
}

.subscription-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
}

.devices-card {
  margin-top: 20px;
}

.devices-card .card-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.3rem;
}

.devices-card .card-header p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .subscription-container {
    padding: 10px;
  }
  
  .url-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .url-label {
    min-width: auto;
  }
  
  .qr-codes {
    flex-direction: column;
    gap: 20px;
  }
  
  .subscription-actions {
    flex-direction: column;
  }
  
  .status-item {
    margin-bottom: 20px;
  }
}
</style> 