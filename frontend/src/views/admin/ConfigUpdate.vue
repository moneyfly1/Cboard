<template>
  <div class="config-update">
    <!-- 状态卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-content">
            <div class="status-icon" :class="status.is_running ? 'running' : 'stopped'">
              <el-icon><VideoPlay v-if="!status.is_running" /><VideoPause v-else /></el-icon>
            </div>
            <div class="status-text">
              <div class="status-title">{{ status.is_running ? '运行中' : '已停止' }}</div>
              <div class="status-desc">更新任务状态</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-content">
            <div class="status-icon" :class="status.scheduled_enabled ? 'enabled' : 'disabled'">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="status-text">
              <div class="status-title">{{ status.scheduled_enabled ? '已启用' : '未启用' }}</div>
              <div class="status-desc">定时任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-content">
            <div class="status-icon" :class="status.config_exists ? 'success' : 'warning'">
              <el-icon><Document /></el-icon>
            </div>
            <div class="status-text">
              <div class="status-title">{{ status.config_exists ? '已生成' : '未生成' }}</div>
              <div class="status-desc">配置文件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="status-card">
          <div class="status-content">
            <div class="status-icon info">
              <el-icon><Clock /></el-icon>
            </div>
            <div class="status-text">
              <div class="status-title">{{ formatTime(status.last_update) }}</div>
              <div class="status-desc">最后更新</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能状态提示 -->
    <el-alert
      title="节点采集功能已启用"
      type="success"
      :closable="false"
      style="margin-bottom: 20px;"
    >
      <template #default>
        <p>节点采集功能已启用，可以正常使用。</p>
        <p>请确保已正确配置节点源URL和过滤关键词。</p>
      </template>
    </el-alert>

    <!-- 操作按钮 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>操作控制</span>
      </template>
      <div class="action-buttons">
        <el-button 
          type="primary" 
          :loading="loading.start"
          @click="startUpdate"
          :disabled="status.is_running"
        >
          <el-icon><VideoPlay /></el-icon>
          开始更新
        </el-button>
        <el-button 
          type="warning" 
          :loading="loading.stop"
          @click="stopUpdate"
          :disabled="!status.is_running"
        >
          <el-icon><VideoPause /></el-icon>
          停止更新
        </el-button>
        <el-button 
          type="info" 
          :loading="loading.test"
          @click="testUpdate"
          :disabled="status.is_running"
        >
          <el-icon><View /></el-icon>
          测试更新
        </el-button>
        <el-button 
          type="success" 
          :loading="loading.refresh"
          @click="refreshStatus"
        >
          <el-icon><Refresh /></el-icon>
          刷新状态
        </el-button>
      </div>
    </el-card>

    <!-- 配置设置 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>配置设置</span>
          <el-button type="primary" size="small" @click="saveConfig" :loading="loading.save">
            <el-icon><Check /></el-icon>
            保存配置
          </el-button>
        </div>
      </template>
      
      <el-form :model="config" label-width="120px">
        <el-form-item label="节点源URL">
          <div v-for="(url, index) in config.urls" :key="index" class="url-item">
            <el-input v-model="config.urls[index]" placeholder="请输入节点源URL" />
            <el-button 
              type="danger" 
              size="small" 
              @click="removeUrl(index)"
              :disabled="config.urls.length <= 1"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button type="primary" size="small" @click="addUrl">
            <el-icon><Plus /></el-icon>
            添加URL
          </el-button>
        </el-form-item>
        
        <el-form-item label="目标目录">
          <el-input v-model="config.target_dir" placeholder="配置文件保存目录" />
        </el-form-item>
        
        <el-form-item label="v2ray文件名">
          <el-input v-model="config.v2ray_file" placeholder="v2ray配置文件名称" />
        </el-form-item>
        
        <el-form-item label="clash文件名">
          <el-input v-model="config.clash_file" placeholder="clash配置文件名称" />
        </el-form-item>
        
        <el-form-item label="更新间隔(秒)">
          <el-input-number 
            v-model="config.update_interval" 
            :min="300" 
            :max="86400"
            placeholder="定时更新间隔"
          />
        </el-form-item>
        
        <el-form-item label="启用定时任务">
          <el-switch v-model="config.enable_schedule" />
        </el-form-item>
        
        <el-form-item label="过滤关键词">
          <div v-for="(keyword, index) in config.filter_keywords" :key="index" class="keyword-item">
            <el-input v-model="config.filter_keywords[index]" placeholder="过滤关键词" />
            <el-button 
              type="danger" 
              size="small" 
              @click="removeKeyword(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
          <el-button type="primary" size="small" @click="addKeyword">
            <el-icon><Plus /></el-icon>
            添加关键词
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 生成的文件 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <span>生成的文件</span>
      </template>
      
      <el-table :data="fileList" style="width: 100%">
        <el-table-column prop="name" label="文件名" width="200" />
        <el-table-column prop="path" label="路径" />
        <el-table-column prop="size" label="大小" width="120">
          <template #default="scope">
            {{ formatFileSize(scope.row.size) }}
          </template>
        </el-table-column>
        <el-table-column prop="modified" label="修改时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.modified) }}
          </template>
        </el-table-column>
        <el-table-column prop="exists" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.exists ? 'success' : 'danger'">
              {{ scope.row.exists ? '存在' : '不存在' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 更新日志 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="log-header-left">
            <span>更新日志</span>
            <el-tag v-if="isLogPolling" type="success" size="small" class="live-indicator">
              <el-icon><VideoPlay /></el-icon>
              实时更新中
            </el-tag>
            <el-tag v-if="newLogCount > 0" type="info" size="small" class="new-log-indicator">
              <el-icon><Bell /></el-icon>
              {{ newLogCount }} 条新日志
            </el-tag>
          </div>
          <div>
            <el-button type="primary" size="small" @click="refreshLogs">
              <el-icon><Refresh /></el-icon>
              刷新日志
            </el-button>
            <el-button type="warning" size="small" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清理日志
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="log-container">
        <div 
          v-for="(log, index) in logs" 
          :key="index" 
          class="log-item"
          :class="log.level"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">{{ log.level.toUpperCase() }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <div v-if="logs.length === 0" class="no-logs">
          暂无日志
        </div>
      </div>
    </el-card>

  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  VideoPlay, VideoPause, Timer, Document, Clock, Refresh, 
  Check, Delete, Plus, View, Bell
} from '@element-plus/icons-vue'
import { configUpdateAPI } from '@/utils/api'
import api from '@/utils/api'

// API导入检查

export default {
  name: 'ConfigUpdate',
  components: {
    VideoPlay, VideoPause, Timer, Document, Clock, Refresh,
    Check, Delete, Plus, View, Bell
  },
  setup() {
    const status = ref({
      is_running: false,
      scheduled_enabled: false,
      last_update: null,
      next_update: null,
      config_exists: false
    })
    
    const config = reactive({
      urls: [''],
      target_dir: './uploads/config',
      v2ray_file: 'xr',
      clash_file: 'clash.yaml',
      update_interval: 3600,
      enable_schedule: false,
      filter_keywords: []
    })
    
    const fileList = ref([])
    const logs = ref([])
    const isLogPolling = ref(false)
    const newLogCount = ref(0)
    
    const loading = reactive({
      start: false,
      stop: false,
      test: false,
      refresh: false,
      save: false,
    })
    
    
    // 轮询相关
    let statusPollingInterval = null
    let refreshInterval = null
    let logPollingInterval = null
    
    // 启动状态轮询
    const startStatusPolling = () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
      }
      
      statusPollingInterval = setInterval(async () => {
        await getStatus()
        // 如果任务停止，停止轮询
        if (!status.value.is_running) {
          stopStatusPolling()
          stopRefreshInterval()
          stopLogPolling()
        }
      }, 1000) // 每1秒检查一次，更频繁地检查状态
    }
    
    // 停止状态轮询
    const stopStatusPolling = () => {
      if (statusPollingInterval) {
        clearInterval(statusPollingInterval)
        statusPollingInterval = null
      }
    }
    
    // 启动定时刷新（仅在任务运行时）
    const startRefreshInterval = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
      
      refreshInterval = setInterval(() => {
        if (!loading.refresh && status.value.is_running) {
          getStatus()
        }
      }, 10000) // 每10秒刷新一次，减少请求频率
    }
    
    // 停止定时刷新
    const stopRefreshInterval = () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
        refreshInterval = null
      }
    }
    
    // 启动日志轮询
    const startLogPolling = () => {
      if (logPollingInterval) {
        clearInterval(logPollingInterval)
      }
      
      isLogPolling.value = true
      logPollingInterval = setInterval(async () => {
        try {
          if (!loading.refresh && status.value.is_running) {
            await getLogs()
          } else if (!status.value.is_running) {
            // 如果任务停止，停止日志轮询
            stopLogPolling()
          }
        } catch (error) {
          console.error('日志轮询错误:', error)
          // 如果连续出错，停止轮询
          stopLogPolling()
        }
      }, 2000) // 每2秒刷新一次日志，更频繁地更新
    }
    
    // 停止日志轮询
    const stopLogPolling = () => {
      if (logPollingInterval) {
        clearInterval(logPollingInterval)
        logPollingInterval = null
      }
      isLogPolling.value = false
    }
    
    // 获取状态
    const getStatus = async () => {
      try {
        const response = await configUpdateAPI.getStatus()
        if (response.data.success) {
          status.value = response.data.data
        } else {
          console.error('获取状态失败:', response.data.message)
        }
      } catch (error) {
        console.error('获取状态失败:', error)
        ElMessage.error('获取状态失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 获取配置
    const getConfig = async () => {
      try {
        const response = await configUpdateAPI.getConfig()
        if (response.data.success) {
          Object.assign(config, response.data.data)
        } else {
          console.error('获取配置失败:', response.data.message)
        }
      } catch (error) {
        console.error('获取配置失败:', error)
        ElMessage.error('获取配置失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 获取文件列表
    const getFiles = async () => {
      try {
        const response = await configUpdateAPI.getFiles()
        if (response.data.success) {
          const files = response.data.data
          fileList.value = [
            {
              name: 'v2ray配置',
              path: files.v2ray?.path || '',
              size: files.v2ray?.size || 0,
              modified: files.v2ray?.modified || null,
              exists: files.v2ray?.exists || false
            },
            {
              name: 'clash配置',
              path: files.clash?.path || '',
              size: files.clash?.size || 0,
              modified: files.clash?.modified || null,
              exists: files.clash?.exists || false
            }
          ]
        } else {
          console.error('获取文件列表失败:', response.data.message)
        }
      } catch (error) {
        console.error('获取文件列表失败:', error)
        ElMessage.error('获取文件列表失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 获取日志
    const getLogs = async () => {
      try {
        const response = await configUpdateAPI.getLogs()
        if (response.data.success) {
          const oldLogCount = logs.value.length
          logs.value = response.data.data
          
          // 如果日志数量增加，自动滚动到底部并更新新日志计数
          if (logs.value.length > oldLogCount) {
            newLogCount.value = logs.value.length - oldLogCount
            setTimeout(() => {
              const logContainer = document.querySelector('.log-container')
              if (logContainer) {
                logContainer.scrollTop = logContainer.scrollHeight
              }
              // 3秒后清除新日志计数提示
              setTimeout(() => {
                newLogCount.value = 0
              }, 3000)
            }, 100)
          }
        } else {
          console.error('获取日志失败:', response.data.message)
        }
      } catch (error) {
        console.error('获取日志失败:', error)
        ElMessage.error('获取日志失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 开始更新
    const startUpdate = async () => {
      loading.start = true
      try {
        const response = await configUpdateAPI.startUpdate()
        
        if (response.data.success) {
          ElMessage.success('更新任务已启动')
          // 立即启动轮询检查状态
          startStatusPolling()
          startRefreshInterval()
          startLogPolling() // 启动日志轮询
          // 立即刷新状态和日志
          await Promise.all([getStatus(), getLogs()])
        } else {
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        console.error('启动更新错误:', error)
        ElMessage.error('启动失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.start = false
      }
    }
    
    // 停止更新
    const stopUpdate = async () => {
      loading.stop = true
      try {
        const response = await configUpdateAPI.stopUpdate()
        
        if (response.data.success) {
          ElMessage.success('更新任务已停止')
          stopStatusPolling() // 停止轮询
          stopRefreshInterval() // 停止定时刷新
          stopLogPolling() // 停止日志轮询
          await getStatus()
        } else {
          ElMessage.error(response.data.message || '停止失败')
        }
      } catch (error) {
        ElMessage.error('停止失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.stop = false
      }
    }
    
    // 测试更新
    const testUpdate = async () => {
      loading.test = true
      try {
        const response = await configUpdateAPI.testUpdate()
        
        if (response.data.success) {
          ElMessage.success('测试任务已启动')
          // 立即启动轮询检查状态
          startStatusPolling()
          startRefreshInterval()
          startLogPolling() // 启动日志轮询
          // 立即刷新状态和日志
          await Promise.all([getStatus(), getLogs()])
        } else {
          ElMessage.error(response.data.message || '启动测试失败')
        }
      } catch (error) {
        ElMessage.error('启动测试失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.test = false
      }
    }
    
    // 刷新状态
    const refreshStatus = async () => {
      loading.refresh = true
      try {
        await Promise.all([getStatus(), getFiles(), getLogs()])
        ElMessage.success('状态已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      } finally {
        loading.refresh = false
      }
    }
    
    // 保存配置
    const saveConfig = async () => {
      loading.save = true
      try {
        const response = await configUpdateAPI.updateConfig(config)
        
        if (response.data.success) {
          ElMessage.success('配置已保存')
        } else {
          ElMessage.error(response.data.message || '保存失败')
        }
      } catch (error) {
        console.error('保存配置错误:', error)
        ElMessage.error('保存失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.save = false
      }
    }
    
    // 刷新日志
    const refreshLogs = async () => {
      await getLogs()
    }
    
    // 清理日志
    const clearLogs = async () => {
      try {
        await ElMessageBox.confirm('确定要清理所有日志吗？', '确认清理', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        const response = await configUpdateAPI.clearLogs()
        
        if (response.data.success) {
          ElMessage.success('日志已清理')
          await getLogs()
        } else {
          ElMessage.error(response.data.message || '清理失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清理失败: ' + (error.response?.data?.message || error.message))
        }
      }
    }
    
    
    
    // 添加URL
    const addUrl = () => {
      config.urls.push('')
    }
    
    // 删除URL
    const removeUrl = (index) => {
      if (config.urls.length > 1) {
        config.urls.splice(index, 1)
      }
    }
    
    // 添加关键词
    const addKeyword = () => {
      config.filter_keywords.push('')
    }
    
    // 删除关键词
    const removeKeyword = (index) => {
      config.filter_keywords.splice(index, 1)
    }
    
    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return '从未'
      try {
        return new Date(timeStr).toLocaleString()
      } catch {
        return timeStr
      }
    }
    
    // 格式化文件大小
    const formatFileSize = (bytes) => {
      if (!bytes) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }
    
    // 初始化
    onMounted(async () => {
      await Promise.all([getStatus(), getConfig(), getFiles(), getLogs()])
      
      // 如果任务正在运行，启动日志轮询
      if (status.value.is_running) {
        startLogPolling()
      }
    })
    
    onUnmounted(() => {
      // 清理轮询
      stopStatusPolling()
      stopRefreshInterval()
      stopLogPolling()
    })
    
    return {
      status,
      config,
      fileList,
      logs,
      loading,
      isLogPolling,
      newLogCount,
      startUpdate,
      stopUpdate,
      testUpdate,
      refreshStatus,
      saveConfig,
      refreshLogs,
      clearLogs,
      addUrl,
      removeUrl,
      addKeyword,
      removeKeyword,
      formatTime,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.config-update {
  padding: 20px;
}

.status-card {
  height: 100px;
}

.status-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.status-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.status-icon.running {
  background-color: #67c23a;
}

.status-icon.stopped {
  background-color: #909399;
}

.status-icon.enabled {
  background-color: #409eff;
}

.status-icon.disabled {
  background-color: #909399;
}

.status-icon.success {
  background-color: #67c23a;
}

.status-icon.warning {
  background-color: #e6a23c;
}

.status-icon.info {
  background-color: #409eff;
}

.status-text {
  flex: 1;
}

.status-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 5px;
}

.status-desc {
  color: #666;
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-indicator {
  animation: pulse 2s infinite;
}

.new-log-indicator {
  animation: bounce 1s ease-in-out;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-3px);
  }
  60% {
    transform: translateY(-2px);
  }
}

.url-item, .keyword-item {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.url-item .el-input, .keyword-item .el-input {
  flex: 1;
}

.log-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
  background-color: #f5f7fa;
}

.log-item {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
  padding: 5px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 12px;
}

.log-item.info {
  background-color: #e1f3d8;
}

.log-item.warning {
  background-color: #fdf6ec;
}

.log-item.error {
  background-color: #fef0f0;
}

.log-item.success {
  background-color: #e1f3d8;
}

.log-time {
  color: #666;
  min-width: 150px;
}

.log-level {
  font-weight: bold;
  min-width: 60px;
}

.log-message {
  flex: 1;
}

.no-logs {
  text-align: center;
  color: #999;
  padding: 20px;
}

.form-tip {
  color: #999;
  font-size: 12px;
  margin-top: 5px;
}

.dialog-footer {
  text-align: right;
}

/* 移除所有输入框的圆角和阴影效果，设置为简单长方形 */
:deep(.el-input__wrapper) {
  border-radius: 0 !important;
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
  background-color: #ffffff !important;
}

:deep(.el-select .el-input__wrapper) {
  border-radius: 0 !important;
  box-shadow: none !important;
  border: 1px solid #dcdfe6 !important;
  background-color: #ffffff !important;
}

:deep(.el-input__inner) {
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  background-color: transparent !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc !important;
  box-shadow: none !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #1677ff !important;
  box-shadow: none !important;
}
</style>
