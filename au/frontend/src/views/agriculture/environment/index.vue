<template>
  <div class="app-container agri-page" v-loading="loading">
    <div class="ambient ambient-left"></div>
    <div class="ambient ambient-right"></div>

    <AgriPageHeader
      class="page-hero"
      title="田间环境监测"
      eyebrow="FIELD ENVIRONMENT"
      icon="Sunny"
      description="统一查看空气、土壤与气象监测真实数据，支持实时状态、历史趋势、异常预警和模型输入统计。"
    >
      <div class="hero-live-status">
        <span class="hero-live-dot"></span>
        <div>
          <strong>实时监测中</strong>
          <small>{{ loading ? '正在同步数据' : `${refreshCountdown} 秒后自动刷新` }}</small>
        </div>
        <el-progress
          type="circle"
          :percentage="refreshProgress"
          :width="36"
          :stroke-width="3"
          :show-text="false"
          color="#4bd3a2"
        />
      </div>
      <el-button class="ghost-button" icon="Refresh" :loading="loading" @click="loadData">刷新数据</el-button>
      <el-button type="primary" icon="Download" @click="exportData">导出数据</el-button>
    </AgriPageHeader>

    <main class="page-content">
      <el-card class="filter-card surface-card" shadow="never">
        <template #header>
          <div class="panel-heading compact-heading">
            <div>
              <span class="panel-eyebrow">DATA FILTER</span>
              <h3>监测范围筛选</h3>
            </div>
            <div class="scope-pill">
              <span class="scope-dot"></span>
              当前范围：{{ selectedScopeName }}
            </div>
          </div>
        </template>

        <el-form
          :model="filters"
          class="filter-form"
          label-position="top"
        >
          <el-form-item label="水稻基地" class="filter-item base-filter">
            <el-select v-model="filters.baseId" clearable placeholder="全部基地" @change="onBaseChange">
              <el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>

          <el-form-item label="监测地块" class="filter-item plot-filter">
            <el-select v-model="filters.plotId" clearable placeholder="全部地块" @change="loadData">
              <el-option v-for="item in plotOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>

          <el-form-item label="监测设备" class="filter-item device-filter">
            <el-select v-model="filters.deviceId" clearable placeholder="全部设备" @change="loadData">
              <el-option
                v-for="item in deviceOptions"
                :key="item.deviceId"
                :label="item.deviceName || item.deviceAddr"
                :value="item.deviceId"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="时间范围" class="filter-item time-filter">
            <el-date-picker
              v-model="filters.dateRange"
              type="datetimerange"
              value-format="YYYY-MM-DD HH:mm:ss"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
            />
          </el-form-item>

          <el-form-item class="filter-action">
            <el-button type="primary" icon="Search" @click="loadData">查询监测数据</el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-alert
        v-if="errorMessage"
        class="page-alert"
        :title="errorMessage"
        type="error"
        show-icon
        :closable="false"
      />

      <section class="status-strip" aria-label="监测概览">
        <article class="status-card status-card-time">
          <div class="status-card-top">
            <span class="status-label">数据更新时间</span>
            <span class="status-index">01</span>
          </div>
          <strong>{{ lastUpdatedAt || '暂无数据' }}</strong>
          <small>{{ loading ? '正在同步平台数据' : `距下次刷新还有 ${refreshCountdown} 秒` }}</small>
          <span class="status-progress"><i :style="{ width: `${refreshProgress}%` }"></i></span>
        </article>

        <article class="status-card status-card-device">
          <div class="status-card-top">
            <span class="status-label">接入设备</span>
            <span class="status-index">02</span>
          </div>
          <strong>{{ devices.length }}<em>台</em></strong>
          <small>在线 {{ onlineDeviceCount }} 台 · 离线 {{ offlineDeviceCount }} 台</small>
          <span class="status-progress"><i :style="{ width: `${onlineRate}%` }"></i></span>
        </article>

        <article class="status-card status-card-record">
          <div class="status-card-top">
            <span class="status-label">最新记录</span>
            <span class="status-index">03</span>
          </div>
          <strong>{{ latestRows.length }}<em>条</em></strong>
          <small>设备最新状态 · 历史表共 {{ records.length }} 条</small>
          <span class="status-progress"><i :style="{ width: `${dataIntegrityRate}%` }"></i></span>
        </article>

        <article class="status-card status-card-alert" :class="{ active: alertTotal > 0 }">
          <div class="status-card-top">
            <span class="status-label">异常提示</span>
            <span class="status-index">04</span>
          </div>
          <strong>{{ alertTotal }}<em>条</em></strong>
          <small>{{ alertTotal ? `高风险 ${highAlertCount} 条，请及时关注` : '当前未发现异常信息' }}</small>
          <span class="status-progress"><i :style="{ width: alertTotal ? '100%' : '0%' }"></i></span>
        </article>
      </section>

      <div class="section-heading">
        <div>
          <span class="section-eyebrow">REAL-TIME METRICS</span>
          <h2>关键环境指标</h2>
        </div>
        <p>展示最新一条真实传感器记录，并标记数据质量与异常状态。</p>
      </div>

     <section class="metric-grid">
  <article
    v-for="(item, index) in metrics"
    :key="item.code"
    class="metric-item"
    :class="[item.status, `metric-${index + 1}`]"
  >
    <!-- 顶部彩色强调线 -->
    <span class="metric-accent-line"></span>

    <!-- 右侧半透明背景图标 -->
    <div class="metric-background-icon">
      <el-icon>
        <component :is="item.icon" />
      </el-icon>
    </div>

    <!-- 卡片顶部 -->
    <div class="metric-header">
      <div class="metric-title-group">
        <div class="metric-icon">
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
        </div>

        <div class="metric-title-text">
          <span class="metric-label">{{ item.label }}</span>
          <small>实时监测数据</small>
        </div>
      </div>

      <span class="metric-state">
        <i></i>
        {{
          item.status === 'normal'
            ? '运行正常'
            : item.status === 'empty'
              ? '等待接入'
              : '需要关注'
        }}
      </span>
    </div>

    <!-- 核心数值区域 -->
    <div class="metric-main">
      <div class="metric-value-row">
        <strong>{{ item.value }}</strong>
        <small v-if="item.unit">{{ item.unit }}</small>
      </div>

      <span
        v-if="item.trendAvailable"
        class="metric-trend"
        :class="item.trendDirection"
        :title="`较前一条真实记录变化 ${item.trendText}`"
      >
        <b>
          {{
            item.trendDirection === 'up'
              ? '↑'
              : item.trendDirection === 'down'
                ? '↓'
                : '—'
          }}
        </b>
        {{ item.trendText }}
      </span>

      <span v-else class="metric-trend neutral">
        <b>—</b>
        暂无趋势
      </span>
    </div>

    <!-- 底部信息 -->
    <div class="metric-footer">
      <span class="metric-footer-dot"></span>
      <p :title="item.note">{{ item.note }}</p>
    </div>
  </article>
