<template>
  <div class="config-admin-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>配置管理</h2>
          <p>管理系统配置文件和节点配置</p>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 系统配置 -->
        <el-tab-pane label="系统配置" name="system">
          <el-form
            ref="systemFormRef"
            :model="systemForm"
            label-width="120px"
          >
            <el-form-item label="网站名称">
              <el-input v-model="systemForm.site_name" />
            </el-form-item>
            
            <el-form-item label="网站描述">
              <el-input
                v-model="systemForm.site_description"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            
            <el-form-item label="网站Logo">
              <el-upload
                class="avatar-uploader"
                :action="uploadUrl"
                :show-file-list="false"
                :on-success="handleLogoSuccess"
                :before-upload="beforeLogoUpload"
              >
                <img v-if="systemForm.logo_url" :src="systemForm.logo_url" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </el-form-item>
            
            <el-form-item label="维护模式">
              <el-switch v-model="systemForm.maintenance_mode" />
            </el-form-item>
            
            <el-form-item label="维护信息">
              <el-input
                v-model="systemForm.maintenance_message"
                type="textarea"
                :rows="3"
                :disabled="!systemForm.maintenance_mode"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveSystemConfig" :loading="systemLoading">
                保存系统配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 软件下载配置 -->
        <el-tab-pane label="软件下载配置" name="software">
          <div class="config-section">
            <h3>软件下载链接配置</h3>
            <el-form
              ref="softwareFormRef"
              :model="softwareForm"
              label-width="150px"
            >
              <!-- Windows软件 -->
              <el-divider content-position="left">Windows 软件</el-divider>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Clash for Windows">
                    <el-input v-model="softwareForm.clash_windows_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="V2rayN">
                    <el-input v-model="softwareForm.v2rayn_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Mihomo Part">
                    <el-input v-model="softwareForm.mihomo_windows_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Sparkle">
                    <el-input v-model="softwareForm.sparkle_windows_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Hiddify">
                    <el-input v-model="softwareForm.hiddify_windows_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Flash">
                    <el-input v-model="softwareForm.flash_windows_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <!-- Android软件 -->
              <el-divider content-position="left">Android 软件</el-divider>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Clash Meta">
                    <el-input v-model="softwareForm.clash_android_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="V2rayNG">
                    <el-input v-model="softwareForm.v2rayng_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Hiddify">
                    <el-input v-model="softwareForm.hiddify_android_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <!-- 占位，保持布局 -->
                </el-col>
              </el-row>
              
              <!-- macOS软件 -->
              <el-divider content-position="left">macOS 软件</el-divider>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Flash">
                    <el-input v-model="softwareForm.flash_macos_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="Mihomo Part">
                    <el-input v-model="softwareForm.mihomo_macos_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Sparkle">
                    <el-input v-model="softwareForm.sparkle_macos_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <!-- 占位，保持布局 -->
                </el-col>
              </el-row>
              
              <!-- iOS软件 -->
              <el-divider content-position="left">iOS 软件</el-divider>
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="Shadowrocket">
                    <el-input v-model="softwareForm.shadowrocket_url" placeholder="请输入下载链接" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <!-- 占位，保持布局 -->
                </el-col>
              </el-row>
              
              <el-form-item>
                <el-button type="primary" @click="saveSoftwareConfig" :loading="softwareLoading">
                  保存软件配置
                </el-button>
                <el-button @click="loadSoftwareConfig">
                  重新加载
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 节点配置 -->
        <el-tab-pane label="节点配置" name="nodes">
          <div class="config-section">
            <h3>Clash 配置</h3>
            <el-form>
              <el-form-item label="配置文件">
                <el-input
                  v-model="clashConfig"
                  type="textarea"
                  :rows="15"
                  placeholder="请输入Clash配置文件内容"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveClashConfig" :loading="clashLoading">
                  保存Clash配置
                </el-button>
                <el-button @click="loadClashConfig">
                  加载当前配置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="config-section">
            <h3>V2Ray 配置</h3>
            <el-form>
              <el-form-item label="配置文件">
                <el-input
                  v-model="v2rayConfig"
                  type="textarea"
                  :rows="15"
                  placeholder="请输入V2Ray配置文件内容"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveV2rayConfig" :loading="v2rayLoading">
                  保存V2Ray配置
                </el-button>
                <el-button @click="loadV2rayConfig">
                  加载当前配置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="config-section">
            <h3>Clash 失效配置</h3>
            <el-form>
              <el-form-item label="失效配置文件">
                <el-input
                  v-model="clashConfigInvalid"
                  type="textarea"
                  :rows="10"
                  placeholder="请输入Clash失效配置文件内容（用于无效用户）"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveClashConfigInvalid" :loading="clashInvalidLoading">
                  保存Clash失效配置
                </el-button>
                <el-button @click="loadClashConfigInvalid">
                  加载当前失效配置
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <div class="config-section">
            <h3>V2Ray 失效配置</h3>
            <el-form>
              <el-form-item label="失效配置文件">
                <el-input
                  v-model="v2rayConfigInvalid"
                  type="textarea"
                  :rows="10"
                  placeholder="请输入V2Ray失效配置文件内容（用于无效用户）"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="saveV2rayConfigInvalid" :loading="v2rayInvalidLoading">
                  保存V2Ray失效配置
                </el-button>
                <el-button @click="loadV2rayConfigInvalid">
                  加载当前失效配置
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 邮件配置 -->
        <el-tab-pane label="邮件配置" name="email">
          <el-form
            ref="emailFormRef"
            :model="emailForm"
            label-width="120px"
          >
            <el-form-item label="SMTP服务器">
              <el-input v-model="emailForm.smtp_host" placeholder="例如: smtp.gmail.com" />
            </el-form-item>
            
            <el-form-item label="SMTP端口">
              <el-input-number v-model="emailForm.smtp_port" :min="1" :max="65535" />
            </el-form-item>
            
            <el-form-item label="邮箱账号">
              <el-input v-model="emailForm.email_username" placeholder="邮箱地址" />
            </el-form-item>
            
            <el-form-item label="邮箱密码">
              <el-input
                v-model="emailForm.email_password"
                type="password"
                placeholder="邮箱密码或授权码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="发件人名称">
              <el-input v-model="emailForm.sender_name" placeholder="发件人显示名称" />
            </el-form-item>
            
            <el-form-item label="加密方式">
              <el-select v-model="emailForm.smtp_encryption" placeholder="选择加密方式">
                <el-option label="TLS (推荐)" value="tls" />
                <el-option label="SSL" value="ssl" />
                <el-option label="无加密" value="none" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="发件人邮箱">
              <el-input v-model="emailForm.from_email" placeholder="发件人邮箱地址" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveEmailConfig" :loading="emailLoading">
                保存邮件配置
              </el-button>
              <el-button type="success" @click="testEmail" :loading="testLoading">
                测试邮件发送
              </el-button>
              <el-button type="warning" @click="testEmailToUser" :loading="testUserLoading">
                发送测试邮件给用户
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>


        <!-- 支付设置 -->
        <el-tab-pane label="支付设置" name="payment">
          <div class="payment-settings-section">
            <div class="section-header">
              <h3>支付配置管理</h3>
              <div class="header-actions">
                <el-button type="primary" @click="savePaymentSettings" :loading="paymentLoading">
                  保存支付设置
                </el-button>
                <el-button @click="testPaymentConfig" :loading="testPaymentLoading">
                  测试配置
                </el-button>
              </div>
            </div>
            
            <el-form :model="paymentForm" label-width="120px" class="payment-form">
              <!-- Basic Settings -->
              <el-divider content-position="left">基本设置</el-divider>
              <el-form-item label="启用支付">
                <el-switch v-model="paymentForm.payment_enabled" />
              </el-form-item>
              <el-form-item label="默认支付方式">
                <el-select v-model="paymentForm.default_payment_method" placeholder="选择默认支付方式">
                  <el-option label="支付宝" value="alipay" />
                  <el-option label="微信支付" value="wechat" />
                  <el-option label="PayPal" value="paypal" />
                  <el-option label="Stripe" value="stripe" />
                  <el-option label="银行转账" value="bank_transfer" />
                </el-select>
              </el-form-item>
              <el-form-item label="货币单位">
                <el-select v-model="paymentForm.currency">
                  <el-option label="人民币 (CNY)" value="CNY" />
                  <el-option label="美元 (USD)" value="USD" />
                  <el-option label="欧元 (EUR)" value="EUR" />
                </el-select>
              </el-form-item>

              <!-- Alipay Config -->
              <el-divider content-position="left" v-if="paymentForm.default_payment_method === 'alipay'">支付宝配置</el-divider>
              <template v-if="paymentForm.default_payment_method === 'alipay'">
                <el-form-item label="支付宝AppID" prop="alipay_app_id">
                  <el-input v-model="paymentForm.alipay_app_id" placeholder="请输入支付宝AppID" />
                </el-form-item>
                <el-form-item label="支付宝私钥" prop="alipay_private_key">
                  <el-input v-model="paymentForm.alipay_private_key" type="textarea" :rows="4" placeholder="请输入支付宝商户私钥" />
                </el-form-item>
                <el-form-item label="支付宝公钥" prop="alipay_public_key">
                  <el-input v-model="paymentForm.alipay_public_key" type="textarea" :rows="4" placeholder="请输入支付宝公钥" />
                </el-form-item>
                <el-form-item label="支付宝网关">
                  <el-input v-model="paymentForm.alipay_gateway" placeholder="https://openapi.alipay.com/gateway.do" />
                </el-form-item>
              </template>

              <!-- WeChat Pay Config -->
              <el-divider content-position="left" v-if="paymentForm.default_payment_method === 'wechat'">微信支付配置</el-divider>
              <template v-if="paymentForm.default_payment_method === 'wechat'">
                <el-form-item label="微信AppID" prop="wechat_app_id">
                  <el-input v-model="paymentForm.wechat_app_id" placeholder="请输入微信AppID" />
                </el-form-item>
                <el-form-item label="微信商户号" prop="wechat_mch_id">
                  <el-input v-model="paymentForm.wechat_mch_id" placeholder="请输入微信商户号" />
                </el-form-item>
                <el-form-item label="微信API密钥" prop="wechat_api_key">
                  <el-input v-model="paymentForm.wechat_api_key" type="password" placeholder="请输入微信API密钥" show-password />
                </el-form-item>
                <el-form-item label="微信证书路径">
                  <el-input v-model="paymentForm.wechat_cert_path" placeholder="请输入微信证书文件路径" />
                </el-form-item>
                <el-form-item label="微信私钥路径">
                  <el-input v-model="paymentForm.wechat_key_path" placeholder="请输入微信私钥文件路径" />
                </el-form-item>
              </template>

              <!-- PayPal Config -->
              <el-divider content-position="left" v-if="paymentForm.default_payment_method === 'paypal'">PayPal配置</el-divider>
              <template v-if="paymentForm.default_payment_method === 'paypal'">
                <el-form-item label="PayPal客户端ID" prop="paypal_client_id">
                  <el-input v-model="paymentForm.paypal_client_id" placeholder="请输入PayPal客户端ID" />
                </el-form-item>
                <el-form-item label="PayPal密钥" prop="paypal_secret">
                  <el-input v-model="paymentForm.paypal_secret" type="password" placeholder="请输入PayPal密钥" show-password />
                </el-form-item>
                <el-form-item label="PayPal模式">
                  <el-select v-model="paymentForm.paypal_mode">
                    <el-option label="沙箱模式" value="sandbox" />
                    <el-option label="生产模式" value="live" />
                  </el-select>
                </el-form-item>
              </template>

              <!-- Stripe Config -->
              <el-divider content-position="left" v-if="paymentForm.default_payment_method === 'stripe'">Stripe配置</el-divider>
              <template v-if="paymentForm.default_payment_method === 'stripe'">
                <el-form-item label="Stripe发布密钥" prop="stripe_publishable_key">
                  <el-input v-model="paymentForm.stripe_publishable_key" placeholder="请输入Stripe发布密钥" />
                </el-form-item>
                <el-form-item label="Stripe密钥" prop="stripe_secret_key">
                  <el-input v-model="paymentForm.stripe_secret_key" type="password" placeholder="请输入Stripe密钥" show-password />
                </el-form-item>
                <el-form-item label="Stripe Webhook密钥">
                  <el-input v-model="paymentForm.stripe_webhook_secret" type="password" placeholder="请输入Stripe Webhook密钥" show-password />
                </el-form-item>
              </template>

              <!-- Bank Transfer Config -->
              <el-divider content-position="left" v-if="paymentForm.default_payment_method === 'bank_transfer'">银行转账配置</el-divider>
              <template v-if="paymentForm.default_payment_method === 'bank_transfer'">
                <el-form-item label="银行名称" prop="bank_name">
                  <el-input v-model="paymentForm.bank_name" placeholder="请输入银行名称" />
                </el-form-item>
                <el-form-item label="银行账号" prop="bank_account">
                  <el-input v-model="paymentForm.bank_account" placeholder="请输入银行账号" />
                </el-form-item>
                <el-form-item label="开户行" prop="bank_branch">
                  <el-input v-model="paymentForm.bank_branch" placeholder="请输入开户行" />
                </el-form-item>
                <el-form-item label="收款人姓名" prop="account_holder">
                  <el-input v-model="paymentForm.account_holder" placeholder="请输入收款人姓名" />
                </el-form-item>
              </template>

              <!-- Callback URLs -->
              <el-divider content-position="left">回调地址设置</el-divider>
              <el-form-item label="同步回调地址">
                <el-input v-model="paymentForm.return_url" placeholder="请输入同步回调地址" />
              </el-form-item>
              <el-form-item label="异步回调地址">
                <el-input v-model="paymentForm.notify_url" placeholder="请输入异步回调地址" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 备份恢复 -->
        <el-tab-pane label="备份恢复" name="backup">
          <div class="backup-section">
            <h3>配置备份</h3>
            <el-button type="primary" @click="exportConfig">
              <i class="el-icon-download"></i>
              导出配置
            </el-button>
            
            <el-upload
              class="upload-demo"
              :auto-upload="false"
              :on-change="handleConfigImport"
              :before-upload="beforeConfigUpload"
              accept=".json"
            >
              <el-button type="success">
                <i class="el-icon-upload"></i>
                导入配置
              </el-button>
            </el-upload>
          </div>

          <div class="backup-section">
            <h3>备份历史</h3>
            <el-table :data="backupHistory" style="width: 100%">
              <el-table-column prop="filename" label="文件名" />
              <el-table-column prop="created_at" label="创建时间" />
              <el-table-column prop="size" label="文件大小" />
              <el-table-column label="操作" width="200">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    @click="downloadBackup(row.filename)"
                  >
                    下载
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    @click="deleteBackup(row.filename)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { configAPI, softwareConfigAPI } from '@/utils/api'
import { adminAPI } from '@/utils/api'
import { useRouter } from 'vue-router'

