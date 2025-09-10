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
      title="节点采集功能已暂时关闭"
      type="warning"
      :closable="false"
      style="margin-bottom: 20px;"
    >
      <template #default>
        <p>节点采集功能已暂时关闭，等待后期开发。</p>
        <p>如需使用此功能，请联系开发人员。</p>
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
          <span>更新日志</span>
          <div>
            <el-button type="primary" size="small" @click="refreshLogs">
              <el-icon><Refresh /></el-icon>
              刷新日志
            </el-button>
            <el-button type="warning" size="small" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清理日志
            </el-button>
            <el-button type="success" size="small" @click="startLogCleanup">
              <el-icon><Timer /></el-icon>
              启动自动清理
            </el-button>
            <el-button type="danger" size="small" @click="stopLogCleanup">
              <el-icon><VideoPause /></el-icon>
              停止自动清理
            </el-button>
            <el-button type="info" size="small" @click="showCleanupIntervalDialog">
              <el-icon><Setting /></el-icon>
              设置清理间隔
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

    <!-- 清理间隔设置对话框 -->
    <el-dialog
      v-model="cleanupIntervalDialogVisible"
      title="设置日志清理间隔"
      width="400px"
      :before-close="handleCleanupIntervalDialogClose"
    >
      <el-form :model="cleanupIntervalForm" label-width="120px">
        <el-form-item label="清理间隔（分钟）">
          <el-input-number
            v-model="cleanupIntervalForm.interval_minutes"
            :min="1"
            :max="1440"
            placeholder="请输入清理间隔"
            style="width: 100%"
          />
          <div class="form-tip">
            建议设置范围：1-1440分钟（1分钟到24小时）
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cleanupIntervalDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCleanupInterval" :loading="loading.cleanupInterval">
            保存设置
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  VideoPlay, VideoPause, Timer, Document, Clock, Refresh, 
  Check, Delete, Plus, View 
} from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'
import api from '@/utils/api'

// 调试：直接测试API导入
console.log('ConfigUpdate.vue - adminAPI导入测试:', adminAPI)
console.log('ConfigUpdate.vue - startConfigUpdate方法:', adminAPI?.startConfigUpdate)
console.log('ConfigUpdate.vue - api对象:', api)

