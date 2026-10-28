<template>
  <div class="app-container prescription-page">
    <AgriPageHeader
      title="水稻精准施药处方图"
      eyebrow="变量施药处方图生成"
      icon="Aim"
      description=""
    >
      <el-button icon="Plus" @click="plotDialogOpen = true">录入地块信息</el-button>
      <el-button type="primary" icon="UploadFilled" @click="triggerUpload">
        上传原始 TIFF
      </el-button>
      <input
        ref="fileInput"
        hidden
        type="file"
        accept=".tif,.tiff,.zip"
        @change="handleFile"
      />
    </AgriPageHeader>

    <section class="summary-grid">
      <article v-for="item in summaryCards" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}<small>{{ item.unit }}</small></strong>
        <p>{{ item.note }}</p>
      </article>
    </section>

    <el-card shadow="never" class="prescription-panel">
      <template #header>
        <div class="card-title">
          <span>处方图生成与结果展示</span>
          <el-tag type="success">VariablePrescriptionIntegratedAlgorithm</el-tag>
        </div>
      </template>

      <div class="stage-strip">
        <article
          v-for="stage in stages"
          :key="stage.key"
          :class="{ active: stage.key === processState, done: stage.done }"
        >
          <i>{{ stage.index }}</i>
          <div>
            <strong>{{ stage.title }}</strong>
            <span>{{ stage.note }}</span>
          </div>
        </article>
      </div>

      <div class="prescription-workbench">
        <section class="result-window">
          <div class="result-window-head">
            <div class="window-title">
              <span class="step-number">01</span>
              <div>
                <strong>病害热力图</strong>
                <small>GENERATED HEATMAP</small>
              </div>
            </div>
            <el-button
              v-if="selectedFile"
              link
              type="primary"
              icon="UploadFilled"
              @click="triggerUpload"
            >
              更换原始数据
            </el-button>
          </div>

          <div
            class="visual-stage image-viewer"
            :class="{ empty: !heatmapUrl, 'has-image': heatmapUrl, dragging: imageViews.heatmap.dragging }"
            @wheel.prevent="handleImageWheel('heatmap', $event)"
            @pointerdown="startImageDrag('heatmap', $event)"
            @pointermove="moveImageDrag('heatmap', $event)"
            @pointerup="endImageDrag('heatmap', $event)"
            @pointercancel="endImageDrag('heatmap', $event)"
            @pointerleave="endImageDrag('heatmap', $event)"
            @dblclick="resetImageView('heatmap')"
          >
            <img
              v-if="heatmapUrl"
              class="result-image"
              :src="heatmapUrl"
              :style="imageViewStyle('heatmap')"
              alt="变量施药热力图"
              draggable="false"
              @load="resetImageView('heatmap')"
              @dragstart.prevent
            />
            <div v-else class="stage-empty">
              <el-icon><Picture /></el-icon>
              <strong>{{ selectedFile ? '原始数据已上传，正在等待热力图结果' : '上传原始 GeoTIFF 数据' }}</strong>
              <span>{{ selectedFile ? selectedFile.name : '支持 .tif、.tiff，或包含 GeoTIFF 的 ZIP 数据包；上传后自动执行热力图和处方图生成流程' }}</span>
              <el-button type="primary" plain @click="triggerUpload">选择原始数据</el-button>
            </div>
          </div>

          <div class="window-footer">
            <span>{{ heatmapFileName || '算法第一步输出：病害热力图' }}</span>
            <small>{{ selectedFile ? `输入数据：${selectedFile.name}` : '等待本地数据' }}</small>
          </div>
        </section>

        <section class="result-window prescription-window">
          <div class="result-window-head">
            <div class="window-title">
              <span class="step-number">02</span>
              <div>
                <strong>施药处方图</strong>
                <small>PRESCRIPTION RESULT</small>
              </div>
            </div>
            <el-tag :type="stateTagType">{{ stateLabel }}</el-tag>
          </div>

          <div class="prescription-result">
            <div class="dose-legend">
              <strong>推荐药量（升/亩）</strong>
              <span>3.00</span>
              <div class="dose-bar"></div>
              <span>1.50</span>
            </div>
            <div
              class="visual-stage image-viewer prescription-image"
              :class="{ empty: !prescriptionUrl, 'has-image': prescriptionUrl, dragging: imageViews.prescription.dragging }"
              @wheel.prevent="handleImageWheel('prescription', $event)"
              @pointerdown="startImageDrag('prescription', $event)"
              @pointermove="moveImageDrag('prescription', $event)"
              @pointerup="endImageDrag('prescription', $event)"
              @pointercancel="endImageDrag('prescription', $event)"
              @pointerleave="endImageDrag('prescription', $event)"
              @dblclick="resetImageView('prescription')"
            >
              <img
                v-if="prescriptionUrl"
                class="result-image"
                :src="prescriptionUrl"
                :style="imageViewStyle('prescription')"
                alt="变量施药处方图"
                draggable="false"
                @load="resetImageView('prescription')"
                @dragstart.prevent
              />
              <div v-else class="stage-empty">
                <el-icon><Aim /></el-icon>
                <strong>{{ running ? '正在按顺序生成热力图和处方图' : '等待生成施药处方图' }}</strong>
                <span>{{ selectedFile ? '当前任务会先生成左侧热力图，再生成右侧处方图' : '请先上传原始 TIFF/ZIP 数据' }}</span>
              </div>
            </div>
          </div>

          <div class="result-metrics">
            <article>
              <el-icon><FirstAidKit /></el-icon>
              <span>主要病害</span>
              <strong>稻瘟病</strong>
            </article>
            <article>
              <el-icon><PieChart /></el-icon>
              <span>处方地块</span>
              <strong>{{ fieldCount }} 块</strong>
            </article>
            <article>
              <el-icon><SetUp /></el-icon>
              <span>推荐药量</span>
              <strong>{{ averageDose }} 升/亩</strong>
            </article>
            <article>
              <el-icon><CircleCheck /></el-icon>
              <span>生成完整率</span>
              <strong>{{ completionRate }}</strong>
            </article>
          </div>

          <div class="recommendation">
            <el-icon><Tickets /></el-icon>
            <span>{{ recommendation }}</span>
          </div>

          <el-button
            class="result-action"
            type="primary"
            :disabled="!selectedFile || running"
            @click="runPrescription"
          >
            {{ running ? '自动生成中' : selectedFile ? '重新生成热力图和处方图' : '上传原始数据后自动生成' }}
          </el-button>
        </section>
      </div>
    </el-card>

    <el-card shadow="never" class="records-panel">
      <template #header>
        <div class="card-title records-card-title">
          <span>处方图生成记录</span>
          <small>仅显示真实模型任务</small>
        </div>
      </template>
      <el-table
        :data="pagedRecords"
        class="prescription-record-table"
        table-layout="fixed"
        stripe
        empty-text="暂无变量施药处方图生成记录"
      >
        <el-table-column type="index" label="序号" width="72" align="center" :index="recordIndexMethod" />
        <el-table-column prop="date" label="生成时间" min-width="160" align="center" />
        <el-table-column prop="name" label="任务名称" min-width="260" />
        <el-table-column prop="algorithm" label="算法模型" min-width="230" align="center" />
        <el-table-column prop="fieldCount" label="处方地块" min-width="110" align="center" />
        <el-table-column prop="averageDose" label="平均药量" min-width="130" align="center" />
        <el-table-column prop="state" label="运行状态" min-width="120" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.state === 'success' ? 'success' : 'info'">
              {{ scope.row.state === 'success' ? '已完成' : scope.row.state }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="records-pagination">
        <el-pagination
          v-model:current-page="recordCurrentPage"
          :page-size="recordPageSize"
          :total="records.length"
          layout="total, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <el-dialog v-model="plotDialogOpen" title="录入地块信息" width="560px">
      <el-form :model="plotForm" label-width="100px">
        <el-form-item label="地块编号"><el-input v-model="plotForm.code" placeholder="如 A02" /></el-form-item>
        <el-form-item label="所属基地"><el-input v-model="plotForm.base" placeholder="如 海城实验基地" /></el-form-item>
        <el-form-item label="面积"><el-input v-model="plotForm.area" placeholder="如 12.8 亩" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="plotForm.note" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="plotDialogOpen = false">取消</el-button>
        <el-button type="primary" @click="savePlotInfo">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="VariablePrescription">
import AgriPageHeader from '@/components/AgriPageHeader'
import { addFileFile, down, listFile } from '@/api/file/file'
import { listAlgorithm, listContainer } from '@/api/container/container'
import { addTask, executeTask, getTask, listTask } from '@/api/task/task'

const { proxy } = getCurrentInstance()

const MODEL_NAME = 'variable_prescription_residual_liquidgate_gcn.pt'
const ALGORITHM_NAME = 'VariablePrescriptionIntegratedAlgorithm'
const TASK_REMARK = '变量施药处方图页面提交'

const fileInput = ref()
const selectedFile = ref(null)
const heatmapUrl = ref('')
const prescriptionUrl = ref('')
const heatmapFileName = ref('')
const prescriptionFileName = ref('')
const processState = ref('idle')
const running = ref(false)
const pollTimer = ref(null)
const objectUrls = ref([])
const fields = ref([])
const currentTaskId = ref(null)
const records = ref([])
const recordCurrentPage = ref(1)
const recordPageSize = 5
const plotDialogOpen = ref(false)
const plotForm = reactive({ code: '', base: '', area: '', note: '' })
const imageViews = reactive({
  heatmap: { scale: 1, x: 0, y: 0, dragging: false, startX: 0, startY: 0, startViewX: 0, startViewY: 0 },
  prescription: { scale: 1, x: 0, y: 0, dragging: false, startX: 0, startY: 0, startViewX: 0, startViewY: 0 }
})

const stages = computed(() => [
  { key: 'uploaded', index: '01', title: '原始数据上传', note: selectedFile.value ? selectedFile.value.name : '等待 TIFF/ZIP 数据', done: ['uploaded', 'heatmap', 'prescription', 'success'].includes(processState.value) },
  { key: 'heatmap', index: '02', title: '热力图生成', note: heatmapUrl.value ? '已生成热力分区' : running.value ? '算法正在生成热力图' : '等待算法输出', done: ['heatmap', 'prescription', 'success'].includes(processState.value) },
  { key: 'prescription', index: '03', title: '处方图构建', note: prescriptionUrl.value ? '已生成施药处方' : running.value ? '热力图完成后继续生成处方图' : '等待处方构建', done: ['prescription', 'success'].includes(processState.value) }
])

const fieldCount = computed(() => fields.value.length || '--')
const highDoseFields = computed(() => fields.value.filter(item => Number(item.dose_L_per_mu || item.dose) >= 2.5))
const averageDose = computed(() => {
  const doses = fields.value.map(item => Number(item.dose_L_per_mu || item.dose)).filter(Number.isFinite)
  if (!doses.length) return '--'
  return (doses.reduce((sum, value) => sum + value, 0) / doses.length).toFixed(2)
})
const completionRate = computed(() => prescriptionUrl.value ? '100%' : '--')
const recommendation = computed(() => {
  if (!fields.value.length) return '上传 8 波段 GeoTIFF 后，系统会先生成病害热力图，再构建变量施药处方图。'
  const targets = highDoseFields.value.length ? highDoseFields.value : fields.value
  const names = targets.slice(0, 4).map((item, index) => `地块${item.field_id || index + 1}`).join('、')
  return `处方建议：${names} 优先施药；高剂量区提高喷施量，低剂量区按图减量作业。`
})

const summaryCards = computed(() => [
  { label: '今日生成处方图', value: todayRecordCount.value, unit: '张', note: '来自真实模型任务' },
  { label: '重点处方地块', value: highDoseFields.value.length || '--', unit: '块', note: highDoseFields.value.length ? '推荐药量 >= 2.5 升/亩' : '等待处方结果' },
  { label: '平均推荐药量', value: averageDose.value, unit: averageDose.value === '--' ? '' : '升/亩', note: '按处方地块统计' },
  { label: '处方生成完整率', value: completionRate.value, unit: '', note: '热力图与处方图均生成后为 100%' }
])

const todayRecordCount = computed(() => {
  const today = formatDate(new Date()).slice(0, 10)
  return records.value.filter(item => String(item.date).startsWith(today)).length
})

const stateLabel = computed(() => ({
  idle: '未生成',
  uploaded: running.value ? '生成中' : '待生成',
  heatmap: '热力图完成',
  prescription: '处方图完成',
  success: '完成生成',
  failed: '生成失败'
}[processState.value] || '未生成'))

const stateTagType = computed(() => ({
  idle: 'info',
  uploaded: 'warning',
  heatmap: 'primary',
  prescription: 'success',
  success: 'success',
  failed: 'danger'
}[processState.value] || 'info'))

const pagedRecords = computed(() => {
  const start = (recordCurrentPage.value - 1) * recordPageSize
  return records.value.slice(start, start + recordPageSize)
})

function triggerUpload() {
  fileInput.value?.click()
}

function handleFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!/\.(tif|tiff|zip)$/i.test(file.name)) {
    proxy.$modal.msgError('请选择 GeoTIFF 文件或包含 GeoTIFF 的 ZIP 数据包')
    return
  }
  clearResult()
  selectedFile.value = file
  processState.value = 'uploaded'
  proxy.$modal.msgSuccess('原始数据已加载，开始自动生成热力图和处方图')
  runPrescription()
}

