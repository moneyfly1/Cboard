<template>
  <div class="email-stats">
    <div class="page-header">
      <h1>邮件系统监控</h1>
      <div class="header-actions">
        <el-button @click="refreshStats" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="startQueueProcessor">
          <el-icon><VideoPlay /></el-icon>
          启动队列
        </el-button>
        <el-button type="warning" @click="stopQueueProcessor">
          <el-icon><VideoPause /></el-icon>
          停止队列
        </el-button>
      </div>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ overview.total_emails || 0 }}</div>
            <div class="stat-label">总邮件数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number success">{{ overview.sent_emails || 0 }}</div>
            <div class="stat-label">已发送</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number warning">{{ overview.pending_emails || 0 }}</div>
            <div class="stat-label">待发送</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number danger">{{ overview.failed_emails || 0 }}</div>
            <div class="stat-label">发送失败</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 队列状态 -->
    <el-card class="queue-status">
      <template #header>
        <div class="card-header">
          <span>队列处理器状态</span>
          <el-tag :type="queueStatus.is_running ? 'success' : 'danger'">
            {{ queueStatus.is_running ? '运行中' : '已停止' }}
          </el-tag>
        </div>
      </template>
      
      <el-descriptions :column="3" border>
        <el-descriptions-item label="批处理大小">{{ queueStatus.batch_size }}</el-descriptions-item>
        <el-descriptions-item label="处理间隔">{{ queueStatus.processing_interval }}秒</el-descriptions-item>
        <el-descriptions-item label="最大重试次数">{{ queueStatus.max_retries }}</el-descriptions-item>
        <el-descriptions-item label="重试延迟">{{ queueStatus.retry_delays?.join(', ') }}秒</el-descriptions-item>
      </el-descriptions>
      
      <div class="queue-actions">
        <el-button @click="pauseQueueProcessor">暂停队列</el-button>
        <el-button @click="resumeQueueProcessor">恢复队列</el-button>
        <el-button type="primary" @click="retryFailedEmails">重试失败邮件</el-button>
        <el-button type="warning" @click="cleanupOldEmails">清理旧邮件</el-button>
      </div>
    </el-card>

    <!-- 每日统计图表 -->
    <el-card class="daily-stats">
      <template #header>
        <div class="card-header">
          <span>每日邮件发送统计</span>
          <el-select v-model="selectedDays" @change="fetchDailyStats" style="width: 120px">
            <el-option label="最近7天" :value="7" />
            <el-option label="最近30天" :value="30" />
            <el-option label="最近90天" :value="90" />
          </el-select>
        </div>
      </template>
      
      <div class="chart-container" v-loading="chartLoading">
        <div ref="dailyChart" style="height: 400px;"></div>
      </div>
    </el-card>

    <!-- 邮件类型分布 -->
    <el-row :gutter="20" class="type-distribution">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>邮件类型分布</span>
          </template>
          <div class="chart-container" v-loading="chartLoading">
            <div ref="typeChart" style="height: 300px;"></div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>重试次数分布</span>
          </template>
          <div class="chart-container" v-loading="chartLoading">
            <div ref="retryChart" style="height: 300px;"></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 性能指标 -->
    <el-card class="performance-stats">
      <template #header>
        <span>性能指标</span>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="performance-item">
            <div class="performance-label">成功率</div>
            <div class="performance-value">
              <el-progress 
                :percentage="performance.success_rate" 
                :color="getProgressColor(performance.success_rate)"
              />
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="performance-item">
            <div class="performance-label">队列健康度</div>
            <div class="performance-value">
              <el-tag :type="getHealthTagType(performance.queue_health)">
                {{ performance.queue_health }}
              </el-tag>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="performance-item">
            <div class="performance-label">平均重试次数</div>
            <div class="performance-value">{{ performance.avg_retry_count || 0 }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- SMTP配置信息 -->
    <el-card class="smtp-config">
      <template #header>
        <span>SMTP配置信息</span>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="SMTP服务器">{{ smtpConfig.host }}</el-descriptions-item>
        <el-descriptions-item label="端口">{{ smtpConfig.port }}</el-descriptions-item>
        <el-descriptions-item label="加密方式">{{ smtpConfig.encryption }}</el-descriptions-item>
        <el-descriptions-item label="发件人">{{ smtpConfig.from_name }} &lt;{{ smtpConfig.from_email }}&gt;</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ smtpConfig.username }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="smtpConfig.enabled ? 'success' : 'danger'">
            {{ smtpConfig.enabled ? '已启用' : '已禁用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

export default {
  name: 'EmailStats',
  components: {
    Refresh, VideoPlay, VideoPause
  },
  setup() {
    const loading = ref(false)
    const chartLoading = ref(false)
    
    const overview = reactive({
      total_emails: 0,
      sent_emails: 0,
      pending_emails: 0,
      failed_emails: 0
    })
    
    const queueStatus = reactive({
      is_running: false,
      batch_size: 10,
      processing_interval: 5,
      max_retries: 3,
      retry_delays: [60, 300, 1800]
    })
    
    const performance = reactive({
      success_rate: 0,
      queue_health: 'unknown',
      avg_retry_count: 0
    })
    
    const smtpConfig = reactive({
      host: '',
      port: '',
      encryption: '',
      from_name: '',
      from_email: '',
      username: '',
      enabled: false
    })
    
    const selectedDays = ref(7)
    const dailyStats = ref([])
    
    // 图表实例
    let dailyChart = null
    let typeChart = null
    let retryChart = null
    
    // 获取概览统计
    const fetchOverview = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/overview')
        const data = await response.json()
        if (data.success) {
          const stats = data.data
          Object.assign(overview, {
            total_emails: stats.basic_stats.total,
            sent_emails: stats.basic_stats.sent,
            pending_emails: stats.basic_stats.pending,
            failed_emails: stats.basic_stats.failed
          })
          
          Object.assign(queueStatus, stats.queue_stats)
          Object.assign(performance, {
            success_rate: stats.basic_stats.total > 0 ? 
              Math.round((stats.basic_stats.sent / stats.basic_stats.total) * 100) : 0,
            queue_health: stats.queue_stats.queue_health || 'unknown',
            avg_retry_count: stats.queue_stats.avg_retry_count || 0
          })
        }
      } catch (error) {
        ElMessage.error('获取概览统计失败')
      }
    }
    
    // 获取队列状态
    const fetchQueueStatus = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/queue/status')
        const data = await response.json()
        if (data.success) {
          Object.assign(queueStatus, data.data)
        }
      } catch (error) {
        ElMessage.error('获取队列状态失败')
      }
    }
    
    // 获取每日统计
    const fetchDailyStats = async () => {
      chartLoading.value = true
      try {
        const response = await fetch(`/api/v1/email-stats/daily?days=${selectedDays.value}`)
        const data = await response.json()
        if (data.success) {
          dailyStats.value = data.data
          updateDailyChart()
        }
      } catch (error) {
        ElMessage.error('获取每日统计失败')
      } finally {
        chartLoading.value = false
      }
    }
    
    // 获取类型分布
    const fetchTypeDistribution = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/by-type')
        const data = await response.json()
        if (data.success) {
          updateTypeChart(data.data.by_type)
        }
      } catch (error) {
        ElMessage.error('获取类型分布失败')
      }
    }
    
    // 获取性能统计
    const fetchPerformanceStats = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/performance')
        const data = await response.json()
        if (data.success) {
          Object.assign(performance, data.data)
        }
      } catch (error) {
        ElMessage.error('获取性能统计失败')
      }
    }
    
    // 获取SMTP配置
    const fetchSmtpConfig = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/smtp/config')
        const data = await response.json()
        if (data.success) {
          Object.assign(smtpConfig, data.data)
        }
      } catch (error) {
        ElMessage.error('获取SMTP配置失败')
      }
    }
    
    // 刷新统计
    const refreshStats = async () => {
      loading.value = true
      try {
        await Promise.all([
          fetchOverview(),
          fetchQueueStatus(),
          fetchDailyStats(),
          fetchTypeDistribution(),
          fetchPerformanceStats(),
          fetchSmtpConfig()
        ])
        ElMessage.success('统计信息已刷新')
      } catch (error) {
        ElMessage.error('刷新统计失败')
      } finally {
        loading.value = false
      }
    }
    
    // 启动队列处理器
    const startQueueProcessor = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/queue/start', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('队列处理器已启动')
          fetchQueueStatus()
        }
      } catch (error) {
        ElMessage.error('启动队列处理器失败')
      }
    }
    
    // 停止队列处理器
    const stopQueueProcessor = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/queue/stop', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('队列处理器已停止')
          fetchQueueStatus()
        }
      } catch (error) {
        ElMessage.error('停止队列处理器失败')
      }
    }
    
    // 暂停队列处理器
    const pauseQueueProcessor = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/queue/pause', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('队列处理器已暂停')
          fetchQueueStatus()
        }
      } catch (error) {
        ElMessage.error('暂停队列处理器失败')
      }
    }
    
    // 恢复队列处理器
    const resumeQueueProcessor = async () => {
      try {
        const response = await fetch('/api/v1/email-stats/queue/resume', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('队列处理器已恢复')
          fetchQueueStatus()
        }
      } catch (error) {
        ElMessage.error('恢复队列处理器失败')
      }
    }
    
    // 重试失败邮件
    const retryFailedEmails = async () => {
      try {
        await ElMessageBox.confirm('确定要重试所有失败的邮件吗？', '确认重试')
        
        const response = await fetch('/api/v1/email-stats/queue/retry-failed', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success(data.message)
          refreshStats()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重试失败邮件失败')
        }
      }
    }
    
    // 清理旧邮件
    const cleanupOldEmails = async () => {
      try {
        await ElMessageBox.confirm('确定要清理30天前的旧邮件吗？', '确认清理')
        
        const response = await fetch('/api/v1/email-stats/cleanup?days=30', { method: 'POST' })
        const data = await response.json()
        if (data.success) {
          ElMessage.success(data.message)
          refreshStats()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清理旧邮件失败')
        }
      }
    }
    
    // 更新每日统计图表
    const updateDailyChart = () => {
      if (!dailyChart) return
      
      const dates = dailyStats.value.map(item => item.date)
      const sentData = dailyStats.value.map(item => item.sent)
      const failedData = dailyStats.value.map(item => item.failed)
      
      dailyChart.setOption({
        xAxis: { data: dates },
        series: [
          { data: sentData, name: '已发送' },
          { data: failedData, name: '发送失败' }
        ]
      })
    }
    
    // 更新类型分布图表
    const updateTypeChart = (typeData) => {
      if (!typeChart) return
      
      const data = Object.entries(typeData).map(([name, value]) => ({ name, value }))
      
      typeChart.setOption({
        series: [{ data }]
      })
    }
    
    // 获取进度条颜色
    const getProgressColor = (percentage) => {
      if (percentage >= 80) return '#67C23A'
      if (percentage >= 60) return '#E6A23C'
      return '#F56C6C'
    }
    
    // 获取健康度标签类型
    const getHealthTagType = (health) => {
      switch (health) {
        case 'healthy': return 'success'
        case 'warning': return 'warning'
        case 'critical': return 'danger'
        default: return 'info'
      }
    }
    
    // 初始化图表
    const initCharts = () => {
      // 每日统计图表
      dailyChart = echarts.init(document.querySelector('.daily-chart'))
      dailyChart.setOption({
        title: { text: '每日邮件发送统计' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['已发送', '发送失败'] },
        xAxis: { type: 'category', data: [] },
        yAxis: { type: 'value' },
        series: [
          { type: 'line', name: '已发送', data: [] },
          { type: 'line', name: '发送失败', data: [] }
        ]
      })
      
      // 类型分布图表
      typeChart = echarts.init(document.querySelector('.type-chart'))
      typeChart.setOption({
        title: { text: '邮件类型分布' },
        tooltip: { trigger: 'item' },
        series: [{ type: 'pie', radius: '50%', data: [] }]
      })
      
      // 重试次数图表
      retryChart = echarts.init(document.querySelector('.retry-chart'))
      retryChart.setOption({
        title: { text: '重试次数分布' },
        tooltip: { trigger: 'item' },
        series: [{ type: 'bar', data: [] }]
      })
    }
    
    onMounted(() => {
      initCharts()
      refreshStats()
    })
    
    onUnmounted(() => {
      if (dailyChart) dailyChart.dispose()
      if (typeChart) typeChart.dispose()
      if (retryChart) retryChart.dispose()
    })
    
    return {
      loading,
      chartLoading,
      overview,
      queueStatus,
      performance,
      smtpConfig,
      selectedDays,
      dailyStats,
      refreshStats,
      startQueueProcessor,
      stopQueueProcessor,
      pauseQueueProcessor,
      resumeQueueProcessor,
      retryFailedEmails,
      cleanupOldEmails,
      fetchDailyStats,
      getProgressColor,
      getHealthTagType
    }
  }
}
</script>

<style scoped>
.email-stats {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.stats-overview {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 10px;
}

.stat-number.success { color: #67C23A; }
.stat-number.warning { color: #E6A23C; }
.stat-number.danger { color: #F56C6C; }

.stat-label {
  color: #606266;
  font-size: 14px;
}

.queue-status {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.queue-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}

.daily-stats {
  margin-bottom: 20px;
}

.chart-container {
  position: relative;
}

.type-distribution {
  margin-bottom: 20px;
}

.performance-stats {
  margin-bottom: 20px;
}

.performance-item {
  text-align: center;
  padding: 20px;
}

.performance-label {
  color: #606266;
  margin-bottom: 10px;
}

.performance-value {
  font-size: 18px;
  font-weight: bold;
}

.smtp-config {
  margin-bottom: 20px;
}
</style>
