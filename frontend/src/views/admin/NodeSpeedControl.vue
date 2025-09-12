<template>
  <div class="node-management-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>节点管理</h1>
      <p>查看节点统计信息</p>
    </div>

    <!-- 节点统计 -->
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-data-analysis"></i>
          节点统计
        </div>
      </template>
      
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
          <div class="stat-number">{{ nodeStats.offline }}</div>
          <div class="stat-label">离线节点</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ nodeStats.regions }}</div>
          <div class="stat-label">地区数量</div>
        </div>
      </div>
    </el-card>

    <!-- 节点列表 -->
    <el-card class="nodes-card">
      <template #header>
        <div class="card-header">
          <i class="el-icon-connection"></i>
          节点列表
        </div>
      </template>
      
      <el-table :data="nodeList" style="width: 100%">
        <el-table-column prop="name" label="节点名称" min-width="200">
          <template #default="{ row }">
            <div class="node-name">
              <i :class="getNodeIcon(row.type)"></i>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.type)">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="region" label="地区" width="120">
          <template #default="{ row }">
            <el-tag :type="getRegionColor(row.region)">
              {{ row.region }}
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
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { nodeAPI, adminAPI } from '@/utils/api'

export default {
  name: 'NodeSpeedControl',
  setup() {
    const nodeStats = reactive({
      total: 0,
      online: 0,
      offline: 0,
      regions: 0
    })
    
    const nodeList = ref([])
    
    // 获取节点统计 - 从数据库Clash配置获取真实数据
    const fetchNodeStats = async () => {
      try {
        const response = await adminAPI.getNodesStats()
        console.log('节点统计API响应:', response)
        
        // 处理API响应数据
        if (response.data && response.data.data) {
          const stats = response.data.data
          nodeStats.total = stats.total_nodes || 0
          nodeStats.online = stats.online_nodes || 0
          nodeStats.offline = stats.offline_nodes || 0
          nodeStats.regions = stats.regions || 0
        } else if (response.data) {
          const stats = response.data
          nodeStats.total = stats.total_nodes || 0
          nodeStats.online = stats.online_nodes || 0
          nodeStats.offline = stats.offline_nodes || 0
          nodeStats.regions = stats.regions || 0
        }
        
        // 强制更新响应式数据
        console.log('更新后的节点统计数据:', {
          total: nodeStats.total,
          online: nodeStats.online,
          offline: nodeStats.offline,
          regions: nodeStats.regions
        })
        console.log('节点统计数据:', nodeStats)
      } catch (error) {
        console.error('获取节点统计失败:', error)
      }
    }
    
    // 获取节点列表 - 从数据库Clash配置获取真实数据
    const fetchNodeList = async () => {
      try {
        const response = await nodeAPI.getNodes()
        console.log('节点列表API响应:', response)
        
        // 处理API响应数据
        if (response.data && response.data.data && response.data.data.nodes) {
          nodeList.value = response.data.data.nodes
        } else if (response.data && response.data.nodes) {
          nodeList.value = response.data.nodes
        } else if (response.data && Array.isArray(response.data)) {
          nodeList.value = response.data
        } else {
          nodeList.value = []
        }
        
        console.log('节点列表数据:', nodeList.value)
      } catch (error) {
        console.error('获取节点列表失败:', error)
      }
    }
    
    // 获取节点图标
    const getNodeIcon = (type) => {
      const icons = {
        ssr: 'el-icon-connection',
        ss: 'el-icon-connection',
        v2ray: 'el-icon-connection',
        vmess: 'el-icon-connection',
        trojan: 'el-icon-connection',
        vless: 'el-icon-connection',
        hysteria: 'el-icon-connection',
        hysteria2: 'el-icon-connection',
        tuic: 'el-icon-connection'
      }
      return icons[type] || 'el-icon-connection'
    }
    
    // 获取类型颜色
    const getTypeColor = (type) => {
      const colors = {
        ssr: 'primary',
        ss: 'success',
        v2ray: 'warning',
        vmess: 'info',
        trojan: 'danger',
        vless: 'success',
        hysteria: 'warning',
        hysteria2: 'info',
        tuic: 'primary'
      }
      return colors[type] || 'info'
    }
    
    // 获取地区颜色
    const getRegionColor = (region) => {
      const colors = {
        '香港': 'success',
        '美国': 'primary',
        '日本': 'warning',
        '新加坡': 'info',
        '英国': 'danger',
        '德国': 'success',
        '法国': 'primary',
        '加拿大': 'warning'
      }
      return colors[region] || 'info'
    }
    
    onMounted(() => {
      fetchNodeStats()
      fetchNodeList()
    })
    
    return {
      nodeStats,
      nodeList,
      getNodeIcon,
      getTypeColor,
      getRegionColor
    }
  }
}
</script>

<style scoped>
.node-management-container {
  padding: 2rem;
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

.stats-card, .nodes-card {
  margin-bottom: 2rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: #333;
}

.card-header i {
  font-size: 1.2rem;
  color: #1677ff;
}

.stats-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  padding: 1rem 0;
}

.stat-item {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  color: #1677ff;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  color: #666;
  font-weight: 500;
}

.node-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.node-name i {
  color: #1677ff;
  font-size: 1.1rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .node-management-container {
    padding: 1rem;
  }
  
  .stats-content {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }
  
  .stat-item {
    padding: 1rem;
  }
  
  .stat-number {
    font-size: 2rem;
  }
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