function clearResult() {
  objectUrls.value.forEach(url => URL.revokeObjectURL(url))
  objectUrls.value = []
  heatmapUrl.value = ''
  prescriptionUrl.value = ''
  heatmapFileName.value = ''
  prescriptionFileName.value = ''
  fields.value = []
  currentTaskId.value = null
  resetImageView('heatmap')
  resetImageView('prescription')
}

function hasImage(type) {
  return type === 'heatmap' ? Boolean(heatmapUrl.value) : Boolean(prescriptionUrl.value)
}

function resetImageView(type) {
  const view = imageViews[type]
  if (!view) return
  view.scale = 1
  view.x = 0
  view.y = 0
  view.dragging = false
  view.startX = 0
  view.startY = 0
  view.startViewX = 0
  view.startViewY = 0
}

function imageViewStyle(type) {
  const view = imageViews[type]
  return {
    transform: `translate3d(${view.x}px, ${view.y}px, 0) scale(${view.scale})`
  }
}

function handleImageWheel(type, event) {
  if (!hasImage(type)) return
  const view = imageViews[type]
  const direction = event.deltaY < 0 ? 1 : -1
  const nextScale = Math.min(5, Math.max(0.5, Number((view.scale + direction * 0.15).toFixed(2))))
  view.scale = nextScale
  if (nextScale === 1) {
    view.x = 0
    view.y = 0
  }
}

