<template>
  <div class="devices-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>设备管理</h1>
      <p>管理您的订阅设备</p>
    </div>

    <!-- 设备统计 -->
    <el-card class="stats-card">
      <div class="stats-content">
        <div class="stat-item">
          <div class="stat-number">{{ deviceStats.total }}</div>
          <div class="stat-label">总设备数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ deviceStats.online }}</div>
          <div class="stat-label">在线设备</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ deviceStats.mobile }}</div>
          <div class="stat-label">移动设备</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ deviceStats.desktop }}</div>
          <div class="stat-label">桌面设备</div>
        </div>
      </div>
    </el-card>

    <!-- 设备列表 -->
    <el-card class="devices-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-monitor"></i>
          设备列表
          <el-button 
            type="primary" 
            size="small" 
            @click="refreshDevices"
            :loading="loading"
          >
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </template>

      <el-table 
        :data="devices" 
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="name" label="设备名称" min-width="150">
          <template #default="{ row }">
            <div class="device-name">
              <i :class="getDeviceIcon(row.type)"></i>
              <span>{{ row.name || '未知设备' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="设备类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getDeviceTypeColor(row.type)">
              {{ getDeviceTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="ip" label="IP地址" width="140">
          <template #default="{ row }">
            <span class="ip-address">{{ row.ip }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="last_access" label="最后访问" width="180">
          <template #default="{ row }">
            <span>{{ formatTime(row.last_access) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="user_agent" label="User Agent" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.user_agent" placement="top">
              <span class="user-agent">{{ truncateUserAgent(row.user_agent) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
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

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && devices.length === 0" 
        description="暂无设备记录"
      >
        <el-button type="primary" @click="refreshDevices">
          刷新设备列表
        </el-button>
      </el-empty>
    </el-card>

    <!-- 设备类型统计 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-pie-chart"></i>
          设备类型统计
        </div>
      </template>
      
      <div class="chart-container">
        <div class="chart-item" v-for="(count, type) in deviceTypeStats" :key="type">
          <div class="chart-label">{{ getDeviceTypeName(type) }}</div>
          <div class="chart-bar">
            <div 
              class="chart-fill" 
              :style="{ width: getPercentage(count) + '%' }"
            ></div>
          </div>
          <div class="chart-count">{{ count }}</div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { subscriptionAPI } from '@/utils/api'
import dayjs from 'dayjs'

export default {
  name: 'Devices',
  setup() {
    const loading = ref(false)
    const devices = ref([])

    const deviceStats = reactive({
      total: 0,
      online: 0,
      mobile: 0,
      desktop: 0
    })

    const deviceTypeStats = computed(() => {
      const stats = {}
      devices.value.forEach(device => {
        const type = device.type || 'unknown'
        stats[type] = (stats[type] || 0) + 1
      })
      return stats
    })

    // 获取设备列表
    const fetchDevices = async () => {
      loading.value = true
      try {
        const response = await subscriptionAPI.getUserDevices()
        devices.value = response.data.devices || []
        
        // 计算统计数据
        updateDeviceStats()
      } catch (error) {
        ElMessage.error('获取设备列表失败')
      } finally {
        loading.value = false
      }
    }

    // 更新设备统计
    const updateDeviceStats = () => {
      deviceStats.total = devices.value.length
      deviceStats.online = devices.value.filter(d => isOnline(d.last_access)).length
      deviceStats.mobile = devices.value.filter(d => d.type === 'mobile').length
      deviceStats.desktop = devices.value.filter(d => d.type === 'desktop').length
    }

    // 刷新设备列表
    const refreshDevices = () => {
      fetchDevices()
    }

    // 移除设备
    const removeDevice = async (deviceId) => {
      try {
        await ElMessageBox.confirm(
          '确定要移除这个设备吗？移除后该设备将无法继续使用订阅服务。',
          '确认移除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        // 设置移除状态
        const device = devices.value.find(d => d.id === deviceId)
        if (device) {
          device.removing = true
        }

        await subscriptionAPI.removeDevice(deviceId)
        ElMessage.success('设备移除成功')
        
        // 重新获取设备列表
        await fetchDevices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('移除设备失败')
        }
      }
    }

    // 获取设备图标
    const getDeviceIcon = (type) => {
      const icons = {
        mobile: 'el-icon-mobile-phone',
        desktop: 'el-icon-monitor',
        tablet: 'el-icon-tablet',
        tv: 'el-icon-video-camera',
        unknown: 'el-icon-question'
      }
      return icons[type] || icons.unknown
    }

    // 获取设备类型名称
    const getDeviceTypeName = (type) => {
      const names = {
        mobile: '移动设备',
        desktop: '桌面设备',
        tablet: '平板设备',
        tv: '电视设备',
        unknown: '未知设备'
      }
      return names[type] || names.unknown
    }

    // 获取设备类型颜色
    const getDeviceTypeColor = (type) => {
      const colors = {
        mobile: 'success',
        desktop: 'primary',
        tablet: 'warning',
        tv: 'info',
        unknown: 'info'
      }
      return colors[type] || colors.unknown
    }

    // 格式化时间
    const formatTime = (time) => {
      if (!time) return '未知'
      return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
    }

    // 截断User Agent
    const truncateUserAgent = (ua) => {
      if (!ua) return '未知'
      return ua.length > 50 ? ua.substring(0, 50) + '...' : ua
    }

    // 检查是否在线（24小时内访问过）
    const isOnline = (lastAccess) => {
      if (!lastAccess) return false
      const lastTime = dayjs(lastAccess)
      const now = dayjs()
      return now.diff(lastTime, 'hour') < 24
    }

    // 计算百分比
    const getPercentage = (count) => {
      if (deviceStats.total === 0) return 0
      return Math.round((count / deviceStats.total) * 100)
    }

    onMounted(() => {
      fetchDevices()
    })

    return {
      loading,
      devices,
      deviceStats,
      deviceTypeStats,
      fetchDevices,
      refreshDevices,
      removeDevice,
      getDeviceIcon,
      getDeviceTypeName,
      getDeviceTypeColor,
      formatTime,
      truncateUserAgent,
      getPercentage
    }
  }
}
</script>

<style scoped>
.devices-container {
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
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.stats-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  padding: 1rem 0;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #1677ff;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.devices-card,
.chart-card {
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-weight: 600;
}

.device-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.device-name i {
  font-size: 1.2rem;
  color: #1677ff;
}

.ip-address {
  font-family: 'Courier New', monospace;
  color: #666;
}

.user-agent {
  color: #666;
  font-size: 0.9rem;
}

.chart-container {
  padding: 1rem 0;
}

.chart-item {
  display: flex;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
}

.chart-label {
  width: 100px;
  font-weight: 500;
  color: #333;
}

.chart-bar {
  flex: 1;
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.chart-fill {
  height: 100%;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.chart-count {
  width: 60px;
  text-align: right;
  font-weight: 600;
  color: #1677ff;
}

@media (max-width: 768px) {
  .devices-container {
    padding: 10px;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .chart-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .chart-label {
    width: auto;
  }
  
  .chart-bar {
    width: 100%;
  }
  
  .chart-count {
    width: auto;
  }
}
</style> 