</section>

      <div class="section-heading chart-section-heading">
        <div>
          <span class="section-eyebrow">TREND & ALERT</span>
          <h2>趋势分析与风险状态</h2>
        </div>
        <p>{{ autoRefreshText }}</p>
      </div>

      <section class="content-grid">
        <el-card shadow="never" class="chart-panel surface-card air-panel">
          <template #header>
            <div class="panel-heading">
              <div>
                <span class="panel-eyebrow">AIR CONDITION</span>
                <h3>空气温湿度变化</h3>
              </div>
              <span class="panel-meta">{{ selectedScopeName }}</span>
            </div>
          </template>
          <div ref="airChartRef" class="chart chart-main"></div>
        </el-card>

        <el-card shadow="never" class="alert-panel surface-card">
  <template #header>
    <div class="panel-heading alert-panel-heading">
      <div>
        <span class="panel-eyebrow">RISK CENTER</span>
        <h3>环境风险与设备异常</h3>
      </div>

      <div class="alert-total">
        <span class="alert-total-dot" :class="{ active: alertTotal > 0 }"></span>
        <strong>{{ alertTotal }}</strong>
        <small>条待关注</small>
      </div>
    </div>
  </template>

  <div v-if="alertTotal" class="risk-center">
    <!-- 顶部风险概览 -->
    <div class="risk-overview">
      <article class="risk-overview-card environment-risk">
        <div class="risk-overview-icon">
          <el-icon><Warning /></el-icon>
        </div>

        <div class="risk-overview-info">
          <span>农业环境风险</span>
          <small>温湿度、土壤及气象指标</small>
        </div>

        <div class="risk-overview-value">
          <strong>{{ environmentAlerts.length }}</strong>
          <small>条</small>
        </div>
      </article>

      <article class="risk-overview-card device-risk">
        <div class="risk-overview-icon">
          <el-icon><Monitor /></el-icon>
        </div>

        <div class="risk-overview-info">
          <span>设备运行异常</span>
          <small>离线、预警及通信状态</small>
        </div>

        <div class="risk-overview-value">
          <strong>{{ deviceAlerts.length }}</strong>
          <small>条</small>
        </div>
      </article>
    </div>

    <!-- 农业环境风险 -->
    <section class="risk-section">
      <div class="risk-section-heading">
        <div>
          <span class="risk-section-mark environment"></span>
          <strong>农业环境风险</strong>
        </div>

        <span class="risk-section-count">
          {{ environmentAlerts.length }} 条
        </span>
      </div>

      <div v-if="environmentAlerts.length" class="alert-list">
        <article
          v-for="item in environmentAlerts"
          :key="`${item.title}-${item.deviceId}-${item.observedAt}`"
          class="alert-item"
          :class="`level-${item.level || 'low'}`"
        >
          <!-- 左侧风险等级 -->
          <div class="alert-level-box" :class="item.level">
            <span class="alert-level-icon">!</span>
            <small>
              {{
                item.level === 'high'
                  ? '高风险'
                  : item.level === 'medium'
                    ? '中风险'
                    : '低风险'
              }}
            </small>
          </div>

          <!-- 中间告警内容 -->
          <div class="alert-content">
            <div class="alert-content-title">
              <strong>{{ item.title }}</strong>

              <span class="alert-type-tag">
                环境指标
              </span>
            </div>

            <p>{{ item.content }}</p>
          </div>

          <!-- 右侧设备及时间 -->
          <div class="alert-meta">
            <div class="alert-device">
              <el-icon><Location /></el-icon>
              <span>{{ item.deviceName || item.deviceAddr || '未知设备' }}</span>
            </div>

            <small>{{ formatDateTime(item.observedAt) }}</small>
          </div>
        </article>
      </div>

      <div v-else class="risk-empty-row">
        <span class="risk-empty-icon">✓</span>
        <div>
          <strong>环境指标运行正常</strong>
          <p>当前未检测到真实农业环境风险。</p>
        </div>
      </div>
    </section>

    <!-- 设备运行异常 -->
    <section class="risk-section">
      <div class="risk-section-heading">
        <div>
          <span class="risk-section-mark device"></span>
          <strong>设备运行异常</strong>
        </div>

        <span class="risk-section-count">
          {{ deviceAlerts.length }} 条
        </span>
      </div>

      <div v-if="deviceAlerts.length" class="alert-list">
        <article
          v-for="item in deviceAlerts"
          :key="`${item.title}-${item.deviceId}-${item.observedAt}`"
          class="alert-item"
          :class="`level-${item.level || 'low'}`"
        >
          <!-- 左侧风险等级 -->
          <div class="alert-level-box" :class="item.level">
            <span class="alert-level-icon">!</span>
            <small>
              {{
                item.level === 'high'
                  ? '高风险'
                  : item.level === 'medium'
                    ? '中风险'
                    : '低风险'
              }}
            </small>
          </div>

          <!-- 中间异常内容 -->
          <div class="alert-content">
            <div class="alert-content-title">
              <strong>{{ item.title }}</strong>

              <span class="alert-type-tag device">
                设备状态
              </span>
            </div>

            <p>{{ item.content }}</p>
          </div>

          <!-- 右侧设备及时间 -->
          <div class="alert-meta">
            <div class="alert-device">
              <el-icon><Monitor /></el-icon>
              <span>{{ item.deviceName || item.deviceAddr || '未知设备' }}</span>
            </div>

            <small>{{ formatDateTime(item.observedAt) }}</small>
          </div>
        </article>
      </div>

      <div v-else class="risk-empty-row">
        <span class="risk-empty-icon">✓</span>
        <div>
          <strong>监测设备运行正常</strong>
          <p>当前未检测到真实设备异常。</p>
        </div>
      </div>
    </section>
  </div>

  <!-- 无任何风险 -->
  <div v-else class="empty-state risk-empty-state">
    <div class="risk-safe-visual">
      <span class="risk-safe-ring ring-one"></span>
      <span class="risk-safe-ring ring-two"></span>
      <span class="risk-safe-icon">✓</span>
    </div>

    <strong>当前环境运行平稳</strong>
    <p>暂未检测到真实环境风险或设备异常。</p>

    <div class="safe-status-list">
      <span>
        <i></i>
        环境指标正常
      </span>

      <span>
        <i></i>
        设备运行正常
      </span>
    </div>
  </div>