function startImageDrag(type, event) {
  if (!hasImage(type)) return
  const view = imageViews[type]
  view.dragging = true
  view.startX = event.clientX
  view.startY = event.clientY
  view.startViewX = view.x
  view.startViewY = view.y
  event.currentTarget?.setPointerCapture?.(event.pointerId)
}

function moveImageDrag(type, event) {
  const view = imageViews[type]
  if (!view?.dragging) return
  view.x = view.startViewX + event.clientX - view.startX
  view.y = view.startViewY + event.clientY - view.startY
}

function endImageDrag(type, event) {
  const view = imageViews[type]
  if (!view) return
  view.dragging = false
  event?.currentTarget?.releasePointerCapture?.(event.pointerId)
}

function getRows(response) {
  if (Array.isArray(response?.rows)) return response.rows
  if (Array.isArray(response?.data?.rows)) return response.data.rows
  if (Array.isArray(response?.data)) return response.data
  return []
}

async function resolvePrescriptionAlgorithm() {
  const containerResponse = await listContainer({ pageNum: 1, pageSize: 100 })
  const containers = getRows(containerResponse)
  for (const container of containers) {
    const algorithmResponse = await listAlgorithm(container.id)
    const algorithmMap = algorithmResponse?.data && typeof algorithmResponse.data === 'object'
      ? algorithmResponse.data
      : {}
    const algorithmName = Object.prototype.hasOwnProperty.call(algorithmMap, ALGORITHM_NAME)
      ? ALGORITHM_NAME
      : Object.keys(algorithmMap).find(name => /VariablePrescription/i.test(name))
    if (algorithmName) return { containerId: container.id, algorithmName }
  }
  throw new Error('未找到变量施药处方图算法服务，请确认算力平台已启动并已加载算法')
}

