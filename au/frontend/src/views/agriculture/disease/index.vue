<template>
  <div class="app-container agri-page">
    <AgriPageHeader
      title="水稻病害检测"
      eyebrow="农业智能监测"
      icon="Aim"
      description=""
    >
      <el-button icon="Plus" @click="surveyOpen = true">录入病害调查</el-button>
      <el-button type="primary" icon="UploadFilled" @click="triggerUpload">上传病害图片</el-button>
      <input ref="fileInput" hidden type="file" accept="image/*" @change="handleFile" />
    </AgriPageHeader>

    <section class="summary-grid">
      <article v-for="item in summary" :key="item.label" class="summary-card">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}<small>{{ item.unit }}</small></strong>
        <p>{{ item.note }}</p>
      </article>
    </section>

    <section class="main-grid">
      <el-card shadow="never" class="upload-panel">
        <template #header><div class="card-title"><span>病害图像智能检测</span><el-tag type="success">Pyramid-YOLOv8</el-tag></div></template>
        <div class="image-workbench equal-detection-workbench">
          <!-- 左侧：原始待检测图片 -->
          <section class="detect-window upload-window">
            <div class="detect-window-head">
              <div class="detect-window-title">
                <span class="step-number">01</span>
                <div>
                  <strong>待检测图片</strong>
                  <small>ORIGINAL IMAGE</small>
                </div>
              </div>

              <el-button
                v-if="previewUrl"
                link
                type="primary"
                icon="UploadFilled"
                @click="triggerUpload"
              >
                更换图片
              </el-button>
            </div>

            <div class="image-stage" :class="{ empty: !previewUrl }">
              <img
                v-if="previewUrl"
                :src="previewUrl"
                alt="待检测水稻病害图像"
              />

              <div v-else class="upload-empty">
                <el-icon><Picture /></el-icon>
                <strong>上传需要检测的水稻病害图片</strong>
                <span>支持 JPG、PNG，单张不超过 20 MB</span>
                <el-button type="primary" plain @click="triggerUpload">
                  选择图片
                </el-button>
              </div>
            </div>

            <div class="detect-window-footer">
              <span>原始图像预览</span>
              <small>{{ previewUrl ? '图片已加载，可开始检测' : '等待上传图片' }}</small>
            </div>
          </section>

          <!-- 右侧：检测结果 -->
          <section class="detect-window result-window">
            <div class="detect-window-head">
              <div class="detect-window-title">
                <span class="step-number">02</span>
                <div>
                  <strong>检测结果</strong>
                  <small>DETECTION RESULT</small>
                </div>
              </div>

              <el-tag :type="detectionTagType">
                {{ detectionStateLabel }}
              </el-tag>
            </div>

            <div class="result-image-stage" :class="{ empty: !resultUrl }">
              <img
                v-if="resultUrl"
                :src="resultUrl"
                alt="水稻病害检测结果"
              />

              <div v-else class="result-empty">
                <el-icon><Aim /></el-icon>
                <strong>{{ detectionState === 'running' ? '算法正在分析图片' : '等待生成检测结果' }}</strong>
                <span>{{ previewUrl ? '点击下方按钮启动 Pyramid-YOLOv8 检测' : '请先在左侧上传需要检测的图片' }}</span>
              </div>
            </div>

            <div class="result-metrics">
              <article>
                <span>病害类型</span>
                <strong>{{ detectionSummary.diseaseType }}</strong>
              </article>
              <article>
                <span>检测目标数</span>
                <strong>{{ detectionSummary.detectionCount }}</strong>
              </article>
              <article>
                <span>最高置信度</span>
                <strong>{{ detectionSummary.maxConfidence }}</strong>
              </article>
              <article>
                <span>输入图片数</span>
                <strong>{{ detectionSummary.inputImages }}</strong>
              </article>
            </div>

            <el-button
              class="result-action"
              :disabled="!previewUrl || detectionState === 'uploading' || detectionState === 'running'"
              type="primary"
              @click="runDetection"
            >
              {{ detectionState === 'uploading' ? '正在上传图片' : detectionState === 'running' ? '正在检测' : previewUrl ? '开始检测' : '等待上传图片' }}
            </el-button>
          </section>
        </div>
      </el-card>

    </section>

    <el-card shadow="never" class="records-panel">
      <template #header>
        <div class="card-title records-card-title">
          <span>病害调查与检测记录</span>
          <div class="record-actions">
            <el-button icon="Refresh" :loading="recordsLoading" @click="loadRecords">刷新记录</el-button>
            <el-button type="primary" plain icon="Download" :disabled="recordsLoading || !filteredRecords.length" @click="exportRecords">导出筛选结果</el-button>
          </div>
        </div>
      </template>
      <el-form class="record-filters" :model="recordFilters" inline @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="recordFilters.keyword" placeholder="任务编号、病害、基地" clearable />
        </el-form-item>
        <el-form-item label="病害类型">
          <el-select v-model="recordFilters.disease" placeholder="全部类型" clearable>
            <el-option v-for="disease in recordDiseaseOptions" :key="disease" :label="disease" :value="disease" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker v-model="recordFilters.dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" />
        </el-form-item>
        <el-form-item><el-button @click="resetRecordFilters">重置</el-button></el-form-item>
      </el-form>
      <p class="record-count" aria-live="polite">共 {{ records.length }} 条记录，筛选出 {{ filteredRecords.length }} 条；导出包含全部筛选结果。</p>
      <el-alert v-if="recordsError" :title="recordsError" type="error" :closable="false" show-icon />
      <el-table
        v-loading="recordsLoading"
        :data="pagedRecords"
        class="disease-record-table"
        :row-key="recordRowKey"
        table-layout="fixed"
        stripe
        :empty-text="recordsError ? '记录加载失败，请点击刷新重试' : records.length ? '没有符合筛选条件的记录' : '暂无已完成的图像检测记录'"
      >
        <el-table-column
          type="index"
          label="序号"
          width="72"
          align="center"
          :index="recordIndexMethod"
        />

        <el-table-column prop="date" label="调查日期" min-width="145" align="center">
          <template #default="scope">
            <div class="record-date-cell">
              <span class="record-calendar-dot"></span>
              <strong>{{ scope.row.date }}</strong>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="base" label="基地" min-width="230">
          <template #default="scope">
            <div class="record-base-cell">
              <span class="record-base-icon">田</span>
              <div>
                <strong>{{ scope.row.base }}</strong>
                <small>{{ scope.row.field !== '--' ? `${scope.row.field} 地块` : '未关联基地/地块' }}</small>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="disease" label="病害类型" min-width="130" align="center">
          <template #default="scope">
            <span class="record-disease-name">{{ scope.row.disease }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="detectionCount" label="检测目标数" min-width="120" align="center">
          <template #default="scope">
            {{ scope.row.detectionCount }}
          </template>
        </el-table-column>

        <el-table-column prop="confidence" label="最高置信度" min-width="130" align="center">
          <template #default="scope">
            {{ scope.row.confidence }}
          </template>
        </el-table-column>

        <el-table-column prop="di" label="病情指数 DI" min-width="140" align="center">
          <template #default="scope">
            <span
              class="record-di-value"
              :class="{
                high: Number(scope.row.di) >= 30,
                medium: Number(scope.row.di) >= 20 && Number(scope.row.di) < 30,
                low: Number(scope.row.di) < 20
              }"
            >
              {{ scope.row.di }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="风险等级" min-width="140" align="center">
          <template #default="scope">
            <span class="record-risk-badge" :class="scope.row.type">
              <i></i>
              {{ scope.row.risk }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="source" label="数据来源" min-width="150" align="center">
          <template #default="scope">
            <span class="record-source-tag">{{ scope.row.source }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="operator" label="调查人员" min-width="150" align="center">
          <template #default="scope">
            <div class="record-operator">
              <span>{{ String(scope.row.operator || '系').slice(0, 1) }}</span>
              <strong>{{ scope.row.operator }}</strong>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="note" label="处理状态" min-width="180" align="center">
          <template #default="scope">
            <span
              class="record-status-badge"
              :class="{
                completed: String(scope.row.note).includes('完成'),
                pending: String(scope.row.note).includes('待'),
                handled: String(scope.row.note).includes('建议'),
                watching: String(scope.row.note).includes('观察')
              }"
            >
              <i></i>
              {{ scope.row.note }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="scope">
            <el-button link type="primary" @click="viewRecord(scope.row)">查看结果</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="records-pagination">
        <el-pagination
          v-model:current-page="recordCurrentPage"
          :page-size="recordPageSize"
          :total="filteredRecords.length"
          layout="total, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <el-dialog v-model="recordDetailOpen" title="历史检测结果" width="min(900px, 94vw)" @close="clearRecordDetail">
      <el-descriptions v-if="selectedRecord" :column="2" border>
        <el-descriptions-item label="任务编号">{{ selectedRecord.taskId }}</el-descriptions-item>
        <el-descriptions-item label="检测日期">{{ selectedRecord.date }}</el-descriptions-item>
        <el-descriptions-item label="病害类型">{{ selectedRecord.disease }}</el-descriptions-item>
        <el-descriptions-item label="检测目标数">{{ selectedRecord.detectionCount }}</el-descriptions-item>
        <el-descriptions-item label="最高置信度">{{ selectedRecord.confidence }}</el-descriptions-item>
        <el-descriptions-item label="输入图片数">{{ selectedRecord.inputImages }}</el-descriptions-item>
      </el-descriptions>
      <div v-loading="recordDetailLoading" class="record-detail-image">
        <el-image v-if="recordDetailUrl" :src="recordDetailUrl" :preview-src-list="[recordDetailUrl]" fit="contain" preview-teleported />
        <el-empty v-else :description="recordDetailLoading ? '正在加载标注图片' : '暂无标注图片'" />
      </div>
      <template #footer><el-button @click="recordDetailOpen = false">关闭</el-button></template>
    </el-dialog>

    <el-dialog v-model="surveyOpen" title="录入稻瘟病调查数据" width="620px">
      <el-form :model="surveyForm" label-width="110px">
        <el-row :gutter="16">
          <el-col :span="12"><el-form-item label="调查基地"><el-select v-model="surveyForm.base"><el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="调查地块"><el-select v-model="surveyForm.field"><el-option v-for="item in fieldOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="调查日期"><el-date-picker v-model="surveyForm.date" type="date" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="病害类型"><el-select v-model="surveyForm.disease"><el-option label="稻瘟病" value="稻瘟病" /><el-option label="纹枯病" value="纹枯病" /><el-option label="稻曲病" value="稻曲病" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="病株数"><el-input-number v-model="surveyForm.diseased" :min="0" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="总株数"><el-input-number v-model="surveyForm.total" :min="1" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="surveyForm.note" type="textarea" :rows="3" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="surveyOpen=false">取消</el-button><el-button type="primary" @click="saveSurvey">保存调查记录</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup name="DiseaseAnalysis">
import AgriPageHeader from '@/components/AgriPageHeader'
import { baseOptions, fieldOptions } from '@/data/agriculture'
import { addFileFile, listFile, down } from '@/api/file/file'
import { listContainer, listAlgorithm } from '@/api/container/container'
import { addTask, executeTask, getTask, listTask } from '@/api/task/task'
import { saveAs } from 'file-saver'
import { diseaseRecordsCsv, fetchDiseaseTasks, filterDiseaseRecords } from '@/utils/diseaseRecords'

const { proxy } = getCurrentInstance()
const fileInput = ref()
const previewUrl = ref('')
const resultUrl = ref('')
const uploadedFile = ref(null)
const detectionState = ref('idle')
const detectionTaskId = ref(null)
const detectionPollTimer = ref(null)
const detectionObjectUrls = ref([])
const detectionSummary = reactive({
  diseaseType: '--',
  detectionCount: '--',
  maxConfidence: '--',
  inputImages: '--'
})
const surveyOpen = ref(false)
const surveyForm = reactive({ base: 'haicheng', field: 'A01', date: new Date(), disease: '稻瘟病', diseased: 8, total: 50, note: '' })

const summary = [
  { label: '今日检测图片', value: '156', unit: '张', note: '较昨日增加 18 张' },
  { label: '重点风险地块', value: '3', unit: '块', note: 'A02、B01、B03' },
  { label: '平均病情指数', value: '18.6', unit: '', note: '较上次调查 +2.8' },
  { label: '模型预测准确率', value: '91.4', unit: '%', note: '近 30 天综合评估' }
]
const records = ref([])
const recordsLoading = ref(false)
const recordsError = ref('')
const recordFilters = reactive({ keyword: '', disease: '', dateRange: [] })
const filteredRecords = computed(() => filterDiseaseRecords(records.value, recordFilters))
const recordDiseaseOptions = computed(() => [...new Set(records.value.flatMap(record => String(record.disease || '').split('、')).filter(Boolean))].sort())
const recordDetailOpen = ref(false)
const recordDetailLoading = ref(false)
const selectedRecord = ref(null)
const recordDetailUrl = ref('')
let recordDetailRequest = 0

const recordCurrentPage = ref(1)
const recordPageSize = 4

const pagedRecords = computed(() => {
  const start = (recordCurrentPage.value - 1) * recordPageSize
  return filteredRecords.value.slice(start, start + recordPageSize)
})

watch(recordFilters, () => { recordCurrentPage.value = 1 }, { deep: true })
watch(() => filteredRecords.value.length, total => {
  recordCurrentPage.value = Math.min(recordCurrentPage.value, Math.max(1, Math.ceil(total / recordPageSize)))
})

function resetRecordFilters() {
  Object.assign(recordFilters, { keyword: '', disease: '', dateRange: [] })
  recordCurrentPage.value = 1
}

function exportRecords() {
  if (recordsLoading.value || !filteredRecords.value.length) return
  const date = formatRecordDate(new Date()).slice(0, 10)
  saveAs(new Blob([diseaseRecordsCsv(filteredRecords.value)], { type: 'text/csv;charset=utf-8' }), `病害检测记录-${date}.csv`)
  proxy.$modal.msgSuccess(`已导出 ${filteredRecords.value.length} 条检测记录`)
}

function clearRecordDetail() {
  recordDetailRequest += 1
  if (recordDetailUrl.value) URL.revokeObjectURL(recordDetailUrl.value)
  recordDetailUrl.value = ''
  recordDetailLoading.value = false
  selectedRecord.value = null
}

async function viewRecord(record) {
  clearRecordDetail()
  const requestId = recordDetailRequest
  selectedRecord.value = record
  recordDetailOpen.value = true
  recordDetailLoading.value = true
  try {
    const blob = await down(record.imageFileId)
    if (requestId !== recordDetailRequest || !recordDetailOpen.value) return
    recordDetailUrl.value = URL.createObjectURL(blob)
  } catch (error) {
    if (requestId === recordDetailRequest) proxy.$modal.msgError('标注图片加载失败，请关闭后重试')
  } finally {
    if (requestId === recordDetailRequest) recordDetailLoading.value = false
  }
}

function recordIndexMethod(index) {
  return (recordCurrentPage.value - 1) * recordPageSize + index + 1
}

function recordRowKey(row, index) {
  return row.id || `${row.date}-${row.taskId || index}`
}

const detectionStateLabel = computed(() => ({
  idle: '未分析',
  ready: '待检测',
  uploading: '上传中',
  running: '检测中',
  success: '已完成',
  failed: '检测失败'
}[detectionState.value] || '未分析'))

const detectionTagType = computed(() => ({
  idle: 'info',
  ready: 'warning',
  uploading: 'primary',
  running: 'primary',
  success: 'success',
  failed: 'danger'
}[detectionState.value] || 'info'))

function triggerUpload() { fileInput.value?.click() }
function handleFile(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    proxy.$modal.msgError('请选择 JPG、PNG 等图像文件')
    return
  }
  if (file.size > 20 * 1024 * 1024) {
    proxy.$modal.msgError('单张图片不能超过 20 MB')
    return
  }
  resetDetectionResult()
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)
  uploadedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  detectionState.value = 'ready'
  proxy.$modal.msgSuccess('图片已加载，请点击“开始检测”')
}

function resetDetectionResult() {
  if (resultUrl.value) {
    URL.revokeObjectURL(resultUrl.value)
    resultUrl.value = ''
  }
  detectionObjectUrls.value.forEach(url => URL.revokeObjectURL(url))
  detectionObjectUrls.value = []
  detectionTaskId.value = null
  detectionSummary.diseaseType = '--'
  detectionSummary.detectionCount = '--'
  detectionSummary.maxConfidence = '--'
  detectionSummary.inputImages = '--'
}

function getRows(response) {
  if (Array.isArray(response?.rows)) return response.rows
  if (Array.isArray(response?.data?.rows)) return response.data.rows
  if (Array.isArray(response?.data)) return response.data
  return []
}

async function resolveDiseaseAlgorithm() {
  const containerResponse = await listContainer({ pageNum: 1, pageSize: 100 })
  const containerRows = getRows(containerResponse)
  const preferredNames = ['RiceDiseasePyramidYOLOv8Algorithm', 'RiceDiseaseYOLOv8Algorithm']

  for (const container of containerRows) {
    const algorithmResponse = await listAlgorithm(container.id)
    const algorithmMap = algorithmResponse?.data && typeof algorithmResponse.data === 'object'
      ? algorithmResponse.data
      : {}
    const algorithmName = preferredNames.find(name => Object.prototype.hasOwnProperty.call(algorithmMap, name))
      || Object.keys(algorithmMap).find(name => /RiceDisease|PyramidYOLO/i.test(name))
    if (algorithmName) {
      return { containerId: container.id, algorithmName }
    }
  }

  throw new Error('未找到水稻病害 Pyramid-YOLOv8 算法服务，请先确认算法容器已启动')
}

function createSafeUploadFile(file) {
  const extension = (file.name.match(/\.[^.]+$/)?.[0] || '.jpg').toLowerCase()
  const safeExtension = /\.(jpg|jpeg|png|bmp|tif|tiff|webp)$/.test(extension) ? extension : '.jpg'
  const safeName = `rice_disease_${Date.now()}${safeExtension}`
  return new File([file], safeName, {
    type: file.type || 'application/octet-stream',
    lastModified: file.lastModified
  })
}

async function uploadInputFile(file) {
  const safeFile = createSafeUploadFile(file)
  const formData = new FormData()
  formData.append('file', safeFile)
  formData.append('name', safeFile.name)
  formData.append('type', 'image')
  formData.append('root', '1')
  const response = await addFileFile(formData)
  const fileId = response?.data?.file_id
  if (!fileId) throw new Error('图片已上传，但后端没有返回文件编号')
  return fileId
}

function wait(ms) {
  return new Promise(resolve => {
    detectionPollTimer.value = window.setTimeout(resolve, ms)
  })
}

async function waitForTask(taskId) {
  for (let attempt = 0; attempt < 180; attempt += 1) {
    const response = await getTask(taskId)
    const task = response?.data || {}
    if (task.result && Number(task.result) > 0) return Number(task.result)
    if (task.state === 'failed' || task.state === 'error') {
      throw new Error('算法任务执行失败，请到“农业模型分析任务”查看日志')
    }
    await wait(2000)
  }
  throw new Error('算法任务执行超时，请到“农业模型分析任务”查看运行状态')
}

async function collectResultFiles(rootId, depth = 0, visited = new Set()) {
  if (!rootId || depth > 6 || visited.has(rootId)) return []
  visited.add(rootId)

  const entries = getRows(await listFile({ pageNum: 1, pageSize: 100, root: rootId }))
  const result = [...entries]
  for (const entry of entries) {
    // Older result records marked folders such as annotated/labels as unknown.
    const isFolder = entry.type === 'dir' || ['annotated', 'labels'].includes(entry.name)
    if (isFolder) {
      result.push(...await collectResultFiles(entry.id, depth + 1, visited))
    }
  }
  return result
}

async function loadDetectionMetadata(resultFolderId) {
  const resultFiles = await collectResultFiles(resultFolderId)
  const metadata = {
    imageFile: resultFiles.find(file => /\.(jpg|jpeg|png|bmp|webp)$/i.test(file.name)),
    diseaseType: '未检出',
    detectionCount: '--',
    maxConfidence: '--',
    inputImages: '--'
  }

  const summaryFile = resultFiles.find(file => file.name === 'summary.json')
  if (summaryFile) {
    const summaryBlob = await down(summaryFile.id)
    const summary = JSON.parse(await summaryBlob.text())
    metadata.detectionCount = summary.total_detections ?? 0
    metadata.inputImages = summary.input_images ?? 0
    const confidence = summary.images?.[0]?.max_confidence
    metadata.maxConfidence = Number.isFinite(Number(confidence))
      ? `${(Number(confidence) * 100).toFixed(1)}%`
      : '--'
  }

  const detectionsFile = resultFiles.find(file => file.name === 'detections.json')
  if (detectionsFile) {
    const detectionsBlob = await down(detectionsFile.id)
    const detections = JSON.parse(await detectionsBlob.text())
    const classNames = [...new Set((Array.isArray(detections) ? detections : [])
      .map(item => item.class_name)
      .filter(Boolean))]
    metadata.diseaseType = classNames.length ? classNames.join('、') : '未检出'
  }

  return metadata
}

async function loadResultFiles(resultFolderId) {
  const metadata = await loadDetectionMetadata(resultFolderId)
  if (metadata.imageFile) {
    const blob = await down(metadata.imageFile.id)
    resultUrl.value = URL.createObjectURL(blob)
    detectionObjectUrls.value.push(resultUrl.value)
  }

  detectionSummary.diseaseType = metadata.diseaseType
  detectionSummary.detectionCount = metadata.detectionCount
  detectionSummary.maxConfidence = metadata.maxConfidence
  detectionSummary.inputImages = metadata.inputImages

  if (!resultUrl.value) {
    throw new Error('算法已完成，但没有找到标注结果图片')
  }
  return metadata
}

function formatRecordDate(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).replace('T', ' ').slice(0, 16)
  const pad = number => String(number).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function toDetectionRecord(task, metadata) {
  return {
    id: `detection-task-${task.id}`,
    taskId: task.id,
    imageFileId: metadata.imageFile?.id,
    inputImages: metadata.inputImages,
    date: formatRecordDate(task.endTime || task.end_time || task.initTime || task.init_time),
    base: '--',
    field: '--',
    disease: metadata.diseaseType || '未检出',
    detectionCount: metadata.detectionCount ?? '--',
    confidence: metadata.maxConfidence || '--',
    di: '--',
    risk: '--',
    type: 'neutral',
    source: '图像检测',
    operator: '系统',
    note: '已完成'
  }
}

async function loadRecords() {
  if (recordsLoading.value) return
  recordsLoading.value = true
  recordsError.value = ''
  try {
    const tasks = await fetchDiseaseTasks(listTask)
    const loadedRecords = []
    let skipped = 0
    // Limit concurrent file requests when retrieving a long detection history.
    for (let start = 0; start < tasks.length; start += 6) {
      const batch = await Promise.all(tasks.slice(start, start + 6).map(async task => {
        try {
          const metadata = await loadDetectionMetadata(Number(task.result))
          if (!metadata.imageFile) { skipped += 1; return null }
          return toDetectionRecord(task, metadata)
        } catch (error) {
          skipped += 1
          console.warn(`跳过没有完整结果文件的检测任务 ${task.id}`, error)
          return null
        }
      }))
      loadedRecords.push(...batch)
    }
    records.value = loadedRecords
      .filter(Boolean)
      .sort((left, right) => String(right.date).localeCompare(String(left.date)))
    if (skipped) recordsError.value = `${skipped} 条任务的结果暂时无法读取，当前筛选和导出仅包含成功加载的记录。可点击刷新重试。`
    const pageCount = Math.max(1, Math.ceil(filteredRecords.value.length / recordPageSize))
    if (recordCurrentPage.value > pageCount) recordCurrentPage.value = pageCount
  } catch (error) {
    recordsError.value = records.value.length ? '刷新失败，保留上次加载的记录，请稍后重试。' : '读取检测记录失败，请稍后点击刷新重试。'
    console.warn('读取水稻病害检测记录失败', error)
  } finally {
    recordsLoading.value = false
  }
}

async function runDetection() {
  if (!uploadedFile.value || ['uploading', 'running'].includes(detectionState.value)) return
  detectionState.value = 'uploading'
  resetDetectionResult()
  try {
    const [fileId, algorithm] = await Promise.all([
      uploadInputFile(uploadedFile.value),
      resolveDiseaseAlgorithm()
    ])
    const taskName = `水稻病害图像检测-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`
    const args = {
      args: [{
        file_ids: [fileId],
        model_name: 'pyramid_yolov8_rice_disease_best.pt',
        conf: 0.25,
        iou: 0.45,
        imgsz: 640,
        line_width: 3,
        save_txt: true,
        save_conf: true,
        device: ''
      }]
    }
    const taskResponse = await addTask({
      name: taskName,
      container: algorithm.containerId,
      algo: algorithm.algorithmName,
      args: JSON.stringify(args),
      remark: '水稻病害检测页面提交'
    })
    const taskId = taskResponse?.data?.task_id
    if (!taskId) throw new Error('检测任务创建成功，但没有返回任务编号')
    detectionTaskId.value = taskId
    detectionState.value = 'running'
    await executeTask(taskId)
    const resultFolderId = await waitForTask(taskId)
    await loadResultFiles(resultFolderId)
    await loadRecords()
    detectionState.value = 'success'
    proxy.$modal.msgSuccess('水稻病害图像检测完成，结果已加载')
  } catch (error) {
    detectionState.value = 'failed'
    proxy.$modal.msgError(error?.message || '水稻病害检测失败')
  } finally {
    if (detectionPollTimer.value) {
      clearTimeout(detectionPollTimer.value)
      detectionPollTimer.value = null
    }
  }
}

function saveSurvey() { surveyOpen.value = false; proxy.$modal.msgSuccess('病害调查记录已保存，DI 已自动计算') }
onMounted(() => {
  loadRecords()
})
onBeforeUnmount(() => {
  clearRecordDetail()
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
  }
  if (resultUrl.value) URL.revokeObjectURL(resultUrl.value)
  detectionObjectUrls.value.forEach(url => URL.revokeObjectURL(url))
  if (detectionPollTimer.value) clearTimeout(detectionPollTimer.value)
})
</script>

