<template>
  <div class="packages-admin-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>套餐管理</h2>
          <el-button type="primary" @click="showAddDialog">
            <i class="el-icon-plus"></i>
            添加套餐
          </el-button>
        </div>
      </template>

      <!-- 搜索和筛选 -->
      <div class="search-section">
        <el-form :inline="true" :model="searchForm">
          <el-form-item label="套餐名称">
            <el-input
              v-model="searchForm.name"
              placeholder="搜索套餐名称"
              clearable
            />
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
              <el-option label="启用" value="active" />
              <el-option label="禁用" value="inactive" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleSearch">
              <i class="el-icon-search"></i>
              搜索
            </el-button>
            <el-button @click="resetSearch">
              <i class="el-icon-refresh"></i>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 套餐列表 -->
      <el-table
        :data="packages"
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="套餐名称" />
        <el-table-column prop="price" label="价格">
          <template #default="{ row }">
            ¥{{ row.price }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_days" label="时长">
          <template #default="{ row }">
            {{ row.duration_days }} 天
          </template>
        </el-table-column>
        <el-table-column prop="device_limit" label="设备限制" />
        <el-table-column prop="is_recommended" label="推荐">
          <template #default="{ row }">
            <el-tag :type="row.is_recommended ? 'success' : 'info'">
              {{ row.is_recommended ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="editPackage(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="deletePackage(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑套餐对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑套餐' : '添加套餐'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="套餐名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入套餐名称" />
        </el-form-item>
        
        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="form.price"
            :min="0"
            :precision="2"
            :step="0.01"
            placeholder="请输入价格"
          />
        </el-form-item>
        
        <el-form-item label="时长(天)" prop="duration_days">
          <el-input-number
            v-model="form.duration_days"
            :min="1"
            :precision="0"
            placeholder="请输入时长"
          />
        </el-form-item>
        
        <el-form-item label="设备限制" prop="device_limit">
          <el-input-number
            v-model="form.device_limit"
            :min="1"
            :precision="0"
            placeholder="请输入设备限制"
          />
        </el-form-item>
        
        <el-form-item label="推荐套餐" prop="is_recommended">
          <el-switch v-model="form.is_recommended" />
        </el-form-item>
        
        <el-form-item label="状态" prop="is_active">
          <el-select v-model="form.is_active" placeholder="选择状态">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入套餐描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitLoading"
          >
            {{ isEdit ? '更新' : '添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '@/utils/api'

export default {
  name: 'AdminPackages',
  setup() {
    const loading = ref(false)
    const submitLoading = ref(false)
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const formRef = ref()
    const packages = ref([])

    const searchForm = reactive({
      name: '',
      status: ''
    })

    const pagination = reactive({
      page: 1,
      size: 20,
      total: 0
    })

    const form = reactive({
      name: '',
      price: 0,
      duration_days: 30,
      device_limit: 1,
      is_recommended: false,
      is_active: true,
      description: ''
    })

    const rules = {
      name: [
        { required: true, message: '请输入套餐名称', trigger: 'blur' }
      ],
      price: [
        { required: true, message: '请输入价格', trigger: 'blur' }
      ],
      duration_days: [
        { required: true, message: '请输入时长', trigger: 'blur' }
      ],
      device_limit: [
        { required: true, message: '请输入设备限制', trigger: 'blur' }
      ],
      is_active: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }

    // 获取套餐列表
    const fetchPackages = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          size: pagination.size,
          ...searchForm
        }
        const response = await adminAPI.getPackages(params)
        console.log('套餐API响应:', response)
        console.log('套餐响应数据结构:', response.data)
        packages.value = response.data.data?.packages || response.data.items || []
        pagination.total = response.data.data?.total || response.data.total || 0
      } catch (error) {
        ElMessage.error('获取套餐列表失败')
        console.error('获取套餐列表失败:', error)
      } finally {
        loading.value = false
      }
    }

    // 搜索
    const handleSearch = () => {
      pagination.page = 1
      fetchPackages()
    }

    // 重置搜索
    const resetSearch = () => {
      Object.assign(searchForm, {
        name: '',
        status: ''
      })
      pagination.page = 1
      fetchPackages()
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pagination.size = size
      pagination.page = 1
      fetchPackages()
    }

    const handleCurrentChange = (page) => {
      pagination.page = page
      fetchPackages()
    }

    // 显示添加对话框
    const showAddDialog = () => {
      isEdit.value = false
      resetForm()
      dialogVisible.value = true
    }

    // 编辑套餐
    const editPackage = (packageData) => {
      isEdit.value = true
      Object.assign(form, packageData)
      dialogVisible.value = true
    }

    // 重置表单
    const resetForm = () => {
      Object.assign(form, {
        name: '',
        price: 0,
        duration_days: 30,
        device_limit: 1,
        is_recommended: false,
        is_active: true,
        description: ''
      })
      if (formRef.value) {
        formRef.value.resetFields()
      }
    }

    // 提交表单
    const handleSubmit = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        submitLoading.value = true

        if (isEdit.value) {
          await adminAPI.updatePackage(form.id, form)
          ElMessage.success('套餐更新成功')
        } else {
          await adminAPI.createPackage(form)
          ElMessage.success('套餐添加成功')
        }

        dialogVisible.value = false
        fetchPackages()
      } catch (error) {
        if (error.response?.data?.message) {
          ElMessage.error(error.response.data.message)
        } else {
          ElMessage.error('操作失败')
        }
      } finally {
        submitLoading.value = false
      }
    }

    // 删除套餐
    const deletePackage = async (id) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这个套餐吗？',
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await adminAPI.deletePackage(id)
        ElMessage.success('套餐删除成功')
        fetchPackages()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
          console.error('删除套餐失败:', error)
        }
      }
    }

    onMounted(() => {
      fetchPackages()
    })

    return {
      loading,
      submitLoading,
      dialogVisible,
      isEdit,
      formRef,
      packages,
      searchForm,
      pagination,
      form,
      rules,
      handleSearch,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      showAddDialog,
      editPackage,
      handleSubmit,
      deletePackage
    }
  }
}
</script>

<style scoped>
.packages-admin-container {
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

.search-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.pagination-section {
  margin-top: 20px;
  text-align: right;
}

@media (max-width: 768px) {
  .packages-admin-container {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .search-section .el-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .search-section .el-form-item {
    margin-bottom: 0;
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