async function uploadInputFile(file) {
  const formData = new FormData()
  const suffix = file.name.split('.').pop()?.toLowerCase() || 'file'
  formData.append('file', file)
  formData.append('name', file.name)
  formData.append('type', suffix)
  formData.append('root', '1')
  const response = await addFileFile(formData)
  const fileId = response?.data?.file_id
  if (!fileId) throw new Error('数据已上传，但后端没有返回文件编号')
  return fileId
}

function wait(ms) {
  return new Promise(resolve => {
    pollTimer.value = window.setTimeout(resolve, ms)
  })
}

async function waitForTask(taskId) {
  for (let attempt = 0; attempt < 240; attempt += 1) {
    const response = await getTask(taskId)
    const task = response?.data || {}
    if (task.result && Number(task.result) > 0 && task.state === 'success') return Number(task.result)
    if (task.state === 'failed' || task.state === 'error') {
      throw new Error('算法任务执行失败，请到“农业模型分析任务”查看日志')
    }
    await wait(2000)
  }
  throw new Error('算法任务执行超时，请到“农业模型分析任务”查看运行状态')
}

async function collectResultFiles(rootId, depth = 0, visited = new Set()) {
  if (!rootId || depth > 8 || visited.has(rootId)) return []
  visited.add(rootId)
  const entries = getRows(await listFile({ pageNum: 1, pageSize: 200, root: rootId }))
  const result = [...entries]
  for (const entry of entries) {
    if (entry.type === 'dir') {
      result.push(...await collectResultFiles(entry.id, depth + 1, visited))
    }
  }
  return result
}

