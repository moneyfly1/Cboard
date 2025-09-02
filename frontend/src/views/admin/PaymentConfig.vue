<template>
  <div class="admin-payment-config">
    <el-card>
      <template #header>
        <div class="header-content">
          <span>支付配置管理</span>
          <div class="header-actions">
            <el-button type="success" @click="exportConfigs">
              <el-icon><Download /></el-icon>
              导出配置
            </el-button>
            <el-button type="warning" @click="showBulkOperationsDialog = true">
              <el-icon><Operation /></el-icon>
              批量操作
            </el-button>
            <el-button type="info" @click="showStatisticsDialog = true">
              <el-icon><DataAnalysis /></el-icon>
              配置统计
            </el-button>
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><Plus /></el-icon>
              添加支付配置
            </el-button>
          </div>
        </div>
      </template>

      <!-- 支付配置列表 -->
      <el-table :data="paymentConfigs" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="pay_type" label="支付类型" width="120">
          <template #default="scope">
            <el-tag :type="getTypeTagType(scope.row.pay_type)">
              {{ getTypeText(scope.row.pay_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="app_id" label="应用ID" min-width="200">
          <template #default="scope">
            <span v-if="scope.row.app_id">{{ scope.row.app_id }}</span>
            <span v-else class="text-muted">未配置</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="1"
              :inactive-value="0"
              @change="toggleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editConfig(scope.row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteConfig(scope.row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑支付配置对话框 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingConfig ? '编辑支付配置' : '添加支付配置'"
      width="600px"
    >
      <el-form :model="configForm" label-width="120px">
        <el-form-item label="支付类型">
          <el-select v-model="configForm.pay_type" placeholder="选择支付类型">
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
            <el-option label="PayPal" value="paypal" />
          </el-select>
        </el-form-item>

        <el-form-item label="应用ID" v-if="configForm.pay_type === 'alipay' || configForm.pay_type === 'wechat'">
          <el-input v-model="configForm.app_id" placeholder="请输入应用ID" />
        </el-form-item>

        <el-form-item label="商户私钥" v-if="configForm.pay_type === 'alipay'">
          <el-input
            v-model="configForm.merchant_private_key"
            type="textarea"
            :rows="4"
            placeholder="请输入商户私钥"
          />
        </el-form-item>

        <el-form-item label="同步回调地址">
          <el-input v-model="configForm.return_url" placeholder="请输入同步回调地址" />
        </el-form-item>

        <el-form-item label="异步回调地址">
          <el-input v-model="configForm.notify_url" placeholder="请输入异步回调地址" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="configForm.status" placeholder="选择状态">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            {{ editingConfig ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Operation, Plus } from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminPaymentConfig',
  components: { Download, Operation, Plus },
  setup() {
    const api = useApi()
    const loading = ref(false)
    const saving = ref(false)
    const paymentConfigs = ref([])
    const showAddDialog = ref(false)
    const showBulkOperationsDialog = ref(false)
    const showStatisticsDialog = ref(false)
    const editingConfig = ref(null)

    const configForm = reactive({
      pay_type: '',
      app_id: '',
      merchant_private_key: '',
      return_url: '',
      notify_url: '',
      status: 1
    })

    const loadPaymentConfigs = async () => {
      loading.value = true
      try {
        const response = await api.get('/payment-config')
        paymentConfigs.value = response.data.items
      } catch (error) {
        ElMessage.error('加载支付配置列表失败')
      } finally {
        loading.value = false
      }
    }

    const saveConfig = async () => {
      saving.value = true
      try {
        if (editingConfig.value) {
          await api.put(`/payment-config/${editingConfig.value.id}`, configForm)
          ElMessage.success('支付配置更新成功')
        } else {
          await api.post('/payment-config', configForm)
          ElMessage.success('支付配置创建成功')
        }

        showAddDialog.value = false
        resetConfigForm()
        loadPaymentConfigs()
      } catch (error) {
        ElMessage.error('操作失败')
      } finally {
        saving.value = false
      }
    }

    const editConfig = (config) => {
      editingConfig.value = config
      Object.assign(configForm, config)
      showAddDialog.value = true
    }

    const deleteConfig = async (config) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除支付配置 "${config.pay_type}" 吗？`,
          '确认删除',
          { type: 'warning' }
        )
        await api.delete(`/payment-config/${config.id}`)
        ElMessage.success('支付配置删除成功')
        loadPaymentConfigs()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const toggleStatus = async (config) => {
      try {
        const newStatus = config.status === 1 ? 0 : 1
        await api.put(`/payment-config/${config.id}/status`, { status: newStatus })
        ElMessage.success(`支付配置${newStatus === 1 ? '启用' : '禁用'}成功`)
      } catch (error) {
        ElMessage.error('状态更新失败')
        config.status = config.status === 1 ? 0 : 1
      }
    }

    const resetConfigForm = () => {
      Object.assign(configForm, {
        pay_type: '',
        app_id: '',
        merchant_private_key: '',
        return_url: '',
        notify_url: '',
        status: 1
      })
    }

    const getTypeText = (type) => {
      const typeMap = {
        'alipay': '支付宝',
        'wechat': '微信支付',
        'paypal': 'PayPal'
      }
      return typeMap[type] || type
    }

    const getTypeTagType = (type) => {
      const typeMap = {
        'alipay': 'success',
        'wechat': 'primary',
        'paypal': 'warning'
      }
      return typeMap[type] || 'info'
    }

    const exportConfigs = () => {
      ElMessage.info('导出功能开发中')
    }

    onMounted(() => {
      loadPaymentConfigs()
    })

    return {
      loading,
      saving,
      paymentConfigs,
      showAddDialog,
      showBulkOperationsDialog,
      showStatisticsDialog,
      editingConfig,
      configForm,
      loadPaymentConfigs,
      saveConfig,
      editConfig,
      deleteConfig,
      toggleStatus,
      resetConfigForm,
      getTypeText,
      getTypeTagType,
      exportConfigs
    }
  }
}
</script>

<style scoped>
.admin-payment-config {
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

.text-muted {
  color: #909399;
  font-style: italic;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>