export default {
  name: 'AdminConfig',
  components: {
    Plus
  },
  setup() {
    const activeTab = ref('system')
    const systemFormRef = ref()
    const emailFormRef = ref()
    const softwareFormRef = ref()
    
    const systemLoading = ref(false)
    const clashLoading = ref(false)
    const v2rayLoading = ref(false)
    const clashInvalidLoading = ref(false)
    const v2rayInvalidLoading = ref(false)
    const emailLoading = ref(false)
    const testLoading = ref(false)
    const testUserLoading = ref(false)
    const paymentLoading = ref(false)
    const testPaymentLoading = ref(false)
    const softwareLoading = ref(false)
    
    const clashConfig = ref('')
    const v2rayConfig = ref('')
    const clashConfigInvalid = ref('')
    const v2rayConfigInvalid = ref('')
    const backupHistory = ref([])
    
    const uploadUrl = '/api/admin/upload'

    const systemForm = reactive({
      site_name: '',
      site_description: '',
      logo_url: '',
      maintenance_mode: false,
      maintenance_message: ''
    })

    const emailForm = reactive({
      smtp_host: '',
      smtp_port: 587,
      email_username: '',
      email_password: '',
      sender_name: '',
      smtp_encryption: 'tls',
      from_email: ''
    })

    const paymentForm = reactive({
      payment_enabled: false,
      default_payment_method: 'alipay',
      currency: 'CNY',
      // 支付宝配置
      alipay_app_id: '',
      alipay_private_key: '',
      alipay_public_key: '',
      alipay_gateway: 'https://openapi.alipay.com/gateway.do',
      // 微信支付配置
      wechat_app_id: '',
      wechat_mch_id: '',
      wechat_api_key: '',
      wechat_cert_path: '',
      wechat_key_path: '',
      // PayPal配置
      paypal_client_id: '',
      paypal_secret: '',
      paypal_mode: 'sandbox',
      // Stripe配置
      stripe_publishable_key: '',
      stripe_secret_key: '',
      stripe_webhook_secret: '',
      // 银行转账配置
      bank_name: '',
      bank_account: '',
      bank_branch: '',
      account_holder: '',
      // 回调地址
      return_url: '',
      notify_url: ''
    })

    const softwareForm = reactive({
      // Windows软件
      clash_windows_url: '',
      v2rayn_url: '',
      mihomo_windows_url: '',
      sparkle_windows_url: '',
      hiddify_windows_url: '',
      flash_windows_url: '',
      
      // Android软件
      clash_android_url: '',
      v2rayng_url: '',
      hiddify_android_url: '',
      
      // macOS软件
      flash_macos_url: '',
      mihomo_macos_url: '',
      sparkle_macos_url: '',
      
      // iOS软件
      shadowrocket_url: ''
    })


    const router = useRouter()

    // 保存系统配置
    const saveSystemConfig = async () => {
      systemLoading.value = true
      try {
        await configAPI.saveSystemConfig(systemForm)
        ElMessage.success('系统配置保存成功')
        // 重新加载配置以确保数据同步
        await loadSystemConfig()
      } catch (error) {
        console.error('保存系统配置失败:', error)
        ElMessage.error('保存失败')
      } finally {
        systemLoading.value = false
      }
    }

    // 保存Clash配置
    const saveClashConfig = async () => {
      clashLoading.value = true
      try {
        await configAPI.saveClashConfig(clashConfig.value)
        ElMessage.success('Clash配置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        clashLoading.value = false
      }
    }

    // 保存V2Ray配置
    const saveV2rayConfig = async () => {
      v2rayLoading.value = true
      try {
        await configAPI.saveV2rayConfig(v2rayConfig.value)
        ElMessage.success('V2Ray配置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        v2rayLoading.value = false
      }
    }

    // 保存软件配置
    const saveSoftwareConfig = async () => {
      softwareLoading.value = true
      try {
        await softwareConfigAPI.updateSoftwareConfig(softwareForm)
        ElMessage.success('软件配置保存成功')
      } catch (error) {
        console.error('保存软件配置失败:', error)
        ElMessage.error('保存失败')
      } finally {
        softwareLoading.value = false
      }
    }

    // 加载软件配置
    const loadSoftwareConfig = async () => {
      try {
        const response = await softwareConfigAPI.getSoftwareConfig()
        if (response.data && response.data.success) {
          // 后端返回的是ResponseBase格式，数据在response.data.data中
          Object.assign(softwareForm, response.data.data)
          ElMessage.success('软件配置加载成功')
        }
      } catch (error) {
        console.error('加载软件配置失败:', error)
        ElMessage.error('加载失败')
      }
    }

    // 保存邮件配置
    const saveEmailConfig = async () => {
      emailLoading.value = true
      try {
        // 准备邮件配置数据
        const emailConfigData = {
          smtp_host: emailForm.smtp_host,
          smtp_port: emailForm.smtp_port,
          email_username: emailForm.email_username,
          email_password: emailForm.email_password,
          sender_name: emailForm.sender_name,
          smtp_encryption: emailForm.smtp_encryption,
          from_email: emailForm.from_email
        }
        await configAPI.saveEmailConfig(emailConfigData)
        ElMessage.success('邮件配置保存成功')
        // 重新加载配置以确保数据同步
        await loadEmailConfig()
      } catch (error) {
        console.error('保存邮件配置失败:', error)
        ElMessage.error('保存失败')
      } finally {
        emailLoading.value = false
      }
    }

    // 测试邮件
    const testEmail = async () => {
      testLoading.value = true
      try {
        await configAPI.testEmail()
        ElMessage.success('测试邮件发送成功')
      } catch (error) {
        ElMessage.error('测试邮件发送失败')
      } finally {
        testLoading.value = false
      }
    }

    // 发送测试邮件给指定用户
    const testEmailToUser = async () => {
      testUserLoading.value = true
      try {
        const testEmail = '3219904322@qq.com'
        await configAPI.testEmailToUser(testEmail)
        ElMessage.success(`测试邮件已发送给 ${testEmail}`)
      } catch (error) {
        console.error('发送测试邮件失败:', error)
        ElMessage.error('发送测试邮件失败')
      } finally {
        testUserLoading.value = false
      }
    }

    // 加载配置
    const loadClashConfig = async () => {
      try {
        const response = await configAPI.getClashConfig()
        if (response.data && response.data.success) {
          clashConfig.value = response.data.data
        }
      } catch (error) {
        console.error('加载Clash配置失败:', error)
        ElMessage.error('加载Clash配置失败')
      }
    }

    const loadV2rayConfig = async () => {
      try {
        const response = await configAPI.getV2rayConfig()
        if (response.data && response.data.success) {
          v2rayConfig.value = response.data.data
        }
      } catch (error) {
        console.error('加载V2Ray配置失败:', error)
        ElMessage.error('加载V2Ray配置失败')
      }
    }

    // 保存Clash失效配置
    const saveClashConfigInvalid = async () => {
      clashInvalidLoading.value = true
      try {
        await configAPI.saveClashConfigInvalid(clashConfigInvalid.value)
        ElMessage.success('Clash失效配置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        clashInvalidLoading.value = false
      }
    }

    // 保存V2Ray失效配置
    const saveV2rayConfigInvalid = async () => {
      v2rayInvalidLoading.value = true
      try {
        await configAPI.saveV2rayConfigInvalid(v2rayConfigInvalid.value)
        ElMessage.success('V2Ray失效配置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      } finally {
        v2rayInvalidLoading.value = false
      }
    }

    // 加载Clash失效配置
    const loadClashConfigInvalid = async () => {
      try {
        const response = await configAPI.getClashConfigInvalid()
        if (response.data && response.data.success) {
          clashConfigInvalid.value = response.data.data
        }
      } catch (error) {
        console.error('加载Clash失效配置失败:', error)
        ElMessage.error('加载Clash失效配置失败')
      }
    }

    // 加载V2Ray失效配置
    const loadV2rayConfigInvalid = async () => {
      try {
        const response = await configAPI.getV2rayConfigInvalid()
        if (response.data && response.data.success) {
          v2rayConfigInvalid.value = response.data.data
        }
      } catch (error) {
        console.error('加载V2Ray失效配置失败:', error)
        ElMessage.error('加载V2Ray失效配置失败')
      }
    }

    // 导出配置
    const exportConfig = async () => {
      try {
        const response = await configAPI.exportConfig()
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json'
        })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `xboard-config-${new Date().toISOString().split('T')[0]}.json`
        a.click()
        window.URL.revokeObjectURL(url)
        ElMessage.success('配置导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
      }
    }

    // 文件上传处理
    const handleLogoSuccess = (response) => {
      systemForm.logo_url = response.data.url
      ElMessage.success('Logo上传成功')
    }

    const beforeLogoUpload = (file) => {
      const isImage = file.type.startsWith('image/')
      const isLt2M = file.size / 1024 / 1024 < 2

      if (!isImage) {
        ElMessage.error('只能上传图片文件!')
        return false
      }
      if (!isLt2M) {
        ElMessage.error('图片大小不能超过 2MB!')
        return false
      }
      return true
    }

    const handleConfigImport = async (file, fileList) => {
      try {
        // 读取文件内容
        const fileContent = await readFileContent(file.raw)
        const configData = JSON.parse(fileContent)
        
        // 调用导入API
        await configAPI.importConfig(configData)
        
        ElMessage.success('配置导入成功')
        
        // 重新加载所有配置
        await loadSystemConfig()
        await loadEmailConfig()
        await loadPaymentConfig()
        await loadSoftwareConfig()
        await loadClashConfig()
        await loadV2rayConfig()
        await loadClashConfigInvalid()
        await loadV2rayConfigInvalid()
      } catch (error) {
        console.error('导入配置失败:', error)
        ElMessage.error('导入配置失败: ' + (error.message || '未知错误'))
      }
    }
    
    // 读取文件内容的辅助函数
    const readFileContent = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => resolve(e.target.result)
        reader.onerror = (e) => reject(e)
        reader.readAsText(file)
      })
    }

    const beforeConfigUpload = (file) => {
      const isJSON = file.type === 'application/json'
      if (!isJSON) {
        ElMessage.error('只能上传JSON文件!')
        return false
      }
      return true
    }

    // 加载系统配置
    const loadSystemConfig = async () => {
      try {
        const response = await configAPI.getSystemConfig()
        if (response.data && response.data.success) {
          const configData = response.data.data
          Object.assign(systemForm, configData)
        }
      } catch (error) {
        console.error('加载系统配置失败:', error)
        ElMessage.error('加载系统配置失败')
      }
    }

    // 加载邮件配置
    const loadEmailConfig = async () => {
      try {
        const response = await configAPI.getEmailConfig()
        console.log('邮件配置响应:', response)
        if (response.data && response.data.success) {
          // 后端返回的是ResponseBase格式，数据在response.data.data中
          const configData = response.data.data
          // 映射字段名称
          emailForm.smtp_host = configData.smtp_host || ''
          emailForm.smtp_port = configData.smtp_port || 587
          emailForm.email_username = configData.email_username || configData.smtp_username || ''
          emailForm.email_password = configData.email_password || configData.smtp_password || ''
          emailForm.sender_name = configData.sender_name || ''
          emailForm.smtp_encryption = configData.smtp_encryption || 'tls'
          emailForm.from_email = configData.from_email || ''
          console.log('邮件配置已加载:', emailForm)
        }
      } catch (error) {
        console.error('加载邮件配置失败:', error)
        ElMessage.error('加载邮件配置失败')
      }
    }


    // 格式化日期
    const formatDate = (timestamp) => {
      const date = new Date(timestamp)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    }

    // 获取邮件状态标签类型
    const getEmailStatusTagType = (status) => {
      switch (status) {
        case 'pending':
          return 'info'
        case 'sending':
          return 'warning'
        case 'sent':
          return 'success'
        case 'failed':
          return 'danger'
        default:
          return 'info'
      }
    }

    // 获取邮件状态文本
    const getEmailStatusText = (status) => {
      switch (status) {
        case 'pending':
          return '待发送'
        case 'sending':
          return '发送中'
        case 'sent':
          return '已发送'
        case 'failed':
          return '发送失败'
        default:
          return status
      }
    }

    // 保存支付设置
    const savePaymentSettings = async () => {
      paymentLoading.value = true
      try {
        // 将前端字段名映射到后端配置键名
        const configData = {
          enable_payment: paymentForm.payment_enabled, // 映射到后端使用的键名
          default_payment_method: paymentForm.default_payment_method,
          currency: paymentForm.currency,
          alipay_app_id: paymentForm.alipay_app_id,
          alipay_private_key: paymentForm.alipay_private_key,
          alipay_public_key: paymentForm.alipay_public_key,
          alipay_gateway: paymentForm.alipay_gateway,
          wechat_app_id: paymentForm.wechat_app_id,
          wechat_mch_id: paymentForm.wechat_mch_id,
          wechat_api_key: paymentForm.wechat_api_key,
          wechat_cert_path: paymentForm.wechat_cert_path,
          wechat_key_path: paymentForm.wechat_key_path,
          paypal_client_id: paymentForm.paypal_client_id,
          paypal_secret: paymentForm.paypal_secret,
          paypal_mode: paymentForm.paypal_mode,
          stripe_publishable_key: paymentForm.stripe_publishable_key,
          stripe_secret_key: paymentForm.stripe_secret_key,
          stripe_webhook_secret: paymentForm.stripe_webhook_secret,
          bank_name: paymentForm.bank_name,
          bank_account: paymentForm.bank_account,
          bank_branch: paymentForm.bank_branch,
          account_holder: paymentForm.account_holder,
          return_url: paymentForm.return_url,
          notify_url: paymentForm.notify_url
        }
        
        await configAPI.savePaymentSettings(configData)
        ElMessage.success('支付设置保存成功')
        // 重新加载配置以确保数据同步
        await loadPaymentSettings()
      } catch (error) {
        console.error('保存支付设置失败:', error)
        ElMessage.error('保存支付设置失败')
      } finally {
        paymentLoading.value = false
      }
    }

    // 测试支付配置
    const testPaymentConfig = async () => {
      testPaymentLoading.value = true
      try {
        await configAPI.testPaymentConfig(paymentForm)
        ElMessage.success('支付配置测试成功')
      } catch (error) {
        ElMessage.error('支付配置测试失败')
      } finally {
        testPaymentLoading.value = false
      }
    }

    // 加载支付设置
    const loadPaymentSettings = async () => {
      try {
        const response = await configAPI.getPaymentSettings()
        if (response.data && response.data.success) {
          const configs = response.data.data.payment_configs || []
          configs.forEach(config => {
            if (config.key && config.value !== undefined) {
              // 映射配置键名到表单字段
              const fieldMapping = {
                'enable_payment': 'payment_enabled',
                'default_payment_method': 'default_payment_method',
                'currency': 'currency',
                'alipay_app_id': 'alipay_app_id',
                'alipay_private_key': 'alipay_private_key',
                'alipay_public_key': 'alipay_public_key',
                'alipay_gateway': 'alipay_gateway',
                'wechat_app_id': 'wechat_app_id',
                'wechat_mch_id': 'wechat_mch_id',
                'wechat_api_key': 'wechat_api_key',
                'wechat_cert_path': 'wechat_cert_path',
                'wechat_key_path': 'wechat_key_path',
                'paypal_client_id': 'paypal_client_id',
                'paypal_secret': 'paypal_secret',
                'paypal_mode': 'paypal_mode',
                'stripe_publishable_key': 'stripe_publishable_key',
                'stripe_secret_key': 'stripe_secret_key',
                'stripe_webhook_secret': 'stripe_webhook_secret',
                'bank_name': 'bank_name',
                'bank_account': 'bank_account',
                'bank_branch': 'bank_branch',
                'account_holder': 'account_holder',
                'return_url': 'return_url',
                'notify_url': 'notify_url'
              }
              
              if (fieldMapping[config.key]) {
                const fieldName = fieldMapping[config.key]
                // 根据字段名判断类型，而不是config.type
                if (fieldName === 'payment_enabled') {
                  // 确保布尔值正确处理，支持多种格式
                  paymentForm[fieldName] = config.value === 'true' || config.value === 'True' || config.value === true || config.value === 1
                } else if (fieldName === 'currency' || fieldName === 'default_payment_method') {
                  paymentForm[fieldName] = config.value
                } else {
                  paymentForm[fieldName] = config.value
                }
              }
            }
          })
          console.log('支付配置已加载:', paymentForm)
        }
      } catch (error) {
        console.error('加载支付设置失败:', error)
        ElMessage.error('加载支付设置失败')
      }
    }

    onMounted(() => {
      loadSystemConfig()
      loadEmailConfig()
      loadClashConfig()
      loadV2rayConfig()
      loadClashConfigInvalid()
      loadV2rayConfigInvalid()
      loadPaymentSettings()
      loadSoftwareConfig()
    })

    return {
      activeTab,
      systemFormRef,
      emailFormRef,
      systemLoading,
      clashLoading,
      v2rayLoading,
      clashInvalidLoading,
      v2rayInvalidLoading,
      emailLoading,
      testLoading,
      testUserLoading,
      paymentLoading,
      testPaymentLoading,
      softwareLoading,
      systemForm,
      emailForm,
      paymentForm,
      softwareForm,
      clashConfig,
      v2rayConfig,
      clashConfigInvalid,
      v2rayConfigInvalid,
      backupHistory,
      uploadUrl,
      saveSystemConfig,
      saveClashConfig,
      saveV2rayConfig,
      saveSoftwareConfig,
      loadSoftwareConfig,
      saveClashConfigInvalid,
      saveV2rayConfigInvalid,
      saveEmailConfig,
      testEmail,
      testEmailToUser,
      loadClashConfig,
      loadV2rayConfig,
      loadClashConfigInvalid,
      loadV2rayConfigInvalid,
      exportConfig,
      handleLogoSuccess,
      beforeLogoUpload,
      handleConfigImport,
      beforeConfigUpload,
      formatDate,
      savePaymentSettings,
      testPaymentConfig,
      loadPaymentSettings
    }
  }
}
</script>

<style scoped>
.config-admin-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.card-header p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.config-section {
  margin-bottom: 30px;
}

.config-section h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.avatar-uploader {
  text-align: center;
}

.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  border-radius: 6px;
}

.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-uploader .el-upload:hover {
  border-color: #409eff;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
}

.backup-section {
  margin-bottom: 30px;
}

.backup-section h3 {
  color: #333;
  margin-bottom: 20px;
  font-size: 1.2rem;
}

.backup-section .el-button {
  margin-right: 15px;
  margin-bottom: 15px;
}

.email-queue-section {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.queue-stats {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-number {
  font-size: 1.8rem;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
  margin-top: 5px;
}

.queue-filter {
  margin-bottom: 20px;
}

.pagination-wrapper {
  text-align: right;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .config-admin-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .backup-section .el-button {
  width: 100%;
    margin-right: 0;
  }

  .header-actions {
    flex-direction: column;
    gap: 10px;
  }
}

.payment-settings-section {
  padding: 20px;
}

.payment-form {
  max-width: 800px;
}

.payment-form .el-divider {
  margin: 30px 0 20px 0;
}

.payment-form .el-divider:first-child {
  margin-top: 0;
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