async function loadResultFiles(resultFolderId) {
  const resultFiles = await collectResultFiles(resultFolderId)
  const summaryFile = resultFiles.find(file => file.name === 'summary.json')
  const heatmapFile = resultFiles.find(file => /disease_heatmap\.png$/i.test(file.name))
  const prescriptionFile = resultFiles.find(file => /^final_fieldblock_prescription\.png$/i.test(file.name))

  if (summaryFile) {
    const summaryBlob = await down(summaryFile.id)
    const summary = JSON.parse(await summaryBlob.text())
    fields.value = Array.isArray(summary.fields) ? summary.fields : []
  }

  if (heatmapFile) {
    const blob = await down(heatmapFile.id)
    heatmapUrl.value = URL.createObjectURL(blob)
    objectUrls.value.push(heatmapUrl.value)
    heatmapFileName.value = heatmapFile.name
    processState.value = 'heatmap'
  }

  if (prescriptionFile) {
    const blob = await down(prescriptionFile.id)
    prescriptionUrl.value = URL.createObjectURL(blob)
    objectUrls.value.push(prescriptionUrl.value)
    prescriptionFileName.value = prescriptionFile.name
    processState.value = 'prescription'
  }

  if (!heatmapUrl.value || !prescriptionUrl.value) {
    throw new Error('算法已完成，但没有找到热力图或处方图 PNG 结果')
  }
}

