<template>
  <div class="section">
    <div class="section-header">
      <h2 class="section-title">农业算法管理 - 服务ID: {{ containerId }}</h2>
      <div class="operation-buttons">
        <el-button type="primary" @click="addAlgorithm1">接入农业算法</el-button>
        <el-button type="success" @click="getRunLogs">获取运行日志</el-button>
        <el-button type="warning" @click="getRunningTasks">获取运行任务</el-button>
      </div>
    </div>
    
    <div class="search-area">
      <el-input
        v-model="algorithmSearch"
        placeholder="搜索农业算法名称或类型"
        clearable
        style="width: 300px"
      >
        <template #append>
          <el-button :icon="SearchIcon" @click="searchAlgorithms" />
        </template>
      </el-input>
    </div>
    
    <div class="data-table">
      <el-table :data="filteredAlgorithms" stripe style="width:100%" v-loading="loading">
        <el-table-column prop="algo_name" label="农业算法名称" width="180" />
        <el-table-column prop="type" label="算法类型" width="120" />
        <el-table-column prop="version" label="版本" width="100" />
        <el-table-column prop="intro" label="描述" />
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="editAlgorithm(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteAlgorithm(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="algorithmCurrentPage"
        v-model:page-size="algorithmPageSize"
        :page-sizes="[5, 10, 20]"
        :total="algorithms.length"
        layout="total, sizes, prev, pager, next"
      />
    </div>
    
    <!-- 运行日志显示区域 -->
    <div v-if="showLogs" class="log-container">
      <div class="log-header">
        <h3>运行日志</h3>
        <el-button type="primary" size="small" @click="getRunLogs">刷新日志</el-button>
      </div>
      <div class="log-content">
        <div v-if="logsLoading" class="loading">加载中...</div>
        <div v-else-if="logs.length === 0" class="no-data">暂无日志数据</div>
        <div v-else v-for="(log, index) in logs" :key="index" class="log-line">{{ log }}</div>
      </div>
    </div>
    
    <!-- 运行任务显示区域 -->
    <div v-if="showTasks" class="log-container">
      <div class="log-header">
        <h3>运行中的任务</h3>
        <el-button type="primary" size="small" @click="getRunningTasks">刷新任务</el-button>
      </div>
      <div class="task-list">
        <div v-if="tasksLoading" class="loading">加载中...</div>
        <div v-else-if="runningTasks.length === 0" class="no-data">暂无运行中的任务</div>
        <div v-else v-for="task in runningTasks" :key="task.id" class="task-item">
          <div class="task-info">
            <div class="task-name">{{ task.name || '未命名任务' }}</div>
            <div class="task-id">任务ID: {{ task.id }}</div>
          </div>
          <div class="task-progress">
            <el-progress :percentage="task.progress || 0" />
          </div>
          <div class="task-status">
            <el-tag :type="getStatusType(task.status)">{{ task.status || '未知' }}</el-tag>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 算法编辑/添加对话框 -->
    <el-dialog
      v-model="algorithmDialogVisible"
      :title="isEditingAlgorithm ? '编辑农业算法' : '接入农业算法'"
      width="500px"
    >
      <el-form  ref="algorithmRef" :model="currentAlgorithm" label-width="100px">
        <el-form-item label="服务ID">
          <el-input v-model="currentAlgorithm.container_id" disabled />
        </el-form-item>
        <el-form-item label="农业算法名称" prop="algo_name" :rules="[{ required: true, message: '请输入农业算法名称', trigger: 'blur' }]">
          <el-input v-model="currentAlgorithm.algo_name" />
        </el-form-item>
        <el-form-item label="农业任务说明">
          <el-input v-model="currentAlgorithm.intro" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="算法程序文件" v-if="!isEditingAlgorithm" :rules="[{ required: !isEditingAlgorithm, message: '请上传算法程序文件', trigger: 'change' }]">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".py"
          >
            <el-button size="small" type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">请上传.py算法程序文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="algorithmDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveAlgorithm" :loading="saveLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed, nextTick, getCurrentInstance } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { addAlgorithm, getLog, getTasking, listAlgorithm,delAlgorithm } from '@/api/container/container'

