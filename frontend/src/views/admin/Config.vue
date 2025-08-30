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
        </el-tab-pane>

        <!-- 邮件配置 -->
        <el-tab-pane label="邮件配置" name="email">
          <el-form
            ref="emailFormRef"
            :model="emailForm"
            label-width="120px"
          >
            <el-form-item label="SMTP服务器">
              <el-input v-model="emailForm.smtp_host" placeholder="例如: smtp.qq.com" />
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
            
            <el-form-item>
              <el-button type="primary" @click="saveEmailConfig" :loading="emailLoading">
                保存邮件配置
              </el-button>
              <el-button type="success" @click="testEmail" :loading="testLoading">
                测试邮件发送
              </el-button>
            </el-form-item>
          </el-form>
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
              :action="uploadUrl"
              :on-success="handleConfigImport"
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
import { configAPI } from '@/utils/api'

export default {
  name: 'AdminConfig',
  components: {
    Plus
  },
  setup() {
    const activeTab = ref('system')
    const systemFormRef = ref()
    const emailFormRef = ref()
    
    const systemLoading = ref(false)
    const clashLoading = ref(false)
    const v2rayLoading = ref(false)
    const emailLoading = ref(false)
    const testLoading = ref(false)
    
    const clashConfig = ref('')
    const v2rayConfig = ref('')
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
      sender_name: ''
    })

    // 保存系统配置
    const saveSystemConfig = async () => {
      systemLoading.value = true
      try {
        await configAPI.saveSystemConfig(systemForm)
        ElMessage.success('系统配置保存成功')
      } catch (error) {
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

    // 保存邮件配置
    const saveEmailConfig = async () => {
      emailLoading.value = true
      try {
        await configAPI.saveEmailConfig(emailForm)
        ElMessage.success('邮件配置保存成功')
      } catch (error) {
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

    // 加载配置
    const loadClashConfig = async () => {
      try {
        const response = await configAPI.getClashConfig()
        clashConfig.value = response.data
      } catch (error) {
        ElMessage.error('加载配置失败')
      }
    }

    const loadV2rayConfig = async () => {
      try {
        const response = await configAPI.getV2rayConfig()
        v2rayConfig.value = response.data
      } catch (error) {
        ElMessage.error('加载配置失败')
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

    const handleConfigImport = (response) => {
      ElMessage.success('配置导入成功')
      // 重新加载配置
      loadSystemConfig()
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
        Object.assign(systemForm, response.data)
      } catch (error) {
        console.error('加载系统配置失败:', error)
      }
    }

    // 加载邮件配置
    const loadEmailConfig = async () => {
      try {
        const response = await configAPI.getEmailConfig()
        Object.assign(emailForm, response.data)
      } catch (error) {
        console.error('加载邮件配置失败:', error)
      }
    }

    onMounted(() => {
      loadSystemConfig()
      loadEmailConfig()
      loadClashConfig()
      loadV2rayConfig()
    })

    return {
      activeTab,
      systemFormRef,
      emailFormRef,
      systemLoading,
      clashLoading,
      v2rayLoading,
      emailLoading,
      testLoading,
      systemForm,
      emailForm,
      clashConfig,
      v2rayConfig,
      backupHistory,
      uploadUrl,
      saveSystemConfig,
      saveClashConfig,
      saveV2rayConfig,
      saveEmailConfig,
      testEmail,
      loadClashConfig,
      loadV2rayConfig,
      exportConfig,
      handleLogoSuccess,
      beforeLogoUpload,
      handleConfigImport,
      beforeConfigUpload
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
}
</style> 