async function runPrescription() {
  if (!selectedFile.value || running.value) return
  const sourceFile = selectedFile.value
  running.value = true
  clearResult()
  selectedFile.value = sourceFile
  processState.value = 'uploaded'
  try {
    const [fileId, algorithm] = await Promise.all([
      uploadInputFile(selectedFile.value),
      resolvePrescriptionAlgorithm()
    ])
    const taskName = `水稻精准施药处方图-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`
    const args = {
      args: [{
        file_ids: [fileId],
        model_name: MODEL_NAME,
        device: 'cpu',
        tile_size: 256,
        batch_size: 4096,
        stride: 3,
        resolution: 1024,
        shrink_radius: 1,
        minimum_field_area: 300,
        max_erosion: 12,
        save_visual_steps: true,
        visualization_dpi: 120
      }]
    }
    const taskResponse = await addTask({
      name: taskName,
      container: algorithm.containerId,
      algo: algorithm.algorithmName,
      args: JSON.stringify(args),
      remark: TASK_REMARK
    })
    const taskId = taskResponse?.data?.task_id
    if (!taskId) throw new Error('任务创建成功，但没有返回任务编号')
    currentTaskId.value = taskId
    await executeTask(taskId)
    const resultFolderId = await waitForTask(taskId)
    await loadResultFiles(resultFolderId)
    processState.value = 'success'
    await loadRecords()
    proxy.$modal.msgSuccess('变量施药处方图生成完成')
  } catch (error) {
    processState.value = 'failed'
    proxy.$modal.msgError(error?.message || '变量施药处方图生成失败')
  } finally {
    running.value = false
    if (pollTimer.value) {
      clearTimeout(pollTimer.value)
      pollTimer.value = null
    }
  }
}

async function loadRecordSummary(resultFolderId) {
  const resultFiles = await collectResultFiles(resultFolderId)
  const summaryFile = resultFiles.find(file => file.name === 'summary.json')
  if (!summaryFile) return { fieldCount: '--', averageDose: '--' }
  const summaryBlob = await down(summaryFile.id)
  const summary = JSON.parse(await summaryBlob.text())
  const summaryFields = Array.isArray(summary.fields) ? summary.fields : []
  const doses = summaryFields.map(item => Number(item.dose_L_per_mu || item.dose)).filter(Number.isFinite)
  return {
    fieldCount: summaryFields.length || '--',
    averageDose: doses.length ? `${(doses.reduce((sum, value) => sum + value, 0) / doses.length).toFixed(2)} 升/亩` : '--'
  }
}

async function loadRecords() {
  try {
    const response = await listTask({ pageNum: 1, pageSize: 100, remark: TASK_REMARK })
    const tasks = getRows(response).filter(task => String(task.remark || '').includes(TASK_REMARK))
    const loaded = await Promise.all(tasks.map(async task => {
      let resultInfo = { fieldCount: '--', averageDose: '--' }
      if (task.result && Number(task.result) > 0) {
        try {
          resultInfo = await loadRecordSummary(Number(task.result))
        } catch (error) {
          console.warn(`读取处方图任务结果失败 ${task.id}`, error)
        }
      }
      return {
        id: task.id,
        name: task.name,
        algorithm: task.algo || ALGORITHM_NAME,
        state: task.state,
        date: formatDate(task.endTime || task.end_time || task.initTime || task.init_time),
        ...resultInfo
      }
    }))
    records.value = loaded.sort((left, right) => String(right.date).localeCompare(String(left.date)))
  } catch (error) {
    records.value = []
    console.warn('读取变量施药处方图任务记录失败', error)
  }
}

function recordIndexMethod(index) {
  return (recordCurrentPage.value - 1) * recordPageSize + index + 1
}