const SearchIcon = {
  template: '<svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg" width="14" height="14"><path d="M909.6 854.5L649.9 594.8C690.2 542.7 712 479 712 412c0-80.2-31.3-155.4-87.9-212.1-56.6-56.7-132-87.9-212.1-87.9s-155.5 31.3-212.1 87.9C143.2 256.5 112 331.8 112 412c0 80.1 31.3 155.5 87.9 212.1C256.5 680.8 331.8 712 412 712c67 0 130.6-21.8 182.7-62l259.7 259.6a8.2 8.2 0 0 0 11.6 0l43.6-43.5a8.2 8.2 0 0 0 0-11.6zM570.4 570.4C528 612.7 471.8 636 412 636s-116-23.3-158.4-65.6C211.3 528 188 471.8 188 412s23.3-116.1 65.6-158.4C296 211.3 352.2 188 412 188s116.1 23.2 158.4 65.6S636 352.2 636 412s-23.3 116.1-65.6 158.4z" fill="currentColor"></path></svg>'
}

export default {
  name: 'AlgorithmManagement',
  props: {
    containerId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const { proxy } = getCurrentInstance();
 
    const algorithms = ref([])
    const loading = ref(false)
    const saveLoading = ref(false)
    const algorithmSearch = ref('')
    const algorithmCurrentPage = ref(1)
    const algorithmPageSize = ref(5)
    const algorithmDialogVisible = ref(false)
    const isEditingAlgorithm = ref(false)
    const currentAlgorithm = ref({
      algo_name: '',
      intro: '',
      container_id: props.containerId,
      args_intro: '{}',
      args: '()',
      file: null
    })

    const uploadRef = ref(null)
    const algorithmRef = ref(null)
    const showLogs = ref(false)
    const showTasks = ref(false)
    const logs = ref([])
    const runningTasks = ref([])
    const logsLoading = ref(false)
    const tasksLoading = ref(false)
    
    
    
    const filteredAlgorithms = computed(() => {
      let result = Array.isArray(algorithms.value) ? algorithms.value : []
    
      if (algorithmSearch.value) {
        const search = algorithmSearch.value.toLowerCase()
        result = result.filter(item => 
          item && item.algo_name && item.algo_name.toLowerCase().includes(search) || 
          item && item.type && item.type.toLowerCase().includes(search)
        )
      }

      const start = (algorithmCurrentPage.value - 1) * algorithmPageSize.value
      const end = start + algorithmPageSize.value
      return result.slice(start, end)
    })
    
    onMounted(() => {
      getList();
    });

    watch(() => props.containerId, (newVal, oldVal) => {
      if (newVal !== oldVal) {
        getList();
      }
    });
    
    const handleFileChange = (file) => {
      if (file.raw && !file.raw.name.endsWith('.py')) {
        ElMessage.error('只能上传.py文件')
        uploadRef.value.clearFiles()
        return
      }
      currentAlgorithm.value.file = file.raw
    }
    
    const handleFileRemove = () => {
      currentAlgorithm.value.file = null
    }
    
    // 算法操作方法
    const addAlgorithm1 = () => {
      currentAlgorithm.value = {
        algo_name: '',
        intro: '',
        container_id: props.containerId,
        args_intro: '{}',
        args: '()',
        file: null
      }
      isEditingAlgorithm.value = false
      algorithmDialogVisible.value = true
      nextTick(() => {
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
        if (algorithmRef.value) {
          algorithmRef.value.clearValidate()
        }
      })
    }
    
  const editAlgorithm = (algorithm) => {
      currentAlgorithm.value = { 
        ...algorithm,
        file: null 
      }
      isEditingAlgorithm.value = true
      algorithmDialogVisible.value = true
      nextTick(() => {
        if (uploadRef.value) {
          uploadRef.value.clearFiles()
        }
      })
    }
    
    const deleteAlgorithm = (algorithm) => {
  ElMessageBox.confirm(
    `确定要删除算法 "${algorithm.algo_name}" 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    delAlgorithm(props.containerId, algorithm.algo_name).then(response => {
      console.log('删除算法成功:', response)
      ElMessage.success('删除成功')
      getList() 
    }).catch(error => {
      console.error('删除失败:', error)
      ElMessage.error('删除失败: ' + (error.response?.data?.message || error.message))
    })
  }).catch(() => {
  })
}
    
/** 查询算法列表 */
function getList() {
  console.log('开始获取算法列表，containerId:', props.containerId)
  loading.value = true
  listAlgorithm(props.containerId).then(response => {
    console.log('完整响应:', response)
    console.log('响应数据:', response.data)

    if (response && response.data && typeof response.data === 'object') {

      const algorithmsArray = Object.entries(response.data).map(([algo_name, algoInfo]) => {
        return {
          id: algo_name, 
          algo_name: algo_name,
          type: '农业分析算法', 
          version: '1.0', 
          intro: algoInfo.intro || '',
          args_intro: algoInfo.args_intro || '{}',
          args: algoInfo.args || '()',
          container_id: props.containerId
        }
      })
      
      algorithms.value = algorithmsArray
      console.log('转换后的算法数组:', algorithms.value)
    } else {
      algorithms.value = []
      console.warn('响应数据格式异常:', response)
    }
    
    loading.value = false
  }).catch(error => {
    console.error('获取农业算法列表失败:', error)
    loading.value = false
    ElMessage.error('获取农业算法列表失败')
  })
  
}
const saveAlgorithm = async () => {
  if (!algorithmRef.value) return
  
  try {
    const valid = await algorithmRef.value.validate()
    if (!valid) return
    
    if (!currentAlgorithm.value.algo_name) {
      ElMessage.error('请输入农业算法名称')
      return
    }
    
    if (!isEditingAlgorithm.value && !currentAlgorithm.value.file) {
      ElMessage.error('请上传算法程序文件')
      return
    }
    
    saveLoading.value = true
    
    if (isEditingAlgorithm.value) {
      const index =algorithms.value.findIndex(a => a.id === currentAlgorithm.value.id)
          if (index !== -1) {
            algorithms.value[index] = { 
              ... algorithms.value[index],
              ...currentAlgorithm.value
            }
          }
          ElMessage.success('模型更新成功')
           algorithmDialogVisible.value = false
          
    } else {
      const formData = new FormData()
      formData.append('algo_name', currentAlgorithm.value.algo_name)
      formData.append('intro', currentAlgorithm.value.intro || '')
      formData.append('container_id', props.containerId.toString())
      formData.append('args_intro', currentAlgorithm.value.args_intro || '{}')
      formData.append('args', currentAlgorithm.value.args || '()')
      if (currentAlgorithm.value.file) {
        formData.append('file', currentAlgorithm.value.file)
      }
      
      console.log('开始上传算法，数据:', {
        algo_name: currentAlgorithm.value.algo_name,
        container_id: props.containerId
      })
      
      addAlgorithm(formData).then(response => {
        console.log('上传算法成功，响应:', response)
        ElMessage.success("上传成功")
        algorithmDialogVisible.value = false
        
        // 强制重新获取数据
        setTimeout(() => {
          console.log('重新获取列表...')
          getList()
        }, 500)
        
      }).catch(error => {
        console.error("上传错误:", error)
        if (error.response?.data?.detail) {
          ElMessage.error("上传失败: " + JSON.stringify(error.response.data.detail))
        } else {
          ElMessage.error("上传失败: " + (error.response?.data?.message || error.message))
        }
      }).finally(() => {
        saveLoading.value = false
      })
    }
  } catch (error) {
    console.error('表单验证失败:', error)
    saveLoading.value = false
  }
}
    const searchAlgorithms = () => {
      algorithmCurrentPage.value = 1
    }
    
   // 获取运行日志 
const getRunLogs = async () => {
  showLogs.value = true
  showTasks.value = false
  logsLoading.value = true
  
  try {
    const response = await getLog(props.containerId)
    console.log('日志响应数据:', response) 
    if (response && response.logs !== undefined) {
      if (typeof response.logs === 'string') {
        if (response.logs.trim() === '') {
          logs.value = ['暂无日志内容']
        } else {
          logs.value = response.logs.split('\n')
        }
      } else {
        logs.value = ['日志格式异常: ' + JSON.stringify(response.logs)]
      }
    } else if (response && response.data && response.data.logs !== undefined) {
      if (typeof response.data.logs === 'string') {
        if (response.data.logs.trim() === '') {
          logs.value = ['暂无日志内容']
        } else {
          logs.value = response.data.logs.split('\n')
        }
      } else {
        logs.value = ['日志格式异常: ' + JSON.stringify(response.data.logs)]
      }
    } else {
      logs.value = ['无法解析日志数据: ' + JSON.stringify(response)]
    }
    
    ElMessage.success('运行日志获取成功')
  } catch (error) {
    console.error('获取运行日志失败:', error)
    ElMessage.error('获取运行日志失败')
    logs.value = ['获取日志失败: ' + (error.response?.data?.message || error.message || '未知错误')]
  } finally {
    logsLoading.value = false
  }
}

    // 获取运行任务 
    const getRunningTasks = async () => {
      showTasks.value = true
      showLogs.value = false
      tasksLoading.value = true
      
      try {
        const response = await getTasking(props.containerId)
        if (Array.isArray(response)) {
          runningTasks.value = response
        } else if (response.data && Array.isArray(response.data)) {
          runningTasks.value = response.data
        } else {
          runningTasks.value = [response]
        }
        ElMessage.success('运行任务获取成功')
      } catch (error) {
        console.error('获取运行任务失败:', error)
        ElMessage.error('获取运行任务失败')
        runningTasks.value = []
      } finally {
        tasksLoading.value = false
      }
    }

    const getStatusType = (status) => {
      const statusMap = {
        '运行中': 'warning',
        '已完成': 'success',
        '失败': 'danger',
        '等待中': 'info'
      }
      return statusMap[status] || 'info'
    }
    
    return {
      algorithms,
      algorithmSearch,
      algorithmCurrentPage,
      algorithmPageSize,
      algorithmDialogVisible,
      isEditingAlgorithm,
      currentAlgorithm,
      showLogs,
      showTasks,
      logs,
      runningTasks,
      logsLoading,
      tasksLoading,
      loading,
      saveLoading,
      filteredAlgorithms,
      uploadRef,
      algorithmRef,
      addAlgorithm1,
      editAlgorithm,
      deleteAlgorithm,
      saveAlgorithm,
      searchAlgorithms,
      getRunLogs,
      getRunningTasks,
      handleFileChange,
      handleFileRemove,
      getStatusType,
      SearchIcon
    }
  }
}
</script>

<style scoped>
.section {
  flex: 1;
  background:rgba(6,29,47,.92);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(90, 205, 237, 0.14);
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.operation-buttons {
  display: flex;
  gap: 10px;
}

.search-area {
  margin-bottom: 15px;
}

.data-table {
  flex: 1;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: flex-end;
}

.log-container {
  margin-top: 20px;
  border-top: 1px solid rgba(90, 205, 237, 0.14);
  padding-top: 15px;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.log-content {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 10px;
}

.log-line {
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-all;
}

.task-list {
  margin-top: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid rgba(90, 205, 237, 0.14);
  border-radius: 4px;
  margin-bottom: 8px;
  background-color:rgba(5,24,40,.86);
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.task-id {
  font-size: 12px;
  color: #909399;
}

.task-progress {
  flex: 2;
  margin: 0 20px;
}

.loading {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.no-data {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
