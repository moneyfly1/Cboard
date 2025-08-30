<template>
  <div class="nodes-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>节点列表</h1>
      <p>查看可用的节点信息</p>
    </div>

    <!-- 节点统计 -->
    <el-card class="stats-card">
      <div class="stats-content">
        <div class="stat-item">
          <div class="stat-number">{{ nodeStats.total }}</div>
          <div class="stat-label">总节点数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ nodeStats.online }}</div>
          <div class="stat-label">在线节点</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ nodeStats.regions }}</div>
          <div class="stat-label">地区数量</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ nodeStats.types }}</div>
          <div class="stat-label">节点类型</div>
        </div>
      </div>
    </el-card>

    <!-- 节点列表 -->
    <el-card class="nodes-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-connection"></i>
          节点列表
          <div class="header-actions">
            <el-select v-model="filterRegion" placeholder="选择地区" clearable>
              <el-option
                v-for="region in regions"
                :key="region"
                :label="region"
                :value="region"
              />
            </el-select>
            <el-select v-model="filterType" placeholder="选择类型" clearable>
              <el-option
                v-for="type in nodeTypes"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
            <el-button 
              type="primary" 
              size="small" 
              @click="refreshNodes"
              :loading="loading"
            >
              <i class="el-icon-refresh"></i>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table 
        :data="filteredNodes" 
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="name" label="节点名称" min-width="150">
          <template #default="{ row }">
            <div class="node-name">
              <i :class="getNodeIcon(row.type)"></i>
              <span>{{ row.name }}</span>
              <el-tag 
                v-if="row.is_recommended" 
                type="success" 
                size="small"
              >
                推荐
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="region" label="地区" width="120">
          <template #default="{ row }">
            <el-tag :type="getRegionColor(row.region)">
              {{ row.region }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'online' ? 'success' : 'danger'">
              {{ row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="load" label="负载" width="120">
          <template #default="{ row }">
            <div class="load-indicator">
              <div class="load-bar">
                <div 
                  class="load-fill" 
                  :style="{ width: row.load + '%' }"
                  :class="getLoadClass(row.load)"
                ></div>
              </div>
              <span class="load-text">{{ row.load }}%</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="speed" label="速度" width="120">
          <template #default="{ row }">
            <span class="speed-text">{{ formatSpeed(row.speed) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="uptime" label="在线时间" width="150">
          <template #default="{ row }">
            <span>{{ formatUptime(row.uptime) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="testNode(row)"
              :loading="row.testing"
            >
              测试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <el-empty 
        v-if="!loading && filteredNodes.length === 0" 
        description="暂无节点信息"
      >
        <el-button type="primary" @click="refreshNodes">
          刷新节点列表
        </el-button>
      </el-empty>
    </el-card>

    <!-- 节点详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="节点详情"
      width="600px"
    >
      <div class="node-detail" v-if="selectedNode">
        <div class="detail-item">
          <span class="label">节点名称：</span>
          <span class="value">{{ selectedNode.name }}</span>
        </div>
        <div class="detail-item">
          <span class="label">地区：</span>
          <span class="value">{{ selectedNode.region }}</span>
        </div>
        <div class="detail-item">
          <span class="label">类型：</span>
          <span class="value">{{ selectedNode.type }}</span>
        </div>
        <div class="detail-item">
          <span class="label">状态：</span>
          <span class="value">
            <el-tag :type="selectedNode.status === 'online' ? 'success' : 'danger'">
              {{ selectedNode.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </span>
        </div>
        <div class="detail-item">
          <span class="label">负载：</span>
          <span class="value">{{ selectedNode.load }}%</span>
        </div>
        <div class="detail-item">
          <span class="label">速度：</span>
          <span class="value">{{ formatSpeed(selectedNode.speed) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">在线时间：</span>
          <span class="value">{{ formatUptime(selectedNode.uptime) }}</span>
        </div>
        <div class="detail-item">
          <span class="label">延迟：</span>
          <span class="value">{{ selectedNode.latency }}ms</span>
        </div>
        <div class="detail-item">
          <span class="label">描述：</span>
          <span class="value">{{ selectedNode.description || '暂无描述' }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { nodeAPI } from '@/utils/api'

export default {
  name: 'Nodes',
  setup() {
    const loading = ref(false)
    const nodes = ref([])
    const filterRegion = ref('')
    const filterType = ref('')
    const detailDialogVisible = ref(false)
    const selectedNode = ref(null)

    const nodeStats = reactive({
      total: 0,
      online: 0,
      regions: 0,
      types: 0
    })

    // 过滤后的节点列表
    const filteredNodes = computed(() => {
      let result = nodes.value

      if (filterRegion.value) {
        result = result.filter(node => node.region === filterRegion.value)
      }

      if (filterType.value) {
        result = result.filter(node => node.type === filterType.value)
      }

      return result
    })

    // 获取地区列表
    const regions = computed(() => {
      return [...new Set(nodes.value.map(node => node.region))]
    })

    // 获取节点类型列表
    const nodeTypes = computed(() => {
      return [...new Set(nodes.value.map(node => node.type))]
    })

    // 获取节点列表
    const fetchNodes = async () => {
      loading.value = true
      try {
        const response = await nodeAPI.getNodes()
        nodes.value = response.data.nodes || []
        
        // 计算统计数据
        updateNodeStats()
      } catch (error) {
        ElMessage.error('获取节点列表失败')
      } finally {
        loading.value = false
      }
    }

    // 更新节点统计
    const updateNodeStats = () => {
      nodeStats.total = nodes.value.length
      nodeStats.online = nodes.value.filter(n => n.status === 'online').length
      nodeStats.regions = regions.value.length
      nodeStats.types = nodeTypes.value.length
    }

    // 刷新节点列表
    const refreshNodes = () => {
      fetchNodes()
    }

    // 测试节点
    const testNode = async (node) => {
      node.testing = true
      try {
        const response = await nodeAPI.testNode(node.id)
        ElMessage.success(`节点 ${node.name} 测试完成，延迟: ${response.data.latency}ms`)
      } catch (error) {
        ElMessage.error(`节点 ${node.name} 测试失败`)
      } finally {
        node.testing = false
      }
    }

    // 获取节点图标
    const getNodeIcon = (type) => {
      const icons = {
        ssr: 'el-icon-connection',
        v2ray: 'el-icon-connection',
        trojan: 'el-icon-connection',
        vmess: 'el-icon-connection'
      }
      return icons[type] || 'el-icon-connection'
    }

    // 获取地区颜色
    const getRegionColor = (region) => {
      const colors = {
        '香港': 'success',
        '新加坡': 'warning',
        '日本': 'primary',
        '美国': 'info',
        '韩国': 'success'
      }
      return colors[region] || 'info'
    }

    // 获取类型颜色
    const getTypeColor = (type) => {
      const colors = {
        ssr: 'success',
        v2ray: 'primary',
        trojan: 'warning',
        vmess: 'info'
      }
      return colors[type] || 'info'
    }

    // 获取负载颜色
    const getLoadClass = (load) => {
      if (load < 30) return 'load-low'
      if (load < 70) return 'load-medium'
      return 'load-high'
    }

    // 格式化速度
    const formatSpeed = (speed) => {
      if (speed < 1024) return speed + ' B/s'
      if (speed < 1024 * 1024) return (speed / 1024).toFixed(1) + ' KB/s'
      return (speed / (1024 * 1024)).toFixed(1) + ' MB/s'
    }

    // 格式化在线时间
    const formatUptime = (uptime) => {
      const days = Math.floor(uptime / 86400)
      const hours = Math.floor((uptime % 86400) / 3600)
      const minutes = Math.floor((uptime % 3600) / 60)
      
      if (days > 0) return `${days}天${hours}小时`
      if (hours > 0) return `${hours}小时${minutes}分钟`
      return `${minutes}分钟`
    }

    onMounted(() => {
      fetchNodes()
    })

    return {
      loading,
      nodes,
      filterRegion,
      filterType,
      detailDialogVisible,
      selectedNode,
      nodeStats,
      filteredNodes,
      regions,
      nodeTypes,
      fetchNodes,
      refreshNodes,
      testNode,
      getNodeIcon,
      getRegionColor,
      getTypeColor,
      getLoadClass,
      formatSpeed,
      formatUptime
    }
  }
}
</script>

<style scoped>
.nodes-container {
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

.nodes-card {
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

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.node-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.node-name i {
  font-size: 1.2rem;
  color: #1677ff;
}

.load-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.load-bar {
  width: 60px;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.load-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.load-low {
  background: #52c41a;
}

.load-medium {
  background: #faad14;
}

.load-high {
  background: #ff4d4f;
}

.load-text {
  font-size: 0.9rem;
  color: #666;
  min-width: 40px;
}

.speed-text {
  font-family: 'Courier New', monospace;
  color: #1677ff;
  font-weight: 500;
}

.node-detail {
  padding: 1rem 0;
}

.detail-item {
  display: flex;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-item .label {
  width: 120px;
  font-weight: 500;
  color: #666;
}

.detail-item .value {
  flex: 1;
  color: #333;
}

@media (max-width: 768px) {
  .nodes-container {
    padding: 10px;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .detail-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .detail-item .label {
    width: auto;
  }
}
</style> 