function formatDate(value) {
  if (!value) return '--'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).replace('T', ' ').slice(0, 16)
  const pad = number => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function savePlotInfo() {
  plotDialogOpen.value = false
  proxy.$modal.msgSuccess('地块信息已记录，可用于处方图结果备注')
}

onMounted(() => {
  loadRecords()
})

onBeforeUnmount(() => {
  clearResult()
  if (pollTimer.value) clearTimeout(pollTimer.value)
})
</script>

<style lang="scss" scoped>
.prescription-page {
  min-height: calc(100vh - 84px);
  color: #284a31;
  background: linear-gradient(180deg, #f4f9f4 0%, #edf6ef 100%) !important;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.summary-card,
.prescription-panel,
.records-panel {
  border: 1px solid rgba(89, 157, 103, 0.18) !important;
  border-radius: 14px !important;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(241, 248, 242, 0.98)) !important;
  box-shadow: 0 8px 20px rgba(66, 101, 72, 0.09), inset 0 0 0 1px rgba(255, 255, 255, 0.65) !important;
}

.summary-card {
  padding: 18px 20px;
  text-align: center;

  span {
    color: #687c6e;
    font-size: 13px;
  }

  strong {
    display: block;
    margin: 7px 0 4px;
    color: #143e22;
    font-size: 28px;
    line-height: 1;
  }

  small {
    margin-left: 4px;
    font-size: 13px;
  }

  p {
    margin: 0;
    color: #6d7c70;
    font-size: 12px;
  }
}

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #163d23;
  font-size: 17px;
  font-weight: 800;
}

.stage-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;

  article {
    display: flex;
    min-width: 0;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border: 1px solid rgba(89, 157, 103, 0.13);
    border-radius: 12px;
    background: rgba(247, 251, 248, 0.96);
  }

  i {
    display: grid;
    width: 34px;
    height: 34px;
    flex: 0 0 34px;
    place-items: center;
    color: #4f9d63;
    border-radius: 10px;
    background: rgba(79, 157, 99, 0.1);
    font-style: normal;
    font-weight: 800;
  }

  strong,
  span {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  strong {
    color: #264b31;
    font-size: 14px;
  }

  span {
    margin-top: 4px;
    color: #6b8070;
    font-size: 12px;
  }

  .active,
  .done {
    border-color: rgba(63, 141, 87, 0.35);
    background: linear-gradient(145deg, rgba(240, 249, 242, 0.98), rgba(232, 246, 235, 0.98));
  }
}