</el-card>

        <el-card shadow="never" class="chart-panel surface-card soil-panel">
          <template #header>
            <div class="panel-heading">
              <div>
                <span class="panel-eyebrow">SOIL CONDITION</span>
                <h3>土壤水热状态</h3>
              </div>
              <span class="panel-meta">温度 / 水分</span>
            </div>
          </template>
          <div ref="soilChartRef" class="chart chart-secondary"></div>
        </el-card>

        <el-card shadow="never" class="chart-panel surface-card weather-panel">
          <template #header>
            <div class="panel-heading">
              <div>
                <span class="panel-eyebrow">WEATHER FACTORS</span>
                <h3>光照、CO₂ 与降雨</h3>
              </div>
              <span class="panel-meta">真实历史曲线</span>
            </div>
          </template>
          <div ref="weatherChartRef" class="chart chart-secondary"></div>
        </el-card>
      </section>

      <el-card shadow="never" class="table-panel surface-card">
        <template #header>
          <div class="panel-heading table-heading">
            <div>
              <span class="panel-eyebrow">HISTORY RECORDS</span>
              <h3>全部历史监测记录</h3>
            </div>
            <div class="table-heading-meta">
              <span>
                第 {{ paginationStart }}–{{ paginationEnd }} 条 /
                筛选后 {{ filteredRecords.length }} 条
              </span>
              <em>数据库全部历史记录，共 {{ records.length }} 条</em>
            </div>
          </div>
        </template>

        <div class="record-toolbar">
          <div class="record-search">
            <el-input
              v-model="recordKeyword"
              clearable
              prefix-icon="Search"
              placeholder="搜索设备名称或采集时间"
            />
            <el-select v-model="recordView" class="record-view-select">
              <el-option label="全部记录" value="all" />
              <el-option label="设备正常" value="normal" />
              <el-option label="设备异常" value="deviceAbnormal" />
              <el-option label="数据异常" value="dataAbnormal" />
            </el-select>
          </div>
          <div class="record-health">
            <span><i class="health-dot normal"></i>正常 {{ normalRecordCount }}</span>
            <span><i class="health-dot warning"></i>需关注 {{ abnormalRecordCount }}</span>
          </div>
        </div>

        <div class="table-wrap">
          <el-table
            :data="paginatedRecords"
            stripe
            :empty-text="tableEmptyText"
            :row-class-name="tableRowClassName"
            max-height="520"
          >
            <el-table-column prop="time" label="采集时间" width="170" fixed="left" />
            <el-table-column prop="device" label="监测设备" min-width="170" show-overflow-tooltip />
            <el-table-column prop="temperature" label="空气温度(℃)" min-width="125" align="center" />
            <el-table-column prop="humidity" label="空气湿度(%)" min-width="125" align="center" />
            <el-table-column prop="soilTemp" label="土壤温度(℃)" min-width="125" align="center" />
            <el-table-column prop="soilMoisture" label="土壤水分(%)" min-width="125" align="center" />
            <el-table-column prop="light" label="光照" min-width="105" align="center" />
            <el-table-column prop="co2" label="CO₂(ppm)" min-width="110" align="center" />
            <el-table-column prop="battery" label="电池电量(%)" min-width="120" align="center" />
            <el-table-column label="设备状态" align="center" width="112" fixed="right">
              <template #default="scope">
                <el-tag :type="statusTagType(scope.row.deviceStatus)" effect="plain" round>
                  {{ deviceStatusText(scope.row.deviceStatus) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="质量状态" align="center" width="112" fixed="right">
              <template #default="scope">
                <el-tag :type="scope.row.quality === 'normal' ? 'success' : 'warning'" effect="plain" round>
                  {{ qualityText(scope.row.quality) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <div class="record-pagination">
          <el-pagination
            v-model:current-page="recordCurrentPage"
            :page-size="recordPageSize"
            :total="filteredRecords.length"
            background
            layout="total, prev, pager, next, jumper"
            @current-change="handleRecordPageChange"
          />
        </div>
      </el-card>
    </main>
  </div>
</template>


<script setup name="EnvironmentMonitor">
import * as echarts from 'echarts'
import AgriPageHeader from '@/components/AgriPageHeader'
import {
  getEnvironmentAlerts,
  getEnvironmentHistory,
  getEnvironmentLatest,
  listAgriDevices
} from '@/api/agriculture/environment'

const { proxy } = getCurrentInstance()

const metricDefs = [
  { code: 'air_temperature', label: '空气温度', unit: '℃', icon: 'Sunny' },
  { code: 'relative_humidity', label: '空气湿度', unit: '%', icon: 'Pouring' },
  { code: 'soil_temperature', label: '土壤温度', unit: '℃', icon: 'Sunrise' },
  { code: 'soil_moisture', label: '土壤水分', unit: '%', icon: 'Drizzling' },
  { code: 'illuminance', label: '光照强度', unit: '', icon: 'Odometer' },
  { code: 'co2_concentration', label: 'CO2浓度', unit: 'ppm', icon: 'Connection' },
  { code: 'battery_level', label: '电池电量', unit: '%', icon: 'Battery' },
  { code: 'rainfall', label: '降雨数据', unit: 'mm', icon: 'Cloudy' }
]

const filters = reactive({
  baseId: '',
  plotId: '',
  deviceId: undefined,
  dateRange: defaultDateRange()
})
const loading = ref(false)
const errorMessage = ref('')
const devices = ref([])
const latestRows = ref([])

/* 当前时间范围内的历史数据：只用于趋势曲线 */
const historyRows = ref([])

/* 不受顶部时间范围限制的全部历史数据：用于历史记录表格 */
const allHistoryRows = ref([])

const environmentAlerts = ref([])
const deviceAlerts = ref([])
const lastUpdatedAt = ref('')
const airChartRef = ref()
const soilChartRef = ref()
const weatherChartRef = ref()
const refreshCountdown = ref(60)
const recordKeyword = ref('')
const recordView = ref('all')
const recordCurrentPage = ref(1)
const recordPageSize = 10
let charts = []
let refreshTimer = null
let countdownTimer = null
let resizeObserver = null

const chartTextColor = '#3f5948'
const chartMutedColor = '#718177'
const chartGridLine = 'rgba(74, 128, 82, 0.14)'
const tooltipStyle = {
  backgroundColor: 'rgba(255, 255, 255, 0.98)',
  borderColor: 'rgba(74, 128, 82, 0.24)',
  borderWidth: 1,
  padding: [10, 12],
  textStyle: { color: '#3f5948', fontSize: 12 }
}

const baseOptions = computed(() => {
  const values = uniqueOptions(devices.value.map(item => item.baseId).filter(Boolean))
  return values.map(value => ({ value, label: value }))
})

const plotOptions = computed(() => {
  const values = devices.value
    .filter(item => !filters.baseId || item.baseId === filters.baseId)
    .map(item => item.plotId)
    .filter(Boolean)
  return uniqueOptions(values).map(value => ({ value, label: value }))
})

const deviceOptions = computed(() => {
  return devices.value.filter(item => {
    if (filters.baseId && item.baseId !== filters.baseId) return false
    if (filters.plotId && item.plotId !== filters.plotId) return false
    return true
  })
})

const selectedLatest = computed(() => {
  if (!latestRows.value.length) return null
  const rows = [...latestRows.value].sort((a, b) => new Date(b.observedAt || b.lastSeenAt || 0) - new Date(a.observedAt || a.lastSeenAt || 0))
  return rows[0]
})

const metrics = computed(() => {
  const metricMap = selectedLatest.value?.metrics || {}
  return metricDefs.map(def => {
    const item = metricMap[def.code]
    const hasValue = item && item.value !== null && item.value !== undefined
    const unit = hasValue ? (item.unit || def.unit) : ''
    return {
      ...def,
      value: hasValue ? formatNumber(item.value) : '暂无数据',
      unit,
      status: metricStatus(item),
      note: metricNote(item),
      ...metricTrend(def.code)
    }
  })
})

const records = computed(() => {
  const grouped = new Map()

  allHistoryRows.value.forEach(item => {
    const observedAt = item.observedAt || item.collectTime || item.timestamp
    if (!observedAt || !item.metricCode) return

    const deviceKey = item.deviceId || item.deviceAddr || item.nodeId || 'unknown-device'
    const groupKey = `${deviceKey}__${observedAt}`

    if (!grouped.has(groupKey)) {
      grouped.set(groupKey, {
        key: groupKey,
        observedAt,
        deviceId: item.deviceId,
        deviceAddr: item.deviceAddr,
        deviceName: item.deviceName,
        baseId: item.baseId,
        plotId: item.plotId,
        metrics: {}
      })
    }

    grouped.get(groupKey).metrics[item.metricCode] = item
  })

  return [...grouped.values()]
    .map(row => {
      const metrics = row.metrics || {}
      return {
        key: row.key,
        observedAt: row.observedAt,
        time: formatDateTime(row.observedAt),
        device: row.deviceName || row.deviceAddr || '--',
        temperature: metricCell(metrics.air_temperature),
        humidity: metricCell(metrics.relative_humidity),
        soilTemp: metricCell(metrics.soil_temperature),
        soilMoisture: metricCell(metrics.soil_moisture),
        light: metricCell(metrics.illuminance, true),
        co2: metricCell(metrics.co2_concentration),
        battery: metricCell(metrics.battery_level),
        deviceStatus: resolveHistoryDeviceStatus(row),
        quality: rowQuality(metrics)
      }
    })
    .sort((a, b) => new Date(b.observedAt || 0) - new Date(a.observedAt || 0))
})

const alertTotal = computed(() => environmentAlerts.value.length + deviceAlerts.value.length)
const highAlertCount = computed(() => [...environmentAlerts.value, ...deviceAlerts.value].filter(item => item.level === 'high').length)
const onlineDeviceCount = computed(() => devices.value.filter(item => item.deviceStatus === 'normal').length)
const offlineDeviceCount = computed(() => devices.value.filter(item => item.deviceStatus === 'offline').length)
const onlineRate = computed(() => devices.value.length ? Math.round((onlineDeviceCount.value / devices.value.length) * 100) : 0)
const refreshProgress = computed(() => Math.max(0, Math.min(100, Math.round((refreshCountdown.value / 60) * 100))))
const dataIntegrityRate = computed(() => {
  let total = 0
  let valid = 0
  latestRows.value.forEach(row => {
    Object.values(row.metrics || {}).forEach(item => {
      total += 1
      if (item && item.value !== null && item.value !== undefined && !['invalid', 'unmapped'].includes(item.qualityFlag)) valid += 1
    })
  })
  return total ? Math.round((valid / total) * 100) : 0
})
const filteredRecords = computed(() => {
  const keyword = recordKeyword.value.trim().toLowerCase()
  return records.value.filter(row => {
    const matchKeyword = !keyword || `${row.device} ${row.time}`.toLowerCase().includes(keyword)
    let matchView = true
    if (recordView.value === 'normal') matchView = row.deviceStatus === 'normal' && row.quality === 'normal'
    if (recordView.value === 'deviceAbnormal') matchView = ['offline', 'alarming', 'preAlarming'].includes(row.deviceStatus)
    if (recordView.value === 'dataAbnormal') matchView = row.quality !== 'normal'
    return matchKeyword && matchView
  })
})

const paginatedRecords = computed(() => {
  const start = (recordCurrentPage.value - 1) * recordPageSize
  return filteredRecords.value.slice(start, start + recordPageSize)
})

const paginationStart = computed(() => {
  if (!filteredRecords.value.length) return 0
  return (recordCurrentPage.value - 1) * recordPageSize + 1
})

const paginationEnd = computed(() => {
  return Math.min(
    recordCurrentPage.value * recordPageSize,
    filteredRecords.value.length
  )
})

const normalRecordCount = computed(() => records.value.filter(row => row.deviceStatus === 'normal' && row.quality === 'normal').length)
const abnormalRecordCount = computed(() => records.value.length - normalRecordCount.value)
const autoRefreshText = computed(() => lastUpdatedAt.value ? `自动刷新 ${refreshCountdown}s · 最近同步 ${lastUpdatedAt.value}` : `自动刷新 ${refreshCountdown}s`)
const selectedScopeName = computed(() => {
  const device = devices.value.find(item => item.deviceId === filters.deviceId)
  if (device) return device.deviceName || device.deviceAddr
  return filters.plotId || filters.baseId || '全部设备'
})
const tableEmptyText = computed(() => errorMessage.value || '暂无真实监测数据')

function defaultDateRange() {
  const end = new Date()
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
  return [formatPickerTime(start), formatPickerTime(end)]
}

function onBaseChange() {
  filters.plotId = ''
  filters.deviceId = undefined
  loadData()
}

async function loadData() {
  if (loading.value) return
  loading.value = true
  errorMessage.value = ''
  try {
    const baseParams = buildParams()
    /* 趋势图：按顶部选择的时间范围查询 */
    const historyParams = {
      ...buildParams(true),
      metricCodes: metricDefs.map(item => item.code).join(',')
    }

    /* 历史记录表格：不传 startTime/endTime，读取全部历史记录 */
    const allHistoryParams = {
      ...buildParams(false),
      metricCodes: metricDefs.map(item => item.code).join(',')
    }

    const [
      deviceRes,
      latestRes,
      historyRes,
      allHistoryRes,
      alertRes
    ] = await Promise.all([
      listAgriDevices(baseParams),
      getEnvironmentLatest(baseParams),
      getEnvironmentHistory(historyParams),
      getEnvironmentHistory(allHistoryParams),
      getEnvironmentAlerts(baseParams)
    ])
    devices.value = normalizeArray(deviceRes)
    latestRows.value = normalizeArray(latestRes)

    /* 曲线使用当前时间范围数据 */
    historyRows.value = normalizeArray(historyRes)

    /* 表格使用全部历史数据 */
    allHistoryRows.value = normalizeArray(allHistoryRes)

    recordCurrentPage.value = 1
    const alerts = alertRes.data || {}
    environmentAlerts.value = alerts.environmentAlerts || []
    deviceAlerts.value = alerts.deviceAlerts || []
    lastUpdatedAt.value = formatDateTime(new Date())
    refreshCountdown.value = 60
    await nextTick()
    renderCharts()
  } catch (error) {
    errorMessage.value = '真实环境监测接口请求失败，请检查后台服务、数据库和物联网网关连接。'
    latestRows.value = []
    historyRows.value = []
    allHistoryRows.value = []
    environmentAlerts.value = []
    deviceAlerts.value = []
    await nextTick()
    renderCharts()
  } finally {
    loading.value = false
  }
}

async function exportData() {
  try {
    const res = await getEnvironmentHistory({
      ...buildParams(true),
      metricCodes: metricDefs.map(item => item.code).join(',')
    })
    const rows = normalizeArray(res)
    if (!rows.length) {
      proxy.$modal.msgWarning('暂无真实历史数据可导出')
      return
    }
    const header = ['采集时间', '设备地址', '设备名称', '地块', '指标', '数值', '单位', '质量状态', '报警等级']
    const csvRows = rows.map(item => [
      formatDateTime(item.observedAt),
      item.deviceAddr || '',
      item.deviceName || '',
      item.plotId || '',
      item.metricCode || '',
      item.value ?? '',
      item.unit || '',
      item.qualityFlag || '',
      item.alarmLevel ?? ''
    ])
    downloadCsv([header, ...csvRows], `田间环境监测_${formatFileTime(new Date())}.csv`)
  } catch (error) {
    proxy.$modal.msgError('导出失败，请先确认真实历史接口可用')
  }
}

function renderCharts() {
  if (!airChartRef.value || !soilChartRef.value || !weatherChartRef.value) return
  const air = echarts.getInstanceByDom(airChartRef.value) || echarts.init(airChartRef.value)
  const soil = echarts.getInstanceByDom(soilChartRef.value) || echarts.init(soilChartRef.value)
  const weather = echarts.getInstanceByDom(weatherChartRef.value) || echarts.init(weatherChartRef.value)

  air.setOption(lineOption([
    { code: 'air_temperature', name: '空气温度', color: '#57c8d7', unit: '℃', axis: 0 },
    { code: 'relative_humidity', name: '相对湿度', color: '#4bd3a2', unit: '%', axis: 1 }
  ], '暂无真实空气温湿度历史数据'), true)
  soil.setOption(lineOption([
    { code: 'soil_temperature', name: '土壤温度', color: '#efc66d', unit: '℃', axis: 0 },
    { code: 'soil_moisture', name: '土壤水分', color: '#58b9d7', unit: '%', axis: 1 }
  ], '暂无真实土壤历史数据'), true)
  weather.setOption(lineOption([
    { code: 'illuminance', name: '光照', color: '#e9ad68', unit: 'Lux', axis: 0 },
    { code: 'co2_concentration', name: 'CO₂', color: '#8faee6', unit: 'ppm', axis: 1 },
    { code: 'rainfall', name: '降雨', color: '#52c9b5', unit: 'mm', axis: 2, type: 'bar' }
  ], '暂无真实光照、CO₂ 或降雨历史数据'), true)
  charts = [air, soil, weather]
}

function lineOption(seriesDefs, emptyText) {
  const rows = historyRows.value.filter(item => seriesDefs.some(def => def.code === item.metricCode))
  const times = uniqueOptions(rows.map(item => item.observedAt).filter(Boolean)).sort((a, b) => new Date(a) - new Date(b))
  const labels = times.map(formatChartTime)
  const valueMap = new Map()
  rows.forEach(item => valueMap.set(`${item.metricCode}__${item.observedAt}`, item.value))

  const yAxisCount = Math.max(1, ...seriesDefs.map(def => (def.axis ?? 0) + 1))
  const axisDefs = Array.from({ length: yAxisCount }, (_, axisIndex) => {
    const def = seriesDefs.find(item => (item.axis ?? 0) === axisIndex) || seriesDefs[0]
    const isLeft = axisIndex === 0
    return {
      type: 'value',
      scale: true,
      position: isLeft ? 'left' : 'right',
      offset: axisIndex > 1 ? (axisIndex - 1) * 48 : 0,
      name: def.unit || '',
      nameGap: 10,
      nameTextStyle: { color: def.color, fontSize: 10, fontWeight: 600 },
      axisLabel: {
        color: chartMutedColor,
        fontSize: 10,
        margin: 10,
        formatter: value => formatAxisValue(value)
      },
      axisLine: {
        show: axisIndex > 0,
        lineStyle: { color: `${def.color}45` }
      },
      axisTick: { show: false },
      splitNumber: 5,
      splitLine: {
        show: axisIndex === 0,
        lineStyle: { type: 'dashed', color: chartGridLine }
      }
    }
  })

  const series = seriesDefs.map((def, index) => {
    const isBar = def.type === 'bar'
    return {
      name: def.name,
      type: isBar ? 'bar' : 'line',
      yAxisIndex: def.axis ?? 0,
      smooth: isBar ? false : 0.35,
      showSymbol: true,
      symbol: 'circle',
      symbolSize: 7,
      connectNulls: false,
      barMaxWidth: 12,
      barMinHeight: 2,
      emphasis: { focus: 'series', scale: true },
      lineStyle: isBar ? undefined : { width: 2.4, color: def.color, cap: 'round' },
      itemStyle: isBar
        ? { color: def.color, borderRadius: [4, 4, 0, 0], opacity: 0.78 }
        : { color: def.color, borderColor: '#ffffff', borderWidth: 2 },
      areaStyle: isBar ? undefined : {
        opacity: 1,
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: `${def.color}30` },
          { offset: 0.72, color: `${def.color}08` },
          { offset: 1, color: `${def.color}00` }
        ])
      },
      data: times.map(time => {
        const value = valueMap.get(`${def.code}__${time}`)
        return value !== null && value !== undefined && Number.isFinite(Number(value)) ? Number(value) : null
      }),
      z: isBar ? 1 : 3 + index
    }
  })

  const rightAxisSpace = Math.max(0, yAxisCount - 1) * 48

  return {
    animationDuration: 650,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      confine: true,
      axisPointer: {
        type: 'cross',
        crossStyle: { color: 'rgba(112, 195, 184, 0.28)' },
        lineStyle: { color: 'rgba(112, 195, 184, 0.36)', width: 1 }
      },
      formatter: params => {
        if (!params?.length) return ''
        const lines = params.map(param => {
          const def = seriesDefs[param.seriesIndex]
          const value = param.value === null || param.value === undefined ? '--' : formatNumber(param.value)
          return `${param.marker}<span style="color:#718177">${param.seriesName}</span><b style="float:right;margin-left:22px;color:#183322">${value} ${def?.unit || ''}</b>`
        })
        return `<div style="margin-bottom:7px;color:#183322;font-weight:700">${params[0].axisValue}</div>${lines.join('<br/>')}`
      },
      ...tooltipStyle
    },
    color: seriesDefs.map(item => item.color),
    legend: {
      data: seriesDefs.map(item => item.name),
      top: 0,
      right: 4,
      itemWidth: 14,
      itemHeight: 7,
      itemGap: 18,
      icon: 'roundRect',
      selectedMode: true,
      textStyle: { color: chartTextColor, fontSize: 11, fontWeight: 600 }
    },
    grid: { left: 52, right: 24 + rightAxisSpace, top: 48, bottom: 36, containLabel: false },
    dataZoom: [
      { type: 'inside', xAxisIndex: 0, filterMode: 'none', zoomOnMouseWheel: true, moveOnMouseMove: true }
    ],
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: seriesDefs.some(item => item.type === 'bar'),
      axisLabel: { color: chartMutedColor, fontSize: 10, margin: 13, hideOverlap: true },
      axisLine: { lineStyle: { color: 'rgba(74, 128, 82, 0.18)' } },
      axisTick: { show: false }
    },
    yAxis: yAxisCount === 1 ? axisDefs[0] : axisDefs,
    graphic: rows.length ? [] : [{
      type: 'group',
      left: 'center',
      top: 'middle',
      children: [
        {
          type: 'circle',
          shape: { cx: 0, cy: -13, r: 17 },
          style: { fill: 'rgba(79, 154, 90, 0.08)', stroke: 'rgba(79, 154, 90, 0.20)' }
        },
        {
          type: 'text',
          left: -4,
          top: -22,
          style: { text: '—', fill: '#4f9a5a', fontSize: 18, fontWeight: 700 }
        },
        {
          type: 'text',
          left: 'center',
          top: 18,
          style: { text: emptyText, fill: '#718177', fontSize: 12, fontWeight: 600, textAlign: 'center' }
        }
      ]
    }],
    series
  }
}