export default {
  name: 'ConfigUpdate',
  components: {
    VideoPlay, VideoPause, Timer, Document, Clock, Refresh,
    Check, Delete, Plus, View
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
    
    const loading = reactive({
      start: false,
      stop: false,
      test: false,
      refresh: false,
      save: false,
      cleanupInterval: false
    })
    
    // 清理间隔设置相关
    const cleanupIntervalDialogVisible = ref(false)
    const cleanupIntervalForm = reactive({
      interval_minutes: 10
    })
    
    // 轮询相关
    let statusPollingInterval = null
    let refreshInterval = null
    
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
        }
      }, 2000) // 每2秒检查一次
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
    
    // 获取状态
    const getStatus = async () => {
      try {
        let response
        if (typeof adminAPI.getConfigUpdateStatus === 'function') {
          response = await adminAPI.getConfigUpdateStatus()
        } else {
          response = await api.get('/admin/config-update/status')
        }
        
        if (response.data.success) {
          status.value = response.data.data
        }
      } catch (error) {
        console.error('获取状态失败:', error)
      }
    }
    
    // 获取配置
    const getConfig = async () => {
      try {
        let response
        if (typeof adminAPI.getConfigUpdateConfig === 'function') {
          response = await adminAPI.getConfigUpdateConfig()
        } else {
          response = await api.get('/admin/config-update/config')
        }
        
        if (response.data.success) {
          Object.assign(config, response.data.data)
        }
      } catch (error) {
        console.error('获取配置失败:', error)
      }
    }
    
    // 获取文件列表
    const getFiles = async () => {
      try {
        let response
        if (typeof adminAPI.getConfigUpdateFiles === 'function') {
          response = await adminAPI.getConfigUpdateFiles()
        } else {
          response = await api.get('/admin/config-update/files')
        }
        
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
        }
      } catch (error) {
        console.error('获取文件列表失败:', error)
      }
    }
    
    // 获取日志
    const getLogs = async () => {
      try {
        let response
        if (typeof adminAPI.getConfigUpdateLogs === 'function') {
          response = await adminAPI.getConfigUpdateLogs()
        } else {
          response = await api.get('/admin/config-update/logs')
        }
        
        if (response.data.success) {
          logs.value = response.data.data
        }
      } catch (error) {
        console.error('获取日志失败:', error)
      }
    }
    
    // 开始更新
    const startUpdate = async () => {
      loading.start = true
      try {
        // 调试信息
        console.log('adminAPI对象:', adminAPI)
        console.log('startConfigUpdate方法:', adminAPI.startConfigUpdate)
        
        let response
        if (typeof adminAPI.startConfigUpdate === 'function') {
          response = await adminAPI.startConfigUpdate()
        } else {
          // 备用方案：直接使用api对象
          console.log('使用备用API调用方案')
          response = await api.post('/admin/config-update/start')
        }
        
        if (response.data.success) {
          ElMessage.success('更新任务已启动')
          // 立即刷新状态
          await getStatus()
          // 启动轮询检查状态
          startStatusPolling()
          startRefreshInterval()
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
        let response
        if (typeof adminAPI.stopConfigUpdate === 'function') {
          response = await adminAPI.stopConfigUpdate()
        } else {
          response = await api.post('/admin/config-update/stop')
        }
        
        if (response.data.success) {
          ElMessage.success('更新任务已停止')
          stopStatusPolling() // 停止轮询
          stopRefreshInterval() // 停止定时刷新
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
        let response
        if (typeof adminAPI.testConfigUpdate === 'function') {
          response = await adminAPI.testConfigUpdate()
        } else {
          response = await api.post('/admin/config-update/test')
        }
        
        if (response.data.success) {
          ElMessage.success('测试任务已启动')
          await getStatus()
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
        let response
        if (typeof adminAPI.updateConfigUpdateConfig === 'function') {
          response = await adminAPI.updateConfigUpdateConfig(config)
        } else {
          response = await api.put('/admin/config-update/config', config)
        }
        
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
        
        let response
        if (typeof adminAPI.clearConfigUpdateLogs === 'function') {
          response = await adminAPI.clearConfigUpdateLogs()
        } else {
          response = await api.post('/admin/config-update/logs/clear')
        }
        
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
    
    // 启动日志自动清理
    const startLogCleanup = async () => {
      try {
        let response
        if (typeof adminAPI.startLogCleanupTimer === 'function') {
          response = await adminAPI.startLogCleanupTimer()
        } else {
          response = await api.post('/admin/config-update/logs/cleanup/start')
        }
        
        if (response.data.success) {
          ElMessage.success(response.data.message || '日志自动清理已启动')
        } else {
          ElMessage.error(response.data.message || '启动失败')
        }
      } catch (error) {
        ElMessage.error('启动失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 停止日志自动清理
    const stopLogCleanup = async () => {
      try {
        let response
        if (typeof adminAPI.stopLogCleanupTimer === 'function') {
          response = await adminAPI.stopLogCleanupTimer()
        } else {
          response = await api.post('/admin/config-update/logs/cleanup/stop')
        }
        
        if (response.data.success) {
          ElMessage.success('日志自动清理已停止')
        } else {
          ElMessage.error(response.data.message || '停止失败')
        }
      } catch (error) {
        ElMessage.error('停止失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 显示清理间隔设置对话框
    const showCleanupIntervalDialog = async () => {
      try {
        // 先获取当前的清理间隔
        const response = await api.get('/admin/config-update/logs/cleanup/interval')
        if (response.data.success) {
          cleanupIntervalForm.interval_minutes = response.data.data.interval_minutes
        }
        cleanupIntervalDialogVisible.value = true
      } catch (error) {
        ElMessage.error('获取当前清理间隔失败: ' + (error.response?.data?.message || error.message))
      }
    }
    
    // 保存清理间隔设置
    const saveCleanupInterval = async () => {
      try {
        loading.cleanupInterval = true
        const response = await api.put('/admin/config-update/logs/cleanup/interval', {
          interval_minutes: cleanupIntervalForm.interval_minutes
        })
        
        if (response.data.success) {
          ElMessage.success(`清理间隔已设置为${cleanupIntervalForm.interval_minutes}分钟`)
          cleanupIntervalDialogVisible.value = false
        } else {
          ElMessage.error(response.data.message || '设置失败')
        }
      } catch (error) {
        ElMessage.error('设置失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.cleanupInterval = false
      }
    }
    
    // 处理清理间隔对话框关闭
    const handleCleanupIntervalDialogClose = (done) => {
      done()
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
      // 调试信息
      console.log('ConfigUpdate组件已挂载')
      console.log('adminAPI对象:', adminAPI)
      console.log('adminAPI.startConfigUpdate:', adminAPI.startConfigUpdate)
      console.log('typeof adminAPI.startConfigUpdate:', typeof adminAPI.startConfigUpdate)
      
      await Promise.all([getStatus(), getConfig(), getFiles(), getLogs()])
      
      // 不再自动启动定时刷新，只在任务运行时才刷新
    })
    
    onUnmounted(() => {
      // 清理轮询
      stopStatusPolling()
      stopRefreshInterval()
    })
    
    return {
      status,
      config,
      fileList,
      logs,
      loading,
      cleanupIntervalDialogVisible,
      cleanupIntervalForm,
      startUpdate,
      stopUpdate,
      testUpdate,
      refreshStatus,
      saveConfig,
      refreshLogs,
      clearLogs,
      startLogCleanup,
      stopLogCleanup,
      showCleanupIntervalDialog,
      saveCleanupInterval,
      handleCleanupIntervalDialogClose,
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
</style>
