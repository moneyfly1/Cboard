<template>
  <div class="admin-subscriptions">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>订阅管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportSubscriptions">
              <el-icon><Download /></el-icon>
              导出订阅
            </el-button>
            <el-button type="warning" @click="clearAllDevices">
              <el-icon><Delete /></el-icon>
              清理设备数
            </el-button>
            <el-button type="info" @click="showColumnSettings = true">
              <el-icon><Setting /></el-icon>
              列设置
            </el-button>
            <el-button type="primary" @click="showAppleStats">
              <el-icon><Apple /></el-icon>
              苹果
            </el-button>
            <el-button type="success" @click="showOnlineStats">
              <el-icon><Monitor /></el-icon>
              在线
            </el-button>
            <el-dropdown @command="handleSortCommand">
              <el-button type="default">
                最新↓<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="add_time_desc">添加时间 (降序)</el-dropdown-item>
                  <el-dropdown-item command="add_time_asc">添加时间 (升序)</el-dropdown-item>
                  <el-dropdown-item command="expire_time_desc">到期时间 (降序)</el-dropdown-item>
                  <el-dropdown-item command="expire_time_asc">到期时间 (升序)</el-dropdown-item>
                  <el-dropdown-item command="device_count_desc">设备数量 (降序)</el-dropdown-item>
                  <el-dropdown-item command="device_count_asc">设备数量 (升序)</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="输入QQ或任意订阅地址查询"
          class="search-input"
          @keyup.enter="searchSubscriptions"
        >
          <template #append>
            <el-button type="primary" @click="searchSubscriptions">搜索</el-button>
          </template>
        </el-input>
        
        <div class="sort-info">
          <span class="current-sort">当前排序: {{ currentSortText }}</span>
          <el-button size="small" @click="clearSort">清除排序</el-button>
        </div>
      </div>

      <!-- 订阅列表 -->
      <el-table 
        :data="subscriptions" 
        style="width: 100%" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
        row-key="id"
      >
        <!-- 选择列 -->
        <el-table-column type="selection" width="55" />
        
        <!-- QQ号码/邮箱列 -->
        <el-table-column label="QQ号码" width="140" fixed="left">
          <template #default="scope">
            <div class="qq-info">
              <div class="qq-number">{{ scope.row.user?.email || scope.row.user?.username || '未知' }}</div>
              <el-button 
                size="small" 
                type="success" 
                @click="showUserDetails(scope.row)"
                class="detail-btn"
              >
                详情
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <!-- 结束时间列 -->
        <el-table-column label="结束时间" width="160">
          <template #default="scope">
            <div class="expire-time-section">
              <el-date-picker
                v-model="scope.row.expire_time"
                type="date"
                placeholder="年/月/日"
                format="YYYY/MM/DD"
                value-format="YYYY-MM-DD"
                size="small"
                @change="updateExpireTime(scope.row)"
                class="expire-picker"
              />
              <div class="quick-buttons">
                <el-button size="small" @click="addTime(scope.row, 180)">+半年</el-button>
                <el-button size="small" @click="addTime(scope.row, 365)">+一年</el-button>
                <el-button size="small" @click="addTime(scope.row, 730)">+两年</el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- 二维码列 -->
        <el-table-column label="二维码" width="100" align="center">
          <template #default="scope">
            <div class="qr-code-section">
              <div 
                class="qr-code" 
                @click="showQRCode(scope.row)"
                v-if="scope.row.subscription_url"
              >
                <img :src="generateQRCode(scope.row.subscription_url)" alt="QR Code" />
              </div>
              <el-text v-else type="info" size="small">无订阅</el-text>
            </div>
          </template>
        </el-table-column>
        
        <!-- 手机短链列 -->
        <el-table-column label="手机短链" width="180">
          <template #default="scope">
            <div class="subscription-link">
              <el-link 
                v-if="scope.row.v2ray_url" 
                :href="scope.row.v2ray_url" 
                target="_blank"
                type="primary"
                class="link-text"
              >
                {{ scope.row.v2ray_url }}
              </el-link>
              <el-text v-else type="info" size="small">未配置</el-text>
            </div>
          </template>
        </el-table-column>
        
        <!-- CLASH短链列 -->
        <el-table-column label="CLASH短链" width="180">
          <template #default="scope">
            <div class="subscription-link">
              <el-link 
                v-if="scope.row.clash_url" 
                :href="scope.row.clash_url" 
                target="_blank"
                type="primary"
                class="link-text"
              >
                {{ scope.row.clash_url }}
              </el-link>
              <el-text v-else type="info" size="small">未配置</el-text>
            </div>
          </template>
        </el-table-column>
        
        
        <!-- 苹果列 -->
        <el-table-column label="苹果" width="70" align="center">
          <template #default="scope">
            <el-tag type="info" size="small">{{ scope.row.apple_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- CLASH列 -->
        <el-table-column label="CLASH" width="70" align="center">
          <template #default="scope">
            <el-tag type="warning" size="small">{{ scope.row.clash_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- 在线列 -->
        <el-table-column label="在线" width="70" align="center">
          <template #default="scope">
            <el-tag type="success" size="small">{{ scope.row.online_devices || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <!-- 最大设备数列 -->
        <el-table-column label="最大设备数" width="130">
          <template #default="scope">
            <div class="device-limit-section">
              <el-input-number
                v-model="scope.row.device_limit"
                :min="0"
                :max="999"
                size="small"
                @change="updateDeviceLimit(scope.row)"
                class="device-limit-input"
              />
              <div class="quick-device-buttons">
                <el-button size="small" @click="addDeviceLimit(scope.row, 5)">+5</el-button>
                <el-button size="small" @click="addDeviceLimit(scope.row, 10)">+10</el-button>
                <el-button size="small" @click="addDeviceLimit(scope.row, 15)">+15</el-button>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <!-- 操作列 -->
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <div class="action-buttons">
              <div class="button-row">
                <el-button size="small" type="success" @click="goToUserBackend(scope.row)">
                  后台
                </el-button>
                <el-button size="small" type="primary" @click="resetSubscription(scope.row)">
                  重置
                </el-button>
                <el-button size="small" type="info" @click="sendSubscriptionEmail(scope.row)">
                  发送
                </el-button>
              </div>
              <div class="button-row">
                <el-button 
                  size="small" 
                  :type="scope.row.is_active ? 'warning' : 'success'"
                  @click="toggleSubscriptionStatus(scope.row)"
                >
                  {{ scope.row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button size="small" type="danger" @click="deleteUser(scope.row)">
                  删除
                </el-button>
                <el-button size="small" type="danger" @click="clearUserDevices(scope.row)">
                  清理
                </el-button>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户详情对话框 -->
    <el-dialog v-model="showUserDetailDialog" title="用户详细信息" width="900px" :close-on-click-modal="false">
      <div v-if="selectedUser" class="user-detail-content">
        <!-- 基本信息 -->
        <el-card class="detail-section">
          <template #header>
            <h4>基本信息</h4>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="用户ID">{{ selectedUser.user?.id }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ selectedUser.user?.username }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ selectedUser.user?.email }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ formatDate(selectedUser.user?.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ formatDate(selectedUser.user?.last_login) || '从未登录' }}</el-descriptions-item>
            <el-descriptions-item label="激活状态">
              <el-tag :type="selectedUser.user?.is_active ? 'success' : 'danger'">
                {{ selectedUser.user?.is_active ? '已激活' : '未激活' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="邮箱验证">
              <el-tag :type="selectedUser.user?.is_verified ? 'success' : 'warning'">
                {{ selectedUser.user?.is_verified ? '已验证' : '未验证' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="管理员权限">
              <el-tag :type="selectedUser.user?.is_admin ? 'danger' : 'info'">
                {{ selectedUser.user?.is_admin ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 订阅信息 -->
        <el-card class="detail-section">
          <template #header>
            <h4>订阅信息</h4>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订阅状态">
              <el-tag :type="getSubscriptionStatusType(selectedUser.status)">
                {{ getSubscriptionStatusText(selectedUser.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="到期时间">{{ formatDate(selectedUser.expire_time) }}</el-descriptions-item>
            <el-descriptions-item label="设备限制">{{ selectedUser.device_limit }}</el-descriptions-item>
            <el-descriptions-item label="当前设备">{{ selectedUser.current_devices || 0 }}</el-descriptions-item>
            <el-descriptions-item label="在线设备">{{ selectedUser.online_devices || 0 }}</el-descriptions-item>
            <el-descriptions-item label="V2Ray订阅次数">{{ selectedUser.v2ray_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="Clash订阅次数">{{ selectedUser.clash_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="苹果设备数">{{ selectedUser.apple_count || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 订阅地址 -->
        <el-card class="detail-section">
          <template #header>
            <h4>订阅地址</h4>
          </template>
          <div class="subscription-urls">
            <div class="url-item">
              <label>V2Ray订阅地址:</label>
              <el-input v-model="selectedUser.v2ray_url" readonly>
                <template #append>
                  <el-button @click="copyToClipboard(selectedUser.v2ray_url)">复制</el-button>
                </template>
              </el-input>
            </div>
            <div class="url-item">
              <label>Clash订阅地址:</label>
              <el-input v-model="selectedUser.clash_url" readonly>
                <template #append>
                  <el-button @click="copyToClipboard(selectedUser.clash_url)">复制</el-button>
                </template>
              </el-input>
            </div>
          </div>
        </el-card>

        <!-- 在线设备列表 -->
        <el-card class="detail-section">
          <template #header>
            <h4>在线设备列表</h4>
          </template>
          <el-table :data="selectedUser.devices || []" size="small">
            <el-table-column prop="device_name" label="设备名称" />
            <el-table-column prop="device_type" label="设备类型" />
            <el-table-column prop="user_agent" label="User Agent" />
            <el-table-column prop="ip_address" label="IP地址" />
            <el-table-column prop="last_seen" label="最后在线" />
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button size="small" type="danger" @click="removeDevice(scope.row)">移除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- UA记录 -->
        <el-card class="detail-section">
          <template #header>
            <h4>UA记录</h4>
          </template>
          <el-table :data="selectedUser.ua_records || []" size="small">
            <el-table-column prop="user_agent" label="User Agent" />
            <el-table-column prop="device_type" label="设备类型" />
            <el-table-column prop="created_at" label="记录时间" />
            <el-table-column prop="ip_address" label="IP地址" />
          </el-table>
        </el-card>
      </div>
    </el-dialog>

    <!-- 二维码放大对话框 -->
    <el-dialog v-model="showQRDialog" title="订阅二维码" width="400px" center>
      <div class="qr-dialog-content">
        <div class="qr-code-large">
          <img :src="currentQRCode" alt="QR Code" />
        </div>
        <div class="qr-info">
          <p>扫描二维码即可添加订阅</p>
          <el-button type="primary" @click="downloadQRCode">下载二维码</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 列设置对话框 -->
    <el-dialog v-model="showColumnSettings" title="列设置" width="500px">
      <el-checkbox-group v-model="visibleColumns">
        <el-checkbox label="qq">QQ号码</el-checkbox>
        <el-checkbox label="expire_time">结束时间</el-checkbox>
        <el-checkbox label="qr_code">二维码</el-checkbox>
        <el-checkbox label="v2ray_url">手机短链</el-checkbox>
        <el-checkbox label="clash_url">CLASH短链</el-checkbox>
        <el-checkbox label="created_at">添加时间</el-checkbox>
        <el-checkbox label="apple_count">苹果</el-checkbox>
        <el-checkbox label="clash_count">CLASH</el-checkbox>
        <el-checkbox label="online_devices">在线</el-checkbox>
        <el-checkbox label="device_limit">最大设备数</el-checkbox>
        <el-checkbox label="actions">操作</el-checkbox>
      </el-checkbox-group>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, Delete, Setting, Apple, Monitor, ArrowDown, View
} from '@element-plus/icons-vue'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AdminSubscriptions',
  components: {
    Download, Delete, Setting, Apple, Monitor, ArrowDown, View
  },
  setup() {
    const loading = ref(false)
    const subscriptions = ref([])
    const selectedSubscriptions = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const searchQuery = ref('')
    const currentSort = ref('add_time_desc')
    const showUserDetailDialog = ref(false)
    const showQRDialog = ref(false)
    const showColumnSettings = ref(false)
    const selectedUser = ref(null)
    const currentQRCode = ref('')
    const visibleColumns = ref([
      'qq', 'expire_time', 'qr_code', 'v2ray_url', 'clash_url', 
      'created_at', 'apple_count', 'clash_count', 'online_devices', 
      'device_limit', 'actions'
    ])

    // 计算当前排序文本
    const currentSortText = computed(() => {
      const sortMap = {
        'add_time_desc': '添加时间 (降序)',
        'add_time_asc': '添加时间 (升序)',
        'expire_time_desc': '到期时间 (降序)',
        'expire_time_asc': '到期时间 (升序)',
        'device_count_desc': '设备数量 (降序)',
        'device_count_asc': '设备数量 (升序)'
      }
      return sortMap[currentSort.value] || '添加时间 (降序)'
    })

    // 加载订阅列表
    const loadSubscriptions = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          search: searchQuery.value,
          sort: currentSort.value
        }
        
        const response = await adminAPI.getSubscriptions(params)
        console.log('订阅管理API响应:', response)
        
        if (response.data?.success !== false) {
          subscriptions.value = response.data?.data?.subscriptions || []
          total.value = response.data?.data?.total || 0
          console.log('加载的订阅数据:', subscriptions.value)
        } else {
          ElMessage.error('加载订阅列表失败')
        }
      } catch (error) {
        console.error('加载订阅列表失败:', error)
        ElMessage.error('加载订阅列表失败')
      } finally {
        loading.value = false
      }
    }

    // 搜索订阅
    const searchSubscriptions = () => {
      currentPage.value = 1
      loadSubscriptions()
    }

    // 处理排序命令
    const handleSortCommand = (command) => {
      currentSort.value = command
      loadSubscriptions()
    }

    // 清除排序
    const clearSort = () => {
      currentSort.value = 'add_time_desc'
      loadSubscriptions()
    }

    // 更新到期时间
    const updateExpireTime = async (subscription) => {
      try {
        await adminAPI.updateSubscription(subscription.id, {
          expire_time: subscription.expire_time
        })
        ElMessage.success('到期时间更新成功')
      } catch (error) {
        ElMessage.error('更新到期时间失败')
        console.error('更新到期时间失败:', error)
      }
    }

    // 添加时间
    const addTime = async (subscription, days) => {
      try {
        const currentDate = new Date(subscription.expire_time)
        const newDate = new Date(currentDate.getTime() + days * 24 * 60 * 60 * 1000)
        subscription.expire_time = newDate.toISOString().split('T')[0]
        await updateExpireTime(subscription)
      } catch (error) {
        ElMessage.error('添加时间失败')
        console.error('添加时间失败:', error)
      }
    }

    // 更新设备限制
    const updateDeviceLimit = async (subscription) => {
      try {
        await adminAPI.updateSubscription(subscription.id, {
          device_limit: subscription.device_limit
        })
        ElMessage.success('设备限制更新成功')
      } catch (error) {
        ElMessage.error('更新设备限制失败')
        console.error('更新设备限制失败:', error)
      }
    }

    // 添加设备限制
    const addDeviceLimit = async (subscription, count) => {
      try {
        subscription.device_limit = (subscription.device_limit || 0) + count
        await updateDeviceLimit(subscription)
      } catch (error) {
        ElMessage.error('添加设备限制失败')
        console.error('添加设备限制失败:', error)
      }
    }

    // 生成二维码
    const generateQRCode = (url) => {
      if (!url) return ''
      // 这里应该使用二维码生成库，暂时返回占位符
      return `https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=${encodeURIComponent(url)}`
    }

    // 显示二维码
    const showQRCode = (subscription) => {
      if (subscription.subscription_url) {
        currentQRCode.value = generateQRCode(subscription.subscription_url)
        showQRDialog.value = true
      }
    }

    // 下载二维码
    const downloadQRCode = () => {
      const link = document.createElement('a')
      link.href = currentQRCode.value
      link.download = 'subscription-qr.png'
      link.click()
    }

    // 显示用户详情
    const showUserDetails = async (subscription) => {
      try {
        const response = await adminAPI.getUser(subscription.user.id)
        console.log('用户详情API响应:', response)
        
        selectedUser.value = {
          ...subscription,
          user: response.data?.data || response.data
        }
        showUserDetailDialog.value = true
      } catch (error) {
        ElMessage.error('加载用户详情失败')
        console.error('加载用户详情失败:', error)
      }
    }

    // 复制到剪贴板
    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }

    // 进入用户后台
    const goToUserBackend = (subscription) => {
      // 这里应该实现跳转到用户后台的逻辑
      ElMessage.info('跳转到用户后台功能待实现')
    }

    // 重置订阅
    const resetSubscription = async (subscription) => {
      try {
        await ElMessageBox.confirm('确定要重置该用户的订阅地址吗？', '确认重置', {
          type: 'warning'
        })
        
        await adminAPI.resetUserSubscription(subscription.user.id)
        ElMessage.success('订阅地址重置成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重置订阅失败')
          console.error('重置订阅失败:', error)
        }
      }
    }

    // 发送订阅邮件
    const sendSubscriptionEmail = async (subscription) => {
      try {
        await adminAPI.sendSubscriptionEmail(subscription.user.id)
        ElMessage.success('订阅邮件发送成功')
      } catch (error) {
        ElMessage.error('发送订阅邮件失败')
        console.error('发送订阅邮件失败:', error)
      }
    }

    // 切换订阅状态
    const toggleSubscriptionStatus = async (subscription) => {
      try {
        const newStatus = !subscription.is_active
        await adminAPI.updateSubscription(subscription.id, {
          is_active: newStatus
        })
        subscription.is_active = newStatus
        ElMessage.success(`订阅已${newStatus ? '启用' : '禁用'}`)
      } catch (error) {
        ElMessage.error('更新订阅状态失败')
        console.error('更新订阅状态失败:', error)
      }
    }

    // 删除用户
    const deleteUser = async (subscription) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除该用户吗？这将删除用户的所有信息，包括设备记录、账号信息、邮件信息、UA记录等。此操作不可恢复！',
          '确认删除',
          {
            type: 'error',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )
        
        await adminAPI.deleteUser(subscription.user.id)
        ElMessage.success('用户删除成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除用户失败')
          console.error('删除用户失败:', error)
        }
      }
    }

    // 清理用户设备
    const clearUserDevices = async (subscription) => {
      try {
        await ElMessageBox.confirm('确定要清理该用户的在线设备吗？这将清除所有设备记录和UA记录。', '确认清理', {
          type: 'warning'
        })
        
        await adminAPI.clearUserDevices(subscription.user.id)
        ElMessage.success('设备清理成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('清理设备失败')
          console.error('清理设备失败:', error)
        }
      }
    }

    // 清理所有设备
    const clearAllDevices = async () => {
      try {
        await ElMessageBox.confirm('确定要清理所有用户的设备吗？这将清除所有设备记录。', '确认清理', {
          type: 'warning'
        })
        
        await adminAPI.batchClearDevices()
        ElMessage.success('批量清理设备成功')
        loadSubscriptions()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量清理设备失败')
          console.error('批量清理设备失败:', error)
        }
      }
    }

    // 导出订阅
    const exportSubscriptions = async () => {
      try {
        const response = await adminAPI.exportSubscriptions()
        // 处理导出逻辑
        ElMessage.success('导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
        console.error('导出失败:', error)
      }
    }

    // 显示苹果统计
    const showAppleStats = () => {
      ElMessage.info('苹果设备统计功能待实现')
    }

    // 显示在线统计
    const showOnlineStats = () => {
      ElMessage.info('在线设备统计功能待实现')
    }

    // 移除设备
    const removeDevice = async (device) => {
      try {
        await adminAPI.removeDevice(device.id)
        ElMessage.success('设备移除成功')
        // 重新加载用户详情
        if (selectedUser.value) {
          showUserDetails(selectedUser.value)
        }
      } catch (error) {
        ElMessage.error('移除设备失败')
        console.error('移除设备失败:', error)
      }
    }

    // 获取订阅状态类型
    const getSubscriptionStatusType = (status) => {
      const statusMap = {
        'active': 'success',
        'inactive': 'info',
        'expired': 'danger',
        'paused': 'warning'
      }
      return statusMap[status] || 'info'
    }

    // 获取订阅状态文本
    const getSubscriptionStatusText = (status) => {
      const statusMap = {
        'active': '活跃',
        'inactive': '未激活',
        'expired': '已过期',
        'paused': '已暂停'
      }
      return statusMap[status] || '未知'
    }

    // 格式化日期
    const formatDate = (date) => {
      if (!date) return '-'
      return new Date(date).toLocaleDateString('zh-CN')
    }

    // 处理选择变化
    const handleSelectionChange = (selection) => {
      selectedSubscriptions.value = selection
    }

    // 处理页面大小变化
    const handleSizeChange = (val) => {
      pageSize.value = val
      loadSubscriptions()
    }

    // 处理当前页变化
    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadSubscriptions()
    }

    // 组件挂载时加载数据
    onMounted(() => {
      loadSubscriptions()
    })

    return {
      loading,
      subscriptions,
      selectedSubscriptions,
      currentPage,
      pageSize,
      total,
      searchQuery,
      currentSort,
      currentSortText,
      showUserDetailDialog,
      showQRDialog,
      showColumnSettings,
      selectedUser,
      currentQRCode,
      visibleColumns,
      loadSubscriptions,
      searchSubscriptions,
      handleSortCommand,
      clearSort,
      updateExpireTime,
      addTime,
      updateDeviceLimit,
      addDeviceLimit,
      generateQRCode,
      showQRCode,
      downloadQRCode,
      showUserDetails,
      copyToClipboard,
      goToUserBackend,
      resetSubscription,
      sendSubscriptionEmail,
      toggleSubscriptionStatus,
      deleteUser,
      clearUserDevices,
      clearAllDevices,
      exportSubscriptions,
      showAppleStats,
      showOnlineStats,
      removeDevice,
      getSubscriptionStatusType,
      getSubscriptionStatusText,
      formatDate,
      handleSelectionChange,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.admin-subscriptions {
  padding: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-section {
  margin-bottom: 20px;
}

.search-input {
  width: 400px;
  margin-bottom: 10px;
}

.sort-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #666;
  font-size: 14px;
}

.current-sort {
  font-weight: 500;
}

.qq-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qq-number {
  font-weight: 500;
  color: #303133;
}

.detail-btn {
  width: 100%;
}

.expire-time-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.expire-picker {
  width: 100%;
}

.quick-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.quick-buttons .el-button {
  padding: 2px 6px;
  font-size: 11px;
  min-width: 0;
}

.qr-code-section {
  display: flex;
  justify-content: center;
  align-items: center;
}

.qr-code {
  cursor: pointer;
  transition: transform 0.2s;
}

.qr-code:hover {
  transform: scale(1.1);
}

.qr-code img {
  width: 50px;
  height: 50px;
  border-radius: 4px;
}

.subscription-link {
  word-break: break-all;
}

.link-text {
  font-size: 12px;
}

.device-limit-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.device-limit-input {
  width: 100%;
}

.quick-device-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.quick-device-buttons .el-button {
  padding: 2px 6px;
  font-size: 11px;
  min-width: 0;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.button-row {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.button-row .el-button {
  padding: 3px 6px;
  font-size: 11px;
  flex: 1;
  min-width: 0;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.user-detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0;
  color: #303133;
}

.subscription-urls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.url-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.url-item label {
  font-weight: 500;
  color: #606266;
}

.qr-dialog-content {
  text-align: center;
}

.qr-code-large img {
  width: 200px;
  height: 200px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.qr-info {
  color: #666;
}

.qr-info p {
  margin-bottom: 16px;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .search-input {
    width: 300px;
  }
  
  .header-actions {
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 1200px) {
  .search-input {
    width: 250px;
  }
  
  .header-actions {
    flex-wrap: wrap;
    gap: 6px;
  }
  
  .quick-buttons,
  .quick-device-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  .button-row {
    flex-direction: column;
    gap: 2px;
  }
}

@media (max-width: 768px) {
  .admin-subscriptions {
    padding: 10px;
  }
  
  .search-input {
    width: 100%;
  }
  
  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .quick-buttons,
  .quick-device-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  .button-row {
    flex-direction: column;
    gap: 2px;
  }
  
  .qr-code img {
    width: 40px;
    height: 40px;
  }
}
</style>