function metricTrend(metricCode) {
  let rows = historyRows.value.filter(item => item.metricCode === metricCode && Number.isFinite(Number(item.value)))
  const latest = selectedLatest.value
  if (latest) {
    const scoped = rows.filter(item => {
      if (latest.deviceId && item.deviceId) return item.deviceId === latest.deviceId
      if (latest.deviceAddr && item.deviceAddr) return item.deviceAddr === latest.deviceAddr
      return true
    })
    if (scoped.length >= 2) rows = scoped
  }
  rows.sort((a, b) => new Date(a.observedAt || 0) - new Date(b.observedAt || 0))
  if (rows.length < 2) {
    return { trendAvailable: false, trendDirection: 'neutral', trendText: '--' }
  }
  const previous = Number(rows.at(-2).value)
  const current = Number(rows.at(-1).value)
  const delta = current - previous
  const precision = Math.abs(delta) >= 10 ? 0 : 1
  return {
    trendAvailable: true,
    trendDirection: delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral',
    trendText: `${delta > 0 ? '+' : ''}${delta.toFixed(precision)}`
  }
}

function formatAxisValue(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return value
  if (Math.abs(number) >= 10000) return `${(number / 1000).toFixed(0)}k`
  if (Math.abs(number) >= 1000) return `${(number / 1000).toFixed(1)}k`
  if (Math.abs(number) < 1 && number !== 0) return number.toFixed(1)
  return Number.isInteger(number) ? String(number) : number.toFixed(1)
}

function resolveHistoryDeviceStatus(row) {
  const latestRow = latestRows.value.find(item => {
    if (row.deviceId && item.deviceId) return item.deviceId === row.deviceId
    if (row.deviceAddr && item.deviceAddr) return item.deviceAddr === row.deviceAddr
    return false
  })

  if (latestRow?.deviceStatus) return latestRow.deviceStatus

  const device = devices.value.find(item => {
    if (row.deviceId && item.deviceId) return item.deviceId === row.deviceId
    if (row.deviceAddr && item.deviceAddr) return item.deviceAddr === row.deviceAddr
    return false
  })

  return device?.deviceStatus || 'normal'
}

function handleRecordPageChange(page) {
  recordCurrentPage.value = page
}

function tableRowClassName({ row }) {
  if (['offline', 'alarming'].includes(row.deviceStatus) || ['invalid', 'unmapped'].includes(row.quality)) return 'row-danger'
  if (row.deviceStatus === 'preAlarming' || row.quality !== 'normal') return 'row-warning'
  return ''
}

function buildParams(includeTime = false) {
  const params = {}
  if (filters.baseId) params.baseId = filters.baseId
  if (filters.plotId) params.plotId = filters.plotId
  if (filters.deviceId) params.deviceId = filters.deviceId
  if (includeTime && filters.dateRange?.length === 2) {
    params.startTime = toIso(filters.dateRange[0])
    params.endTime = toIso(filters.dateRange[1])
  }
  return params
}

function normalizeArray(response) {
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.rows)) return response.rows
  return []
}

function metricCell(metric, withUnit = false) {
  if (!metric || metric.value === null || metric.value === undefined) return '暂无数据'
  const value = formatNumber(metric.value)
  if (!withUnit) return value
  return `${value}${metric.unit || ''}`
}

function metricStatus(metric) {
  if (!metric) return 'empty'
  if (metric.qualityFlag === 'invalid' || metric.qualityFlag === 'unmapped') return 'warning'
  if (metric.alarmLevel && metric.alarmLevel !== 0) return 'alarm'
  return 'normal'
}

