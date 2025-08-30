<template>
  <div class="admin-settings">
    <el-card>
      <template #header>
        <span>系统设置</span>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本设置 -->
        <el-tab-pane label="基本设置" name="general">
          <el-form :model="generalSettings" :rules="generalRules" ref="generalFormRef" label-width="120px">
            <el-form-item label="网站名称" prop="site_name">
              <el-input v-model="generalSettings.site_name" />
            </el-form-item>
            <el-form-item label="网站描述" prop="site_description">
              <el-input v-model="generalSettings.site_description" type="textarea" />
            </el-form-item>
            <el-form-item label="网站Logo">
              <el-upload
                class="avatar-uploader"
                :action="uploadUrl"
                :show-file-list="false"
                :on-success="handleLogoSuccess"
                :before-upload="beforeLogoUpload"
              >
                <img v-if="generalSettings.site_logo" :src="generalSettings.site_logo" class="avatar" />
                <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
              </el-upload>
            </el-form-item>
            <el-form-item label="默认主题" prop="default_theme">
              <el-select v-model="generalSettings.default_theme">
                <el-option label="默认主题" value="default" />
                <el-option label="暗色主题" value="dark" />
                <el-option label="蓝色主题" value="blue" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveGeneralSettings">保存基本设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 注册设置 -->
        <el-tab-pane label="注册设置" name="registration">
          <el-form :model="registrationSettings" label-width="120px">
            <el-form-item label="开放注册">
              <el-switch v-model="registrationSettings.registration_enabled" />
            </el-form-item>
            <el-form-item label="邮箱验证">
              <el-switch v-model="registrationSettings.email_verification_required" />
            </el-form-item>
            <el-form-item label="最小密码长度" prop="min_password_length">
              <el-input-number v-model="registrationSettings.min_password_length" :min="6" :max="20" />
            </el-form-item>
            <el-form-item label="邀请码注册">
              <el-switch v-model="registrationSettings.invite_code_required" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveRegistrationSettings">保存注册设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 邮件设置 -->
        <el-tab-pane label="邮件设置" name="email">
          <el-form :model="emailSettings" :rules="emailRules" ref="emailFormRef" label-width="120px">
            <el-form-item label="SMTP服务器" prop="smtp_host">
              <el-input v-model="emailSettings.smtp_host" />
            </el-form-item>
            <el-form-item label="SMTP端口" prop="smtp_port">
              <el-input-number v-model="emailSettings.smtp_port" />
            </el-form-item>
            <el-form-item label="邮箱地址" prop="smtp_user">
              <el-input v-model="emailSettings.smtp_user" />
            </el-form-item>
            <el-form-item label="邮箱密码" prop="smtp_password">
              <el-input v-model="emailSettings.smtp_password" type="password" />
            </el-form-item>
            <el-form-item label="启用TLS">
              <el-switch v-model="emailSettings.smtp_tls" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveEmailSettings">保存邮件设置</el-button>
              <el-button @click="testEmail">测试邮件</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 支付设置 -->
        <el-tab-pane label="支付设置" name="payment">
          <el-form :model="paymentSettings" label-width="120px">
            <el-form-item label="启用支付">
              <el-switch v-model="paymentSettings.payment_enabled" />
            </el-form-item>
            <el-form-item label="默认支付方式" prop="default_payment_method">
              <el-select v-model="paymentSettings.default_payment_method">
                <el-option label="支付宝" value="alipay" />
                <el-option label="微信支付" value="wechat" />
                <el-option label="PayPal" value="paypal" />
              </el-select>
            </el-form-item>
            <el-form-item label="货币单位" prop="currency">
              <el-select v-model="paymentSettings.currency">
                <el-option label="人民币 (CNY)" value="CNY" />
                <el-option label="美元 (USD)" value="USD" />
                <el-option label="欧元 (EUR)" value="EUR" />
              </el-select>
            </el-form-item>
            
            <!-- 支付宝设置 -->
            <el-divider content-position="left">支付宝设置</el-divider>
            <el-form-item label="支付宝AppID" prop="alipay_app_id">
              <el-input v-model="paymentSettings.alipay_app_id" />
            </el-form-item>
            <el-form-item label="支付宝私钥" prop="alipay_private_key">
              <el-input v-model="paymentSettings.alipay_private_key" type="textarea" rows="4" />
            </el-form-item>
            <el-form-item label="支付宝公钥" prop="alipay_public_key">
              <el-input v-model="paymentSettings.alipay_public_key" type="textarea" rows="4" />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="savePaymentSettings">保存支付设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 通知设置 -->
        <el-tab-pane label="通知设置" name="notification">
          <el-form :model="notificationSettings" label-width="120px">
            <el-form-item label="系统通知">
              <el-switch v-model="notificationSettings.system_notifications" />
            </el-form-item>
            <el-form-item label="邮件通知">
              <el-switch v-model="notificationSettings.email_notifications" />
            </el-form-item>
            <el-form-item label="订阅到期提醒">
              <el-switch v-model="notificationSettings.subscription_expiry_notifications" />
            </el-form-item>
            <el-form-item label="新用户注册通知">
              <el-switch v-model="notificationSettings.new_user_notifications" />
            </el-form-item>
            <el-form-item label="新订单通知">
              <el-switch v-model="notificationSettings.new_order_notifications" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveNotificationSettings">保存通知设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 安全设置 -->
        <el-tab-pane label="安全设置" name="security">
          <el-form :model="securitySettings" label-width="120px">
            <el-form-item label="登录失败限制" prop="login_fail_limit">
              <el-input-number v-model="securitySettings.login_fail_limit" :min="3" :max="10" />
            </el-form-item>
            <el-form-item label="登录失败锁定时间(分钟)" prop="login_lock_time">
              <el-input-number v-model="securitySettings.login_lock_time" :min="5" :max="60" />
            </el-form-item>
            <el-form-item label="会话超时时间(分钟)" prop="session_timeout">
              <el-input-number v-model="securitySettings.session_timeout" :min="15" :max="1440" />
            </el-form-item>
            <el-form-item label="启用设备指纹">
              <el-switch v-model="securitySettings.device_fingerprint_enabled" />
            </el-form-item>
            <el-form-item label="启用IP白名单">
              <el-switch v-model="securitySettings.ip_whitelist_enabled" />
            </el-form-item>
            <el-form-item label="IP白名单" v-if="securitySettings.ip_whitelist_enabled">
              <el-input v-model="securitySettings.ip_whitelist" type="textarea" rows="3" placeholder="每行一个IP地址" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSecuritySettings">保存安全设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useApi } from '@/utils/api'

