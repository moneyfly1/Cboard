<template>
  <div class="config-update-test">
    <h2>配置更新测试页面</h2>
    
    <div class="test-section">
      <h3>API测试</h3>
      <button @click="testAPI">测试API调用</button>
      <button @click="testDirectAPI">测试直接API调用</button>
      <div v-if="testResult" class="result">
        <pre>{{ testResult }}</pre>
      </div>
    </div>
    
    <div class="test-section">
      <h3>状态信息</h3>
      <button @click="getStatus">获取状态</button>
      <div v-if="statusResult" class="result">
        <pre>{{ statusResult }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

export default {
  name: 'ConfigUpdateTest',
  setup() {
    const testResult = ref('')
    const statusResult = ref('')
    
    const testAPI = async () => {
      try {
        // 测试adminAPI导入
        const { adminAPI } = await import('@/utils/api')
        console.log('adminAPI对象:', adminAPI)
        console.log('startConfigUpdate方法:', adminAPI.startConfigUpdate)
        
        if (typeof adminAPI.startConfigUpdate === 'function') {
          const response = await adminAPI.startConfigUpdate()
          testResult.value = JSON.stringify(response.data, null, 2)
          ElMessage.success('API调用成功')
        } else {
          testResult.value = 'adminAPI.startConfigUpdate 不是一个函数'
          ElMessage.error('API方法不存在')
        }
      } catch (error) {
        testResult.value = `错误: ${error.message}`
        ElMessage.error('API调用失败')
      }
    }
    
    const testDirectAPI = async () => {
      try {
        const response = await api.post('/admin/config-update/start')
        testResult.value = JSON.stringify(response.data, null, 2)
        ElMessage.success('直接API调用成功')
      } catch (error) {
        testResult.value = `错误: ${error.message}`
        ElMessage.error('直接API调用失败')
      }
    }
    
    const getStatus = async () => {
      try {
        const response = await api.get('/admin/config-update/status')
        statusResult.value = JSON.stringify(response.data, null, 2)
        ElMessage.success('状态获取成功')
      } catch (error) {
        statusResult.value = `错误: ${error.message}`
        ElMessage.error('状态获取失败')
      }
    }
    
    return {
      testResult,
      statusResult,
      testAPI,
      testDirectAPI,
      getStatus
    }
  }
}
</script>

<style scoped>
.config-update-test {
  padding: 20px;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.result {
  margin-top: 10px;
  padding: 10px;
  background-color: #f5f5f5;
  border-radius: 3px;
  max-height: 300px;
  overflow-y: auto;
}

button {
  margin-right: 10px;
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

button:hover {
  background-color: #66b1ff;
}
</style>