function metricNote(metric) {
  if (!metric) return '等待真实传感器数据'
  if (metric.qualityFlag === 'unmapped') return '未配置标准指标映射'
  if (metric.qualityFlag === 'invalid') return '原始数值无效'
  if (metric.alarmInfo) return metric.alarmInfo
  return `更新于 ${formatDateTime(metric.observedAt)}`
}

function rowQuality(metrics) {
  const values = Object.values(metrics || {})
  if (!values.length) return 'empty'
  if (values.some(item => item.qualityFlag === 'invalid')) return 'invalid'
  if (values.some(item => item.qualityFlag === 'unmapped')) return 'unmapped'
  return 'normal'
}

function qualityText(value) {
  const map = { normal: '正常', invalid: '无效', unmapped: '未映射', empty: '暂无数据' }
  return map[value] || value || '暂无数据'
}

function statusTagType(status) {
  if (status === 'normal') return 'success'
  if (status === 'offline') return 'danger'
  if (status === 'alarming') return 'danger'
  if (status === 'preAlarming') return 'warning'
  return 'info'
}

function deviceStatusText(status) {
  const map = { normal: '正常', offline: '离线', alarming: '报警', preAlarming: '预警' }
  return map[status] || status || '未知'
}

function formatNumber(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '暂无数据'
  return Number.isInteger(number) ? String(number) : number.toFixed(1)
}

