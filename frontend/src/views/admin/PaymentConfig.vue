<template>
  <div class="payment-config-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>支付配置管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <i class="el-icon-plus"></i>
        添加支付方式
      </el-button>
    </div>

    <!-- 支付配置列表 -->
    <el-card class="config-list-card">
      <template #header>
        <div class="card-header">
          <span>支付方式列表</span>
          <el-button type="text" @click="loadPaymentConfigs">
            <i class="el-icon-refresh"></i>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="paymentConfigs"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="支付方式" min-width="200">
          <template #default="{ row }">
            <div class="payment-method">
              <img 
                v-if="row.icon" 
                :src="row.icon" 
                :alt="row.display_name"
                class="payment-icon"
              />
              <i v-else class="el-icon-money payment-icon-placeholder"></i>
              <div class="payment-info">
                <div class="payment-name">{{ row.display_name }}</div>
                <div class="payment-type">{{ getPaymentTypeLabel(row.type) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="200" />

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="默认" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="warning">默认</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="sort_order" label="排序" width="80" />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="text" 
              size="small" 
              @click="editConfig(row)"
            >
              编辑
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="toggleConfigStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="setDefaultConfig(row)"
              v-if="!row.is_default"
            >
              设为默认
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              class="danger-text"
              @click="deleteConfig(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
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

    <!-- 创建/编辑支付配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingConfig ? '编辑支付配置' : '添加支付方式'"
      width="800px"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input 
            v-model="configForm.name" 
            placeholder="请输入配置名称（英文）"
            :disabled="editingConfig"
          />
        </el-form-item>

        <el-form-item label="显示名称" prop="display_name">
          <el-input 
            v-model="configForm.display_name" 
            placeholder="请输入显示名称"
          />
        </el-form-item>

        <el-form-item label="支付类型" prop="type">
          <el-select 
            v-model="configForm.type" 
            placeholder="请选择支付类型"
            :disabled="editingConfig"
          >
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
            <el-option label="PayPal" value="paypal" />
            <el-option label="Stripe" value="stripe" />
            <el-option label="加密货币" value="crypto" />
          </el-select>
        </el-form-item>

        <el-form-item label="图标URL" prop="icon">
          <el-input 
            v-model="configForm.icon" 
            placeholder="请输入图标URL"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="configForm.description" 
            type="textarea"
            placeholder="请输入描述信息"
          />
        </el-form-item>

        <el-form-item label="排序" prop="sort_order">
          <el-input-number 
            v-model="configForm.sort_order" 
            :min="0"
            :max="999"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch 
            v-model="configForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch 
            v-model="configForm.is_default"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>

        <!-- 支付配置参数 -->
        <el-form-item label="配置参数">
          <div class="config-params">
            <div v-if="configForm.type === 'alipay'" class="param-section">
              <h4>支付宝配置</h4>
              <el-form-item label="App ID" prop="config.app_id">
                <el-input v-model="configForm.config.app_id" placeholder="支付宝App ID" />
              </el-form-item>
              <el-form-item label="私钥" prop="config.private_key">
                <el-input 
                  v-model="configForm.config.private_key" 
                  type="textarea"
                  placeholder="支付宝私钥"
                  :rows="4"
                />
              </el-form-item>
              <el-form-item label="公钥" prop="config.public_key">
                <el-input 
                  v-model="configForm.config.public_key" 
                  type="textarea"
                  placeholder="支付宝公钥"
                  :rows="4"
                />
              </el-form-item>
              <el-form-item label="回调地址" prop="config.notify_url">
                <el-input v-model="configForm.config.notify_url" placeholder="支付回调地址" />
              </el-form-item>
              <el-form-item label="返回地址" prop="config.return_url">
                <el-input v-model="configForm.config.return_url" placeholder="支付返回地址" />
              </el-form-item>
            </div>

            <div v-else-if="configForm.type === 'wechat'" class="param-section">
              <h4>微信支付配置</h4>
              <el-form-item label="App ID" prop="config.app_id">
                <el-input v-model="configForm.config.app_id" placeholder="微信App ID" />
              </el-form-item>
              <el-form-item label="商户号" prop="config.mch_id">
                <el-input v-model="configForm.config.mch_id" placeholder="微信商户号" />
              </el-form-item>
              <el-form-item label="API密钥" prop="config.key">
                <el-input v-model="configForm.config.key" placeholder="微信API密钥" />
              </el-form-item>
              <el-form-item label="回调地址" prop="config.notify_url">
                <el-input v-model="configForm.config.notify_url" placeholder="支付回调地址" />
              </el-form-item>
              <el-form-item label="返回地址" prop="config.return_url">
                <el-input v-model="configForm.config.return_url" placeholder="支付返回地址" />
              </el-form-item>
            </div>

            <div v-else-if="configForm.type === 'paypal'" class="param-section">
              <h4>PayPal配置</h4>
              <el-form-item label="Client ID" prop="config.client_id">
                <el-input v-model="configForm.config.client_id" placeholder="PayPal Client ID" />
              </el-form-item>
              <el-form-item label="Client Secret" prop="config.client_secret">
                <el-input v-model="configForm.config.client_secret" placeholder="PayPal Client Secret" />
              </el-form-item>
              <el-form-item label="模式" prop="config.mode">
                <el-select v-model="configForm.config.mode">
                  <el-option label="沙盒模式" value="sandbox" />
                  <el-option label="生产模式" value="live" />
                </el-select>
              </el-form-item>
              <el-form-item label="货币" prop="config.currency">
                <el-input v-model="configForm.config.currency" placeholder="货币代码，如USD" />
              </el-form-item>
              <el-form-item label="回调地址" prop="config.notify_url">
                <el-input v-model="configForm.config.notify_url" placeholder="支付回调地址" />
              </el-form-item>
              <el-form-item label="返回地址" prop="config.return_url">
                <el-input v-model="configForm.config.return_url" placeholder="支付返回地址" />
              </el-form-item>
            </div>

            <div v-else-if="configForm.type === 'stripe'" class="param-section">
              <h4>Stripe配置</h4>
              <el-form-item label="Publishable Key" prop="config.publishable_key">
                <el-input v-model="configForm.config.publishable_key" placeholder="Stripe Publishable Key" />
              </el-form-item>
              <el-form-item label="Secret Key" prop="config.secret_key">
                <el-input v-model="configForm.config.secret_key" placeholder="Stripe Secret Key" />
              </el-form-item>
              <el-form-item label="Webhook Secret" prop="config.webhook_secret">
                <el-input v-model="configForm.config.webhook_secret" placeholder="Stripe Webhook Secret" />
              </el-form-item>
              <el-form-item label="货币" prop="config.currency">
                <el-input v-model="configForm.config.currency" placeholder="货币代码，如usd" />
              </el-form-item>
              <el-form-item label="模式" prop="config.mode">
                <el-select v-model="configForm.config.mode">
                  <el-option label="测试模式" value="test" />
                  <el-option label="生产模式" value="live" />
                </el-select>
              </el-form-item>
            </div>

            <div v-else-if="configForm.type === 'crypto'" class="param-section">
              <h4>加密货币配置</h4>
              <el-form-item label="API Key" prop="config.api_key">
                <el-input v-model="configForm.config.api_key" placeholder="API Key" />
              </el-form-item>
              <el-form-item label="Secret Key" prop="config.secret_key">
                <el-input v-model="configForm.config.secret_key" placeholder="Secret Key" />
              </el-form-item>
              <el-form-item label="货币" prop="config.currency">
                <el-input v-model="configForm.config.currency" placeholder="货币代码，如USDT" />
              </el-form-item>
              <el-form-item label="网络" prop="config.network">
                <el-input v-model="configForm.config.network" placeholder="网络，如TRC20" />
              </el-form-item>
              <el-form-item label="回调地址" prop="config.notify_url">
                <el-input v-model="configForm.config.notify_url" placeholder="支付回调地址" />
              </el-form-item>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            {{ editingConfig ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '@/utils/api'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const showCreateDialog = ref(false)
const editingConfig = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const paymentConfigs = ref([])

// 表单数据
const configForm = reactive({
  name: '',
  display_name: '',
  type: '',
  icon: '',
  description: '',
  sort_order: 0,
  is_active: true,
  is_default: false,
  config: {}
})

// 表单验证规则
const configRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '配置名称只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择支付类型', trigger: 'change' }
  ]
}

// 方法
const loadPaymentConfigs = async () => {
  loading.value = true
  try {
    const response = await adminAPI.getPaymentConfigs({
      page: currentPage.value,
      size: pageSize.value
    })
    paymentConfigs.value = response.data.configs
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载支付配置失败')
  } finally {
    loading.value = false
  }
}

const editConfig = (config) => {
  editingConfig.value = config
  Object.assign(configForm, {
    name: config.name,
    display_name: config.display_name,
    type: config.type,
    icon: config.icon || '',
    description: config.description || '',
    sort_order: config.sort_order,
    is_active: config.is_active,
    is_default: config.is_default,
    config: config.config || {}
  })
  showCreateDialog.value = true
}

const saveConfig = async () => {
  saving.value = true
  try {
    if (editingConfig.value) {
      await adminAPI.updatePaymentConfig(editingConfig.value.id, configForm)
      ElMessage.success('支付配置更新成功')
    } else {
      await adminAPI.createPaymentConfig(configForm)
      ElMessage.success('支付配置创建成功')
    }
    showCreateDialog.value = false
    loadPaymentConfigs()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const toggleConfigStatus = async (config) => {
  try {
    await adminAPI.updatePaymentConfig(config.id, {
      is_active: !config.is_active
    })
    ElMessage.success('状态更新成功')
    loadPaymentConfigs()
  } catch (error) {
    ElMessage.error('状态更新失败')
  }
}

const setDefaultConfig = async (config) => {
  try {
    await adminAPI.updatePaymentConfig(config.id, {
      is_default: true
    })
    ElMessage.success('默认支付方式设置成功')
    loadPaymentConfigs()
  } catch (error) {
    ElMessage.error('设置失败')
  }
}

const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除支付配置"${config.display_name}"吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await adminAPI.deletePaymentConfig(config.id)
    ElMessage.success('删除成功')
    loadPaymentConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadPaymentConfigs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadPaymentConfigs()
}

const getPaymentTypeLabel = (type) => {
  const labels = {
    alipay: '支付宝',
    wechat: '微信支付',
    paypal: 'PayPal',
    stripe: 'Stripe',
    crypto: '加密货币'
  }
  return labels[type] || type
}

// 生命周期
onMounted(() => {
  loadPaymentConfigs()
})
</script>

<style scoped lang="scss">
.payment-config-container {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
  }
  
  .config-list-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
  
  .payment-method {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .payment-icon {
      width: 32px;
      height: 32px;
      border-radius: 4px;
    }
    
    .payment-icon-placeholder {
      width: 32px;
      height: 32px;
      background: #f5f7fa;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #909399;
    }
    
    .payment-info {
      .payment-name {
        font-weight: 500;
        margin-bottom: 4px;
      }
      
      .payment-type {
        font-size: 12px;
        color: #666;
      }
    }
  }
  
  .danger-text {
    color: #f56c6c;
  }
  
  .pagination-container {
    margin-top: 20px;
    text-align: center;
  }
  
  .config-params {
    .param-section {
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      padding: 16px;
      margin-bottom: 16px;
      
      h4 {
        margin: 0 0 16px 0;
        color: #303133;
        font-size: 16px;
      }
    }
  }
}
</style> 