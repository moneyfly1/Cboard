<template>
    <div class="statistics-admin-container">
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-cards">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon users">
                <i class="el-icon-user"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ statistics.totalUsers }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon subscriptions">
                <i class="el-icon-connection"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ statistics.activeSubscriptions }}</div>
                <div class="stat-label">活跃订阅</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon orders">
                <i class="el-icon-shopping-cart-2"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ statistics.totalOrders }}</div>
                <div class="stat-label">总订单数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-icon revenue">
                <i class="el-icon-money"></i>
              </div>
              <div class="stat-info">
                <div class="stat-number">¥{{ statistics.totalRevenue }}</div>
                <div class="stat-label">总收入</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
  
      <!-- 图表区域 -->
      <el-row :gutter="20" class="charts-section">
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <h3>用户注册趋势</h3>
              </div>
            </template>
            <div class="chart-container">
              <canvas ref="userChart"></canvas>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <h3>收入统计</h3>
              </div>
            </template>
            <div class="chart-container">
              <canvas ref="revenueChart"></canvas>
            </div>
          </el-card>
        </el-col>
      </el-row>
  
      <!-- 详细统计 -->
      <el-row :gutter="20" class="detailed-stats">
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <h3>用户统计</h3>
              </div>
            </template>
            
            <el-table :data="userStats" style="width: 100%">
              <el-table-column prop="label" label="统计项" />
              <el-table-column prop="value" label="数值" />
              <el-table-column prop="percentage" label="占比">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.percentage"
                    :color="row.color"
                    :show-text="false"
                  />
                  <span style="margin-left: 10px">{{ row.percentage }}%</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card>
            <template #header>
              <div class="card-header">
                <h3>订阅统计</h3>
              </div>
            </template>
            
            <el-table :data="subscriptionStats" style="width: 100%">
              <el-table-column prop="label" label="统计项" />
              <el-table-column prop="value" label="数值" />
              <el-table-column prop="percentage" label="占比">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.percentage"
                    :color="row.color"
                    :show-text="false"
                  />
                  <span style="margin-left: 10px">{{ row.percentage }}%</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
  
      <!-- 最近活动 -->
      <el-card class="recent-activities">
        <template #header>
          <div class="card-header">
            <h3>最近活动</h3>
          </div>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="activity in recentActivities"
            :key="activity.id"
            :timestamp="activity.time"
            :type="activity.type"
          >
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-description">{{ activity.description }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  </template>
  
  <script>
  import { ref, reactive, onMounted } from 'vue'
  import { Chart, registerables } from 'chart.js'
  import { statisticsAPI } from '@/utils/api'
  
  Chart.register(...registerables)
  
  export default {
    name: 'AdminStatistics',
    setup() {
      const userChart = ref(null)
      const revenueChart = ref(null)
      
      const statistics = reactive({
        totalUsers: 0,
        activeSubscriptions: 0,
        totalOrders: 0,
        totalRevenue: 0
      })
  
      const userStats = ref([])
      const subscriptionStats = ref([])
      const recentActivities = ref([])
  
      // 获取统计数据
      const fetchStatistics = async () => {
        try {
          const response = await statisticsAPI.getStatistics()
          Object.assign(statistics, response.data.overview)
          userStats.value = response.data.userStats
          subscriptionStats.value = response.data.subscriptionStats
          recentActivities.value = response.data.recentActivities
        } catch (error) {
          console.error('获取统计数据失败:', error)
        }
      }
  
      // 初始化用户注册趋势图表
      const initUserChart = async () => {
        try {
          const response = await statisticsAPI.getUserTrend()
          const ctx = userChart.value.getContext('2d')
          
          new Chart(ctx, {
            type: 'line',
            data: {
              labels: response.data.labels,
              datasets: [{
                label: '新用户注册',
                data: response.data.data,
                borderColor: '#409eff',
                backgroundColor: 'rgba(64, 158, 255, 0.1)',
                tension: 0.4
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false
                }
              },
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }
          })
        } catch (error) {
          console.error('初始化用户图表失败:', error)
        }
      }
  
      // 初始化收入统计图表
      const initRevenueChart = async () => {
        try {
          const response = await statisticsAPI.getRevenueTrend()
          const ctx = revenueChart.value.getContext('2d')
          
          new Chart(ctx, {
            type: 'bar',
            data: {
              labels: response.data.labels,
              datasets: [{
                label: '收入',
                data: response.data.data,
                backgroundColor: '#67c23a',
                borderColor: '#67c23a',
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false
                }
              },
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }
          })
        } catch (error) {
          console.error('初始化收入图表失败:', error)
        }
      }
  
      onMounted(() => {
        fetchStatistics()
        initUserChart()
        initRevenueChart()
      })
  
      return {
        userChart,
        revenueChart,
        statistics,
        userStats,
        subscriptionStats,
        recentActivities
      }
    }
  }
  </script>
  
  <style scoped>
  .statistics-admin-container {
    padding: 20px;
  }
  
  .stats-cards {
    margin-bottom: 20px;
  }
  
  .stat-card {
    height: 120px;
  }
  
  .stat-content {
    display: flex;
    align-items: center;
    height: 100%;
  }
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 20px;
  }
  
  .stat-icon i {
    font-size: 24px;
    color: white;
  }
  
  .stat-icon.users {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .stat-icon.subscriptions {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }
  
  .stat-icon.orders {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }
  
  .stat-icon.revenue {
    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  }
  
  .stat-info {
    flex: 1;
  }
  
  .stat-number {
    font-size: 2rem;
    font-weight: 700;
    color: #333;
    margin-bottom: 5px;
  }
  
  .stat-label {
    color: #666;
    font-size: 0.9rem;
  }
  
  .charts-section {
    margin-bottom: 20px;
  }
  
  .chart-container {
    height: 300px;
    position: relative;
  }
  
  .card-header h3 {
    margin: 0;
    color: #333;
    font-size: 1.2rem;
  }
  
  .detailed-stats {
    margin-bottom: 20px;
  }
  
  .recent-activities {
    margin-bottom: 20px;
  }
  
  .activity-content {
    padding: 10px 0;
  }
  
  .activity-title {
    font-weight: 600;
    color: #333;
    margin-bottom: 5px;
  }
  
  .activity-description {
    color: #666;
    font-size: 0.9rem;
  }
  
  @media (max-width: 768px) {
    .statistics-admin-container {
      padding: 10px;
    }
    
    .stats-cards .el-col {
      margin-bottom: 15px;
    }
    
    .charts-section .el-col {
      margin-bottom: 20px;
    }
    
    .detailed-stats .el-col {
      margin-bottom: 20px;
    }
    
    .stat-number {
      font-size: 1.5rem;
    }
    
    .chart-container {
      height: 250px;
    }
  }
  </style>