function formatDateTime(value) {
  if (!value) return '暂无数据'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = item => String(item).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatPickerTime(date) {
  const pad = item => String(item).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function formatChartTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = item => String(item).padStart(2, '0')
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function formatFileTime(date) {
  return formatPickerTime(date).replace(/[-:\s]/g, '')
}

function toIso(value) {
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toISOString()
}

function uniqueOptions(values) {
  return [...new Set(values)]
}

function downloadCsv(rows, filename) {
  const content = rows.map(row => row.map(csvCell).join(',')).join('\n')
  const blob = new Blob([`\ufeff${content}`], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = filename
  link.click()
  URL.revokeObjectURL(link.href)
}

function csvCell(value) {
  const text = String(value ?? '')
  return `"${text.replace(/"/g, '""')}"`
}

function resizeCharts() {
  charts.forEach(chart => chart.resize())
}

watch([recordKeyword, recordView], () => {
  recordCurrentPage.value = 1
})

watch(
  () => filteredRecords.value.length,
  total => {
    const maxPage = Math.max(1, Math.ceil(total / recordPageSize))
    if (recordCurrentPage.value > maxPage) {
      recordCurrentPage.value = maxPage
    }
  }
)

onMounted(() => {
  loadData()
  refreshTimer = window.setInterval(loadData, 60000)
  countdownTimer = window.setInterval(() => {
    refreshCountdown.value = refreshCountdown.value > 0 ? refreshCountdown.value - 1 : 0
  }, 1000)
  window.addEventListener('resize', resizeCharts)

  if (window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => resizeCharts())
    ;[airChartRef.value, soilChartRef.value, weatherChartRef.value].filter(Boolean).forEach(element => resizeObserver.observe(element))
  }
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
  if (countdownTimer) window.clearInterval(countdownTimer)
  if (resizeObserver) resizeObserver.disconnect()
  window.removeEventListener('resize', resizeCharts)
  charts.forEach(chart => chart.dispose())
})
</script>

<style lang="scss" scoped>
/* =========================================================
   田间环境监测 · 专业浅色农业科技风
   设计原则：
   1. 白色与浅灰作为主背景，降低视觉疲劳
   2. 稻叶绿作为主品牌色，蓝绿与琥珀色作为数据辅助色
   3. 统一卡片圆角、阴影、字号和间距
   4. 保留所有现有接口、图表、筛选、自动刷新与导出逻辑
========================================================= */

.agri-page {
  --page-bg: #f3f7f3;
  --page-bg-deep: #edf3ee;
  --surface: rgba(255, 255, 255, 0.97);
  --surface-soft: #f7faf7;
  --surface-muted: #f1f6f2;
  --border: #dce8df;
  --border-strong: #c8dbcd;
  --text-main: #183626;
  --text-secondary: #4f6657;
  --text-muted: #7b8e81;
  --green: #3f8f59;
  --green-strong: #2f7446;
  --green-soft: #eaf5ec;
  --cyan: #3b93a7;
  --blue: #547fc4;
  --yellow: #d79b38;
  --danger: #d85f5f;

  position: relative;
  min-height: calc(100vh - 84px);
  overflow: hidden;
  color: var(--text-main);
  font-family:
    Inter,
    "PingFang SC",
    "Microsoft YaHei",
    Arial,
    sans-serif;
  background:
    radial-gradient(circle at 12% 0%, rgba(96, 166, 111, 0.12), transparent 26%),
    radial-gradient(circle at 90% 8%, rgba(75, 151, 177, 0.08), transparent 24%),
    linear-gradient(180deg, #f8fbf8 0%, var(--page-bg) 42%, var(--page-bg-deep) 100%);
}

.agri-page *,
.agri-page *::before,
.agri-page *::after {
  box-sizing: border-box;
}

.ambient {
  position: absolute;
  z-index: 0;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(100px);
  opacity: 0.11;
}

.ambient-left {
  top: 320px;
  left: -190px;
  background: #69b978;
}

.ambient-right {
  top: 700px;
  right: -200px;
  background: #6ca9c2;
}

.page-hero,
.page-content {
  position: relative;
  z-index: 1;
}

.page-hero {
  margin-bottom: 16px;
}

.page-content {
  width: min(100%, 1880px);
  margin: 0 auto;
  padding: 0 20px 30px;
}

/* =========================================================
   页面顶部实时状态与按钮
========================================================= */

.hero-live-status {
  display: flex;
  align-items: center;
  min-width: 176px;
  gap: 10px;
  padding: 7px 8px 7px 12px;
  border: 1px solid rgba(63, 143, 89, 0.2);
  border-radius: 12px;
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 6px 18px rgba(39, 93, 55, 0.08);
  backdrop-filter: blur(12px);
}

.hero-live-status > div {
  min-width: 0;
  flex: 1;
}

.hero-live-status strong,
.hero-live-status small {
  display: block;
  white-space: nowrap;
}

.hero-live-status strong {
  color: #245438;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 750;
}

.hero-live-status small {
  margin-top: 3px;
  color: var(--text-muted);
  font-size: 10px;
}

.hero-live-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 8px;
  border-radius: 50%;
  background: #46a766;
  box-shadow:
    0 0 0 4px rgba(70, 167, 102, 0.12),
    0 0 13px rgba(70, 167, 102, 0.32);
  animation: live-pulse 2.2s ease-in-out infinite;
}

.hero-live-status :deep(.el-progress-circle__track) {
  stroke: #e5eee7;
}

@keyframes live-pulse {
  0%,
  100% {
    opacity: 0.62;
    transform: scale(0.92);
  }

  50% {
    opacity: 1;
    transform: scale(1.06);
  }
}

:deep(.el-button:not(.is-link):not(.is-text):not(.el-button--text)) {
  min-height: 38px;
  border-color: #3f8f59 !important;
  border-radius: 9px;
  color: #ffffff !important;
  background: linear-gradient(180deg, #4b9e64, #377f4f) !important;
  box-shadow: 0 7px 17px rgba(45, 116, 70, 0.16);
  font-size: 12px;
  font-weight: 700;
}

:deep(.el-button:not(.is-link):not(.is-text):not(.el-button--text):hover) {
  border-color: #32784a !important;
  background: linear-gradient(180deg, #55a86c, #32784a) !important;
  box-shadow: 0 9px 22px rgba(45, 116, 70, 0.22);
}

:deep(.ghost-button:not(.is-link):not(.is-text):not(.el-button--text)) {
  color: #356848 !important;
  border-color: #cfe0d3 !important;
  background: #f6faf7 !important;
  box-shadow: none;
}

:deep(.ghost-button:not(.is-link):not(.is-text):not(.el-button--text):hover) {
  color: #245438 !important;
  border-color: #9fc3a8 !important;
  background: #ecf6ee !important;
}

:deep(.el-button:not(.is-link):not(.is-text):not(.el-button--text).is-disabled) {
  color: #98a69b !important;
  border-color: #dce5de !important;
  background: #eef2ef !important;
  box-shadow: none;
}

/* =========================================================
   通用卡片与标题
========================================================= */

.surface-card {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 15px;
  background: var(--surface);
  box-shadow:
    0 10px 30px rgba(39, 72, 48, 0.07),
    0 1px 2px rgba(39, 72, 48, 0.04);
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.surface-card:hover {
  border-color: #c9ddce;
  box-shadow:
    0 15px 38px rgba(39, 72, 48, 0.1),
    0 2px 4px rgba(39, 72, 48, 0.04);
}

.surface-card :deep(.el-card__header) {
  padding: 17px 20px 15px;
  border-bottom: 1px solid #e6eee8;
  background: linear-gradient(180deg, #ffffff, #fbfdfb);
}

.surface-card :deep(.el-card__body) {
  padding: 18px 20px 20px;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  gap: 20px;
}

.panel-heading h3 {
  margin: 5px 0 0;
  color: var(--text-main);
  font-size: 17px;
  line-height: 1.25;
  font-weight: 750;
  letter-spacing: 0.1px;
}

.panel-eyebrow,
.section-eyebrow {
  display: block;
  color: var(--green);
  font-size: 10px;
  line-height: 1;
  font-weight: 800;
  letter-spacing: 1.45px;
}

.panel-meta {
  flex: 0 0 auto;
  padding: 7px 11px;
  color: #2f6844;
  border: 1px solid #cce0d1;
  border-radius: 8px;
  background: #eef7f0;
  font-size: 12px;
  font-weight: 700;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin: 27px 2px 14px;
}

.section-heading h2 {
  margin: 6px 0 0;
  color: #173724;
  font-size: 22px;
  line-height: 1.22;
  font-weight: 780;
  letter-spacing: 0.1px;
}

.section-heading p {
  max-width: 620px;
  margin: 0 0 2px;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.55;
  text-align: right;
}

/* =========================================================
   监测范围筛选
========================================================= */

.filter-card {
  margin-bottom: 16px;
}

.filter-card :deep(.el-card__header) {
  padding-top: 15px;
  padding-bottom: 14px;
}

.filter-card :deep(.el-card__body) {
  padding-top: 17px;
  padding-bottom: 10px;
}

.scope-pill {
  display: flex;
  align-items: center;
  max-width: 46%;
  gap: 8px;
  padding: 7px 12px;
  overflow: hidden;
  color: #356848;
  border: 1px solid #cfe2d4;
  border-radius: 999px;
  background: #eff7f1;
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.scope-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: #4da269;
  box-shadow: 0 0 0 4px rgba(77, 162, 105, 0.1);
}

.filter-form {
  display: grid;
  grid-template-columns:
    minmax(160px, 0.9fr)
    minmax(160px, 0.9fr)
    minmax(190px, 1fr)
    minmax(390px, 1.65fr)
    auto;
  align-items: end;
  gap: 0 14px;
}

.filter-item,
.filter-action {
  width: 100%;
  margin-right: 0;
  margin-bottom: 10px;
}

.filter-card :deep(.el-form-item.filter-item) {
  display: block;
  width: 100%;
}

.filter-card :deep(.filter-item .el-form-item__label) {
  display: flex;
  width: 100%;
  height: 20px;
  align-items: center;
  justify-content: center;
  margin: 0 0 8px;
  padding: 0;
  color: #486452 !important;
  font-size: 12px;
  line-height: 20px;
  font-weight: 750;
  text-align: center;
}

.filter-card :deep(.filter-item .el-form-item__content) {
  display: block;
  width: 100%;
  margin-left: 0 !important;
  line-height: normal;
}

.filter-card :deep(.el-select),
.filter-card :deep(.el-date-editor),
.filter-card :deep(.el-form-item__content) {
  width: 100%;
}

.filter-card :deep(.el-input__wrapper),
.filter-card :deep(.el-select__wrapper),
.filter-card :deep(.el-date-editor.el-input__wrapper) {
  width: 100%;
  min-width: 0;
  min-height: 40px;
  border: 1px solid #d6e2d9 !important;
  border-radius: 9px;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(45, 78, 54, 0.03) !important;
  transition:
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.filter-card :deep(.el-input__wrapper:hover),
.filter-card :deep(.el-select__wrapper:hover),
.filter-card :deep(.el-date-editor.el-input__wrapper:hover) {
  border-color: #a9c8b1 !important;
}

.filter-card :deep(.el-input__wrapper.is-focus),
.filter-card :deep(.el-select__wrapper.is-focused),
.filter-card :deep(.el-date-editor.el-input__wrapper.is-active) {
  border-color: #5a9d6c !important;
  box-shadow: 0 0 0 3px rgba(63, 143, 89, 0.1) !important;
}

.filter-card :deep(.el-input__inner),
.filter-card :deep(.el-select__placeholder),
.filter-card :deep(.el-select__selected-item),
.filter-card :deep(.el-range-input),
.filter-card :deep(.el-range-separator),
.filter-card :deep(.el-input__icon),
.filter-card :deep(.el-select__caret) {
  color: #355441 !important;
  font-size: 12px;
}

.filter-card :deep(.el-select__selection) {
  display: flex;
  flex: 1;
  justify-content: center;
  min-width: 0;
}

.filter-card :deep(.el-select__selected-item),
.filter-card :deep(.el-select__placeholder),
.filter-card :deep(.el-input__inner) {
  text-align: center;
}

.filter-card :deep(.time-filter .el-range-input) {
  flex: 1;
  min-width: 0;
  text-align: center !important;
}

.filter-card :deep(.time-filter .el-range-separator) {
  display: flex;
  width: 34px;
  flex: 0 0 34px;
  align-items: center;
  justify-content: center;
  padding: 0;
  color: #607767 !important;
  font-weight: 700;
  text-align: center;
}

.filter-action {
  width: auto;
  justify-self: end;
}

.filter-action :deep(.el-button) {
  min-width: 132px;
  height: 40px;
}

.page-alert {
  margin-bottom: 16px;
  border-radius: 11px;
}

/* =========================================================
   顶部状态概览
========================================================= */

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 0;
}

.status-card {
  --card-accent: #4d9b64;

  position: relative;
  min-height: 122px;
  padding: 17px 18px 18px;
  overflow: hidden;
  border: 1px solid #dce8df;
  border-radius: 14px;
  background:
    radial-gradient(circle at 93% 12%, color-mix(in srgb, var(--card-accent) 10%, transparent), transparent 34%),
    linear-gradient(145deg, #ffffff, #f8fbf8);
  box-shadow:
    0 8px 24px rgba(42, 78, 51, 0.055),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
}

.status-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--card-accent) 30%, #dce8df);
  box-shadow: 0 13px 30px rgba(42, 78, 51, 0.085);
}

.status-card::before {
  position: absolute;
  top: 0;
  right: 16px;
  left: 16px;
  height: 3px;
  border-radius: 0 0 5px 5px;
  content: "";
  background: linear-gradient(90deg, transparent, var(--card-accent), transparent);
  opacity: 0.78;
}

.status-card::after {
  position: absolute;
  right: -34px;
  bottom: -50px;
  width: 130px;
  height: 130px;
  border: 1px solid color-mix(in srgb, var(--card-accent) 18%, transparent);
  border-radius: 50%;
  content: "";
  pointer-events: none;
}

.status-card-time {
  --card-accent: #4c92a8;
}

.status-card-device {
  --card-accent: #4a9a63;
}

.status-card-record {
  --card-accent: #667fc0;
}

.status-card-alert {
  --card-accent: #7d9282;
}

.status-card-alert.active {
  --card-accent: #d59a37;
}

.status-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.status-label {
  color: #506b59;
  font-size: 12px;
  font-weight: 700;
}

.status-index {
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  color: color-mix(in srgb, var(--card-accent) 85%, #203a2a);
  border: 1px solid color-mix(in srgb, var(--card-accent) 24%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--card-accent) 8%, white);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.4px;
}

.status-card > strong {
  position: relative;
  z-index: 1;
  display: block;
  min-height: 31px;
  margin-top: 11px;
  overflow: hidden;
  color: #173925;
  font-size: 24px;
  line-height: 1.2;
  font-weight: 780;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.status-card > strong em {
  margin-left: 5px;
  color: #607568;
  font-size: 12px;
  font-style: normal;
  font-weight: 700;
}

.status-card > small {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.45;
}

.status-progress {
  position: absolute;
  right: 18px;
  bottom: 11px;
  left: 18px;
  height: 3px;
  overflow: hidden;
  border-radius: 999px;
  background: #edf2ee;
}

.status-progress i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(
    90deg,
    var(--card-accent),
    color-mix(in srgb, var(--card-accent) 42%, white)
  );
  transition: width 0.4s ease;
}

/* =========================================================
   关键环境指标
========================================================= */

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-item {
  --metric-accent: #4d9b67;
  --metric-accent-rgb: 77, 155, 103;

  position: relative;
  display: flex;
  min-width: 0;
  min-height: 168px;
  padding: 18px 18px 15px;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid #dde8df;
  border-radius: 15px;
  background:
    radial-gradient(
      circle at 94% 88%,
      rgba(var(--metric-accent-rgb), 0.09),
      transparent 31%
    ),
    linear-gradient(
      145deg,
      rgba(var(--metric-accent-rgb), 0.045),
      transparent 40%
    ),
    #ffffff;
  box-shadow:
    0 9px 25px rgba(42, 78, 51, 0.055),
    inset 0 1px 0 #ffffff;
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease;
}

.metric-item:hover {
  transform: translateY(-3px);
  border-color: rgba(var(--metric-accent-rgb), 0.34);
  box-shadow:
    0 15px 34px rgba(42, 78, 51, 0.09),
    0 0 0 1px rgba(var(--metric-accent-rgb), 0.04);
}

.metric-accent-line {
  position: absolute;
  top: 0;
  right: 22px;
  left: 22px;
  height: 3px;
  border-radius: 0 0 5px 5px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(var(--metric-accent-rgb), 0.92),
    transparent
  );
}

.metric-background-icon {
  position: absolute;
  right: -10px;
  bottom: -20px;
  color: rgba(var(--metric-accent-rgb), 0.075);
  font-size: 92px;
  line-height: 1;
  pointer-events: none;
  transform: rotate(-8deg);
  transition:
    transform 0.3s ease,
    color 0.3s ease;
}

.metric-item:hover .metric-background-icon {
  color: rgba(var(--metric-accent-rgb), 0.11);
  transform: rotate(-4deg) scale(1.04);
}

.metric-1 {
  --metric-accent: #4d9d72;
  --metric-accent-rgb: 77, 157, 114;
}

.metric-2 {
  --metric-accent: #468fa5;
  --metric-accent-rgb: 70, 143, 165;
}

.metric-3 {
  --metric-accent: #d09a43;
  --metric-accent-rgb: 208, 154, 67;
}

.metric-4 {
  --metric-accent: #4f9c7a;
  --metric-accent-rgb: 79, 156, 122;
}

.metric-5 {
  --metric-accent: #d2943d;
  --metric-accent-rgb: 210, 148, 61;
}

.metric-6 {
  --metric-accent: #617fb9;
  --metric-accent-rgb: 97, 127, 185;
}

.metric-7 {
  --metric-accent: #579a6d;
  --metric-accent-rgb: 87, 154, 109;
}

.metric-8 {
  --metric-accent: #4d94ad;
  --metric-accent-rgb: 77, 148, 173;
}

.metric-item.warning,
.metric-item.alarm {
  --metric-accent: #d79636;
  --metric-accent-rgb: 215, 150, 54;
  border-color: rgba(215, 150, 54, 0.3);
}

.metric-item.empty {
  --metric-accent: #89978d;
  --metric-accent-rgb: 137, 151, 141;
  opacity: 0.9;
}

.metric-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  min-width: 0;
  gap: 10px;
}

.metric-title-group {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 11px;
}

.metric-icon {
  display: grid;
  width: 41px;
  height: 41px;
  flex: 0 0 41px;
  place-items: center;
  color: var(--metric-accent);
  border: 1px solid rgba(var(--metric-accent-rgb), 0.22);
  border-radius: 11px;
  background: rgba(var(--metric-accent-rgb), 0.08);
  font-size: 19px;
}

.metric-title-text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.metric-label {
  overflow: hidden;
  color: #244532;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 750;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.metric-title-text small {
  color: #839287;
  font-size: 9px;
  line-height: 1.2;
  font-weight: 650;
  letter-spacing: 0.45px;
}

.metric-state {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 5px;
  padding: 5px 8px;
  color: var(--metric-accent);
  border: 1px solid rgba(var(--metric-accent-rgb), 0.2);
  border-radius: 999px;
  background: rgba(var(--metric-accent-rgb), 0.07);
  font-size: 9px;
  line-height: 1;
  font-weight: 750;
  white-space: nowrap;
}

.metric-state i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 6px currentColor;
}

.metric-main {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  min-width: 0;
  gap: 10px;
  margin-top: 19px;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  min-width: 0;
  gap: 6px;
}

.metric-value-row strong {
  overflow: hidden;
  color: #183b27;
  font-size: clamp(26px, 1.65vw, 32px);
  line-height: 1;
  font-weight: 790;
  letter-spacing: -0.7px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.metric-value-row small {
  flex: 0 0 auto;
  color: #64776a;
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
}

.metric-trend {
  display: inline-flex;
  align-items: center;
  flex: 0 0 auto;
  gap: 4px;
  padding: 5px 8px;
  color: #6c7f71;
  border: 1px solid #dfe8e1;
  border-radius: 7px;
  background: #f7faf7;
  font-size: 9px;
  line-height: 1;
  font-weight: 750;
  white-space: nowrap;
}

.metric-trend b {
  font-size: 11px;
}

.metric-trend.up {
  color: #327d4c;
  border-color: #c9e2d0;
  background: #edf7ef;
}

.metric-trend.down {
  color: #397f94;
  border-color: #c9dfe5;
  background: #eef6f8;
}

.metric-trend.neutral {
  color: #7d8b81;
}

.metric-footer {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 7px;
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid #e9efea;
}

.metric-footer-dot {
  width: 5px;
  height: 5px;
  flex: 0 0 5px;
  border-radius: 50%;
  background: rgba(var(--metric-accent-rgb), 0.82);
}

.metric-footer p {
  min-width: 0;
  margin: 0;
  overflow: hidden;
  color: #7c8d81;
  font-size: 9px;
  line-height: 1.4;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* =========================================================
   图表与风险区域布局
========================================================= */

.content-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.air-panel {
  grid-column: span 8;
}

.alert-panel {
  grid-column: span 4;
}

.soil-panel,
.weather-panel {
  grid-column: span 6;
}

.chart {
  width: 100%;
}

.chart-main {
  height: 344px;
}

.chart-secondary {
  height: 282px;
}

/* =========================================================
   环境风险与设备异常
========================================================= */

.alert-panel :deep(.el-card__body) {
  height: 344px;
  padding: 14px 15px 16px;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #c6d8ca transparent;
}

.alert-panel :deep(.el-card__body::-webkit-scrollbar) {
  width: 5px;
}

.alert-panel :deep(.el-card__body::-webkit-scrollbar-thumb) {
  border-radius: 8px;
  background: #c6d8ca;
}

.alert-panel-heading {
  width: 100%;
}

.alert-total {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 7px 10px;
  color: #7f673d;
  border: 1px solid #ead9bd;
  border-radius: 9px;
  background: #fff8ec;
}

.alert-total-dot {
  width: 6px;
  height: 6px;
  margin-right: 2px;
  border-radius: 50%;
  background: #9aa89e;
}

.alert-total-dot.active {
  background: #d69a38;
  box-shadow: 0 0 8px rgba(214, 154, 56, 0.45);
  animation: alert-pulse 2s ease-in-out infinite;
}

.alert-total strong {
  color: #b27823;
  font-size: 16px;
  line-height: 1;
  font-weight: 800;
}

.alert-total small {
  color: #8b7b5d;
  font-size: 10px;
  font-weight: 700;
}

.risk-center {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.risk-overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.risk-overview-card {
  position: relative;
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr) auto;
  align-items: center;
  min-width: 0;
  min-height: 78px;
  gap: 10px;
  padding: 13px;
  overflow: hidden;
  border: 1px solid #dce7df;
  border-radius: 11px;
  background: #f9fbf9;
}

.risk-overview-card::after {
  position: absolute;
  right: -20px;
  bottom: -34px;
  width: 82px;
  height: 82px;
  border: 1px solid currentColor;
  border-radius: 50%;
  content: "";
  opacity: 0.08;
}

.risk-overview-card.environment-risk {
  color: #bf7f25;
  border-color: #ead7b7;
  background: linear-gradient(135deg, #fff9ee, #fffdf8);
}

.risk-overview-card.device-risk {
  color: #397f93;
  border-color: #cfe2e7;
  background: linear-gradient(135deg, #f1f8fa, #fbfdfd);
}

.risk-overview-icon {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border: 1px solid currentColor;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.62);
  font-size: 17px;
  opacity: 0.92;
}

.risk-overview-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 4px;
}

.risk-overview-info span {
  overflow: hidden;
  color: #234432;
  font-size: 14px;
  line-height: 1.25;
  font-weight: 780;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.risk-overview-info small {
  overflow: hidden;
  color: #7e8f83;
  font-size: 10px;
  line-height: 1.35;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.risk-overview-value {
  display: flex;
  align-items: baseline;
  gap: 3px;
}

.risk-overview-value strong {
  color: currentColor;
  font-size: 25px;
  line-height: 1;
  font-weight: 820;
}

.risk-overview-value small {
  color: currentColor;
  font-size: 11px;
  font-weight: 750;
}

.risk-section {
  min-width: 0;
}

.risk-section + .risk-section {
  padding-top: 14px;
  border-top: 1px solid #e5ede7;
}

.risk-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 9px;
}

.risk-section-heading > div {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 8px;
}

.risk-section-heading strong {
  color: #234432;
  font-size: 14px;
  font-weight: 800;
}

.risk-section-mark {
  width: 4px;
  height: 15px;
  border-radius: 4px;
}

.risk-section-mark.environment {
  background: #d49a3e;
}

.risk-section-mark.device {
  background: #4e93a7;
}

.risk-section-count {
  padding: 4px 9px;
  color: #607668;
  border: 1px solid #dce7df;
  border-radius: 999px;
  background: #f7faf7;
  font-size: 10px;
  font-weight: 750;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  position: relative;
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) minmax(118px, 0.64fr);
  align-items: center;
  min-width: 0;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
  border: 1px solid #e0e9e2;
  border-radius: 10px;
  background: #fbfdfb;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
}

.alert-item:hover {
  transform: translateX(2px);
  border-color: #cbdccf;
  background: #f7faf7;
}

.alert-item::before {
  position: absolute;
  top: 10px;
  bottom: 10px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  content: "";
}

.alert-item.level-high::before {
  background: #d85f5f;
}

.alert-item.level-medium::before {
  background: #d59a37;
}

.alert-item.level-low::before {
  background: #4d9b68;
}

.alert-level-box {
  display: flex;
  width: 56px;
  min-height: 54px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: 1px solid #e0e8e2;
  border-radius: 9px;
  background: #f7faf7;
}

.alert-level-icon {
  display: grid;
  width: 21px;
  height: 21px;
  place-items: center;
  border-radius: 50%;
  color: #ffffff;
  background: #819188;
  font-size: 12px;
  font-weight: 800;
}

.alert-level-box.high {
  color: #c64e4e;
  border-color: #efd0d0;
  background: #fff5f5;
}

.alert-level-box.high .alert-level-icon {
  background: #d85f5f;
}

.alert-level-box.medium {
  color: #b77821;
  border-color: #ead9bd;
  background: #fff9ee;
}

.alert-level-box.medium .alert-level-icon {
  background: #d59a37;
}

.alert-level-box.low {
  color: #347b4d;
  border-color: #cfe2d4;
  background: #f1f8f2;
}

.alert-level-box.low .alert-level-icon {
  background: #4d9b68;
}

.alert-level-box small {
  color: currentColor;
  font-size: 10px;
  font-weight: 800;
}

.alert-content {
  min-width: 0;
}

.alert-content-title {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 7px;
}

.alert-content-title strong {
  min-width: 0;
  overflow: hidden;
  color: #244633;
  font-size: 13px;
  line-height: 1.35;
  font-weight: 790;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.alert-type-tag {
  flex: 0 0 auto;
  padding: 4px 7px;
  color: #a86f20;
  border: 1px solid #ead8b8;
  border-radius: 5px;
  background: #fff8ec;
  font-size: 9px;
  line-height: 1;
  font-weight: 750;
}

.alert-type-tag.device {
  color: #397d90;
  border-color: #cde1e6;
  background: #eff7f9;
}

.alert-content p {
  display: -webkit-box;
  margin: 6px 0 0;
  overflow: hidden;
  color: #64776a;
  font-size: 11px;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.alert-meta {
  display: flex;
  min-width: 0;
  min-height: 44px;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  padding-left: 11px;
  border-left: 1px solid #e4ebe6;
  text-align: right;
}

.alert-device {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  min-width: 0;
  gap: 5px;
  color: #5f7466;
  font-size: 10px;
}

.alert-device .el-icon {
  flex: 0 0 auto;
  color: #4c8ea0;
  font-size: 12px;
}

.alert-device span {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.alert-meta > small {
  color: #849389;
  font-size: 9px;
  white-space: nowrap;
}

.risk-empty-row {
  display: flex;
  align-items: center;
  gap: 13px;
  min-height: 70px;
  padding: 13px 15px;
  border: 1px dashed #c9e0cf;
  border-radius: 10px;
  background: #f2f8f3;
}

.risk-empty-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  place-items: center;
  color: #337c4c;
  border: 1px solid #bcd9c4;
  border-radius: 9px;
  background: #e7f4ea;
  font-size: 14px;
  font-weight: 800;
}

.risk-empty-row strong {
  display: block;
  color: #244633;
  font-size: 14px;
  line-height: 1.35;
  font-weight: 800;
}

.risk-empty-row p {
  margin: 5px 0 0;
  color: #738579;
  font-size: 11px;
  line-height: 1.5;
}

.risk-empty-state {
  display: flex;
  height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.risk-safe-visual {
  position: relative;
  display: grid;
  width: 88px;
  height: 88px;
  margin-bottom: 15px;
  place-items: center;
}

.risk-safe-ring {
  position: absolute;
  border: 1px solid #c8dfce;
  border-radius: 50%;
}

.ring-one {
  width: 86px;
  height: 86px;
}

.ring-two {
  width: 64px;
  height: 64px;
  border-style: dashed;
  animation: safe-rotate 14s linear infinite;
}

.risk-safe-icon {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  color: #337c4c;
  border: 1px solid #b9d9c2;
  border-radius: 50%;
  background: #e9f5ec;
  font-size: 19px;
  font-weight: 800;
}

.risk-empty-state > strong {
  color: #244633;
  font-size: 15px;
  font-weight: 800;
}

.risk-empty-state > p {
  margin: 7px 0 15px;
  color: #75877b;
  font-size: 11px;
}

.safe-status-list {
  display: flex;
  align-items: center;
  gap: 8px;
}

.safe-status-list span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 9px;
  color: #477058;
  border: 1px solid #d0e2d4;
  border-radius: 999px;
  background: #f1f8f2;
  font-size: 9px;
  font-weight: 700;
}

.safe-status-list i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #4d9b68;
}

@keyframes alert-pulse {
  0%,
  100% {
    opacity: 0.62;
  }

  50% {
    opacity: 1;
  }
}

@keyframes safe-rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

/* =========================================================
   最新监测记录
========================================================= */

.table-panel {
  margin-top: 14px;
}

.table-heading-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-heading-meta span {
  padding: 6px 10px;
  color: #336a47;
  border: 1px solid #cde1d2;
  border-radius: 8px;
  background: #eff7f1;
  font-size: 11px;
  font-weight: 750;
}

.table-heading-meta em {
  color: #7c8c81;
  font-size: 11px;
  font-style: normal;
}

.record-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 13px;
}

.record-search {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 9px;
}

.record-search :deep(.el-input) {
  width: 270px;
}

.record-view-select {
  width: 132px;
}

.record-toolbar :deep(.el-input__wrapper),
.record-toolbar :deep(.el-select__wrapper) {
  min-height: 36px;
  border: 1px solid #d7e3da;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: none;
}

.record-toolbar :deep(.el-input__wrapper:hover),
.record-toolbar :deep(.el-select__wrapper:hover) {
  border-color: #acc9b3;
}

.record-toolbar :deep(.el-input__inner),
.record-toolbar :deep(.el-select__placeholder),
.record-toolbar :deep(.el-select__selected-item) {
  color: #506759;
  font-size: 11px;
}

.record-health {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #708278;
  font-size: 10px;
  white-space: nowrap;
}

.record-health span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.health-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.health-dot.normal {
  background: #4d9b68;
  box-shadow: 0 0 0 3px rgba(77, 155, 104, 0.1);
}

.health-dot.warning {
  background: #d49a3e;
  box-shadow: 0 0 0 3px rgba(212, 154, 62, 0.1);
}

.table-wrap {
  overflow: hidden;
  border: 1px solid #dfe8e1;
  border-radius: 11px;
  background: #ffffff;
}

.table-panel :deep(.el-card__body) {
  padding-top: 14px;
}

.table-panel :deep(.el-table) {
  --el-table-border-color: #e8eee9;
  --el-table-header-bg-color: #edf6ef;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #f2f8f3;
  --el-table-current-row-bg-color: #eef7f0;
  --el-fill-color-lighter: #f8faf8;

  width: 100%;
  color: #4f6557;
  background: #ffffff;
  font-size: 12px;
}

.table-panel :deep(.el-table th.el-table__cell),
.table-panel :deep(.el-table__header-wrapper th.el-table__cell),
.table-panel :deep(.el-table__fixed-header-wrapper th.el-table__cell) {
  height: 47px;
  padding: 0;
  color: #24573a !important;
  border-bottom: 1px solid #cfe0d3 !important;
  background: #eaf5ec !important;
  font-size: 12px;
  font-weight: 800;
}

.table-panel :deep(.el-table td.el-table__cell) {
  height: 47px;
  padding: 0;
  color: #506659 !important;
  border-bottom-color: #edf1ee !important;
  background: transparent !important;
  font-weight: 550;
}

.table-panel :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: #f2f8f3 !important;
}

.table-panel :deep(.el-table .row-warning td.el-table__cell) {
  background: #fffaf0 !important;
}

.table-panel :deep(.el-table .row-danger td.el-table__cell) {
  background: #fff5f5 !important;
}

.table-panel :deep(.el-table .row-warning td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #d49a3e;
}

.table-panel :deep(.el-table .row-danger td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 #d85f5f;
}

.record-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 58px;
  padding: 13px 2px 0;
}

.record-pagination :deep(.el-pagination) {
  --el-pagination-button-bg-color: #f3f8f4;
  --el-pagination-hover-color: #2f7446;
  --el-pagination-button-color: #506659;
  --el-pagination-bg-color: #f3f8f4;
  --el-pagination-text-color: #607568;
  --el-pagination-button-disabled-bg-color: #f6f8f6;
}

.record-pagination :deep(.el-pager li),
.record-pagination :deep(.btn-prev),
.record-pagination :deep(.btn-next) {
  min-width: 32px;
  height: 32px;
  border: 1px solid #d8e5db;
  border-radius: 7px;
  background: #f7faf7 !important;
  line-height: 30px;
}

.record-pagination :deep(.el-pager li.is-active) {
  color: #ffffff !important;
  border-color: #3f8f59;
  background: #3f8f59 !important;
}

.record-pagination :deep(.el-pagination__jump .el-input__wrapper) {
  border: 1px solid #d7e3da;
  border-radius: 7px;
  box-shadow: none;
}

.table-panel :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.table-panel :deep(.el-table__fixed-right),
.table-panel :deep(.el-table__fixed) {
  box-shadow: none;
}

:deep(.el-tag) {
  font-weight: 700;
}

:deep(.el-empty__description p) {
  color: #7a8b80;
  font-size: 12px;
  font-weight: 550;
}

/* =========================================================
   响应式适配
========================================================= */

@media (max-width: 1500px) {
  .filter-form {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .time-filter {
    grid-column: span 2;
  }

  .filter-action {
    justify-self: end;
  }

  .metric-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1180px) {
  .status-strip,
  .metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .air-panel,
  .alert-panel,
  .soil-panel,
  .weather-panel {
    grid-column: span 12;
  }

  .alert-panel :deep(.el-card__body) {
    height: auto;
    max-height: 430px;
  }
}

@media (max-width: 900px) {
  .page-content {
    padding-right: 14px;
    padding-left: 14px;
  }

  .filter-form {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .time-filter {
    grid-column: span 2;
  }

  .filter-action {
    grid-column: span 2;
    justify-self: stretch;
  }

  .filter-action :deep(.el-button) {
    width: 100%;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 7px;
  }

  .section-heading p {
    text-align: left;
  }

  .table-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .alert-item {
    grid-template-columns: 54px minmax(0, 1fr);
  }

  .alert-meta {
    grid-column: 2;
    align-items: flex-start;
    padding-top: 7px;
    padding-left: 0;
    border-top: 1px solid #e5ece7;
    border-left: 0;
    text-align: left;
  }

  .alert-device {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .filter-form,
  .status-strip,
  .metric-grid,
  .risk-overview {
    grid-template-columns: 1fr;
  }

  .time-filter,
  .filter-action {
    grid-column: span 1;
  }

  .scope-pill,
  .table-heading-meta em,
  .hero-live-status {
    display: none;
  }

  .record-toolbar,
  .record-search {
    align-items: stretch;
    flex-direction: column;
  }

  .record-search :deep(.el-input),
  .record-view-select {
    width: 100%;
  }

  .record-health {
    justify-content: space-between;
  }

  .record-pagination {
    justify-content: center;
    overflow-x: auto;
  }

  .record-pagination :deep(.el-pagination__jump) {
    display: none;
  }

  .panel-heading {
    gap: 10px;
  }

  .panel-heading h3 {
    font-size: 15px;
  }

  .section-heading h2 {
    font-size: 19px;
  }

  .chart-main,
  .chart-secondary {
    height: 270px;
  }

  .safe-status-list {
    flex-direction: column;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-live-dot,
  .metric-item,
  .surface-card,
  .status-card,
  .status-progress i,
  .ring-two,
  .alert-total-dot {
    animation: none !important;
    transition: none !important;
  }
}
</style>