export default {
  name: 'AdminSettings',
  components: {
    Plus
  },
  setup() {
    const api = useApi()
    const activeTab = ref('general')
    const generalFormRef = ref()
    const emailFormRef = ref()
    const uploadUrl = '/api/v1/admin/upload'

    // 基本设置
    const generalSettings = reactive({
      site_name: '',
      site_description: '',
      site_logo: '',
      default_theme: 'default'
    })

    const generalRules = {
      site_name: [
        { required: true, message: '请输入网站名称', trigger: 'blur' }
      ]
    }

    // 注册设置
    const registrationSettings = reactive({
      registration_enabled: true,
      email_verification_required: true,
      min_password_length: 8,
      invite_code_required: false
    })

    // 邮件设置
    const emailSettings = reactive({
      smtp_host: '',
      smtp_port: 587,
      smtp_user: '',
      smtp_password: '',
      smtp_tls: true
    })

    const emailRules = {
      smtp_host: [
        { required: true, message: '请输入SMTP服务器', trigger: 'blur' }
      ],
      smtp_user: [
        { required: true, message: '请输入邮箱地址', trigger: 'blur' }
      ]
    }

    // 支付设置
    const paymentSettings = reactive({
      payment_enabled: true,
      default_payment_method: 'alipay',
      currency: 'CNY',
      alipay_app_id: '',
      alipay_private_key: '',
      alipay_public_key: ''
    })

    // 通知设置
    const notificationSettings = reactive({
      system_notifications: true,
      email_notifications: true,
      subscription_expiry_notifications: true,
      new_user_notifications: true,
      new_order_notifications: true
    })

    // 安全设置
    const securitySettings = reactive({
      login_fail_limit: 5,
      login_lock_time: 30,
      session_timeout: 120,
      device_fingerprint_enabled: true,
      ip_whitelist_enabled: false,
      ip_whitelist: ''
    })

    const loadSettings = async () => {
      try {
        const response = await api.get('/admin/settings')
        const settings = response.data
        
        // 加载各项设置
        Object.assign(generalSettings, settings.general || {})
        Object.assign(registrationSettings, settings.registration || {})
        Object.assign(emailSettings, settings.email || {})
        Object.assign(paymentSettings, settings.payment || {})
        Object.assign(notificationSettings, settings.notification || {})
        Object.assign(securitySettings, settings.security || {})
      } catch (error) {
        ElMessage.error('加载设置失败')
      }
    }

    const saveGeneralSettings = async () => {
      try {
        await generalFormRef.value.validate()
        await api.put('/admin/settings/general', generalSettings)
        ElMessage.success('基本设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const saveRegistrationSettings = async () => {
      try {
        await api.put('/admin/settings/registration', registrationSettings)
        ElMessage.success('注册设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const saveEmailSettings = async () => {
      try {
        await emailFormRef.value.validate()
        await api.put('/admin/settings/email', emailSettings)
        ElMessage.success('邮件设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const savePaymentSettings = async () => {
      try {
        await api.put('/admin/settings/payment', paymentSettings)
        ElMessage.success('支付设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const saveNotificationSettings = async () => {
      try {
        await api.put('/admin/settings/notification', notificationSettings)
        ElMessage.success('通知设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const saveSecuritySettings = async () => {
      try {
        await api.put('/admin/settings/security', securitySettings)
        ElMessage.success('安全设置保存成功')
      } catch (error) {
        ElMessage.error('保存失败')
      }
    }

    const testEmail = async () => {
      try {
        await api.post('/admin/settings/test-email', emailSettings)
        ElMessage.success('测试邮件发送成功')
      } catch (error) {
        ElMessage.error('测试邮件发送失败')
      }
    }

    const handleLogoSuccess = (response) => {
      generalSettings.site_logo = response.url
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

    onMounted(() => {
      loadSettings()
    })

    return {
      activeTab,
      generalSettings,
      generalRules,
      registrationSettings,
      emailSettings,
      emailRules,
      paymentSettings,
      notificationSettings,
      securitySettings,
      generalFormRef,
      emailFormRef,
      uploadUrl,
      saveGeneralSettings,
      saveRegistrationSettings,
      saveEmailSettings,
      savePaymentSettings,
      saveNotificationSettings,
      saveSecuritySettings,
      testEmail,
      handleLogoSuccess,
      beforeLogoUpload
    }
  }
}
</script>

<style scoped>
.admin-settings {
  padding: 20px;
}

.avatar-uploader {
  text-align: center;
}

.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  display: block;
}

.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  text-align: center;
  line-height: 100px;
}
</style> 