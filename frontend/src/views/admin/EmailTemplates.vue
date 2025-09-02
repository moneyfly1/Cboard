<template>
  <div class="email-templates">
    <div class="page-header">
      <h1>邮件模板管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建模板
      </el-button>
    </div>

    <!-- 模板列表 -->
    <el-card class="template-list">
      <template #header>
        <div class="card-header">
          <span>邮件模板列表</span>
          <div class="header-actions">
            <el-button @click="refreshTemplates" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="templates" v-loading="loading" stripe>
        <el-table-column prop="name" label="模板名称" width="150" />
        <el-table-column prop="subject" label="邮件主题" min-width="200" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="previewTemplate(row)">
              <el-icon><View /></el-icon>
              预览
            </el-button>
            <el-button size="small" @click="testTemplate(row)">
              <el-icon><Message /></el-icon>
              测试
            </el-button>
            <el-button size="small" @click="editTemplate(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleTemplateStatus(row)"
            >
              <el-icon><Switch /></el-icon>
              {{ row.is_active ? '停用' : '激活' }}
            </el-button>
            <el-button size="small" @click="duplicateTemplate(row)">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteTemplate(row)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingTemplate ? '编辑模板' : '新建模板'"
      width="80%"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="templateFormRef" 
        :model="templateForm" 
        :rules="templateRules" 
        label-width="120px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="templateForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="邮件主题" prop="subject">
          <el-input v-model="templateForm.subject" placeholder="请输入邮件主题" />
        </el-form-item>
        <el-form-item label="模板内容" prop="content">
          <el-input 
            v-model="templateForm.content" 
            type="textarea" 
            :rows="15"
            placeholder="请输入HTML模板内容，支持Jinja2语法"
          />
        </el-form-item>
        <el-form-item label="模板变量" prop="variables">
          <el-input 
            v-model="templateForm.variables" 
            placeholder="请输入JSON格式的变量说明，如：['username', 'site_name']"
          />
          <div class="form-tip">变量说明：用于描述模板中可用的变量，JSON数组格式</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="templateForm.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTemplate" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览模板对话框 -->
    <el-dialog v-model="showPreviewDialog" title="模板预览" width="70%">
      <div class="preview-section">
        <h3>邮件主题</h3>
        <div class="preview-content">{{ previewData.subject }}</div>
        
        <h3>邮件内容</h3>
        <div class="preview-content" v-html="previewData.content"></div>
      </div>
    </el-dialog>

    <!-- 测试模板对话框 -->
    <el-dialog v-model="showTestDialog" title="测试模板" width="60%">
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="测试邮箱">
          <el-input v-model="testForm.test_email" placeholder="请输入测试邮箱地址" />
        </el-form-item>
        
        <el-form-item label="模板变量">
          <div v-for="variable in templateVariables" :key="variable" class="variable-input">
            <label>{{ variable }}:</label>
            <el-input v-model="testForm.variables[variable]" :placeholder="`请输入${variable}的值`" />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showTestDialog = false">取消</el-button>
        <el-button type="primary" @click="sendTestEmail" :loading="testing">
          发送测试邮件
        </el-button>
      </template>
    </el-dialog>

    <!-- 复制模板对话框 -->
    <el-dialog v-model="showDuplicateDialog" title="复制模板" width="40%">
      <el-form :model="duplicateForm" label-width="120px">
        <el-form-item label="新模板名称" prop="new_name">
          <el-input v-model="duplicateForm.new_name" placeholder="请输入新模板名称" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showDuplicateDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmDuplicate" :loading="duplicating">
          确认复制
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, View, Message, Edit, Switch, CopyDocument, Delete } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'

