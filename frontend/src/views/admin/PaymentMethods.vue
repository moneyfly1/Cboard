<template>
  <div class="admin-payment-methods">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>支付方式管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportPaymentMethods">
              <el-icon><Download /></el-icon>
              导出配置
            </el-button>
            <el-button type="warning" @click="showBulkOperationsDialog = true">
              <el-icon><Operation /></el-icon>
              批量操作
            </el-button>
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              添加支付方式
            </el-button>
          </div>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="支付方式">
          <el-select v-model="searchForm.type" placeholder="选择支付方式" clearable>
            <el-option label="全部" value="" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
            <el-option label="PayPal" value="paypal" />
            <el-option label="Stripe" value="stripe" />
            <el-option label="银行转账" value="bank_transfer" />
            <el-option label="加密货币" value="crypto" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="searchPaymentMethods">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 支付方式列表 -->
      <el-table :data="paymentMethods" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="支付方式名称" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getTypeTagType(scope.row.type)">
              {{ getTypeText(scope.row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="'active'"
              :inactive-value="'inactive'"
              @change="toggleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button size="small" @click="editPaymentMethod(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="info" 
              @click="viewConfig(scope.row)"
            >
              <el-icon><View /></el-icon>
              配置
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deletePaymentMethod(scope.row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
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

    <!-- 添加/编辑支付方式对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="editingPaymentMethod ? '编辑支付方式' : '添加支付方式'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="paymentForm" :rules="paymentRules" ref="paymentFormRef" label-width="120px">
        <el-form-item label="支付方式名称" prop="name">
          <el-input v-model="paymentForm.name" placeholder="请输入支付方式名称" />
        </el-form-item>
        
        <el-form-item label="支付类型" prop="type">
          <el-select v-model="paymentForm.type" placeholder="选择支付类型" @change="handleTypeChange">
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
            <el-option label="PayPal" value="paypal" />
            <el-option label="Stripe" value="stripe" />
            <el-option label="银行转账" value="bank_transfer" />
            <el-option label="加密货币" value="crypto" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-select v-model="paymentForm.status" placeholder="选择状态">
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="paymentForm.sort_order" :min="0" :max="999" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="paymentForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入支付方式描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="savePaymentMethod" :loading="saving">
            {{ editingPaymentMethod ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 支付配置对话框 -->
    <el-dialog v-model="showConfigDialog" title="支付配置" width="800px">
      <div class="config-content" v-if="selectedPaymentMethod">
        <h4>{{ selectedPaymentMethod.name }} 配置</h4>
        
        <!-- 支付宝配置 -->
        <div v-if="selectedPaymentMethod.type === 'alipay'" class="config-section">
          <el-form :model="alipayConfig" label-width="120px">
            <el-form-item label="App ID">
              <el-input v-model="alipayConfig.app_id" placeholder="请输入支付宝App ID" />
            </el-form-item>
            <el-form-item label="商户私钥">
              <el-input 
                v-model="alipayConfig.merchant_private_key" 
                type="textarea" 
                :rows="4"
                placeholder="请输入商户私钥"
              />
            </el-form-item>
            <el-form-item label="支付宝公钥">
              <el-input 
                v-model="alipayConfig.alipay_public_key" 
                type="textarea" 
                :rows="4"
                placeholder="请输入支付宝公钥"
              />
            </el-form-item>
            <el-form-item label="同步回调地址">
              <el-input v-model="alipayConfig.return_url" placeholder="请输入同步回调地址" />
            </el-form-item>
            <el-form-item label="异步回调地址">
              <el-input v-model="alipayConfig.notify_url" placeholder="请输入异步回调地址" />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 微信支付配置 -->
        <div v-if="selectedPaymentMethod.type === 'wechat'" class="config-section">
          <el-form :model="wechatConfig" label-width="120px">
            <el-form-item label="商户号">
              <el-input v-model="wechatConfig.mch_id" placeholder="请输入微信商户号" />
            </el-form-item>
            <el-form-item label="App ID">
              <el-input v-model="wechatConfig.app_id" placeholder="请输入微信App ID" />
            </el-form-item>
            <el-form-item label="API密钥">
              <el-input v-model="wechatConfig.api_key" placeholder="请输入API密钥" />
            </el-form-item>
            <el-form-item label="证书路径">
              <el-input v-model="wechatConfig.cert_path" placeholder="请输入证书路径" />
            </el-form-item>
            <el-form-item label="异步回调地址">
              <el-input v-model="wechatConfig.notify_url" placeholder="请输入异步回调地址" />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- PayPal配置 -->
        <div v-if="selectedPaymentMethod.type === 'paypal'" class="config-section">
          <el-form :model="paypalConfig" label-width="120px">
            <el-form-item label="Client ID">
              <el-input v-model="paypalConfig.client_id" placeholder="请输入PayPal Client ID" />
            </el-form-item>
            <el-form-item label="Secret">
              <el-input v-model="paypalConfig.secret" placeholder="请输入PayPal Secret" />
            </el-form-item>
            <el-form-item label="环境">
              <el-select v-model="paypalConfig.environment">
                <el-option label="沙箱" value="sandbox" />
                <el-option label="生产" value="live" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- Stripe配置 -->
        <div v-if="selectedPaymentMethod.type === 'stripe'" class="config-section">
          <el-form :model="stripeConfig" label-width="120px">
            <el-form-item label="Publishable Key">
              <el-input v-model="stripeConfig.publishable_key" placeholder="请输入Stripe Publishable Key" />
            </el-form-item>
            <el-form-item label="Secret Key">
              <el-input v-model="stripeConfig.secret_key" placeholder="请输入Stripe Secret Key" />
            </el-form-item>
            <el-form-item label="Webhook Secret">
              <el-input v-model="stripeConfig.webhook_secret" placeholder="请输入Webhook Secret" />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 银行转账配置 -->
        <div v-if="selectedPaymentMethod.type === 'bank_transfer'" class="config-section">
          <el-form :model="bankConfig" label-width="120px">
            <el-form-item label="银行名称">
              <el-input v-model="bankConfig.bank_name" placeholder="请输入银行名称" />
            </el-form-item>
            <el-form-item label="账户名">
              <el-input v-model="bankConfig.account_name" placeholder="请输入账户名" />
            </el-form-item>
            <el-form-item label="账号">
              <el-input v-model="bankConfig.account_number" placeholder="请输入账号" />
            </el-form-item>
            <el-form-item label="开户行">
              <el-input v-model="bankConfig.branch" placeholder="请输入开户行" />
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="bankConfig.notes" placeholder="请输入转账备注要求" />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 加密货币配置 -->
        <div v-if="selectedPaymentMethod.type === 'crypto'" class="config-section">
          <el-form :model="cryptoConfig" label-width="120px">
            <el-form-item label="币种">
              <el-select v-model="cryptoConfig.currency" multiple placeholder="选择支持的币种">
                <el-option label="比特币 (BTC)" value="BTC" />
                <el-option label="以太坊 (ETH)" value="ETH" />
                <el-option label="USDT" value="USDT" />
                <el-option label="莱特币 (LTC)" value="LTC" />
              </el-select>
            </el-form-item>
            <el-form-item label="钱包地址">
              <el-input v-model="cryptoConfig.wallet_address" placeholder="请输入钱包地址" />
            </el-form-item>
            <el-form-item label="网络">
              <el-select v-model="cryptoConfig.network">
                <el-option label="主网" value="mainnet" />
                <el-option label="测试网" value="testnet" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
        
        <div class="config-actions">
          <el-button type="primary" @click="saveConfig" :loading="configSaving">
            保存配置
          </el-button>
          <el-button @click="testConfig" :loading="configTesting">
            测试配置
          </el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 批量操作对话框 -->
    <el-dialog v-model="showBulkOperationsDialog" title="批量操作" width="500px">
      <el-form :model="bulkForm" label-width="100px">
        <el-form-item label="操作类型">
          <el-select v-model="bulkForm.operation" placeholder="选择操作">
            <el-option label="批量启用" value="enable" />
            <el-option label="批量禁用" value="disable" />
            <el-option label="批量删除" value="delete" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择支付方式">
          <el-checkbox-group v-model="bulkForm.selectedIds">
            <el-checkbox 
              v-for="method in paymentMethods" 
              :key="method.id" 
              :label="method.id"
            >
              {{ method.name }} ({{ getTypeText(method.type) }})
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBulkOperationsDialog = false">取消</el-button>
          <el-button type="primary" @click="executeBulkOperation" :loading="bulkLoading">
            执行操作
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Download, Operation, Plus, Search, Refresh, Edit, 
  View, Delete 
} from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminPaymentMethods',
  components: {
    Download, Operation, Plus, Search, Refresh, Edit, 
    View, Delete
  },
  setup() {
    const api = useApi()
    const loading = ref(false)
    const saving = ref(false)
    const configSaving = ref(false)
    const configTesting = ref(false)
    const bulkLoading = ref(false)
    const paymentMethods = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const showAddDialog = ref(false)
    const showConfigDialog = ref(false)
    const showBulkOperationsDialog = ref(false)
    const editingPaymentMethod = ref(null)
    const selectedPaymentMethod = ref(null)
    const paymentFormRef = ref()

    const searchForm = reactive({
      type: '',
      status: ''
    })

    const paymentForm = reactive({
      name: '',
      type: '',
      status: 'active',
      sort_order: 0,
      description: ''
    })

    const bulkForm = reactive({
      operation: '',
      selectedIds: []
    })

    // 各种支付方式的配置
    const alipayConfig = reactive({
      app_id: '',
      merchant_private_key: '',
      alipay_public_key: '',
      return_url: '',
      notify_url: ''
    })

    const wechatConfig = reactive({
      mch_id: '',
      app_id: '',
      api_key: '',
      cert_path: '',
      notify_url: ''
    })

    const paypalConfig = reactive({
      client_id: '',
      secret: '',
      environment: 'sandbox'
    })

    const stripeConfig = reactive({
      publishable_key: '',
      secret_key: '',
      webhook_secret: ''
    })

    const bankConfig = reactive({
      bank_name: '',
      account_name: '',
      account_number: '',
      branch: '',
      notes: ''
    })

    const cryptoConfig = reactive({
      currency: [],
      wallet_address: '',
      network: 'mainnet'
    })

    const paymentRules = {
      name: [
        { required: true, message: '请输入支付方式名称', trigger: 'blur' }
      ],
      type: [
        { required: true, message: '请选择支付类型', trigger: 'change' }
      ],
      status: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }

    const loadPaymentMethods = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          size: pageSize.value,
          ...searchForm
        }
        const response = await api.get('/admin/payment-methods', { params })
        paymentMethods.value = response.data.items
        total.value = response.data.total
      } catch (error) {
        ElMessage.error('加载支付方式列表失败')
      } finally {
        loading.value = false
      }
    }

    const searchPaymentMethods = () => {
      currentPage.value = 1
      loadPaymentMethods()
    }

    const resetSearch = () => {
      Object.assign(searchForm, { type: '', status: '' })
      searchPaymentMethods()
    }

    const handleSizeChange = (val) => {
      pageSize.value = val
      loadPaymentMethods()
    }

    const handleCurrentChange = (val) => {
      currentPage.value = val
      loadPaymentMethods()
    }

    const handleTypeChange = () => {
      // 当支付类型改变时，可以重置相关配置
    }

    const editPaymentMethod = (method) => {
      editingPaymentMethod.value = method
      Object.assign(paymentForm, {
        name: method.name,
        type: method.type,
        status: method.status,
        sort_order: method.sort_order,
        description: method.description || ''
      })
      showAddDialog.value = true
    }

    const savePaymentMethod = async () => {
      try {
        await paymentFormRef.value.validate()
        saving.value = true
        
        if (editingPaymentMethod.value) {
          await api.put(`/admin/payment-methods/${editingPaymentMethod.value.id}`, paymentForm)
          ElMessage.success('支付方式更新成功')
        } else {
          await api.post('/admin/payment-methods', paymentForm)
          ElMessage.success('支付方式创建成功')
        }
        
        showAddDialog.value = false
        editingPaymentMethod.value = null
        resetPaymentForm()
        loadPaymentMethods()
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        saving.value = false
      }
    }

    const deletePaymentMethod = async (method) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除支付方式 "${method.name}" 吗？`, 
          '确认删除', 
          { type: 'warning' }
        )
        await api.delete(`/admin/payment-methods/${method.id}`)
        ElMessage.success('支付方式删除成功')
        loadPaymentMethods()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const toggleStatus = async (method) => {
      try {
        const newStatus = method.status === 'active' ? 'inactive' : 'active'
        await api.put(`/admin/payment-methods/${method.id}/status`, { status: newStatus })
        ElMessage.success(`支付方式${newStatus === 'active' ? '启用' : '禁用'}成功`)
      } catch (error) {
        ElMessage.error('状态更新失败')
        // 恢复原状态
        method.status = method.status === 'active' ? 'inactive' : 'active'
      }
    }

    const viewConfig = async (method) => {
      try {
        const response = await api.get(`/admin/payment-methods/${method.id}/config`)
        selectedPaymentMethod.value = method
        
        // 根据支付类型加载对应配置
        if (method.type === 'alipay') {
          Object.assign(alipayConfig, response.data)
        } else if (method.type === 'wechat') {
          Object.assign(wechatConfig, response.data)
        } else if (method.type === 'paypal') {
          Object.assign(paypalConfig, response.data)
        } else if (method.type === 'stripe') {
          Object.assign(stripeConfig, response.data)
        } else if (method.type === 'bank_transfer') {
          Object.assign(bankConfig, response.data)
        } else if (method.type === 'crypto') {
          Object.assign(cryptoConfig, response.data)
        }
        
        showConfigDialog.value = true
      } catch (error) {
        ElMessage.error('加载配置失败')
      }
    }

    const saveConfig = async () => {
      if (!selectedPaymentMethod.value) return
      
      configSaving.value = true
      try {
        let configData = {}
        
        // 根据支付类型获取对应配置
        if (selectedPaymentMethod.value.type === 'alipay') {
          configData = alipayConfig
        } else if (selectedPaymentMethod.value.type === 'wechat') {
          configData = wechatConfig
        } else if (selectedPaymentMethod.value.type === 'paypal') {
          configData = paypalConfig
        } else if (selectedPaymentMethod.value.type === 'stripe') {
          configData = stripeConfig
        } else if (selectedPaymentMethod.value.type === 'bank_transfer') {
          configData = bankConfig
        } else if (selectedPaymentMethod.value.type === 'crypto') {
          configData = cryptoConfig
        }
        
        await api.put(`/admin/payment-methods/${selectedPaymentMethod.value.id}/config`, configData)
        ElMessage.success('配置保存成功')
      } catch (error) {
        ElMessage.error('配置保存失败')
      } finally {
        configSaving.value = false
      }
    }

    const testConfig = async () => {
      if (!selectedPaymentMethod.value) return
      
      configTesting.value = true
      try {
        await api.post(`/admin/payment-methods/${selectedPaymentMethod.value.id}/test`)
        ElMessage.success('配置测试成功')
      } catch (error) {
        ElMessage.error('配置测试失败')
      } finally {
        configTesting.value = false
      }
    }

    const exportPaymentMethods = async () => {
      try {
        const response = await api.get('/admin/payment-methods/export', { 
          responseType: 'blob',
          params: searchForm 
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `payment_methods_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('支付方式配置导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
      }
    }

    const executeBulkOperation = async () => {
      if (bulkForm.selectedIds.length === 0) {
        ElMessage.warning('请选择要操作的支付方式')
        return
      }

      bulkLoading.value = true
      try {
        const { operation } = bulkForm
        
        if (operation === 'enable') {
          await api.post('/admin/payment-methods/bulk-enable', {
            method_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量启用成功')
        } else if (operation === 'disable') {
          await api.post('/admin/payment-methods/bulk-disable', {
            method_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量禁用成功')
        } else if (operation === 'delete') {
          await ElMessageBox.confirm(
            `确定要删除选中的 ${bulkForm.selectedIds.length} 个支付方式吗？`, 
            '确认删除', 
            { type: 'warning' }
          )
          await api.post('/admin/payment-methods/bulk-delete', {
            method_ids: bulkForm.selectedIds
          })
          ElMessage.success('批量删除成功')
        }
        
        showBulkOperationsDialog.value = false
        loadPaymentMethods()
        bulkForm.selectedIds = []
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量操作失败')
        }
      } finally {
        bulkLoading.value = false
      }
    }

    const resetPaymentForm = () => {
      Object.assign(paymentForm, {
        name: '',
        type: '',
        status: 'active',
        sort_order: 0,
        description: ''
      })
      paymentFormRef.value?.resetFields()
    }

    const getTypeTagType = (type) => {
      const typeMap = {
        'alipay': 'success',
        'wechat': 'primary',
        'paypal': 'warning',
        'stripe': 'info',
        'bank_transfer': 'danger',
        'crypto': 'dark'
      }
      return typeMap[type] || 'info'
    }

    const getTypeText = (type) => {
      const typeMap = {
        'alipay': '支付宝',
        'wechat': '微信支付',
        'paypal': 'PayPal',
        'stripe': 'Stripe',
        'bank_transfer': '银行转账',
        'crypto': '加密货币'
      }
      return typeMap[type] || type
    }

    onMounted(() => {
      loadPaymentMethods()
    })

    return {
      loading,
      saving,
      configSaving,
      configTesting,
      bulkLoading,
      paymentMethods,
      currentPage,
      pageSize,
      total,
      searchForm,
      showAddDialog,
      showConfigDialog,
      showBulkOperationsDialog,
      editingPaymentMethod,
      selectedPaymentMethod,
      paymentForm,
      paymentFormRef,
      paymentRules,
      bulkForm,
      alipayConfig,
      wechatConfig,
      paypalConfig,
      stripeConfig,
      bankConfig,
      cryptoConfig,
      searchPaymentMethods,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      handleTypeChange,
      editPaymentMethod,
      savePaymentMethod,
      deletePaymentMethod,
      toggleStatus,
      viewConfig,
      saveConfig,
      testConfig,
      exportPaymentMethods,
      executeBulkOperation,
      getTypeTagType,
      getTypeText
    }
  }
}
</script>

<style scoped>
.admin-payment-methods {
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
}

.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.config-content {
  padding: 20px 0;
}

.config-content h4 {
  margin-bottom: 20px;
  color: #303133;
  border-bottom: 2px solid #409eff;
  padding-bottom: 10px;
}

.config-section {
  margin-bottom: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.config-actions {
  margin-top: 20px;
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
}
</style>