.prescription-workbench {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.result-window {
  display: grid;
  min-width: 0;
  height: 560px;
  grid-template-rows: 44px minmax(0, 1fr) 38px;
  gap: 10px;
  padding: 14px;
  overflow: hidden;
  border: 1px solid rgba(89, 157, 103, 0.17);
  border-radius: 14px;
  background: rgba(249, 252, 249, 0.98);
  box-shadow: inset 0 0 22px rgba(89, 157, 103, 0.04), 0 8px 22px rgba(0, 0, 0, 0.08);
}

.prescription-window {
  grid-template-rows: 44px minmax(0, 1fr) 80px 50px 38px;
}

.result-window-head,
.window-footer {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-window-head {
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(89, 157, 103, 0.12);
}

.window-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;

  strong,
  small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  strong {
    color: #264b31;
    font-size: 15px;
    line-height: 1.1;
  }

  small {
    margin-top: 4px;
    color: #6b8070;
    font-size: 8px;
    letter-spacing: 1.1px;
  }
}

.step-number {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  color: #4fa66a;
  border: 1px solid rgba(79, 166, 106, 0.24);
  border-radius: 8px;
  background: rgba(79, 166, 106, 0.08);
  font-family: Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
}

.visual-stage {
  position: relative;
  display: grid;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  place-items: center;
  overflow: hidden;
  box-sizing: border-box;
  padding: 16px;
  border: 1px dashed rgba(89, 157, 103, 0.20);
  border-radius: 10px;
  background: linear-gradient(145deg, rgba(250, 253, 250, 0.99), rgba(236, 246, 238, 0.98));

  img {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: contain;
    object-position: center;
    background: #f7fbf8;
  }
}

.image-viewer.has-image {
  padding: 0;
  cursor: grab;
  touch-action: none;
  user-select: none;

  .result-image {
    transform-origin: center center;
    will-change: transform;
  }
}

.image-viewer.dragging {
  cursor: grabbing;
}

.stage-empty {
  display: flex;
  width: 100%;
  height: 100%;
  min-height: 0;
  padding: 24px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 11px;
  color: #667d6b;
  text-align: center;

  .el-icon {
    color: #56aa6e;
    font-size: 56px;
  }

  strong {
    color: #264b31;
    font-size: 15px;
  }

  span {
    max-width: 70%;
    color: #6b8070;
    font-size: 12px;
    line-height: 1.6;
  }
}

.window-footer {
  padding: 0 4px;

  span {
    color: #41694c;
    font-size: 11px;
    font-weight: 650;
  }

  small {
    overflow: hidden;
    color: #718276;
    font-size: 10px;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.prescription-result {
  display: grid;
  min-height: 0;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 14px;
}

.dose-legend {
  display: grid;
  align-content: center;
  gap: 8px;
  color: #45654d;
  font-size: 12px;

  strong {
    color: #294d33;
    line-height: 1.4;
  }
}

.dose-bar {
  width: 16px;
  height: 190px;
  border-radius: 999px;
  background: linear-gradient(180deg, #d60000 0%, #ffa500 30%, #f7e34b 50%, #31b85f 70%, #123cff 100%);
  box-shadow: 0 0 10px rgba(38, 119, 62, 0.2);
}

.prescription-image {
  border-style: solid;

  img {
    width: 100%;
    height: 100%;
  }
}

.result-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;

  article {
    display: grid;
    min-width: 0;
    grid-template-columns: 28px minmax(0, 1fr);
    align-items: center;
    gap: 8px;
    padding: 9px 10px;
    border: 1px solid rgba(89, 157, 103, 0.13);
    border-radius: 9px;
    background: rgba(246, 250, 246, 0.98);
  }

  .el-icon {
    grid-row: span 2;
    color: #3f8d57;
    font-size: 22px;
  }

  span,
  strong {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  span {
    color: #667d6b;
    font-size: 10px;
  }

  strong {
    color: #264b31;
    font-size: 13px;
  }
}

.recommendation {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border: 1px solid rgba(89, 157, 103, 0.13);
  border-radius: 9px;
  background: rgba(239, 248, 241, 0.98);
  color: #41694c;
  line-height: 1.6;

  .el-icon {
    color: #3f8d57;
    font-size: 20px;
  }
}

.result-action {
  width: 100%;
  height: 38px;
}

.records-panel {
  margin-top: 16px;
}

.records-card-title small {
  color: #718276;
  font-size: 12px;
  font-weight: 400;
}

.records-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.prescription-page .el-button--primary {
  color: #ffffff !important;
  border-color: #4a985f !important;
  background: linear-gradient(180deg, #66b77a, #4f9d63) !important;
  box-shadow: 0 4px 12px rgba(68, 143, 89, 0.18) !important;
}

@media (max-width: 1280px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .prescription-workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .summary-grid,
  .stage-strip,
  .result-metrics {
    grid-template-columns: 1fr;
  }

  .result-window,
  .prescription-window {
    height: auto;
    min-height: 520px;
  }

  .prescription-result {
    grid-template-columns: 1fr;
  }

  .dose-bar {
    width: 100%;
    height: 12px;
    background: linear-gradient(90deg, #123cff 0%, #31b85f 30%, #f7e34b 50%, #ffa500 70%, #d60000 100%);
  }
}
</style>