<style lang="scss" scoped>
.record-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.record-actions .el-button { margin-left: 0; }
.record-filters { display: flex; flex-wrap: wrap; gap: 12px; padding: 16px 0 0; }
.record-filters :deep(.el-form-item) { margin: 0; }
.record-filters :deep(.el-select) { width: 160px; }
.record-filters :deep(.el-input) { width: 220px; }
.record-filters :deep(.el-date-editor) { max-width: 100%; }
.record-count { color: #65786a; font-size: 12px; margin: 12px 0; }
.record-detail-image { display: grid; place-items: center; min-height: 280px; margin-top: 16px; }
.record-detail-image .el-image { width: 100%; height: 420px; }
@media (max-width: 700px) {
  .records-card-title { align-items: flex-start; flex-direction: column; gap: 12px; }
  .record-filters :deep(.el-form-item) { width: 100%; }
  .record-filters :deep(.el-form-item__content) { min-width: 0; }
  .record-filters :deep(.el-input), .record-filters :deep(.el-select), .record-filters :deep(.el-date-editor) { width: 100%; }
}
.agri-page{background:#061323;min-height:calc(100vh - 84px)}
.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}.summary-card{padding:18px 20px;border:1px solid #e0eae2;border-radius:14px;background:rgba(6,29,47,.92)}.summary-card span{color:#768179;font-size:13px}.summary-card strong{display:block;margin:7px 0 4px;color:#1f3c29;font-size:28px}.summary-card small{margin-left:4px;font-size:13px}.summary-card p{margin:0;color:#6d7a71;font-size:12px}
.main-grid{display:grid;grid-template-columns:1.5fr .8fr;gap:16px;margin-bottom:16px}.main-grid .el-card,.records-panel{border:1px solid #e0eae2;border-radius:14px}.wide{grid-column:span 1}.card-title{display:flex;align-items:center;justify-content:space-between;color:#2b4232;font-weight:700}.update-time{color:#919b93;font-size:12px;font-weight:400}.ml8{margin-left:8px}
.image-workbench{display:grid;grid-template-columns:1fr 250px;gap:18px}.image-stage{position:relative;min-height:360px;overflow:hidden;border:1px dashed rgba(90,205,237,.26);border-radius:14px;background:rgba(3,20,34,.9)}.image-stage img{width:100%;height:360px;object-fit:cover}.upload-empty{display:flex;height:360px;align-items:center;justify-content:center;flex-direction:column;gap:10px;color:#667d6b}.upload-empty .el-icon{font-size:52px;color:#56aa6e}.upload-empty strong{color:#264b31}.upload-empty span{font-size:12px}.detect-box{position:absolute;left:36%;top:30%;width:34%;height:28%;border:3px solid #e6a23c}.detect-box span{position:absolute;left:-3px;top:-28px;padding:4px 8px;color:#fff;background:#e6a23c;font-size:12px}
.detection-result{padding:17px;border:1px solid rgba(90,205,237,.14);border-radius:14px;background:rgba(3,20,34,.86)}.result-head{display:flex;align-items:flex-start;justify-content:space-between}.result-head span{display:block;color:#667d6b;font-size:12px}.result-head strong{display:block;margin-top:5px;color:#264b31;font-size:20px}.detection-result dl{margin:20px 0}.detection-result dl div{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px dashed rgba(90,205,237,.14)}.detection-result dt{color:#667d6b}.detection-result dd{margin:0;color:#264b31;font-weight:600}
.risk-score{display:flex;align-items:center;gap:20px;padding:10px 0 24px}.score-ring{display:grid;width:126px;height:126px;flex:0 0 126px;place-items:center;align-content:center;border:13px solid #f3c76c;border-radius:50%;background:rgba(5,24,40,.86)}.score-ring strong{color:#c9820c;font-size:34px}.score-ring span{color:#946d30;font-size:12px}.risk-copy p{color:#637268;line-height:1.7}.factor-row{display:grid;grid-template-columns:75px 1fr 30px;align-items:center;gap:10px;margin:14px 0;color:#617066;font-size:13px}.factor-row strong{text-align:right;color:#3e5846}
.trend-chart{height:350px}.advice-list{margin:0;padding:0;list-style:none}.advice-list li{display:grid;grid-template-columns:86px 1fr;gap:12px;padding:14px 0;border-bottom:1px dashed #e2e9e3}.advice-list li:last-child{border-bottom:0}.advice-list b{color:#2e6f3f}.advice-list span{color:#68756c;line-height:1.6}
@media(max-width:1200px){.summary-grid{grid-template-columns:repeat(2,1fr)}.main-grid{grid-template-columns:1fr}.image-workbench{grid-template-columns:1fr}.detection-result{display:grid;grid-template-columns:1fr 1fr;gap:12px}.detection-result .el-button{align-self:end}}
@media(max-width:700px){.summary-grid{grid-template-columns:1fr}.detection-result{display:block}}


/* =========================================================
   病害图像检测工作区：左右两栏完全等宽、等高
========================================================= */

.equal-detection-workbench {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  gap: 18px;
}

/* 两侧外层窗口尺寸完全一致 */
.detect-window {
  display: grid;
  min-width: 0;
  height: 540px;
  padding: 14px;
  overflow: hidden;
  border: 1px solid rgba(89, 157, 103, 0.17);
  border-radius: 14px;
  background: rgba(249, 252, 249, 0.98);
  box-shadow:
    inset 0 0 22px rgba(89, 157, 103, 0.04),
    0 8px 22px rgba(0, 0, 0, 0.12);
}

.upload-window {
  grid-template-rows: 44px minmax(0, 1fr) 38px;
  gap: 10px;
}

.result-window {
  grid-template-rows: 44px minmax(0, 1fr) 88px 38px;
  gap: 10px;
}

.detect-window-head {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(89, 157, 103, 0.12);
}

.detect-window-title {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.detect-window-title > div {
  min-width: 0;
}

.detect-window-title strong,
.detect-window-title small {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.detect-window-title strong {
  color: #264b31;
  font-size: 15px;
  line-height: 1.1;
}

.detect-window-title small {
  margin-top: 4px;
  color: #6b8070;
  font-size: 8px;
  letter-spacing: 1.1px;
}

.step-number {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  color: #4fa66a;
  border: 1px solid rgba(102, 230, 255, 0.34);
  border-radius: 8px;
  background: rgba(102, 230, 255, 0.055);
  font-family: Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
}

/* 左侧原始图片区 */
.equal-detection-workbench .image-stage {
  position: relative;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  border: 1px dashed rgba(89, 157, 103, 0.20);
  border-radius: 10px;
  background:
    linear-gradient(145deg, rgba(250, 253, 250, 0.99), rgba(236, 246, 238, 0.98));
}

.equal-detection-workbench .image-stage img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f5faf6;
}

.equal-detection-workbench .upload-empty {
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
}

.equal-detection-workbench .upload-empty .el-icon {
  font-size: 58px;
  color: #56aa6e;
}

.equal-detection-workbench .upload-empty strong {
  color: #264b31;
  font-size: 15px;
}

.equal-detection-workbench .upload-empty span {
  font-size: 12px;
}

.detect-window-footer {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 4px;
}

.detect-window-footer span {
  color: #41694c;
  font-size: 11px;
  font-weight: 650;
}

.detect-window-footer small {
  overflow: hidden;
  color: #718276;
  font-size: 10px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 右侧检测结果图片区 */
.result-image-stage {
  position: relative;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  border: 1px solid rgba(89, 157, 103, 0.18);
  border-radius: 10px;
  background:
    linear-gradient(145deg, rgba(250, 253, 250, 0.99), rgba(236, 246, 238, 0.98));
}

.result-image-stage img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #f5faf6;
}

.result-empty {
  display: flex;
  width: 100%;
  height: 100%;
  padding: 24px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 10px;
  color: #6b8070;
  text-align: center;
}

.result-empty .el-icon {
  font-size: 52px;
  color: #5aa874;
}

.result-empty strong {
  color: #315c3b;
  font-size: 15px;
}

.result-empty span {
  font-size: 12px;
}

/* 检测框只显示在右侧检测结果中 */
.result-image-stage .detect-box {
  position: absolute;
  top: 29%;
  left: 33%;
  width: 36%;
  height: 30%;
  border: 3px solid #e6a23c;
  box-shadow:
    0 0 0 1px rgba(230, 162, 60, 0.18),
    0 0 16px rgba(230, 162, 60, 0.24);
}

.result-image-stage .detect-box span {
  position: absolute;
  top: -29px;
  left: -3px;
  padding: 5px 9px;
  color: #ffffff;
  background: #e6a23c;
  font-size: 11px;
  white-space: nowrap;
}

/* 右侧四项检测结果 */
.result-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
}

.result-metrics article {
  display: flex;
  min-width: 0;
  padding: 8px 10px;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid rgba(89, 157, 103, 0.12);
  border-radius: 8px;
  background: rgba(242, 249, 243, 0.98);
}

.result-metrics span,
.result-metrics strong {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.result-metrics span {
  color: #667d6b;
  font-size: 10px;
}

.result-metrics strong {
  color: #264b31;
  font-size: 12px;
}

.result-action {
  width: 100%;
  height: 38px;
}

/* 原来的左右比例和固定 250px 结果栏失效 */
.image-workbench {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* 常见笔记本宽度仍保持左右并排 */
@media (max-width: 1200px) {
  .equal-detection-workbench {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .detect-window {
    height: 500px;
  }

  .detection-result {
    display: block;
  }
}

/* 仅在真正较窄的屏幕上改为上下排列 */
@media (max-width: 900px) {
  .equal-detection-workbench {
    grid-template-columns: 1fr;
  }

  .detect-window {
    height: 520px;
  }
}

@media (max-width: 560px) {
  .detect-window {
    height: auto;
    min-height: 480px;
  }

  .upload-window {
    grid-template-rows: 44px 360px 38px;
  }

  .result-window {
    grid-template-rows: 44px 300px auto 38px;
  }

  .result-metrics {
    grid-template-columns: 1fr;
  }
}



/* =========================================================
   删除风险、预测曲线和防控建议后的单模块布局
========================================================= */

.main-grid {
  grid-template-columns: minmax(0, 1fr);
}

.upload-panel {
  grid-column: 1 / -1;
  width: 100%;
}

.equal-detection-workbench {
  width: 100%;
}

/* 已删除模块对应的旧样式不再参与页面显示 */
.risk-panel,
.trend-panel,
.advice-panel {
  display: none;
}



/* =========================================================
   深绿农业科技主题覆盖
   仅修改颜色，不改变布局与功能
========================================================= */

.disease-analysis-page {
  --agri-green: #46b96b;
  --agri-green-light: #5fb477;
  --agri-green-dark: #175b32;
  --agri-green-deep: #061b10;
  --agri-line: rgba(89, 157, 103, 0.18);
}

.page-header,
.stats-grid .stat-card,
.upload-panel,
.records-panel,
.detect-window {
  border-color: rgba(89, 157, 103, 0.18) !important;
  background:
    linear-gradient(
      145deg,
      rgba(248, 252, 248, 0.98),
      rgba(238, 247, 239, 0.98)
    ) !important;
  box-shadow:
    inset 0 0 24px rgba(82, 188, 108, 0.03),
    0 8px 24px rgba(54, 91, 62, 0.10) !important;
}

.page-title h2,
.detect-window-title strong,
.upload-empty strong,
.result-empty strong,
.result-metrics strong {
  color: #23492e !important;
}

.page-title p,
.detect-window-title small,
.upload-empty span,
.result-empty span,
.detect-window-footer small,
.result-metrics span {
  color: #6b8070 !important;
}

.step-number {
  color: #4fa66a !important;
  border-color: rgba(113, 232, 154, 0.34) !important;
  background: rgba(113, 232, 154, 0.06) !important;
}

.equal-detection-workbench .image-stage,
.result-image-stage {
  border-color: rgba(89, 157, 103, 0.20) !important;
  background:
    linear-gradient(
      145deg,
      rgba(250, 253, 250, 0.99),
      rgba(236, 246, 238, 0.98)
    ) !important;
}

.equal-detection-workbench .image-stage img,
.result-image-stage img {
  background: #f5faf6 !important;
}

.equal-detection-workbench .upload-empty .el-icon,
.result-empty .el-icon {
  color: #56aa6e !important;
}

.detect-window-footer span {
  color: #41694c !important;
}

.result-metrics article {
  border-color: rgba(89, 157, 103, 0.13) !important;
  background: rgba(242, 249, 243, 0.98) !important;
}

.disease-analysis-page .el-button--primary {
  border-color: #4b9c62 !important;
  background:
    linear-gradient(180deg, #5bad72, #438f5a) !important;
  box-shadow: 0 5px 14px rgba(68, 143, 89, 0.18) !important;
}

.disease-analysis-page .el-button--primary:hover {
  border-color: #5aae74 !important;
  background:
    linear-gradient(180deg, #6abb7e, #4f9f66) !important;
}

.disease-analysis-page .el-button--primary.is-plain {
  color: #4f9f66 !important;
  border-color: rgba(82, 188, 108, 0.42) !important;
  background: rgba(89, 157, 103, 0.08) !important;
}

.disease-analysis-page .el-button--primary.is-plain:hover {
  color: #ffffff !important;
  background: #4f9f66 !important;
}

.disease-analysis-page .el-tag--info {
  color: #86ad90 !important;
  border-color: rgba(89, 157, 103, 0.18) !important;
  background: rgba(89, 157, 103, 0.08) !important;
}

.records-panel :deep(.el-table),
.records-panel :deep(.el-table__inner-wrapper),
.records-panel :deep(.el-table tr),
.records-panel :deep(.el-table th.el-table__cell),
.records-panel :deep(.el-table td.el-table__cell) {
  border-color: rgba(89, 157, 103, 0.11) !important;
  background: transparent !important;
}

.records-panel :deep(.el-table th.el-table__cell) {
  color: #bfe6c9 !important;
  background: rgba(19, 78, 40, 0.48) !important;
}

.records-panel :deep(.el-table td.el-table__cell) {
  color: #d9efe0 !important;
}

.records-panel :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(89, 157, 103, 0.08) !important;
}



/* =========================================================
   浅绿农业主题修正：提高可读性
========================================================= */

.agri-page {
  background:
    linear-gradient(180deg, #f4f9f4 0%, #eef6ef 100%) !important;
  color: #2d4934 !important;
}

.summary-card,
.upload-panel,
.records-panel,
.detect-window {
  border-color: rgba(89, 157, 103, 0.18) !important;
  background:
    linear-gradient(
      145deg,
      rgba(255, 255, 255, 0.98),
      rgba(241, 248, 242, 0.98)
    ) !important;
  box-shadow:
    0 8px 20px rgba(66, 101, 72, 0.09),
    inset 0 0 0 1px rgba(255, 255, 255, 0.65) !important;
}

.card-title,
.detect-window-title strong,
.upload-empty strong,
.result-empty strong,
.result-metrics strong,
.detect-window-footer span {
  color: #294d33 !important;
}

.summary-card span,
.summary-card p,
.detect-window-title small,
.upload-empty span,
.result-empty span,
.detect-window-footer small,
.result-metrics span {
  color: #6c7f70 !important;
}

.summary-card strong {
  color: #3f8d57 !important;
}

.step-number {
  color: #3f8d57 !important;
  border-color: rgba(79, 166, 106, 0.24) !important;
  background: rgba(79, 166, 106, 0.08) !important;
}

.equal-detection-workbench .image-stage,
.result-image-stage {
  border-color: rgba(89, 157, 103, 0.20) !important;
  background:
    linear-gradient(
      145deg,
      rgba(248, 252, 248, 0.98),
      rgba(236, 246, 238, 0.98)
    ) !important;
}

.equal-detection-workbench .image-stage img,
.result-image-stage img {
  background: #f6faf7 !important;
}

.equal-detection-workbench .upload-empty .el-icon,
.result-empty .el-icon {
  color: #58a86e !important;
}

.result-metrics article {
  border-color: rgba(89, 157, 103, 0.13) !important;
  background: rgba(246, 250, 246, 0.98) !important;
}

.agri-page .el-button--primary {
  color: #ffffff !important;
  border-color: #4a985f !important;
  background:
    linear-gradient(180deg, #66b77a, #4f9d63) !important;
  box-shadow: 0 4px 12px rgba(68, 143, 89, 0.18) !important;
}

.agri-page .el-button--primary:hover {
  border-color: #5fab72 !important;
  background:
    linear-gradient(180deg, #72c285, #5aaa70) !important;
}

.agri-page .el-button--primary.is-plain {
  color: #4b965e !important;
  border-color: rgba(79, 157, 99, 0.30) !important;
  background: rgba(79, 157, 99, 0.06) !important;
}

.agri-page .el-button--primary.is-plain:hover {
  color: #ffffff !important;
  background: #5aaa70 !important;
}

.records-panel :deep(.el-table),
.records-panel :deep(.el-table__inner-wrapper),
.records-panel :deep(.el-table tr),
.records-panel :deep(.el-table td.el-table__cell) {
  background: #ffffff !important;
}

.records-panel :deep(.el-table th.el-table__cell) {
  color: #345b3e !important;
  background: #edf6ee !important;
}

.records-panel :deep(.el-table td.el-table__cell) {
  color: #445b4a !important;
}

.records-panel :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f1f8f2 !important;
}



/* =========================================================
   病害调查与检测记录：浅绿专业表格
========================================================= */

.records-panel {
  overflow: hidden;
  border: 1px solid rgba(89, 157, 103, 0.18) !important;
  border-radius: 14px !important;
  background: #ffffff !important;
  box-shadow: 0 8px 24px rgba(63, 101, 69, 0.08) !important;
}

.records-panel :deep(.el-card__header) {
  padding: 17px 20px !important;
  border-bottom: 1px solid rgba(89, 157, 103, 0.12) !important;
  background:
    linear-gradient(
      90deg,
      rgba(238, 247, 239, 0.96),
      rgba(250, 253, 250, 0.98)
    ) !important;
}

.records-panel :deep(.el-card__body) {
  padding: 0 !important;
}

.disease-record-table {
  width: 100%;
  --el-table-border-color: rgba(89, 157, 103, 0.10);
  --el-table-header-bg-color: #f2f8f3;
  --el-table-row-hover-bg-color: #f4faf5;
  --el-table-tr-bg-color: #ffffff;
  --el-fill-color-lighter: #f8fbf8;
}

.records-panel :deep(.disease-record-table::before),
.records-panel :deep(.el-table__inner-wrapper::before) {
  display: none !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper th.el-table__cell) {
  height: 48px !important;
  padding: 0 !important;
  color: #3a6045 !important;
  border-bottom: 1px solid rgba(89, 157, 103, 0.14) !important;
  background:
    linear-gradient(
      180deg,
      #f5faf6 0%,
      #edf6ef 100%
    ) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper .cell) {
  padding: 0 14px !important;
  line-height: 48px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper td.el-table__cell) {
  height: 66px !important;
  padding: 0 !important;
  color: #465c4b !important;
  border-bottom: 1px solid rgba(89, 157, 103, 0.08) !important;
  background: transparent !important;
  font-size: 12px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper .cell) {
  padding: 0 14px !important;
  line-height: 1.4 !important;
}

.records-panel :deep(.disease-record-table .el-table__row--striped td.el-table__cell) {
  background: #fbfdfb !important;
}

.records-panel :deep(.disease-record-table .el-table__body tr:hover > td.el-table__cell) {
  background: #f1f8f2 !important;
}

.record-date-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-calendar-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: #5eaa72;
  box-shadow: 0 0 0 4px rgba(94, 170, 114, 0.10);
}

.record-date-cell strong {
  color: #405c47;
  font-size: 12px;
  font-weight: 650;
}

.record-base-cell {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.record-base-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  place-items: center;
  color: #4f9662;
  border: 1px solid rgba(79, 150, 98, 0.18);
  border-radius: 9px;
  background: rgba(79, 150, 98, 0.07);
  font-size: 13px;
  font-weight: 800;
}

.record-base-cell > div {
  min-width: 0;
}

.record-base-cell strong,
.record-base-cell small {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.record-base-cell strong {
  color: #31513a;
  font-size: 12px;
  font-weight: 700;
}

.record-base-cell small {
  margin-top: 4px;
  color: #7b8e80;
  font-size: 10px;
}

.record-disease-name {
  display: inline-flex;
  padding: 5px 10px;
  color: #45634d;
  border: 1px solid rgba(89, 157, 103, 0.15);
  border-radius: 999px;
  background: #f3f8f4;
  font-size: 11px;
  font-weight: 650;
}

.record-di-value {
  display: inline-grid;
  min-width: 54px;
  height: 30px;
  padding: 0 10px;
  place-items: center;
  border-radius: 8px;
  font-family: Consolas, monospace;
  font-size: 14px;
  font-weight: 800;
}

.record-di-value.low {
  color: #41835a;
  background: rgba(77, 166, 105, 0.09);
}

.record-di-value.medium {
  color: #b57b1c;
  background: rgba(222, 164, 65, 0.11);
}

.record-di-value.high {
  color: #c65353;
  background: rgba(213, 83, 83, 0.10);
}

.record-risk-badge,
.record-status-badge {
  display: inline-flex;
  min-height: 28px;
  padding: 0 10px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: 999px;
  white-space: nowrap;
  font-size: 10px;
  font-weight: 700;
}

.record-risk-badge i,
.record-status-badge i {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
}

.record-risk-badge.success {
  color: #3f8558;
  border-color: rgba(77, 166, 105, 0.18);
  background: rgba(77, 166, 105, 0.08);
}

.record-risk-badge.neutral {
  color: #718178;
  border-color: rgba(120, 140, 126, 0.18);
  background: rgba(120, 140, 126, 0.07);
}

.record-risk-badge.neutral i {
  background: #8a9a8f;
}

.record-risk-badge.success i {
  background: #50a96a;
}

.record-risk-badge.warning {
  color: #a97219;
  border-color: rgba(222, 164, 65, 0.22);
  background: rgba(222, 164, 65, 0.10);
}

.record-risk-badge.warning i {
  background: #d9a13e;
}

.record-risk-badge.danger {
  color: #bd4f4f;
  border-color: rgba(213, 83, 83, 0.20);
  background: rgba(213, 83, 83, 0.08);
}

.record-risk-badge.danger i {
  background: #d35b5b;
}

.record-source-tag {
  display: inline-flex;
  padding: 5px 9px;
  color: #56705d;
  border: 1px solid rgba(89, 157, 103, 0.13);
  border-radius: 7px;
  background: #f6faf6;
  font-size: 10px;
}

.record-operator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-operator > span {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  color: #ffffff;
  border-radius: 50%;
  background:
    linear-gradient(145deg, #74b984, #4f9662);
  font-size: 10px;
  font-weight: 700;
}

.record-operator strong {
  overflow: hidden;
  color: #485f4e;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.record-status-badge {
  color: #6e7d72;
  border-color: rgba(120, 140, 126, 0.18);
  background: rgba(120, 140, 126, 0.07);
}

.record-status-badge i {
  background: #8a9a8f;
}

.record-status-badge.completed {
  color: #3f8558;
  border-color: rgba(77, 166, 105, 0.18);
  background: rgba(77, 166, 105, 0.08);
}

.record-status-badge.completed i {
  background: #50a96a;
}

.record-status-badge.pending {
  color: #a97219;
  border-color: rgba(222, 164, 65, 0.20);
  background: rgba(222, 164, 65, 0.09);
}

.record-status-badge.pending i {
  background: #d9a13e;
}

.record-status-badge.handled {
  color: #5476a7;
  border-color: rgba(84, 118, 167, 0.18);
  background: rgba(84, 118, 167, 0.08);
}

.record-status-badge.handled i {
  background: #6688b7;
}

.record-status-badge.watching {
  color: #657d69;
  border-color: rgba(101, 125, 105, 0.18);
  background: rgba(101, 125, 105, 0.07);
}

.record-status-badge.watching i {
  background: #7d9681;
}

@media (max-width: 1200px) {
  .records-panel {
    overflow-x: auto;
  }

  .disease-record-table {
    min-width: 1160px;
  }
}



/* =========================================================
   记录表格紧凑版：减少列间空隙
========================================================= */

.records-panel :deep(.disease-record-table) {
  width: 100% !important;
  min-width: 0 !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper th.el-table__cell) {
  height: 42px !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper .cell) {
  padding: 0 8px !important;
  line-height: 42px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper td.el-table__cell) {
  height: 56px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper .cell) {
  padding: 0 8px !important;
}

.record-date-cell,
.record-base-cell,
.record-operator {
  gap: 6px;
}

.record-base-icon {
  width: 28px;
  height: 28px;
  flex-basis: 28px;
  border-radius: 7px;
}

.record-base-cell strong {
  font-size: 11px;
}

.record-base-cell small {
  margin-top: 2px;
  font-size: 9px;
}

.record-calendar-dot {
  width: 6px;
  height: 6px;
  flex-basis: 6px;
  box-shadow: 0 0 0 3px rgba(94, 170, 114, 0.09);
}

.record-disease-name,
.record-source-tag {
  padding: 4px 7px;
}

.record-di-value {
  min-width: 46px;
  height: 27px;
  padding: 0 7px;
  font-size: 13px;
}

.record-risk-badge,
.record-status-badge {
  min-height: 25px;
  padding: 0 8px;
  gap: 5px;
}

.record-operator > span {
  width: 25px;
  height: 25px;
  flex-basis: 25px;
}

@media (max-width: 1200px) {
  .disease-record-table {
    min-width: 1000px !important;
  }
}



/* =========================================================
   记录表格均衡铺满最终修正版
========================================================= */

.records-panel :deep(.disease-record-table) {
  width: 100% !important;
  min-width: 0 !important;
}

.records-panel :deep(.disease-record-table .el-table__inner-wrapper),
.records-panel :deep(.disease-record-table .el-table__header-wrapper),
.records-panel :deep(.disease-record-table .el-table__body-wrapper),
.records-panel :deep(.disease-record-table table) {
  width: 100% !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper th.el-table__cell) {
  height: 46px !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper .cell) {
  padding: 0 10px !important;
  line-height: 46px !important;
  white-space: nowrap !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper td.el-table__cell) {
  height: 60px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper .cell) {
  padding: 0 10px !important;
}

.record-base-cell {
  min-width: 0;
}

.record-base-cell > div {
  min-width: 0;
  flex: 1;
}

.record-base-cell strong,
.record-base-cell small {
  max-width: 100%;
}

/* 宽屏铺满；窄屏才允许横向滚动 */
@media (max-width: 1200px) {
  .records-panel {
    overflow-x: auto;
  }

  .records-panel :deep(.disease-record-table) {
    min-width: 1000px !important;
  }
}



/* =========================================================
   记录列表：均匀列宽 + 每页 4 条分页
========================================================= */

.records-card-title small {
  color: #728476;
  font-size: 11px;
  font-weight: 500;
}

.records-panel :deep(.disease-record-table) {
  width: 100% !important;
  min-width: 0 !important;
}

.records-panel :deep(.disease-record-table .el-table__inner-wrapper),
.records-panel :deep(.disease-record-table .el-table__header-wrapper),
.records-panel :deep(.disease-record-table .el-table__body-wrapper),
.records-panel :deep(.disease-record-table table) {
  width: 100% !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper th.el-table__cell) {
  height: 46px !important;
}

.records-panel :deep(.disease-record-table .el-table__header-wrapper .cell) {
  padding: 0 12px !important;
  line-height: 46px !important;
  text-align: inherit;
  white-space: nowrap !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper td.el-table__cell) {
  height: 62px !important;
}

.records-panel :deep(.disease-record-table .el-table__body-wrapper .cell) {
  padding: 0 12px !important;
}

/* 日期、基地、调查人员内部元素不再制造额外空隙 */
.record-date-cell {
  justify-content: center;
}

.record-base-cell {
  max-width: 100%;
}

.record-operator {
  justify-content: center;
}

/* 分页区域 */
.records-pagination {
  display: flex;
  min-height: 62px;
  padding: 12px 18px;
  align-items: center;
  justify-content: flex-end;
  border-top: 1px solid rgba(89, 157, 103, 0.11);
  background:
    linear-gradient(
      90deg,
      rgba(248, 252, 248, 0.98),
      rgba(239, 247, 240, 0.96)
    );
}

.records-pagination :deep(.el-pagination) {
  --el-pagination-button-bg-color: #ffffff;
  --el-pagination-hover-color: #438f5a;
  --el-pagination-button-disabled-bg-color: #f3f7f3;
  color: #566b5b;
}

.records-pagination :deep(.el-pagination.is-background .btn-prev),
.records-pagination :deep(.el-pagination.is-background .btn-next),
.records-pagination :deep(.el-pagination.is-background .el-pager li) {
  min-width: 30px;
  height: 30px;
  margin: 0 3px;
  color: #4c6653;
  border: 1px solid rgba(89, 157, 103, 0.15);
  border-radius: 7px;
  background: #ffffff;
  line-height: 30px;
}

.records-pagination :deep(.el-pagination.is-background .el-pager li.is-active) {
  color: #ffffff;
  border-color: #4f9d63;
  background: #4f9d63;
}

.records-pagination :deep(.el-pagination__total),
.records-pagination :deep(.el-pagination__jump) {
  color: #65786a;
  font-size: 12px;
}

.records-pagination :deep(.el-pagination__editor.el-input) {
  width: 48px;
}

.records-pagination :deep(.el-pagination__editor .el-input__wrapper) {
  border: 1px solid rgba(89, 157, 103, 0.17);
  border-radius: 7px;
  background: #ffffff;
  box-shadow: none;
}

/* 低于 1200px 才横向滚动，桌面宽屏保持均匀铺满 */
@media (max-width: 1200px) {
  .records-panel {
    overflow-x: auto;
  }

  .records-panel :deep(.disease-record-table) {
    min-width: 1120px !important;
  }

  .records-pagination {
    min-width: 1120px;
  }
}

@media (max-width: 700px) {
  .records-pagination {
    justify-content: center;
  }

  .records-pagination :deep(.el-pagination__jump) {
    display: none;
  }
}
/* 右侧“等待上传图片”按钮：强制白色 */
.agri-page .result-action.el-button--primary.is-disabled,
.agri-page .result-action.el-button--primary.is-disabled:hover,
.agri-page .result-action.el-button--primary.is-disabled:focus {
  --el-button-disabled-bg-color: #ffffff;
  --el-button-disabled-border-color: #d6e3d8;
  --el-button-disabled-text-color: #7d8f82;

  color: #7d8f82 !important;
  border-color: #d6e3d8 !important;
  background: #ffffff !important;
  background-color: #ffffff !important;
  background-image: none !important;
  box-shadow: none !important;
  opacity: 1 !important;
}
</style>