export default {
  name: 'EmailTemplates',
  components: {
    Plus, Refresh, View, Message, Edit, Switch, CopyDocument, Delete
  },
  setup() {
    const loading = ref(false)
    const saving = ref(false)
    const testing = ref(false)
    const duplicating = ref(false)
    
    const templates = ref([])
    const showCreateDialog = ref(false)
    const showPreviewDialog = ref(false)
    const showTestDialog = ref(false)
    const showDuplicateDialog = ref(false)
    
    const editingTemplate = ref(null)
    const previewData = ref({})
    const templateVariables = ref([])
    
    const templateForm = reactive({
      name: '',
      subject: '',
      content: '',
      variables: '',
      is_active: true
    })
    
    const testForm = reactive({
      test_email: '',
      variables: {}
    })
    
    const duplicateForm = reactive({
      new_name: ''
    })
    
    const templateRules = {
      name: [
        { required: true, message: '请输入模板名称', trigger: 'blur' },
        { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      subject: [
        { required: true, message: '请输入邮件主题', trigger: 'blur' }
      ],
      content: [
        { required: true, message: '请输入模板内容', trigger: 'blur' }
      ]
    }
    
    const templateFormRef = ref()
    
    // 获取模板列表
    const fetchTemplates = async () => {
      loading.value = true
      try {
        const response = await fetch('/api/v1/email-templates/')
        const data = await response.json()
        if (data.success) {
          templates.value = data.data.templates
        }
      } catch (error) {
        ElMessage.error('获取模板列表失败')
      } finally {
        loading.value = false
      }
    }
    
    // 刷新模板
    const refreshTemplates = () => {
      fetchTemplates()
    }
    
    // 预览模板
    const previewTemplate = async (template) => {
      try {
        const response = await fetch(`/api/v1/email-templates/${template.name}/preview`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            template_name: template.name,
            variables: {}
          })
        })
        const data = await response.json()
        if (data.success) {
          previewData.value = {
            subject: data.data.preview_subject,
            content: data.data.preview_content
          }
          showPreviewDialog.value = true
        }
      } catch (error) {
        ElMessage.error('预览模板失败')
      }
    }
    
    // 测试模板
    const testTemplate = (template) => {
      editingTemplate.value = template
      templateVariables.value = template.variables ? JSON.parse(template.variables) : []
      testForm.variables = {}
      templateVariables.value.forEach(variable => {
        testForm.variables[variable] = ''
      })
      showTestDialog.value = true
    }
    
    // 发送测试邮件
    const sendTestEmail = async () => {
      if (!testForm.test_email) {
        ElMessage.warning('请输入测试邮箱地址')
        return
      }
      
      testing.value = true
      try {
        const response = await fetch(`/api/v1/email-templates/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            template_name: editingTemplate.value.name,
            test_email: testForm.test_email,
            variables: testForm.variables
          })
        })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('测试邮件发送成功')
          showTestDialog.value = false
        } else {
          ElMessage.error(data.message || '发送失败')
        }
      } catch (error) {
        ElMessage.error('发送测试邮件失败')
      } finally {
        testing.value = false
      }
    }
    
    // 编辑模板
    const editTemplate = (template) => {
      editingTemplate.value = template
      Object.assign(templateForm, {
        name: template.name,
        subject: template.subject,
        content: template.content,
        variables: template.variables || '',
        is_active: template.is_active
      })
      showCreateDialog.value = true
    }
    
    // 保存模板
    const saveTemplate = async () => {
      try {
        await templateFormRef.value.validate()
        
        saving.value = true
        const url = editingTemplate.value 
          ? `/api/v1/email-templates/${editingTemplate.value.id}`
          : '/api/v1/email-templates/'
        
        const method = editingTemplate.value ? 'PUT' : 'POST'
        
        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(templateForm)
        })
        
        const data = await response.json()
        if (data.success) {
          ElMessage.success(editingTemplate.value ? '模板更新成功' : '模板创建成功')
          showCreateDialog.value = false
          editingTemplate.value = null
          resetTemplateForm()
          fetchTemplates()
        } else {
          ElMessage.error(data.message || '保存失败')
        }
      } catch (error) {
        console.error('保存模板失败:', error)
      } finally {
        saving.value = false
      }
    }
    
    // 切换模板状态
    const toggleTemplateStatus = async (template) => {
      try {
        const response = await fetch(`/api/v1/email-templates/${template.id}/toggle-status`, {
          method: 'POST'
        })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('模板状态更新成功')
          fetchTemplates()
        }
      } catch (error) {
        ElMessage.error('更新模板状态失败')
      }
    }
    
    // 复制模板
    const duplicateTemplate = (template) => {
      editingTemplate.value = template
      duplicateForm.new_name = `${template.name}_copy`
      showDuplicateDialog.value = true
    }
    
    // 确认复制
    const confirmDuplicate = async () => {
      if (!duplicateForm.new_name) {
        ElMessage.warning('请输入新模板名称')
        return
      }
      
      duplicating.value = true
      try {
        const response = await fetch(`/api/v1/email-templates/${editingTemplate.value.id}/duplicate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(duplicateForm)
        })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('模板复制成功')
          showDuplicateDialog.value = false
          editingTemplate.value = null
          duplicateForm.new_name = ''
          fetchTemplates()
        } else {
          ElMessage.error(data.message || '复制失败')
        }
      } catch (error) {
        ElMessage.error('复制模板失败')
      } finally {
        duplicating.value = false
      }
    }
    
    // 删除模板
    const deleteTemplate = async (template) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除模板 "${template.name}" 吗？此操作不可恢复。`,
          '确认删除',
          { type: 'warning' }
        )
        
        const response = await fetch(`/api/v1/email-templates/${template.id}`, {
          method: 'DELETE'
        })
        const data = await response.json()
        if (data.success) {
          ElMessage.success('模板删除成功')
          fetchTemplates()
        } else {
          ElMessage.error(data.message || '删除失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除模板失败')
        }
      }
    }
    
    // 重置表单
    const resetTemplateForm = () => {
      Object.assign(templateForm, {
        name: '',
        subject: '',
        content: '',
        variables: '',
        is_active: true
      })
      templateFormRef.value?.resetFields()
    }
    
    onMounted(() => {
      fetchTemplates()
    })
    
    return {
      loading,
      saving,
      testing,
      duplicating,
      templates,
      showCreateDialog,
      showPreviewDialog,
      showTestDialog,
      showDuplicateDialog,
      editingTemplate,
      previewData,
      templateVariables,
      templateForm,
      testForm,
      duplicateForm,
      templateRules,
      templateFormRef,
      formatDate,
      refreshTemplates,
      previewTemplate,
      testTemplate,
      sendTestEmail,
      editTemplate,
      saveTemplate,
      toggleTemplateStatus,
      duplicateTemplate,
      confirmDuplicate,
      deleteTemplate
    }
  }
}
</script>

<style scoped>
.email-templates {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.template-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-section h3 {
  margin: 20px 0 10px 0;
  color: #606266;
}

.preview-content {
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
  min-height: 60px;
}

.variable-input {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.variable-input label {
  width: 100px;
  margin-right: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
