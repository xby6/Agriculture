<template>
  <div
    class="rice-screen rice-bigscreen"
    :class="{ 'public-display': isPublicScreen }"
    v-loading="loading"
  >
    <main class="bigscreen-shell">
      <section class="screen-header">
        <div class="screen-title">
          <h1>田间水稻病害智能检测与预测预报平台</h1>
        </div>
        <button
          v-if="isPublicScreen"
          type="button"
          class="admin-entry"
          title="进入后台管理系统"
          @click="goToAdmin"
        >
          <span class="admin-entry-icon">⚙</span>
          <span>后台管理</span>
        </button>
      </section>

      <section class="kpi-strip">
        <article v-for="item in overviewCards" :key="item.label" class="kpi-card">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
          <small>{{ item.unit }}</small>
        </article>
      </section>

      <section class="screen-body">
        <aside class="screen-side left-side">
          <section class="panel side-panel">
            <PanelTitle title="算力平台状态" />
            <div class="compute-platform-panel">
              <div class="compute-platform-summary">
                <article v-for="item in computePlatformCards" :key="item.key" class="compute-platform-card" :class="item.theme">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.unit }}</small>
                </article>
              </div>
              <div class="compute-platform-list">
                <article
                  v-for="service in computePlatformServices"
                  :key="service.id || service.url"
                  class="compute-service-row"
                  :class="`is-${service.statusKey}`"
                >
                  <i class="compute-service-dot"></i>
                  <div class="compute-service-main">
                    <strong>{{ service.name }}</strong>
                    <span>{{ service.url }}</span>
                  </div>
                  <div class="compute-service-meta">
                    <em>{{ service.status }}</em>
                    <small>{{ service.runningTasks }} 任务</small>
                  </div>
                </article>
                <div v-if="!computePlatformServices.length" class="compute-empty">暂无算力平台服务配置</div>
              </div>
            </div>
          </section>

          <section class="panel side-panel">
            <PanelTitle title="数据资产类型" />
            <div ref="assetChartRef" class="side-chart"></div>
          </section>

          <section class="panel source-panel dashboard-disease-panel">
            <PanelTitle title="病害检测与预测结果" :extra="hasDiseaseData ? '真实结果' : '未接入'" />
            <div class="disease-dashboard-content">
              <div class="disease-stat-grid">
                <article v-for="item in diseaseStatCards" :key="item.key" class="disease-stat-card" :class="item.theme">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.unit }}</small>
                </article>
              </div>

              <div class="disease-risk-section">
                <div class="disease-section-heading">
                  <span>风险分布</span>
                  <small>{{ diseaseRiskTotalLabel }}</small>
                </div>
                <div v-for="item in diseaseRiskDistribution" :key="item.key" class="disease-risk-row">
                  <span>{{ item.label }}</span>
                  <div class="disease-risk-track">
                    <i :style="{ width: `${item.percent}%`, backgroundColor: item.color }"></i>
                  </div>
                  <em>{{ item.percentLabel }}</em>
                  <strong>{{ item.valueLabel }}</strong>
                </div>
              </div>

              <div class="disease-summary-line">
                <span>主要病害：<strong>{{ diseaseSummary.mainDisease }}</strong></span>
                <span>最高置信度：<strong class="warning">{{ diseaseSummary.maxConfidence }}</strong></span>
              </div>
            </div>
          </section>
        </aside>

        <section class="screen-center">
          <section class="panel map-panel dashboard-map-panel">
            <div class="map-head">
              <div class="map-title">
                <PanelTitle
                  title="基地、地块与设备空间态势"
                />
              </div>

              <div class="map-filters">
                <span class="dashboard-map-mode-badge">{{ dashboardMapDataModeText }}</span>

                <el-radio-group
                  v-model="dashboardMapBaseLayer"
                  size="small"
                  class="dashboard-basemap-switch"
                >
                  <el-radio-button
                    v-for="item in dashboardBaseMapOptions"
                    :key="item.value"
                    :label="item.value"
                  >
                    {{ item.label }}
                  </el-radio-button>
                </el-radio-group>

                <div class="dashboard-layer-switch">
                  <el-checkbox-group v-model="dashboardMapVisibleLayers" size="small">
                    <el-checkbox-button
                      v-for="item in dashboardMapLayerOptions"
                      :key="item.value"
                      :label="item.value"
                    >
                      {{ item.label }}
                    </el-checkbox-button>
                  </el-checkbox-group>
                </div>

                <el-select
                  v-model="selectedBaseId"
                  class="dashboard-base-filter"
                  size="small"
                  placeholder="选择基地"
                >
                  <el-option label="全部基地" value="all" />
                  <el-option
                    v-for="base in baseOptions"
                    :key="base.id"
                    :label="base.name"
                    :value="String(base.id)"
                  />
                </el-select>

                <el-input
                  v-model="keyword"
                  class="dashboard-node-filter"
                  size="small"
                  placeholder="搜索节点名称"
                  clearable
                >
                  <template #suffix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>

                <el-button
                  class="dashboard-refresh-button"
                  size="small"
                  type="primary"
                  plain
                  @click="refreshDashboardMap"
                >
                  刷新地图
                </el-button>
              </div>
            </div>

            <div class="dashboard-map-stage" :class="`basemap-${dashboardMapBaseLayer}`">
              <div
                ref="dashboardMapContainer"
                class="dashboard-leaflet-map"
                aria-label="水稻基地、地块和监测设备空间分布地图"
              ></div>

              <div class="dashboard-map-legend">
                <span><i class="map-legend-symbol county"></i>典型区县</span>
                <span><i class="map-legend-symbol boundary"></i>行政边界</span>
                <span><i class="map-legend-symbol base"></i>基地</span>
                <span><i class="map-legend-symbol healthy"></i>健康</span>
                <span><i class="map-legend-symbol low"></i>轻度</span>
                <span><i class="map-legend-symbol medium"></i>中度</span>
                <span><i class="map-legend-symbol high"></i>重度</span>
                <span><i class="map-legend-symbol device"></i>监测设备</span>
              </div>

            </div>
          </section>

          <section class="screen-chart-row">
            <section class="panel environment-dashboard-panel">
              <div class="environment-dashboard-header">
                <div
                  class="environment-dashboard-title-link"
                  role="button"
                  tabindex="0"
                  title="点击进入田间环境监测页面"
                  @click="goToEnvironmentMonitor"
                  @keydown.enter.prevent="goToEnvironmentMonitor"
                  @keydown.space.prevent="goToEnvironmentMonitor"
                >
                  <PanelTitle
                    title="田间环境综合监测"
                    :extra="environmentTrendPointCount ? `${environmentTrendPointCount} 个时间点` : '暂无历史数据'"
                  />
                </div>

                <!-- 设备选择单独占一整行，控制下方全部环境可视化 -->
                <div class="environment-global-controls">
                  <label class="environment-control-item device-control">
                    <span>监测设备</span>
                    <el-select
                      v-model="selectedEnvironmentDeviceId"
                      size="small"
                      filterable
                      placeholder="请选择田间监测设备"
                    >
                      <el-option
                        v-for="item in environmentDeviceOptions"
                        :key="item.deviceId"
                        :label="item.deviceName || item.deviceAddr || `设备${item.deviceId}`"
                        :value="item.deviceId"
                      />
                    </el-select>
                  </label>

                  <label class="environment-control-item range-control">
                    <span>时间范围</span>
                    <el-select
                      v-model="environmentTrendHours"
                      size="small"
                    >
                      <el-option label="近6小时" :value="6" />
                      <el-option label="近12小时" :value="12" />
                      <el-option label="近24小时" :value="24" />
                      <el-option label="近72小时" :value="72" />
                    </el-select>
                  </label>

                  <div class="environment-control-status">
                    <span
                      class="environment-status-dot"
                      :class="selectedEnvironmentDeviceStatusClass"
                    ></span>
                    <div>
                      <small>设备状态</small>
                      <strong>{{ selectedEnvironmentDeviceStatusText }}</strong>
                    </div>
                  </div>

                  <div class="environment-control-time">
                    <small>最近采集</small>
                    <strong>{{ selectedEnvironmentObservedAt }}</strong>
                  </div>

                  <el-button
                    class="environment-refresh-button"
                    size="small"
                    type="primary"
                    plain
                    :loading="environmentTrendLoading"
                    @click="loadEnvironmentTrend"
                  >
                    刷新
                  </el-button>
                </div>
              </div>

              <div
                v-if="selectedEnvironmentDeviceId"
                class="environment-chart-grid"
                v-loading="environmentTrendLoading"
              >
                <article class="environment-chart-cell">
                  <div class="environment-chart-title">
                    <div>
                      <strong>空气温湿度</strong>
                      <small>空气温度 / 相对湿度</small>
                    </div>
                    <span>℃ · %</span>
                  </div>
                  <div ref="airEnvironmentChartRef" class="environment-mini-chart"></div>
                </article>

                <article class="environment-chart-cell">
                  <div class="environment-chart-title">
                    <div>
                      <strong>土壤水热状态</strong>
                      <small>土壤温度 / 土壤水分</small>
                    </div>
                    <span>℃ · %</span>
                  </div>
                  <div ref="soilEnvironmentChartRef" class="environment-mini-chart"></div>
                </article>

                <article class="environment-chart-cell">
                  <div class="environment-chart-title">
                    <div>
                      <strong>光照与 CO₂</strong>
                      <small>光照强度 / CO₂ 浓度</small>
                    </div>
                    <span>Lux · ppm</span>
                  </div>
                  <div ref="lightCo2EnvironmentChartRef" class="environment-mini-chart"></div>
                </article>

                <article class="environment-chart-cell">
                  <div class="environment-chart-title">
                    <div>
                      <strong>降雨与设备电量</strong>
                      <small>降雨量 / 电池电量</small>
                    </div>
                    <span>mm · %</span>
                  </div>
                  <div ref="rainBatteryEnvironmentChartRef" class="environment-mini-chart"></div>
                </article>
              </div>

              <EmptyData
                v-else
                text="暂无可选监测设备，请先接入田间环境传感器。"
              />
            </section>
          </section>
        </section>

        <aside class="screen-side right-side has-task-panel">
          <section class="panel environment-metric-panel">
            <PanelTitle
              title="设备实时环境指标"
              :extra="selectedEnvironmentDeviceName"
            />

            <div v-if="selectedEnvironmentDeviceId" class="environment-metric-content">
              <div class="environment-device-summary">
                <div class="environment-device-identity">
                  <span
                    class="environment-device-state-icon"
                    :class="selectedEnvironmentDeviceStatusClass"
                  >
                    <i></i>
                  </span>
                  <div>
                    <strong :title="selectedEnvironmentDeviceName">
                      {{ selectedEnvironmentDeviceName }}
                    </strong>
                    <small>
                      {{ selectedEnvironmentDeviceStatusText }} ·
                      {{ selectedEnvironmentObservedAt }}
                    </small>
                  </div>
                </div>

                <span class="environment-data-quality">
                  {{ selectedEnvironmentValidMetricCount }}/8 项有效
                </span>
              </div>

              <div class="selected-environment-metric-grid">
                <article
                  v-for="item in selectedEnvironmentMetrics"
                  :key="item.code"
                  class="selected-environment-metric"
                  :class="item.theme"
                >
                  <span>{{ item.label }}</span>
                  <strong>
                    {{ item.value }}
                    <small v-if="item.unit">{{ item.unit }}</small>
                  </strong>
                  <i :class="{ available: item.available }"></i>
                </article>
              </div>
            </div>

            <EmptyData
              v-else
              text="暂无真实环境传感器设备，无法显示环境指标。"
            />
          </section>

          <section class="panel task-panel">
            <PanelTitle title="最近真实模型任务" :extra="latestTasks.length ? `${latestTasks.length} 条` : '暂无数据'" />
            <div v-if="latestTasks.length" class="task-list">
              <article v-for="item in latestTasks" :key="item.id">
                <span class="task-dot" :class="{ done: isTaskDone(item) }"></span>
                <div>
                  <strong>{{ item.name || item.algo || `任务${item.id}` }}</strong>
                  <small>{{ item.algo || item.state || '模型任务' }}</small>
                </div>
                <time>{{ formatShortDate(item.init_time) }}</time>
              </article>
            </div>
            <EmptyData v-else text="暂无真实模型任务记录。" />
          </section>

          <section class="panel ndvi-panel">
            <PanelTitle title="遥感 NDVI 趋势" :extra="ndviTrend.length ? '真实数据' : '未接入'" />
            <div ref="ndviChartRef" class="trend-chart small"></div>
          </section>

        </aside>
      </section>
    </main>
  </div>
</template>

<script setup name="Dashboard">
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { getToken } from '@/utils/auth'
import { getAgricultureOverview } from '@/api/agriculture/statistics'
import {
  getEnvironmentHistory,
  getEnvironmentLatest,
  listAgriDevices
} from '@/api/agriculture/environment'
import {
  MostlyCloudy,
  Pouring,
  Search,
  Sunny
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isPublicScreen = computed(() => route.meta.public === true)

function goToAdmin() {
  if (getToken()) {
    router.push('/admin')
  } else {
    router.push({ path: '/login', query: { redirect: '/admin' } })
  }
}

const loading = ref(false)
const dataError = ref('')
const dashboardData = ref(createEmptyDashboard())
const selectedBaseId = ref('all')
const selectedNodeId = ref(null)
const keyword = ref('')
const dashboardMapContainer = ref(null)
const selectedDemoBaseId = ref('qingyuan')
const selectedDemoPlotId = ref('Q03')
const dashboardMapBaseLayer = ref('terrain')

const tiandituToken = import.meta.env.VITE_TIANDITU_TOKEN || import.meta.env.VITE_TDT_TOKEN || ''
const tiandituSubdomains = ['0', '1', '2', '3', '4', '5', '6', '7']

function createTiandituUrl(layer) {
  return `https://t{s}.tianditu.gov.cn/${layer}_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layer}&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${tiandituToken}`
}

const dashboardBaseMapOptions = [
  { label: '地形图', value: 'terrain' },
  { label: '矢量地图', value: 'vector' },
  { label: '卫星地图', value: 'satellite' }
]

const dashboardBaseMapConfigs = {
  terrain: tiandituToken
    ? {
        url: createTiandituUrl('ter'),
        labelUrl: createTiandituUrl('cta'),
        options: {
          subdomains: tiandituSubdomains,
          attribution: '&copy; 天地图'
        }
      }
    : {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        options: {
          attribution: 'Tiles &copy; Esri'
        }
      },
  vector: tiandituToken
    ? {
        url: createTiandituUrl('vec'),
        labelUrl: createTiandituUrl('cva'),
        options: {
          subdomains: tiandituSubdomains,
          attribution: '&copy; 天地图'
        }
      }
    : {
        url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
        options: {
          subdomains: 'abcd',
          attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
        }
      },
  satellite: tiandituToken
    ? {
        url: createTiandituUrl('img'),
        labelUrl: createTiandituUrl('cia'),
        options: {
          subdomains: tiandituSubdomains,
          attribution: '&copy; 天地图'
        }
      }
    : {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        options: {
          attribution: 'Tiles &copy; Esri'
        }
  }
}

const dashboardMapLayerOptions = [
  { label: '典型区县', value: 'typicalCounty' },
  { label: '行政边界', value: 'adminBoundary' }
]
const dashboardMapVisibleLayers = ref(['typicalCounty', 'adminBoundary'])

const dashboardTypicalCountyAreas = [
  {
    id: 'qingyuan-county',
    name: '清原典型区',
    location: '辽宁省抚顺市清原满族自治县',
    center: [42.10872154, 124.96911137],
    color: '#23d18b',
    radius: [0.22, 0.30],
    demoBaseId: 'qingyuan'
  },
  {
    id: 'donggang-county',
    name: '丹东东港典型区',
    location: '辽宁省丹东市东港市',
    center: [39.92638130, 124.13124693],
    color: '#35a7ff',
    radius: [0.24, 0.32],
    demoBaseId: 'donggang'
  },
  {
    id: 'dandong-academy-county',
    name: '丹东农科院典型区',
    location: '辽宁省丹东市农科院试验区',
    center: [40.47411023, 124.11777270],
    color: '#ffb84d',
    radius: [0.20, 0.28],
    demoBaseId: 'dandong_academy'
  },
  {
    id: 'haicheng-county',
    name: '海城典型区',
    location: '辽宁省鞍山市海城市',
    center: [40.97812011, 122.72505471],
    color: '#ff6b6b',
    radius: [0.22, 0.30],
    demoBaseId: 'haicheng'
  }
]

const dashboardAdministrativeBoundarySources = [
  {
    id: 'china-province',
    name: '全国省级行政边界',
    level: 'province',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
  },
  {
    id: 'liaoning-city',
    name: '辽宁省市级行政边界',
    level: 'city',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/210000_full.json'
  },
  {
    id: 'jilin-city',
    name: '吉林省市级行政边界',
    level: 'city',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/220000_full.json'
  },
  {
    id: 'heilongjiang-city',
    name: '黑龙江省市级行政边界',
    level: 'city',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/230000_full.json'
  },
  {
    id: 'neimenggu-city',
    name: '内蒙古自治区市级行政边界',
    level: 'city',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/150000_full.json'
  },
  {
    id: 'hebei-city',
    name: '河北省市级行政边界',
    level: 'city',
    url: 'https://geo.datav.aliyun.com/areas_v3/bound/130000_full.json'
  }
]

let dashboardAdministrativeBoundaryCollection = null
let dashboardAdministrativeBoundaryPromise = null
let dashboardAdministrativeBoundaryRenderToken = 0

let dashboardMap = null
let dashboardMapTileLayer = null
let dashboardMapTileLabelLayer = null
let dashboardMapLayers = []
let dashboardMapResizeObserver = null
const dashboardMapMarkerIndex = new Map()

const assetChartRef = ref(null)
const taskStateChartRef = ref(null)
const ndviChartRef = ref(null)

const airEnvironmentChartRef = ref(null)
const soilEnvironmentChartRef = ref(null)
const lightCo2EnvironmentChartRef = ref(null)
const rainBatteryEnvironmentChartRef = ref(null)

const environmentDevices = ref([])
const selectedEnvironmentDeviceId = ref(undefined)
const environmentTrendHours = ref(24)
const environmentTrendRows = ref([])
const environmentTrendLoading = ref(false)

let chartInstances = []
const environmentChartInstances = new Map()

const PanelTitle = defineComponent({
  name: 'PanelTitle',
  props: {
    title: { type: String, required: true },
    extra: { type: String, default: '' }
  },
  setup(props) {
    return () => h('div', { class: 'panel-title' }, [
      h('div', { class: 'panel-title-main' }, [
        h('span', { class: 'panel-title-icon', 'aria-hidden': 'true' }),
        h('strong', props.title)
      ]),
      props.extra ? h('span', { class: 'panel-title-extra' }, props.extra) : null
    ])
  }
})

const EmptyData = defineComponent({
  name: 'EmptyData',
  props: {
    text: { type: String, required: true }
  },
  setup(props) {
    return () => h('div', { class: 'empty-data' }, [
      h('strong', '暂无真实数据'),
      h('span', props.text)
    ])
  }
})

const overview = computed(() => dashboardData.value.overview || {})
const charts = computed(() => dashboardData.value.charts || {})
const disease = computed(() => dashboardData.value.disease || {})
const latestTasks = computed(() => dashboardData.value.latest_tasks || [])
const latestFiles = computed(() => dashboardData.value.latest_files || [])
const baseOptions = computed(() => dashboardData.value.bases || [])
const ndviTrend = computed(() => charts.value.ndvi_trend || [])
const computePlatform = computed(() => charts.value.compute_platform || {})
const computePlatformCards = computed(() => [
  {
    key: 'total',
    label: '服务总数',
    value: displayValue(computePlatform.value.total),
    unit: '个',
    theme: 'blue'
  },
  {
    key: 'running',
    label: '运行中',
    value: displayValue(computePlatform.value.running),
    unit: '个',
    theme: 'green'
  },
  {
    key: 'tasks',
    label: '运行任务',
    value: displayValue(computePlatform.value.running_tasks),
    unit: '个',
    theme: 'orange'
  }
])
const computePlatformServices = computed(() => {
  const services = Array.isArray(computePlatform.value.services) ? computePlatform.value.services : []
  return services.map((item) => ({
    id: item.id,
    name: item.name || `模型服务${item.id || ''}`,
    url: item.url || '--',
    status: item.status || '--',
    statusKey: item.status_key || item.statusKey || 'unknown',
    runningTasks: item.running_tasks ?? item.runningTasks ?? 0
  }))
})
const latestEnvironmentRows = ref([])

const dashboardRiskLabel = {
  healthy: '健康',
  low: '轻度',
  medium: '中度',
  high: '重度'
}

const dashboardRiskColors = {
  healthy: '#4f9a62',
  low: '#8fb764',
  medium: '#c6a145',
  high: '#c76565'
}

const dashboardDemoBases = [
  {
    id: 'qingyuan',
    name: '清原实验基地',
    location: '辽宁省抚顺市清原满族自治县',
    coordinate: [42.10872154, 124.96911137],
    plots: [
      { id: 'Q01', code: 'Q01', risk: 'healthy', di: 4.8, predictedDi: 6.2, offset: [-0.0020, -0.0024] },
      { id: 'Q02', code: 'Q02', risk: 'low', di: 9.5, predictedDi: 11.8, offset: [-0.0010, 0.0002] },
      { id: 'Q03', code: 'Q03', risk: 'medium', di: 17.9, predictedDi: 24.6, offset: [-0.0018, 0.0028] },
      { id: 'Q04', code: 'Q04', risk: 'healthy', di: 5.2, predictedDi: 6.9, offset: [0.0012, -0.0022] }
    ]
  },
  {
    id: 'donggang',
    name: '丹东东港实验基地',
    location: '辽宁省丹东市东港市',
    coordinate: [39.92638130, 124.13124693],
    plots: [
      { id: 'DG01', code: 'DG01', risk: 'low', di: 8.6, predictedDi: 10.2, offset: [-0.0018, -0.0022] },
      { id: 'DG02', code: 'DG02', risk: 'medium', di: 19.2, predictedDi: 27.3, offset: [-0.0010, 0.0004] },
      { id: 'DG03', code: 'DG03', risk: 'low', di: 10.1, predictedDi: 13.8, offset: [-0.0016, 0.0028] },
      { id: 'DG04', code: 'DG04', risk: 'healthy', di: 3.9, predictedDi: 5.0, offset: [0.0012, -0.0020] }
    ]
  },
  {
    id: 'dandong_academy',
    name: '丹东农科院实验基地',
    location: '辽宁省丹东市农科院',
    coordinate: [40.47411023, 124.11777270],
    plots: [
      { id: 'DK01', code: 'DK01', risk: 'healthy', di: 3.6, predictedDi: 4.4, offset: [-0.0018, -0.0022] },
      { id: 'DK02', code: 'DK02', risk: 'healthy', di: 4.4, predictedDi: 5.6, offset: [-0.0010, 0.0004] },
      { id: 'DK03', code: 'DK03', risk: 'low', di: 8.3, predictedDi: 10.1, offset: [-0.0016, 0.0028] },
      { id: 'DK04', code: 'DK04', risk: 'medium', di: 15.8, predictedDi: 19.6, offset: [0.0012, -0.0020] }
    ]
  },
  {
    id: 'haicheng',
    name: '海城实验基地',
    location: '辽宁省鞍山市海城市',
    coordinate: [40.97812011, 122.72505471],
    plots: [
      { id: 'HC01', code: 'HC01', risk: 'healthy', di: 4.2, predictedDi: 5.8, offset: [-0.0020, -0.0024] },
      { id: 'HC02', code: 'HC02', risk: 'low', di: 9.8, predictedDi: 12.3, offset: [-0.0010, 0.0002] },
      { id: 'HC03', code: 'HC03', risk: 'medium', di: 18.6, predictedDi: 25.4, offset: [-0.0018, 0.0028] },
      { id: 'HC04', code: 'HC04', risk: 'high', di: 31.8, predictedDi: 38.9, offset: [0.0014, 0.0030] }
    ]
  }
]

const selectedDemoBase = computed(() => {
  return dashboardDemoBases.find(item => item.id === selectedDemoBaseId.value) ||
    dashboardDemoBases[0]
})

const selectedDemoPlot = computed(() => {
  return selectedDemoBase.value?.plots.find(
    item => item.id === selectedDemoPlotId.value
  ) || selectedDemoBase.value?.plots[0] || null
})

const dashboardMapDataModeText = computed(() => {
  return positionedNodes.value.length
    ? `真实节点 ${positionedNodes.value.length} 个`
    : '示例基地模式'
})

const environmentMetricDefs = [
  {
    code: 'air_temperature',
    label: '空气温度',
    unit: '℃',
    theme: 'air-temperature'
  },
  {
    code: 'relative_humidity',
    label: '空气湿度',
    unit: '%',
    theme: 'air-humidity'
  },
  {
    code: 'soil_temperature',
    label: '土壤温度',
    unit: '℃',
    theme: 'soil-temperature'
  },
  {
    code: 'soil_moisture',
    label: '土壤水分',
    unit: '%',
    theme: 'soil-moisture'
  },
  {
    code: 'illuminance',
    label: '光照强度',
    unit: 'Lux',
    theme: 'illuminance'
  },
  {
    code: 'co2_concentration',
    label: 'CO₂浓度',
    unit: 'ppm',
    theme: 'co2'
  },
  {
    code: 'rainfall',
    label: '降雨量',
    unit: 'mm',
    theme: 'rainfall'
  },
  {
    code: 'battery_level',
    label: '电池电量',
    unit: '%',
    theme: 'battery'
  }
]

const environmentChartGroups = [
  {
    key: 'air',
    defs: [
      {
        code: 'air_temperature',
        name: '空气温度',
        unit: '℃',
        color: '#C88745',
        axis: 0
      },
      {
        code: 'relative_humidity',
        name: '相对湿度',
        unit: '%',
        color: '#4E9982',
        axis: 1
      }
    ],
    emptyText: '暂无空气温湿度历史数据'
  },
  {
    key: 'soil',
    defs: [
      {
        code: 'soil_temperature',
        name: '土壤温度',
        unit: '℃',
        color: '#B98952',
        axis: 0
      },
      {
        code: 'soil_moisture',
        name: '土壤水分',
        unit: '%',
        color: '#4E8FA6',
        axis: 1
      }
    ],
    emptyText: '暂无土壤水热历史数据'
  },
  {
    key: 'lightCo2',
    defs: [
      {
        code: 'illuminance',
        name: '光照强度',
        unit: 'Lux',
        color: '#C5A13D',
        axis: 0
      },
      {
        code: 'co2_concentration',
        name: 'CO₂浓度',
        unit: 'ppm',
        color: '#7484A5',
        axis: 1
      }
    ],
    emptyText: '暂无光照与 CO₂ 历史数据'
  },
  {
    key: 'rainBattery',
    defs: [
      {
        code: 'rainfall',
        name: '降雨量',
        unit: 'mm',
        color: '#4C93A0',
        axis: 0,
        type: 'bar'
      },
      {
        code: 'battery_level',
        name: '电池电量',
        unit: '%',
        color: '#5B9868',
        axis: 1
      }
    ],
    emptyText: '暂无降雨与电池历史数据'
  }
]

const environmentDeviceOptions = computed(() => {
  return [...environmentDevices.value].sort((a, b) => {
    const aOnline = String(a.deviceStatus || '').toLowerCase() === 'normal' ? 1 : 0
    const bOnline = String(b.deviceStatus || '').toLowerCase() === 'normal' ? 1 : 0
    if (aOnline !== bOnline) return bOnline - aOnline
    return String(a.deviceName || a.deviceAddr || '').localeCompare(
      String(b.deviceName || b.deviceAddr || ''),
      'zh-CN'
    )
  })
})

const selectedEnvironmentDevice = computed(() => {
  return environmentDevices.value.find(
    item => String(item.deviceId) === String(selectedEnvironmentDeviceId.value)
  ) || null
})

const selectedEnvironmentDeviceName = computed(() => {
  const device = selectedEnvironmentDevice.value
  return device?.deviceName || device?.deviceAddr || '未选择设备'
})

const selectedEnvironmentLatestRow = computed(() => {
  const rows = latestEnvironmentRows.value.filter(row => {
    if (row.deviceId !== undefined && row.deviceId !== null) {
      return String(row.deviceId) === String(selectedEnvironmentDeviceId.value)
    }
    return String(row.deviceAddr || '') === String(selectedEnvironmentDevice.value?.deviceAddr || '')
  })

  return [...rows].sort(
    (a, b) =>
      new Date(b.observedAt || b.lastSeenAt || 0) -
      new Date(a.observedAt || a.lastSeenAt || 0)
  )[0] || null
})

const selectedEnvironmentMetrics = computed(() => {
  const metrics = selectedEnvironmentLatestRow.value?.metrics || {}

  return environmentMetricDefs.map(def => {
    const metric = metrics[def.code]
    const available =
      metric &&
      metric.value !== null &&
      metric.value !== undefined &&
      Number.isFinite(Number(metric.value))

    return {
      ...def,
      available,
      value: available ? environmentMetricValue(metric) : '--',
      unit: metric?.unit || def.unit
    }
  })
})

const selectedEnvironmentValidMetricCount = computed(() => {
  return selectedEnvironmentMetrics.value.filter(item => item.available).length
})

const selectedEnvironmentObservedAt = computed(() => {
  return formatEnvironmentRecordTime(
    selectedEnvironmentLatestRow.value?.observedAt ||
    selectedEnvironmentLatestRow.value?.lastSeenAt
  )
})

const selectedEnvironmentDeviceStatusText = computed(() => {
  const status =
    selectedEnvironmentLatestRow.value?.deviceStatus ||
    selectedEnvironmentDevice.value?.deviceStatus ||
    selectedEnvironmentDevice.value?.status

  return environmentDeviceStatusText(status)
})

const selectedEnvironmentDeviceStatusClass = computed(() => {
  const status =
    selectedEnvironmentLatestRow.value?.deviceStatus ||
    selectedEnvironmentDevice.value?.deviceStatus ||
    selectedEnvironmentDevice.value?.status

  return environmentDeviceStatusClass(status)
})

const environmentTrendPointCount = computed(() => {
  return new Set(
    environmentTrendRows.value
      .map(item => environmentTrendTimeKey(item.observedAt))
      .filter(Boolean)
  ).size
})

const overviewCards = computed(() => [
  { label: '基地组织/个', value: displayValue(overview.value.base_count) },
  { label: '地块/节点/个', value: displayValue(overview.value.field_count) },
  { label: '数据资产/项', value: displayValue(overview.value.data_asset_count) },
  { label: '模型服务/个', value: displayValue(overview.value.model_service_count) },
  { label: '今日模型任务/项', value: displayValue(overview.value.today_model_tasks) },
  {
    label: '设备在线率',
    value: overview.value.device_online_rate === null || overview.value.device_online_rate === undefined
      ? '--'
      : `${overview.value.device_online_rate}`,
    unit: overview.value.device_online_rate === null || overview.value.device_online_rate === undefined ? '' : '%'
  }
])

const fieldNodes = computed(() => dashboardData.value.field_nodes || [])
const filteredNodes = computed(() => {
  const words = keyword.value.trim()
  return fieldNodes.value.filter(item => {
    const matchBase = selectedBaseId.value === 'all' || String(item.dept_id || '') === selectedBaseId.value
    const matchKeyword = !words || String(item.name || '').includes(words)
    return matchBase && matchKeyword
  })
})

const positionedNodes = computed(() => {
  const nodes = filteredNodes.value
    .filter(item => isNumber(item.longitude) && isNumber(item.latitude))

  if (!nodes.length) {
    return []
  }

  const longitudes = nodes.map(item => Number(item.longitude))
  const latitudes = nodes.map(item => Number(item.latitude))
  const minLng = Math.min(...longitudes)
  const maxLng = Math.max(...longitudes)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)
  const lngRange = maxLng - minLng || 1
  const latRange = maxLat - minLat || 1

  return nodes.map(item => ({
    ...item,
    left: `${12 + ((Number(item.longitude) - minLng) / lngRange) * 76}%`,
    top: `${12 + ((maxLat - Number(item.latitude)) / latRange) * 76}%`
  }))
})

const selectedNode = computed(() => {
  if (!positionedNodes.value.length) {
    return null
  }
  return positionedNodes.value.find(item => item.id === selectedNodeId.value) || positionedNodes.value[0]
})

const environmentAvailable = computed(() => !!dashboardData.value.environment)
const environmentMetrics = computed(() => {
  const env = dashboardData.value.environment
  if (!env) return []
  return [
    { key: 'air_temperature', label: '空气温度', unit: '℃', icon: Sunny },
    { key: 'air_humidity', label: '空气湿度', unit: '%RH', icon: Pouring },
    { key: 'soil_temperature', label: '土壤温度', unit: '℃', icon: Sunny },
    { key: 'soil_moisture', label: '土壤湿度', unit: '%', icon: Pouring },
    { key: 'light_klx', label: '光照强度', unit: 'klx', icon: Sunny },
    { key: 'co2_ppm', label: 'CO₂浓度', unit: 'ppm', icon: MostlyCloudy }
  ]
    .filter(item => env[item.key] !== undefined && env[item.key] !== null)
    .map(item => ({ ...item, value: env[item.key] }))
})

function pickDiseaseValue(source, keys) {
  for (const key of keys) {
    const value = source?.[key]
    if (value !== null && value !== undefined && value !== '') {
      return value
    }
  }
  return null
}

function toDiseaseNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function formatDiseasePercent(value) {
  const number = toDiseaseNumber(value)
  if (number === null) return displayValue(value)
  return `${number.toFixed(1)}%`
}

const diseaseRiskDefinitions = [
  { key: 'high', label: '高风险', color: '#e26767', tokens: ['高风险', 'high', '严重'] },
  { key: 'medium', label: '中风险', color: '#f0ad3d', tokens: ['中风险', 'medium', '中度'] },
  { key: 'low', label: '低风险', color: '#72c96f', tokens: ['低风险', 'low', '轻度'] },
  { key: 'normal', label: '正常', color: '#4c9de8', tokens: ['正常', 'healthy', '健康'] }
]

const diseaseRiskDistribution = computed(() => {
  const value = disease.value || {}
  const raw = value.risk_distribution || value.riskDistribution || value.risk_distribution_data
  const rawItems = Array.isArray(raw)
    ? raw
    : Object.entries(raw || {}).map(([key, item]) => {
      return typeof item === 'object' && item !== null ? { ...item, key: item.key || key } : { key, value: item }
    })

  const rows = diseaseRiskDefinitions.map(definition => {
    let count = toDiseaseNumber(pickDiseaseValue(value, [
      `${definition.key}_risk_count`,
      `${definition.key}RiskCount`,
      `${definition.key}_count`,
      `${definition.key}Count`
    ]))

    if (count === null) {
      const matched = rawItems.find(item => {
        const text = String(item?.key || item?.name || item?.label || item?.risk_level || '').toLowerCase()
        return definition.tokens.some(token => text.includes(token.toLowerCase()))
      })
      count = toDiseaseNumber(pickDiseaseValue(matched, ['value', 'count', 'total', 'number']))
    }

    return { ...definition, count }
  })

  const hasCounts = rows.some(item => item.count !== null)
  const total = hasCounts
    ? rows.reduce((sum, item) => sum + (item.count || 0), 0)
    : null

  return rows.map(item => {
    const percent = item.count === null || !total ? 0 : Number(((item.count / total) * 100).toFixed(1))
    return {
      ...item,
      percent,
      percentLabel: item.count === null ? '--' : `${percent.toFixed(1)}%`,
      valueLabel: item.count === null ? '--' : String(item.count)
    }
  })
})

const diseaseRiskTotalLabel = computed(() => {
  const rows = diseaseRiskDistribution.value
  const values = rows.filter(item => item.count !== null)
  if (!values.length) return '暂无真实统计'
  return `${values.reduce((sum, item) => sum + (item.count || 0), 0)} 块`
})

const diseaseStatCards = computed(() => {
  const value = disease.value || {}
  const riskRows = diseaseRiskDistribution.value
  const riskCount = key => riskRows.find(item => item.key === key)?.count ?? null
  const detectionTargetCount = pickDiseaseValue(value, ['detection_target_count', 'detectionTargetCount', 'total_detections', 'totalDetections'])
  const cards = [
    { key: 'samples', label: '检测样本', unit: '份', theme: 'blue', value: pickDiseaseValue(value, ['sample_count', 'sampleCount', 'detection_samples', 'image_count', 'imageCount']) },
    { key: 'plots', label: detectionTargetCount !== null ? '检测目标' : '异常地块', unit: detectionTargetCount !== null ? '个' : '块', theme: 'orange', value: detectionTargetCount ?? pickDiseaseValue(value, ['abnormal_plot_count', 'abnormalPlotCount', 'affected_plot_count', 'affectedPlotCount']) },
    { key: 'high', label: '高风险', unit: '块', theme: 'red', value: riskCount('high') },
    { key: 'medium', label: '中风险', unit: '块', theme: 'orange', value: riskCount('medium') },
    { key: 'low', label: '低风险', unit: '块', theme: 'green', value: riskCount('low') },
    { key: 'alerts', label: '今日预警', unit: '条', theme: 'blue', value: pickDiseaseValue(value, ['today_alert_count', 'todayAlertCount', 'alert_count', 'alertCount']) }
  ]
  return cards.map(item => ({ ...item, value: displayValue(item.value) }))
})

const diseaseSummary = computed(() => {
  const value = disease.value || {}
  return {
    mainDisease: displayValue(pickDiseaseValue(value, ['main_disease', 'mainDisease', 'disease_type', 'diseaseType'])),
    futureRisk: displayValue(pickDiseaseValue(value, ['future_risk', 'futureRisk', 'forecast_risk_level', 'forecastRiskLevel'])),
    maxConfidence: formatDiseasePercent(pickDiseaseValue(value, ['max_confidence', 'maxConfidence', 'highest_confidence', 'highestConfidence']))
  }
})

const hasDiseaseData = computed(() => {
  const value = disease.value || {}
  const hasStats = diseaseStatCards.value.some(item => item.value !== '--')
  const hasRiskRows = diseaseRiskDistribution.value.some(item => item.count !== null)
  const hasSummary = [value.current_di, value.forecast_di_7d, value.risk_level, value.main_disease, value.suggestion]
    .some(item => item !== null && item !== undefined && item !== '')
  return hasStats || hasRiskRows || hasSummary
})

const environmentRecordRows = computed(() => {
  return [...latestEnvironmentRows.value]
    .sort((a, b) => new Date(b.observedAt || b.lastSeenAt || 0) - new Date(a.observedAt || a.lastSeenAt || 0))
    .map((row, index) => {
      const metrics = row.metrics || {}
      const status = row.deviceStatus || row.status || ''
      return {
        key: row.deviceId || row.deviceAddr || `${row.observedAt || row.lastSeenAt || ''}-${index}`,
        time: formatEnvironmentRecordTime(row.observedAt || row.lastSeenAt),
        device: row.deviceName || row.deviceAddr || `设备${index + 1}`,
        temperature: environmentMetricValue(metrics.air_temperature),
        humidity: environmentMetricValue(metrics.relative_humidity),
        soilTemperature: environmentMetricValue(metrics.soil_temperature),
        soilMoisture: environmentMetricValue(metrics.soil_moisture),
        co2: environmentMetricValue(metrics.co2_concentration),
        co2Unit: environmentMetricUnit(metrics.co2_concentration, 'ppm'),
        light: environmentMetricValue(metrics.illuminance),
        lightUnit: environmentMetricUnit(metrics.illuminance, 'Lux'),
        statusText: environmentDeviceStatusText(status),
        statusClass: environmentDeviceStatusClass(status)
      }
    })
})

const shouldScrollEnvironmentRecords = computed(() => environmentRecordRows.value.length > 3)
const scrollingEnvironmentRecords = computed(() => {
  const rows = environmentRecordRows.value
  return shouldScrollEnvironmentRecords.value ? [...rows, ...rows] : rows
})
const environmentScrollDuration = computed(() => Math.max(12, environmentRecordRows.value.length * 3.2))

function goToEnvironmentMonitor() {
  const routes = router.getRoutes()

  const targetRoute = routes.find(route => {
    const routeName = String(route.name || '').toLowerCase()
    const routePath = String(route.path || '').toLowerCase()
    const routeTitle = String(route.meta?.title || '')

    return (
      routeTitle.includes('田间环境监测') ||
      routeName === 'environmentmonitor' ||
      routeName.includes('environmentmonitor') ||
      routePath.includes('environment-monitor') ||
      routePath.includes('environment/monitor') ||
      routePath.includes('field-environment')
    )
  })

  if (targetRoute) {
    if (targetRoute.name) {
      router.push({ name: targetRoute.name })
    } else {
      router.push(targetRoute.path)
    }
    return
  }

  console.warn(
    '未在前端路由表中找到“田间环境监测”页面，请检查该菜单对应的 route name、path 或 meta.title。'
  )
}

function createEmptyDashboard() {
  return {
    overview: {},
    bases: [],
    field_nodes: [],
    environment: null,
    disease: {},
    charts: {
      node_status: [],
      compute_platform: {
        total: 0,
        running: 0,
        abnormal: 0,
        offline: 0,
        unconfigured: 0,
        running_tasks: 0,
        status_counts: [],
        services: []
      },
      file_type: [],
      task_state: [],
      task_by_date: [],
      environment_history: [],
      disease_prediction: [],
      ndvi_trend: []
    },
    latest_tasks: [],
    latest_files: [],
    data_sources: [],
    warnings: [],
    updated_at: ''
  }
}

function displayValue(value) {
  if (value === null || value === undefined || value === '') {
    return '--'
  }
  return value
}

function isNumber(value) {
  return value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value))
}

async function loadDashboard() {
  loading.value = true
  dataError.value = ''
  try {
    const [
      overviewResult,
      environmentResult,
      environmentDeviceResult
    ] = await Promise.allSettled([
      getAgricultureOverview(),
      getEnvironmentLatest({}),
      listAgriDevices({})
    ])

    if (overviewResult.status !== 'fulfilled') {
      throw overviewResult.reason
    }

    dashboardData.value = normalizeDashboard(overviewResult.value?.data)
    latestEnvironmentRows.value = environmentResult.status === 'fulfilled'
      ? normalizeResponseArray(environmentResult.value)
      : []

    environmentDevices.value = environmentDeviceResult.status === 'fulfilled'
      ? normalizeResponseArray(environmentDeviceResult.value)
      : []

    const selectedStillExists = environmentDevices.value.some(
      item => String(item.deviceId) === String(selectedEnvironmentDeviceId.value)
    )

    if (!selectedStillExists) {
      const latestDevice = latestEnvironmentRows.value[0]
      const preferredDevice = environmentDevices.value.find(item => {
        if (latestDevice?.deviceId !== undefined && latestDevice?.deviceId !== null) {
          return String(item.deviceId) === String(latestDevice.deviceId)
        }
        return item.deviceAddr && item.deviceAddr === latestDevice?.deviceAddr
      })

      selectedEnvironmentDeviceId.value =
        preferredDevice?.deviceId ??
        environmentDeviceOptions.value[0]?.deviceId
    }

    await loadEnvironmentTrend()

    if (!selectedNodeId.value && positionedNodes.value.length) {
      selectedNodeId.value = positionedNodes.value[0].id
    }
  } catch (error) {
    dashboardData.value = createEmptyDashboard()
    latestEnvironmentRows.value = []
    environmentDevices.value = []
    environmentTrendRows.value = []
    selectedEnvironmentDeviceId.value = undefined
    dataError.value = '真实数据接口暂不可用，请确认后端服务已启动。'
  } finally {
    loading.value = false
    await nextTick()
    initCharts()
    initDashboardMap()
    renderDashboardMap({ forceFit: true })
  }
}

async function loadEnvironmentTrend() {
  if (!selectedEnvironmentDeviceId.value) {
    environmentTrendRows.value = []
    await nextTick()
    renderEnvironmentCharts()
    return
  }

  environmentTrendLoading.value = true

  try {
    const endTime = new Date()
    const startTime = new Date(
      endTime.getTime() - Number(environmentTrendHours.value) * 60 * 60 * 1000
    )

    const response = await getEnvironmentHistory({
      deviceId: selectedEnvironmentDeviceId.value,
      startTime: startTime.toISOString(),
      endTime: endTime.toISOString(),
      metricCodes: environmentMetricDefs.map(item => item.code).join(',')
    })

    environmentTrendRows.value = normalizeResponseArray(response)
      .map(item => ({
        ...item,
        metricCode: String(item.metricCode || '').trim().toLowerCase(),
        value: Number(item.value)
      }))
      .filter(item =>
        environmentMetricDefs.some(def => def.code === item.metricCode) &&
        item.observedAt &&
        Number.isFinite(item.value)
      )
  } catch (error) {
    environmentTrendRows.value = []
    console.error('加载田间环境综合趋势失败：', error)
  } finally {
    environmentTrendLoading.value = false
    await nextTick()
    renderEnvironmentCharts()
  }
}

function renderEnvironmentCharts() {
  const chartTargets = [
    {
      key: 'air',
      element: airEnvironmentChartRef.value
    },
    {
      key: 'soil',
      element: soilEnvironmentChartRef.value
    },
    {
      key: 'lightCo2',
      element: lightCo2EnvironmentChartRef.value
    },
    {
      key: 'rainBattery',
      element: rainBatteryEnvironmentChartRef.value
    }
  ]

  chartTargets.forEach(target => {
    const group = environmentChartGroups.find(item => item.key === target.key)
    if (!group || !target.element) return

    let chart = environmentChartInstances.get(target.key)

    if (!chart || chart.isDisposed?.()) {
      chart = echarts.init(target.element)
      environmentChartInstances.set(target.key, chart)
    }

    chart.setOption(
      buildEnvironmentChartOption(group.defs, group.emptyText),
      true
    )
  })
}

function buildEnvironmentChartOption(seriesDefs, emptyText) {
  const allowedCodes = new Set(seriesDefs.map(item => item.code))
  const rows = environmentTrendRows.value.filter(item =>
    allowedCodes.has(item.metricCode)
  )

  if (!rows.length) {
    return compactEmptyChartOption(emptyText)
  }

  const timeKeys = [...new Set(
    rows
      .map(item => environmentTrendTimeKey(item.observedAt))
      .filter(Boolean)
  )].sort((a, b) => new Date(a) - new Date(b))

  const valueMap = new Map()

  rows.forEach(item => {
    const timeKey = environmentTrendTimeKey(item.observedAt)
    if (!timeKey) return
    valueMap.set(`${item.metricCode}__${timeKey}`, item.value)
  })

  const yAxis = seriesDefs.map((def, axisIndex) => ({
    type: 'value',
    scale: true,
    position: axisIndex === 0 ? 'left' : 'right',
    name: def.unit,
    nameGap: 6,
    nameTextStyle: {
      color: def.color,
      fontSize: 8,
      fontWeight: 700
    },
    axisLabel: {
      color: '#718177',
      fontSize: 8,
      formatter: value => formatCompactAxisValue(value)
    },
    axisTick: {
      show: false
    },
    axisLine: {
      show: false
    },
    splitNumber: 3,
    splitLine: {
      show: axisIndex === 0,
      lineStyle: {
        type: 'dashed',
        color: 'rgba(80, 130, 92, 0.11)'
      }
    }
  }))

  const series = seriesDefs.map((def, index) => {
    const isBar = def.type === 'bar'

    return {
      name: def.name,
      type: isBar ? 'bar' : 'line',
      yAxisIndex: def.axis ?? index,
      smooth: isBar ? false : 0.32,
      showSymbol: false,
      connectNulls: false,
      barMaxWidth: 8,
      lineStyle: isBar
        ? undefined
        : {
            width: 1.9,
            color: def.color
          },
      itemStyle: isBar
        ? {
            color: def.color,
            opacity: 0.76,
            borderRadius: [3, 3, 0, 0]
          }
        : {
            color: def.color
          },
      areaStyle: isBar
        ? undefined
        : {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {
                offset: 0,
                color: `${def.color}1c`
              },
              {
                offset: 1,
                color: `${def.color}00`
              }
            ])
          },
      data: timeKeys.map(time => {
        const value = valueMap.get(`${def.code}__${time}`)
        return Number.isFinite(Number(value)) ? Number(value) : null
      }),
      z: isBar ? 1 : 3 + index
    }
  })

  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: 'rgba(3, 18, 31, 0.96)',
      borderColor: 'rgba(70, 212, 255, 0.32)',
      extraCssText: 'box-shadow: 0 10px 28px rgba(0, 0, 0, 0.32); border-radius: 8px;',
      padding: [7, 9],
      textStyle: {
        color: '#dff8ff',
        fontSize: 9
      },
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(70, 212, 255, 0.30)'
        }
      }
    },
    legend: {
      top: 7,
      left: 'center',
      itemWidth: 11,
      itemHeight: 5,
      itemGap: 14,
      icon: 'roundRect',
      textStyle: {
        color: '#bfefff',
        fontSize: 9,
        fontWeight: 700
      }
    },
    grid: {
      left: 36,
      right: 36,
      top: 44,
      bottom: 24
    },
    xAxis: {
      type: 'category',
      boundaryGap: seriesDefs.some(item => item.type === 'bar'),
      data: timeKeys.map(formatEnvironmentTrendTime),
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(70, 212, 255, 0.18)'
        }
      },
      axisLabel: {
        color: '#88bbcf',
        fontSize: 7,
        margin: 7,
        hideOverlap: true
      }
    },
    yAxis,
    series
  }
}

function compactEmptyChartOption(text) {
  return {
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: 'middle',
        style: {
          text,
          fill: '#7A8C80',
          fontSize: 9,
          fontWeight: 600
        }
      }
    ]
  }
}

function formatCompactAxisValue(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return value
  if (Math.abs(number) >= 10000) {
    return `${(number / 1000).toFixed(0)}k`
  }
  if (Math.abs(number) >= 1000) {
    return `${(number / 1000).toFixed(1)}k`
  }
  if (Math.abs(number) >= 100) {
    return number.toFixed(0)
  }
  return Number.isInteger(number) ? String(number) : number.toFixed(1)
}

function environmentTrendTimeKey(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  date.setSeconds(0, 0)
  return date.toISOString()
}

function formatEnvironmentTrendTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)

  const pad = item => String(item).padStart(2, '0')
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function createDashboardTileLayer(config, zIndex = 1) {
  return L.tileLayer(config.url, {
    minZoom: 3,
    maxZoom: 18,
    zIndex,
    ...config.options
  })
}

function applyDashboardBaseMapLayer() {
  if (!dashboardMap) return

  const config = dashboardBaseMapConfigs[dashboardMapBaseLayer.value] || dashboardBaseMapConfigs.terrain

  if (dashboardMapTileLayer && dashboardMap.hasLayer(dashboardMapTileLayer)) {
    dashboardMap.removeLayer(dashboardMapTileLayer)
  }

  if (dashboardMapTileLabelLayer && dashboardMap.hasLayer(dashboardMapTileLabelLayer)) {
    dashboardMap.removeLayer(dashboardMapTileLabelLayer)
  }

  dashboardMapTileLayer = createDashboardTileLayer(config, 1).addTo(dashboardMap)
  dashboardMapTileLayer.bringToBack()

  if (config.labelUrl) {
    dashboardMapTileLabelLayer = createDashboardTileLayer(
      {
        url: config.labelUrl,
        options: config.options
      },
      2
    ).addTo(dashboardMap)
  } else {
    dashboardMapTileLabelLayer = null
  }
}

function ensureDashboardMapPanes() {
  if (!dashboardMap) return

  const panes = [
    ['dashboard-boundary-pane', 430],
    ['dashboard-county-pane', 440],
    ['dashboard-plot-pane', 450],
    ['dashboard-sensor-pane', 610],
    ['dashboard-base-pane', 620],
    ['dashboard-label-pane', 700],
    ['dashboard-popup-pane', 720]
  ]

  panes.forEach(([name, zIndex]) => {
    const pane = dashboardMap.getPane(name) || dashboardMap.createPane(name)
    pane.style.zIndex = String(zIndex)
  })
}

function initDashboardMap() {
  if (!dashboardMapContainer.value) return

  if (dashboardMap) {
    dashboardMap.invalidateSize()
    renderDashboardMap()
    return
  }

  dashboardMap = L.map(dashboardMapContainer.value, {
    zoomControl: true,
    attributionControl: true,
    preferCanvas: true
  }).setView([41.2, 123.2], 7)

  ensureDashboardMapPanes()
  applyDashboardBaseMapLayer()

  dashboardMapResizeObserver = new ResizeObserver(() => {
    dashboardMap?.invalidateSize({ pan: false })
  })
  dashboardMapResizeObserver.observe(dashboardMapContainer.value)

  renderDashboardMap({ forceFit: true })
}

function clearDashboardMapLayers() {
  dashboardMapLayers.forEach(layer => {
    if (dashboardMap?.hasLayer(layer)) {
      dashboardMap.removeLayer(layer)
    }
  })
  dashboardMapLayers = []
  dashboardMapMarkerIndex.clear()
}

function refreshDashboardMap() {
  renderDashboardMap({ forceFit: true })
}

function renderDashboardMap(options = {}) {
  if (!dashboardMap) return

  clearDashboardMapLayers()
  renderDashboardAdministrativeBoundaries()
  renderDashboardTypicalCounties()

  if (positionedNodes.value.length) {
    renderRealDashboardNodes(options)
  } else {
    renderDashboardDemoBases(options)
  }

  window.setTimeout(() => {
    dashboardMap?.invalidateSize({ pan: false })
  }, 80)
}

function renderRealDashboardNodes(options = {}) {
  const markers = []

  positionedNodes.value.forEach(node => {
    const latitude = Number(node.latitude)
    const longitude = Number(node.longitude)

    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return

    const statusClass = mapNodeStatusClass(node.status)
    const icon = L.divIcon({
      className: 'dashboard-node-marker-wrapper',
      html: `
        <div class="dashboard-node-marker ${statusClass}">
          <span></span>
          <b>${escapeDashboardMapHtml(node.name || `节点${node.id}`)}</b>
        </div>
      `,
      iconSize: [132, 34],
      iconAnchor: [15, 17]
    })

    const marker = L.marker([latitude, longitude], {
      icon,
      keyboard: true,
      pane: 'dashboard-base-pane',
      riseOnHover: true
    }).addTo(dashboardMap)

    marker.bindPopup(`
      <div class="dashboard-map-popup">
        <strong>${escapeDashboardMapHtml(node.name || `节点${node.id}`)}</strong>
        <span>状态：${escapeDashboardMapHtml(node.status || '未标记')}</span>
        <span>经度：${longitude.toFixed(6)}</span>
        <span>纬度：${latitude.toFixed(6)}</span>
      </div>
    `, { pane: 'dashboard-popup-pane' })

    marker.on('click', () => {
      selectedNodeId.value = node.id
    })

    dashboardMapLayers.push(marker)
    dashboardMapMarkerIndex.set(String(node.id), marker)
    markers.push(marker)
  })

  if (!markers.length) {
    renderDashboardDemoBases(options)
    return
  }

  const group = L.featureGroup(markers)

  if (options.preserveView) {
    return
  }

  if (
    options.forceFit ||
    selectedBaseId.value === 'all' ||
    markers.length > 1
  ) {
    dashboardMap.fitBounds(group.getBounds().pad(0.24), {
      maxZoom: 16,
      animate: true
    })
  } else {
    dashboardMap.setView(markers[0].getLatLng(), 16, {
      animate: true
    })
  }
}

function renderDashboardDemoBases(options = {}) {
  const allBaseMarkers = []

  dashboardDemoBases.forEach(base => {
    const baseIcon = L.divIcon({
      className: 'dashboard-base-marker-wrapper',
      html: `
        <div class="dashboard-base-marker">
          <span></span>
          <b>${escapeDashboardMapHtml(base.name)}</b>
        </div>
      `,
      iconSize: [150, 38],
      iconAnchor: [18, 19]
    })

    const baseMarker = L.marker(base.coordinate, {
      icon: baseIcon,
      pane: 'dashboard-base-pane',
      riseOnHover: true
    }).addTo(dashboardMap)

    baseMarker.bindPopup(`
      <div class="dashboard-map-popup">
        <strong>${escapeDashboardMapHtml(base.name)}</strong>
        <span>${escapeDashboardMapHtml(base.location)}</span>
        <span>示例地块：${base.plots.length} 块</span>
      </div>
    `, { pane: 'dashboard-popup-pane' })

    baseMarker.on('click', () => {
      selectedDemoBaseId.value = base.id
      selectedDemoPlotId.value = base.plots[0]?.id || ''
      renderDashboardMap()
      dashboardMap.setView(base.coordinate, 16, { animate: true })
    })

    dashboardMapLayers.push(baseMarker)
    allBaseMarkers.push(baseMarker)
  })

  const focusBase =
    selectedDemoBase.value ||
    dashboardDemoBases[0]

  focusBase.plots.forEach(plot => {
    const polygon = L.polygon(
      createDashboardPlotBounds(focusBase, plot),
      {
        color: dashboardRiskColors[plot.risk],
        weight: selectedDemoPlotId.value === plot.id ? 3 : 2,
        fillColor: dashboardRiskColors[plot.risk],
        fillOpacity: selectedDemoPlotId.value === plot.id ? 0.48 : 0.27,
        pane: 'dashboard-plot-pane'
      }
    ).addTo(dashboardMap)

    polygon.on('click', () => {
      selectedDemoBaseId.value = focusBase.id
      selectedDemoPlotId.value = plot.id
      renderDashboardMap()
    })

    dashboardMapLayers.push(polygon)
  })

  const sensorOffsets = [
    [-0.0007, -0.0013],
    [0.0004, 0.0015],
    [0.0016, -0.0006]
  ]

  sensorOffsets.forEach((offset, index) => {
    const icon = L.divIcon({
      className: 'dashboard-sensor-marker-wrapper',
      html: '<div class="dashboard-sensor-marker"><span></span></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    })

    const marker = L.marker(
      [
        focusBase.coordinate[0] + offset[0],
        focusBase.coordinate[1] + offset[1]
      ],
      { icon, pane: 'dashboard-sensor-pane' }
    ).addTo(dashboardMap)

    marker.bindTooltip(`监测设备 S0${index + 1}`, { pane: 'dashboard-label-pane' })
    dashboardMapLayers.push(marker)
  })

  if (options.preserveView) {
    return
  }

  if (options.forceFit) {
    const group = L.featureGroup(allBaseMarkers)
    dashboardMap.fitBounds(group.getBounds().pad(0.22), {
      maxZoom: 8,
      animate: true
    })
  } else {
    dashboardMap.setView(focusBase.coordinate, 16, {
      animate: true
    })
  }
}

function isDashboardMapLayerVisible(layer) {
  return dashboardMapVisibleLayers.value.includes(layer)
}

function createDashboardAreaBounds(center, radius) {
  const [latitude, longitude] = center
  const [latRadius, lngRadius] = radius

  return [
    [latitude + latRadius * 0.92, longitude - lngRadius * 0.54],
    [latitude + latRadius * 0.62, longitude + lngRadius * 0.70],
    [latitude + latRadius * 0.02, longitude + lngRadius],
    [latitude - latRadius * 0.82, longitude + lngRadius * 0.58],
    [latitude - latRadius, longitude - lngRadius * 0.18],
    [latitude - latRadius * 0.34, longitude - lngRadius * 0.88]
  ]
}

function renderDashboardAdministrativeBoundaries() {
  if (!isDashboardMapLayerVisible('adminBoundary')) return

  const renderToken = ++dashboardAdministrativeBoundaryRenderToken

  loadDashboardAdministrativeBoundaries()
    .then(collection => {
      if (
        !dashboardMap ||
        renderToken !== dashboardAdministrativeBoundaryRenderToken ||
        !isDashboardMapLayerVisible('adminBoundary')
      ) {
        return
      }

      const layer = L.geoJSON(collection, {
        pane: 'dashboard-boundary-pane',
        style: feature => {
          const level = feature?.properties?.__boundaryLevel
          return {
            color: level === 'province' ? '#58d8ff' : '#ffce64',
            weight: level === 'province' ? 1.8 : 1,
            opacity: level === 'province' ? 0.86 : 0.50,
            fill: false,
            dashArray: level === 'province' ? '10 7' : '5 6',
            interactive: true
          }
        },
        onEachFeature: (feature, boundaryLayer) => {
          const name = feature?.properties?.name || feature?.properties?.fullname
          const sourceName = feature?.properties?.__boundarySourceName

          if (name) {
            boundaryLayer.bindTooltip(
              `${escapeDashboardMapHtml(name)}${sourceName ? ` · ${escapeDashboardMapHtml(sourceName)}` : ''}`,
              {
                sticky: true,
                className: 'dashboard-boundary-hover-label',
                pane: 'dashboard-label-pane'
              }
            )
          }
        }
      }).addTo(dashboardMap)

      dashboardMapLayers.push(layer)
    })
    .catch(() => {
      renderDashboardFallbackAdministrativeBoundaries(renderToken)
    })
}

async function loadDashboardAdministrativeBoundaries() {
  if (dashboardAdministrativeBoundaryCollection) {
    return dashboardAdministrativeBoundaryCollection
  }

  if (dashboardAdministrativeBoundaryPromise) {
    return dashboardAdministrativeBoundaryPromise
  }

  dashboardAdministrativeBoundaryPromise = Promise.allSettled(
    dashboardAdministrativeBoundarySources.map(async source => {
      const response = await fetch(source.url)
      if (!response.ok) {
        throw new Error(`Failed to load boundary ${source.id}`)
      }

      const data = await response.json()
      const features = Array.isArray(data.features) ? data.features : []

      return features.map(feature => ({
        ...feature,
        properties: {
          ...(feature.properties || {}),
          __boundaryLevel: source.level,
          __boundarySourceName: source.name
        }
      }))
    })
  )
    .then(results => {
      const features = results.flatMap(result => (
        result.status === 'fulfilled' ? result.value : []
      ))

      if (!features.length) {
        throw new Error('No administrative boundary features loaded')
      }

      dashboardAdministrativeBoundaryCollection = {
        type: 'FeatureCollection',
        features
      }

      return dashboardAdministrativeBoundaryCollection
    })
    .finally(() => {
      dashboardAdministrativeBoundaryPromise = null
    })

  return dashboardAdministrativeBoundaryPromise
}

function renderDashboardFallbackAdministrativeBoundaries(renderToken) {
  if (
    !dashboardMap ||
    renderToken !== dashboardAdministrativeBoundaryRenderToken ||
    !isDashboardMapLayerVisible('adminBoundary')
  ) {
    return
  }

  const fallbackBoundaries = [
    { name: '辽宁省界', level: 'province', coordinates: [[43.0, 121.0], [42.6, 125.2], [40.2, 125.0], [38.9, 123.1], [40.1, 120.4], [42.1, 119.8], [43.0, 121.0]] },
    { name: '吉林省界', level: 'province', coordinates: [[46.3, 121.5], [46.0, 130.6], [42.6, 131.0], [41.8, 125.0], [43.9, 121.5], [46.3, 121.5]] },
    { name: '黑龙江省界', level: 'province', coordinates: [[53.4, 121.0], [53.2, 135.1], [47.0, 134.4], [44.1, 129.0], [45.2, 121.0], [53.4, 121.0]] },
    { name: '沈阳市界', level: 'city', coordinates: createDashboardAreaBounds([41.80, 123.43], [0.42, 0.55]) },
    { name: '鞍山市界', level: 'city', coordinates: createDashboardAreaBounds([41.10, 122.98], [0.32, 0.45]) },
    { name: '铁岭市界', level: 'city', coordinates: createDashboardAreaBounds([42.29, 123.84], [0.36, 0.50]) },
    { name: '丹东市界', level: 'city', coordinates: createDashboardAreaBounds([40.12, 124.39], [0.34, 0.48]) }
  ]

  const layers = fallbackBoundaries.map(boundary => L.polyline(
    boundary.coordinates,
    {
      color: boundary.level === 'province' ? '#58d8ff' : '#ffce64',
      weight: boundary.level === 'province' ? 1.8 : 1,
      opacity: boundary.level === 'province' ? 0.78 : 0.48,
      dashArray: boundary.level === 'province' ? '10 7' : '5 6',
      interactive: true,
      pane: 'dashboard-boundary-pane'
    }
  ).bindTooltip(boundary.name, {
    sticky: true,
    className: 'dashboard-boundary-hover-label',
    pane: 'dashboard-label-pane'
  }))

  const group = L.layerGroup(layers).addTo(dashboardMap)
  dashboardMapLayers.push(group)
}

function renderDashboardTypicalCounties() {
  if (!isDashboardMapLayerVisible('typicalCounty')) return

  dashboardTypicalCountyAreas.forEach(area => {
    const polygon = L.polygon(
      createDashboardAreaBounds(area.center, area.radius),
      {
        color: area.color,
        weight: 2,
        opacity: 0.90,
        fillColor: area.color,
        fillOpacity: 0.18,
        pane: 'dashboard-county-pane'
      }
    ).addTo(dashboardMap)

    polygon.bindTooltip(
      `<strong>${escapeDashboardMapHtml(area.name)}</strong><small>${escapeDashboardMapHtml(area.location)}</small>`,
      {
        permanent: true,
        direction: 'center',
        className: 'dashboard-county-label',
        pane: 'dashboard-label-pane'
      }
    )

    polygon.on('click', () => {
      selectedDemoBaseId.value = area.demoBaseId
      selectedDemoPlotId.value = dashboardDemoBases.find(base => base.id === area.demoBaseId)?.plots[0]?.id || ''
      renderDashboardMap({ preserveView: true })
    })

    dashboardMapLayers.push(polygon)
  })
}

function createDashboardPlotBounds(base, plot) {
  const [latitude, longitude] = base.coordinate
  const [offsetLatitude, offsetLongitude] = plot.offset
  const centerLatitude = latitude + offsetLatitude
  const centerLongitude = longitude + offsetLongitude
  const height = 0.00075
  const width = 0.00105

  return [
    [centerLatitude - height, centerLongitude - width],
    [centerLatitude - height * 0.85, centerLongitude + width],
    [centerLatitude + height, centerLongitude + width * 0.9],
    [centerLatitude + height * 0.9, centerLongitude - width]
  ]
}

function mapNodeStatusClass(status) {
  const value = String(status || '').toLowerCase()

  if (['normal', 'online', 'running', '正常', '在线'].includes(value)) {
    return 'online'
  }

  if (
    ['alarming', 'alarm', 'warning', 'prealarming', '报警', '预警'].includes(value)
  ) {
    return 'warning'
  }

  if (['offline', '离线'].includes(value)) {
    return 'offline'
  }

  return 'unknown'
}

function escapeDashboardMapHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function normalizeDashboard(data) {
  const normalized = createEmptyDashboard()
  return {
    ...normalized,
    ...(data || {}),
    overview: { ...normalized.overview, ...(data?.overview || {}) },
    charts: { ...normalized.charts, ...(data?.charts || {}) },
    disease: { ...normalized.disease, ...(data?.disease || {}) },
    bases: Array.isArray(data?.bases) ? data.bases : [],
    field_nodes: Array.isArray(data?.field_nodes) ? data.field_nodes : [],
    latest_tasks: Array.isArray(data?.latest_tasks) ? data.latest_tasks : [],
    latest_files: Array.isArray(data?.latest_files) ? data.latest_files : [],
    data_sources: Array.isArray(data?.data_sources) ? data.data_sources : [],
    warnings: Array.isArray(data?.warnings) ? data.warnings : []
  }
}

function disposeCharts() {
  chartInstances.forEach(chart => chart?.dispose())
  chartInstances = []
}

function initCharts() {
  disposeCharts()
  initAssetPieChart(assetChartRef.value, charts.value.file_type, '暂无真实数据资产')
  initBarChart(taskStateChartRef.value, charts.value.task_state, '暂无真实任务状态')
  initLineChart(ndviChartRef.value, ndviTrend.value, 'date', 'value', '暂无真实 NDVI 数据')
}

function initPieChart(el, items, emptyText) {
  if (!el) return
  const chart = echarts.init(el)
  const data = Array.isArray(items) ? items.filter(item => Number(item.value) > 0) : []
  chart.setOption(data.length ? {
    tooltip: { trigger: 'item', backgroundColor: 'rgba(3, 18, 31, 0.96)', borderColor: 'rgba(70,212,255,.32)', textStyle: { color: '#dff8ff' } },
    legend: { right: 4, top: 'middle', itemWidth: 10, itemHeight: 10, textStyle: { color: '#a9d8e8', fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['58%', '80%'],
      center: ['28%', '50%'],
      label: { show: false },
      itemStyle: { borderColor: 'rgba(4, 16, 29, 0.95)', borderWidth: 2 },
      color: ['#36e39a', '#a7f06b', '#ffd15f', '#56c9ff', '#ff6b76', '#8ca7b8'],
      data
    }]
  } : emptyChartOption(emptyText))
  chartInstances.push(chart)
}

function initAssetPieChart(el, items, emptyText) {
  if (!el) return
  const chart = echarts.init(el)
  const data = Array.isArray(items) ? items.filter(item => Number(item.value) > 0) : []
  const total = data.reduce((sum, item) => sum + Number(item.value || 0), 0)

  chart.setOption(data.length ? {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(3, 18, 31, 0.96)',
      borderColor: 'rgba(70,212,255,.32)',
      textStyle: { color: '#dff8ff' },
      formatter: '{b}<br/>数量：{c}<br/>占比：{d}%'
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      left: '46%',
      right: 0,
      top: '7%',
      bottom: '7%',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 5,
      pageIconSize: 8,
      pageTextStyle: { color: '#8fc5d4', fontSize: 9 },
      textStyle: { color: '#b9e8f5', fontSize: 10, width: 135, overflow: 'truncate' },
      formatter(name) {
        const item = data.find(entry => entry.name === name)
        const value = Number(item?.value || 0)
        const percent = total ? ((value / total) * 100).toFixed(1) : '0.0'
        const displayName = name.length > 8 ? `${name.slice(0, 8)}…` : name
        return `${displayName}  ${value} (${percent}%)`
      }
    },
    graphic: [
      {
        type: 'text',
        left: '24%',
        top: '40%',
        style: { text: String(total), fill: '#e3fbff', fontSize: 22, fontWeight: 700, textAlign: 'center' }
      },
      {
        type: 'text',
        left: '24%',
        top: '57%',
        style: { text: '数据资产/项', fill: '#91c9d9', fontSize: 11, textAlign: 'center' }
      }
    ],
    series: [{
      type: 'pie',
      radius: ['57%', '80%'],
      center: ['24%', '50%'],
      label: { show: false },
      itemStyle: { borderColor: 'rgba(4, 16, 29, 0.95)', borderWidth: 2 },
      color: ['#36e39a', '#a7f06b', '#ffd15f', '#56c9ff', '#ff6b76', '#8ca7b8'],
      data
    }]
  } : emptyChartOption(emptyText))
  chartInstances.push(chart)
}

function initLineChart(el, items, xKey, yKey, emptyText) {
  if (!el) return
  const chart = echarts.init(el)
  const data = Array.isArray(items) ? items.filter(item => item[xKey] !== null && item[xKey] !== undefined) : []
  chart.setOption(data.length ? lineOption(
    data.map(item => item[xKey]),
    data.map(item => Number(item[yKey]) || 0)
  ) : emptyChartOption(emptyText))
  chartInstances.push(chart)
}

function initBarChart(el, items, emptyText) {
  if (!el) return
  const chart = echarts.init(el)
  const data = Array.isArray(items) ? items.filter(item => Number(item.value) > 0) : []
  chart.setOption(data.length ? {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(3, 18, 31, 0.96)', borderColor: 'rgba(70,212,255,.32)', textStyle: { color: '#dff8ff' } },
    grid: { left: 42, right: 24, top: 26, bottom: 32 },
    xAxis: { type: 'category', data: data.map(item => item.name), axisTick: { show: false }, axisLine: { lineStyle: { color: 'rgba(70,212,255,.22)' } }, axisLabel: { color: '#92c7d8', fontSize: 10 } },
    yAxis: { type: 'value', axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(70,212,255,.12)' } }, axisLabel: { color: '#92c7d8', fontSize: 10 } },
    series: [{ type: 'bar', barMaxWidth: 30, data: data.map(item => item.value), itemStyle: { color: '#38d996', borderRadius: [4, 4, 0, 0] } }]
  } : emptyChartOption(emptyText))
  chartInstances.push(chart)
}

function lineOption(xData, yData) {
  return {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(3, 18, 31, 0.96)', borderColor: 'rgba(70,212,255,.32)', textStyle: { color: '#dff8ff' } },
    grid: { left: 42, right: 24, top: 26, bottom: 30 },
    xAxis: { type: 'category', boundaryGap: false, data: xData, axisTick: { show: false }, axisLine: { lineStyle: { color: 'rgba(70,212,255,.22)' } }, axisLabel: { color: '#92c7d8', fontSize: 10 } },
    yAxis: { type: 'value', axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#92c7d8', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(70,212,255,.12)' } } },
    series: [{
      name: '真实数量',
      type: 'line',
      smooth: true,
      symbolSize: 6,
      data: yData,
      lineStyle: { color: '#38d996', width: 3 },
      itemStyle: { color: '#6fffd0' },
      areaStyle: { color: 'rgba(56, 217, 150, 0.16)' }
    }]
  }
}

function emptyChartOption(text) {
  return {
    graphic: [{
      type: 'text',
      left: 'center',
      top: 'middle',
      style: { text, fill: '#9bcde0', fontSize: 13, fontWeight: 600 }
    }]
  }
}

function resizeCharts() {
  chartInstances.forEach(chart => chart?.resize())
  environmentChartInstances.forEach(chart => chart?.resize())
  dashboardMap?.invalidateSize({ pan: false })
}

function normalizeResponseArray(response) {
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.rows)) return response.rows
  if (Array.isArray(response)) return response
  return []
}

function environmentMetricValue(metric) {
  if (!metric || metric.value === null || metric.value === undefined) return '--'
  const value = Number(metric.value)
  if (!Number.isFinite(value)) return '--'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function environmentMetricUnit(metric, fallback = '') {
  return metric?.unit || fallback
}

function formatEnvironmentRecordTime(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = item => String(item).padStart(2, '0')
  return `${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function environmentDeviceStatusText(status) {
  const value = String(status || '').toLowerCase()
  if (['normal', 'online', 'running', '正常', '在线'].includes(value)) return '在线'
  if (['alarming', 'alarm', 'warning', 'prealarming', '报警', '预警'].includes(value)) return '预警'
  if (['offline', '离线'].includes(value)) return '离线'
  return status || '未知'
}

function environmentDeviceStatusClass(status) {
  const text = environmentDeviceStatusText(status)
  if (text === '在线') return 'online'
  if (text === '预警') return 'warning'
  if (text === '离线') return 'offline'
  return 'unknown'
}

function formatShortDate(value) {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function isTaskDone(task) {
  const state = String(task.state || '').toLowerCase()
  return ['success', 'done', 'finish', 'finished', '完成', '成功'].includes(state)
}

function latestFileLevel(item) {
  const category = String(item.category || item.type || '')
  return category.includes('目录') ? 'success' : 'warning'
}

function latestFileDescription(item) {
  const category = item.category || '数据资产'
  const type = item.type || '文件'
  const size = formatFileSize(item.size)
  return [category, type, size].filter(Boolean).join(' · ')
}

function formatFileSize(value) {
  const size = Number(value)
  if (!Number.isFinite(size) || size <= 0) return ''
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${Math.round(size)} B`
}

watch(
  [selectedEnvironmentDeviceId, environmentTrendHours],
  ([deviceId]) => {
    if (!deviceId || loading.value) return
    loadEnvironmentTrend()
  }
)

watch(
  [
    selectedBaseId,
    keyword,
    () => positionedNodes.value
      .map(item => `${item.id}:${item.latitude}:${item.longitude}:${item.status}`)
      .join('|')
  ],
  async () => {
    await nextTick()
    renderDashboardMap({ forceFit: true })
  }
)

watch(dashboardMapBaseLayer, () => {
  applyDashboardBaseMapLayer()
})

watch(
  dashboardMapVisibleLayers,
  () => {
    renderDashboardMap({ preserveView: true })
  },
  { deep: true }
)

watch(selectedNodeId, nodeId => {
  if (!nodeId || !dashboardMap) return

  const marker = dashboardMapMarkerIndex.get(String(nodeId))
  if (!marker) return

  dashboardMap.panTo(marker.getLatLng(), {
    animate: true,
    duration: 0.35
  })
  marker.openPopup()
})

onMounted(() => {
  nextTick(() => {
    initDashboardMap()
  })
  loadDashboard()
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  disposeCharts()
  environmentChartInstances.forEach(chart => chart?.dispose())
  environmentChartInstances.clear()

  dashboardMapResizeObserver?.disconnect()
  dashboardMapResizeObserver = null

  clearDashboardMapLayers()
  dashboardMap?.remove()
  dashboardMap = null
  dashboardMapTileLayer = null
  dashboardMapTileLabelLayer = null
})
</script>

<style scoped lang="scss">
.rice-screen {
  --panel: rgba(6, 29, 47, 0.96);
  --line: rgba(46, 190, 101, 0.28);
  --line-soft: rgba(84, 218, 131, 0.14);
  --text: #effff4;
  --muted: #8fc5a2;
  --cyan: #4E9982;
  --green: #37aee2;
  --yellow: #e4bd55;
  --orange: #d49345;
  --red: #dc6b6b;
  min-height: calc(100vh - 64px);
  padding: 12px;
  color: var(--text);
  background:
    linear-gradient(180deg, rgba(6, 19, 35, 0.96), rgba(5, 23, 29, 0.98)),
    #061a11;
}

.screen-grid {
  display: grid;
  grid-template-columns: 280px minmax(620px, 1fr) 415px;
  grid-template-rows: minmax(0, 604px) 182px;
  gap: 12px;
}

.left-stack,
.right-stack,
.center-stack {
  display: grid;
  min-width: 0;
  gap: 12px;
}

.left-stack { grid-template-rows: 274px 176px 176px; }
.right-stack { grid-template-rows: 294px 310px 182px; }
.center-stack { grid-template-rows: minmax(0, 1fr) 180px; }

.panel {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(6, 29, 47, 0.94), rgba(5, 24, 40, 0.98));
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.24);

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    z-index: 2;
    width: 68px;
    height: 2px;
    pointer-events: none;
    background: linear-gradient(90deg, #37aee2, transparent);
  }
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 38px;
  padding: 0 12px;
  border-bottom: 1px solid var(--line-soft);
  background: rgba(3, 20, 34, 0.5);
}

.panel-title-main {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;

  strong {
    overflow: hidden;
    color: #effff4;
    font-size: 14px;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.panel-title-icon {
  display: block;
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: #37aee2;
  box-shadow: 0 0 0 4px rgba(46, 190, 101, 0.12);
}

.panel-title-extra {
  color: #8fc5a2;
  font-size: 12px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 10px 4px;

  article {
    min-width: 0;
    padding: 12px;
    border: 1px solid rgba(84, 218, 131, 0.12);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.62);
  }

  span,
  strong,
  small {
    display: block;
  }

  span {
    color: #8fc5a2;
    font-size: 12px;
  }

  strong {
    margin-top: 8px;
    color: #69d292;
    font-size: 25px;
    line-height: 1;
  }

  small {
    margin-top: 4px;
    color: var(--text);
    font-size: 12px;
  }
}

.data-note {
  margin: 4px 10px 0;
  color: var(--muted);
  font-size: 12px;

  &.error {
    color: var(--yellow);
  }
}

.donut-chart {
  width: 100%;
  height: calc(100% - 36px);
}

.map-panel {
  display: grid;
  grid-template-rows: 36px minmax(0, 1fr);
}

.map-head {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr);
  border-bottom: 1px solid var(--line-soft);

  .panel-title {
    border-bottom: 0;
  }
}

.map-filters {
  display: grid;
  grid-template-columns: 180px minmax(180px, 1fr) 112px;
  gap: 10px;
  align-items: center;
  padding-right: 8px;

  :deep(.el-select__wrapper),
  :deep(.el-input__wrapper) {
    min-height: 26px;
    color: var(--text);
    border-radius: 6px;
    background: rgba(3, 20, 34, 0.9);
    box-shadow: 0 0 0 1px rgba(46, 190, 101, 0.28) inset;
  }
}

.field-map {
  position: relative;
  min-height: 0;
  overflow: hidden;
  background:
    linear-gradient(rgba(84, 218, 131, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(84, 218, 131, 0.08) 1px, transparent 1px),
    radial-gradient(circle at 48% 46%, rgba(46, 190, 101, 0.16), transparent 28%),
    #061a11;
  background-size: 42px 42px, 42px 42px, auto, auto;

  &.empty {
    display: grid;
    place-items: center;
  }
}

.plot-hotspot {
  position: absolute;
  z-index: 3;
  display: grid;
  min-width: 42px;
  max-width: 120px;
  height: 28px;
  place-items: center;
  padding: 0 8px;
  transform: translate(-50%, -50%);
  color: #f4fbff;
  border: 1px solid rgba(84, 218, 131, 0.62);
  border-radius: 3px;
  background: rgba(4, 47, 74, 0.92);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;

  &.active,
  &:hover {
    border-color: rgba(255, 255, 255, 0.9);
    background: rgba(8, 73, 112, 0.95);
    box-shadow: 0 0 0 2px rgba(255,255,255,.1), 0 0 16px rgba(90,205,237,.42);
  }
}

.map-detail {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 4;
  display: grid;
  gap: 5px;
  min-width: 220px;
  padding: 12px;
  border: 1px solid rgba(84, 218, 131, 0.18);
  border-radius: 8px;
  background: rgba(3, 20, 34, 0.86);

  strong {
    color: #fff;
    font-size: 14px;
  }

  span {
    color: var(--muted);
    font-size: 12px;
  }
}

.bottom-charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.trend-chart {
  width: 100%;
  height: calc(100% - 36px);

  &.small {
    height: 146px;
  }
}

.env-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;

  article {
    min-width: 0;
    padding: 12px 8px;
    text-align: center;
    border: 1px solid rgba(84, 218, 131, 0.12);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.62);
  }

  .el-icon {
    color: var(--cyan);
    font-size: 25px;
  }

  span,
  strong {
    display: block;
  }

  span {
    margin-top: 5px;
    color: #8fc5a2;
    font-size: 11px;
  }

  strong {
    margin-top: 7px;
    color: #f2fff6;
    font-size: 21px;
    line-height: 1;
  }

  small {
    margin-left: 4px;
    color: #effff4;
    font-size: 11px;
    font-weight: 400;
  }
}

.disease-result {
  padding: 22px 18px 10px;

  dl,
  dt,
  dd {
    margin: 0;
  }

  dl {
    display: grid;
    gap: 12px;
  }

  div {
    display: grid;
    grid-template-columns: 96px minmax(0, 1fr);
    gap: 8px;
  }

  dt {
    color: #8fc5a2;
    font-size: 12px;
  }

  dd {
    min-width: 0;
    color: #effff4;
    font-size: 13px;
    line-height: 1.5;

    &.warning { color: var(--yellow); font-weight: 700; }
    &.success { color: var(--green); font-weight: 700; }
  }
}

.timeline-panel {
  grid-column: 1 / 3;
}

.timeline {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  height: calc(100% - 36px);
  padding: 24px 24px 8px;

  article {
    position: relative;
    display: grid;
    justify-items: center;
    align-content: start;
    min-width: 0;

    > i {
      position: absolute;
      left: 50%;
      right: -50%;
      top: 22px;
      height: 2px;
      background: rgba(84, 218, 131, 0.16);
    }
  }

  .node {
    position: relative;
    z-index: 2;
    display: grid;
    width: 40px;
    height: 40px;
    place-items: center;
    color: #fff;
    border: 2px solid rgba(84, 218, 131, 0.34);
    border-radius: 50%;
    background: rgba(3, 20, 34, 0.86);
  }

  article.done .node {
    border-color: rgba(84, 218, 131, 0.72);
    background: linear-gradient(180deg, #0d8fd7, #075e8f);
  }

  strong,
  small {
    display: block;
    margin-top: 8px;
    color: #effff4;
    font-size: 12px;
    text-align: center;
  }

  small {
    max-width: 120px;
    margin-top: 4px;
    overflow: hidden;
    color: #8fc5a2;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}

.warning-list {
  display: grid;
  gap: 4px;
  padding: 10px 16px;

  article {
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr) 116px;
    gap: 10px;
    align-items: start;
    padding: 6px 0;
    border-bottom: 1px solid rgba(84, 218, 131, 0.12);
  }

  span {
    width: 9px;
    height: 9px;
    margin-top: 4px;
    border-radius: 50%;

    &.success { background: var(--green); }
    &.warning { background: var(--orange); }
    &.danger { background: var(--red); }
  }

  strong,
  small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  strong {
    color: #e4bd55;
    font-size: 13px;
  }

  small {
    margin-top: 4px;
    color: #8fc5a2;
    font-size: 12px;
  }

  time {
    color: #8fc5a2;
    font-size: 12px;
    text-align: right;
    white-space: nowrap;
  }
}

.empty-data {
  display: grid;
  place-items: center;
  align-content: center;
  height: calc(100% - 36px);
  min-height: 120px;
  padding: 20px;
  color: var(--muted);
  text-align: center;

  strong {
    color: #effff4;
    font-size: 15px;
  }

  span {
    max-width: 300px;
    margin-top: 8px;
    font-size: 12px;
    line-height: 1.7;
  }
}

.field-map > .empty-data {
  height: 100%;
}

@media (max-width: 1500px) {
  .screen-grid {
    grid-template-columns: 270px minmax(560px, 1fr) 380px;
  }
}

@media (max-width: 1200px) {
  .screen-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }

  .left-stack,
  .right-stack,
  .center-stack {
    grid-template-rows: auto;
  }

  .map-panel {
    min-height: 520px;
  }

  .timeline-panel {
    grid-column: auto;
  }

  .warning-panel {
    min-height: 160px;
  }
}

@media (max-width: 760px) {
  .map-head,
  .bottom-charts {
    grid-template-columns: 1fr;
  }

  .map-filters,
  .overview-grid,
  .env-grid,
  .timeline {
    grid-template-columns: 1fr;
  }

  .timeline article > i {
    display: none;
  }
}

.rice-screen {
  --panel: rgba(6, 29, 47, 0.94);
  --panel-soft: rgba(4, 24, 39, 0.72);
  --line: rgba(46, 190, 101, 0.28);
  --line-soft: rgba(84, 218, 131, 0.14);
  --text: #effff4;
  --muted: #8fc5a2;
  --green: #37aee2;
  --cyan: #63d6ca;
  --yellow: #e3bd5a;
  --orange: #d99a49;
  --red: #dc6b6b;
  min-height: calc(100vh - 64px);
  padding: 14px 18px 20px;
  color: var(--text);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.45;
  letter-spacing: 0;
  background:
    linear-gradient(180deg, rgba(6, 19, 35, 0.96), rgba(5, 23, 29, 0.98)),
    #061a11;
}

.rice-screen *,
.rice-screen *::before,
.rice-screen *::after {
  box-sizing: border-box;
  letter-spacing: 0;
}

.dashboard-shell {
  display: grid;
  gap: 14px;
  max-width: 1840px;
  margin: 0 auto;
}

.dashboard-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 18px;
  align-items: center;
  min-height: 126px;
  padding: 20px 22px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(6, 29, 47, 0.94), rgba(5, 24, 40, 0.98));
  box-shadow: 0 14px 32px rgba(0, 0, 0, 0.2);
}

.hero-copy {
  min-width: 0;

  .eyebrow {
    display: block;
    margin-bottom: 6px;
    color: #68dfff;
    font-size: 11px;
    font-weight: 700;
  }

  h1 {
    margin: 0;
    color: #effff4;
    font-size: 26px;
    font-weight: 750;
    line-height: 1.25;
  }

  p {
    max-width: 820px;
    margin: 8px 0 0;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.8;
  }
}

.hero-status {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;

  article {
    min-width: 0;
    padding: 13px 12px;
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.72);
  }

  span,
  strong {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  span {
    color: var(--muted);
    font-size: 12px;
  }

  strong {
    margin-top: 8px;
    color: #effff4;
    font-size: 14px;
    font-weight: 700;
  }
}

.metric-row {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-width: 0;
  min-height: 86px;
  padding: 15px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(3, 20, 34, 0.72);

  span,
  strong,
  small {
    display: block;
  }

  span {
    color: var(--muted);
    font-size: 12px;
  }

  strong {
    margin-top: 8px;
    color: #68dfff;
    font-size: 24px;
    font-weight: 760;
    line-height: 1;
  }

  small {
    margin-top: 6px;
    color: #c8e3ee;
    font-size: 12px;
  }
}

.dashboard-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 390px;
  gap: 14px;
  align-items: start;
}

.main-column,
.side-column {
  display: grid;
  min-width: 0;
  gap: 14px;
}

.panel {
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(6, 29, 47, 0.94), rgba(5, 24, 40, 0.98));
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.18);

  &::before {
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, rgba(46, 190, 101, 0.72), transparent 48%);
  }
}

.panel-title {
  height: 44px;
  padding: 0 16px;
  border-bottom: 1px solid var(--line-soft);
  background: rgba(3, 20, 34, 0.5);
}

.panel-title-main {
  gap: 9px;

  strong {
    color: #effff4;
    font-size: 15px;
    font-weight: 700;
  }
}

.panel-title-icon {
  width: 3px;
  height: 15px;
  flex: 0 0 3px;
  border-radius: 2px;
  background: var(--green);
  box-shadow: none;
}

.panel-title-extra {
  color: #8fc5a2;
  font-size: 12px;
}

.data-note {
  margin: 8px 0 0;
  font-size: 12px;

  &.error {
    color: var(--yellow);
  }
}

.map-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 514px;
}

.map-head {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(420px, 620px);
  gap: 12px;
  align-items: start;
  border-bottom: 1px solid var(--line-soft);
}

.map-title {
  min-width: 0;

  .panel-title {
    height: 42px;
    border-bottom: 0;
    background: transparent;
  }

  p {
    margin: -4px 16px 13px;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
  }
}

.map-filters {
  display: grid;
  grid-template-columns: 180px minmax(180px, 1fr) 124px;
  gap: 10px;
  align-items: center;
  padding: 11px 14px 0 0;

  :deep(.el-select__wrapper),
  :deep(.el-input__wrapper) {
    min-height: 30px;
    color: var(--text);
    border-radius: 6px;
    background: rgba(3, 20, 34, 0.9);
    box-shadow: 0 0 0 1px rgba(46, 190, 101, 0.28) inset;
  }

  :deep(.el-button) {
    min-height: 30px;
    border-radius: 6px;
    font-weight: 700;
  }
}

.field-map {
  position: relative;
  min-height: 410px;
  margin: 0 14px 14px;
  overflow: hidden;
  border: 1px solid rgba(46, 190, 101, 0.24);
  border-radius: 8px;
  background:
    linear-gradient(145deg, rgba(7, 44, 58, 0.84), rgba(4, 24, 32, 0.98)),
    #041a24;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);

  &::before {
    content: '';
    position: absolute;
    inset: 24px;
    z-index: 1;
    border: 1px solid rgba(84, 218, 131, 0.16);
    border-radius: 8px;
    background:
      linear-gradient(135deg, rgba(46, 190, 101, 0.13) 0%, transparent 34%),
      linear-gradient(45deg, transparent 0%, transparent 46%, rgba(99, 214, 202, 0.1) 47%, rgba(99, 214, 202, 0.1) 53%, transparent 54%);
    opacity: 0.72;
    pointer-events: none;
  }

  &.empty {
    display: grid;
    place-items: center;
  }
}

.plot-hotspot {
  z-index: 3;
  min-width: 46px;
  height: 30px;
  padding: 0 10px;
  color: #f5fff7;
  border: 1px solid rgba(84, 218, 131, 0.72);
  border-radius: 999px;
  background: rgba(4, 47, 74, 0.92);
  font-size: 12px;
  font-weight: 700;

  &.active,
  &:hover {
    border-color: #ffffff;
    background: rgba(8, 73, 112, 0.95);
    box-shadow: 0 0 0 3px rgba(84, 218, 131, 0.16), 0 12px 26px rgba(0, 0, 0, 0.22);
  }
}

.map-detail {
  right: 16px;
  bottom: 16px;
  z-index: 4;
  min-width: 230px;
  padding: 14px;
  border: 1px solid rgba(84, 218, 131, 0.24);
  border-radius: 8px;
  background: rgba(3, 19, 31, 0.92);
}

.chart-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.chart-card {
  min-height: 226px;
}

.trend-chart {
  width: 100%;
  height: 180px;

  &.small {
    height: 166px;
  }
}

.task-panel {
  min-height: 216px;
}

.task-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px;
  padding: 14px;

  article {
    display: grid;
    grid-template-columns: 12px minmax(0, 1fr) auto;
    gap: 11px;
    align-items: center;
    min-width: 0;
    padding: 12px;
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.62);
  }

  strong,
  small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  strong {
    color: #effff4;
    font-size: 13px;
    font-weight: 700;
  }

  small,
  time {
    color: var(--muted);
    font-size: 12px;
  }

  time {
    white-space: nowrap;
  }
}

.task-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--orange);

  &.done {
    background: var(--green);
  }
}

.env-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;

  article {
    padding: 13px 10px;
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.62);
  }

  .el-icon {
    color: var(--cyan);
    font-size: 22px;
  }

  span {
    color: var(--muted);
    font-size: 12px;
  }

  strong {
    color: #effff4;
    font-size: 20px;
    font-weight: 760;
  }
}

.disease-result {
  padding: 16px;

  dl {
    gap: 10px;
  }

  div {
    grid-template-columns: 92px minmax(0, 1fr);
    padding-bottom: 8px;
    border-bottom: 1px solid var(--line-soft);
  }

  div:last-child {
    border-bottom: 0;
  }

  dt {
    color: var(--muted);
  }

  dd {
    color: #effff4;
  }
}

.mini-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 14px;

  article {
    min-width: 0;
    border: 1px solid var(--line-soft);
    border-radius: 8px;
    background: rgba(3, 20, 34, 0.62);
  }

  span {
    display: block;
    padding: 10px 12px 0;
    color: var(--muted);
    font-size: 12px;
  }
}

.mini-donut {
  width: 100%;
  height: 150px;
}

.source-list {
  display: grid;
  gap: 2px;
  padding: 12px 14px;

  article {
    display: grid;
    grid-template-columns: 9px minmax(0, 1fr) auto;
    gap: 10px;
    align-items: start;
    padding: 10px 0;
    border-bottom: 1px solid var(--line-soft);
  }

  article:last-child {
    border-bottom: 0;
  }

  span {
    width: 8px;
    height: 8px;
    margin-top: 5px;
    border-radius: 50%;

    &.success { background: var(--green); }
    &.warning { background: var(--orange); }
    &.danger { background: var(--red); }
  }

  strong,
  small {
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  strong {
    color: #f0d06d;
    font-size: 13px;
    font-weight: 700;
  }

  small,
  time {
    color: var(--muted);
    font-size: 12px;
  }

  time {
    white-space: nowrap;
  }
}

.empty-data {
  position: relative;
  z-index: 2;
  height: auto;
  min-height: 152px;
  padding: 22px;

  strong {
    color: #effff4;
    font-size: 15px;
    font-weight: 700;
  }

  span {
    max-width: 360px;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.8;
  }
}

.field-map > .empty-data {
  height: 100%;
}

@media (max-width: 1460px) {
  .dashboard-layout {
    grid-template-columns: 1fr;
  }

  .side-column {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .dashboard-hero,
  .map-head {
    grid-template-columns: 1fr;
  }

  .hero-status,
  .metric-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .map-filters {
    grid-template-columns: 180px minmax(180px, 1fr) 124px;
    padding: 0 14px 14px;
  }
}

@media (max-width: 760px) {
  .rice-screen {
    padding: 12px;
  }

  .dashboard-hero,
  .metric-card,
  .panel {
    border-radius: 8px;
  }

  .hero-status,
  .metric-row,
  .dashboard-layout,
  .chart-row,
  .side-column,
  .mini-chart-grid,
  .map-filters,
  .env-grid {
    grid-template-columns: 1fr;
  }

  .field-map {
    min-height: 340px;
  }
}

.rice-bigscreen {
  --panel: rgba(6, 28, 43, 0.9);
  --panel-soft: rgba(10, 43, 55, 0.76);
  --line: rgba(46, 190, 101, 0.28);
  --line-soft: rgba(84, 218, 131, 0.14);
  --text: #effff4;
  --muted: #8fc5a2;
  --green: #55d98b;
  --cyan: #3fd87c;
  --yellow: #f2c765;
  --orange: #e79a45;
  --red: #e26767;
  min-height: calc(100vh - 64px);
  padding: 10px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(6, 19, 35, 0.96), rgba(5, 23, 29, 0.98)),
    #061a11;
}

.rice-bigscreen.public-display {
  width: 100vw;
  height: 100vh;
  min-height: 0;
}

.public-display .bigscreen-shell {
  height: calc(100vh - 20px);
  min-height: 0;
}

.public-display .screen-body {
  min-height: 0;
  overflow: hidden;
}

.bigscreen-shell {
  display: grid;
  grid-template-rows: 44px 66px minmax(0, 1fr);
  gap: 8px;
  width: 100%;
  height: calc(100vh - 84px);
  min-height: 720px;
  margin: 0 auto;
}

.screen-header {
  display: grid;
  grid-template-columns: 1fr;
  align-items: center;
  position: relative;
  gap: 10px;
  padding: 6px 10px;
  border: 1px solid rgba(46, 190, 101, 0.26);
  border-radius: 8px;
  background: linear-gradient(90deg, rgba(5, 18, 32, 0.96), rgba(6, 29, 47, 0.92));
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
}

.admin-entry {
  position: absolute;
  top: 50%;
  right: 12px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 32px;
  padding: 0 14px;
  border: 1px solid rgba(84, 218, 131, 0.52);
  border-radius: 7px;
  color: #dff8ff;
  background: linear-gradient(180deg, rgba(27, 75, 105, 0.9), rgba(10, 45, 69, 0.94));
  box-shadow: 0 0 16px rgba(63, 216, 124, 0.12);
  font-size: 13px;
  cursor: pointer;
  transform: translateY(-50%);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.admin-entry:hover {
  border-color: rgba(84, 218, 131, 0.9);
  box-shadow: 0 0 20px rgba(63, 216, 124, 0.24);
  transform: translateY(-50%) translateY(-1px);
}

.admin-entry-icon {
  color: var(--cyan);
  font-size: 15px;
}

.screen-title {
  justify-self: center;
  display: grid;
  width: min(520px, 42vw);
  height: 30px;
  place-items: center;
  min-width: 0;
  padding: 0 28px;
  border: 1px solid rgba(84, 218, 131, 0.32);
  border-radius: 999px;
  background:
    linear-gradient(180deg, rgba(24, 82, 48, 0.92), rgba(10, 55, 32, 0.94)),
    #061a11;
  box-shadow: 0 0 18px rgba(63, 216, 124, 0.12);
  text-align: center;

  h1 {
    margin: 0;
    color: #f4fdff;
    font-size: 21px;
    font-weight: 800;
    line-height: 1;
    text-shadow: 0 0 16px rgba(63, 216, 124, 0.22);
  }
}

.kpi-strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
}

.kpi-card {
  position: relative;
  min-width: 0;
  padding: 8px 12px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(6, 30, 48, 0.92), rgba(5, 33, 35, 0.92));

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, rgba(63, 216, 124, 0.72), transparent 58%);
  }

  span,
  strong,
  small {
    position: relative;
    z-index: 1;
    display: block;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  span {
    color: #9bc7d9;
    font-size: 11px;
  }

  strong {
    margin-top: 5px;
    color: #62e29b;
    font-size: 22px;
    font-weight: 800;
    line-height: 1;
  }

  small {
    margin-top: 3px;
    color: #d8eef6;
    font-size: 11px;
  }
}

.screen-body {
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr) 360px;
  gap: 10px;
  min-height: 0;
}

.screen-side,
.screen-center {
  display: grid;
  min-width: 0;
  min-height: 0;
  gap: 10px;
}

.left-side {
  grid-template-rows: 188px 188px minmax(0, 1fr);
}

.right-side {
  grid-template-rows: 218px 208px minmax(0, 1fr);
}

.right-side.has-task-panel {
  grid-template-rows: 170px 170px 118px minmax(130px, 1fr);
}

.screen-center {
  grid-template-rows: minmax(0, 1fr) 182px;
}

.rice-bigscreen .panel {
  border-color: var(--line);
  border-radius: 8px;
  background: linear-gradient(145deg, rgba(6, 29, 47, 0.9), rgba(5, 25, 33, 0.96));
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.018), 0 12px 24px rgba(0, 0, 0, 0.18);
}

.rice-bigscreen .panel-title {
  height: 38px;
  padding: 0 12px;
  background: rgba(5, 24, 40, 0.44);
}

.rice-bigscreen .panel-title-main strong {
  color: #effff4;
  font-size: 14px;
}

.rice-bigscreen .panel-title-icon {
  width: 3px;
  height: 14px;
  flex-basis: 3px;
  background: var(--cyan);
}

.side-chart {
  width: 100%;
  height: 150px;
}

.compute-platform-panel {
  height: calc(100% - 38px);
  min-height: 0;
  padding: 9px 12px 12px;
  display: grid;
  grid-template-rows: 52px minmax(0, 1fr);
  gap: 8px;
}

.compute-platform-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  min-width: 0;
}

.compute-platform-card {
  min-width: 0;
  border: 1px solid rgba(42, 199, 255, 0.22);
  border-radius: 7px;
  padding: 7px 8px;
  background: linear-gradient(145deg, rgba(9, 48, 73, 0.9), rgba(5, 24, 40, 0.92));
  box-shadow: inset 0 0 18px rgba(38, 195, 255, 0.06);
}

.compute-platform-card span,
.compute-platform-card small {
  display: block;
  overflow: hidden;
  color: rgba(191, 230, 244, 0.78);
  font-size: 10px;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compute-platform-card strong {
  display: inline-block;
  margin-top: 4px;
  color: #67f7b1;
  font-size: 19px;
  line-height: 1;
  text-shadow: 0 0 12px rgba(60, 255, 172, 0.42);
}

.compute-platform-card small {
  display: inline-block;
  margin-left: 3px;
}

.compute-platform-card.orange strong {
  color: #ffd064;
  text-shadow: 0 0 12px rgba(255, 196, 75, 0.34);
}

.compute-platform-card.blue strong {
  color: #6be4ff;
  text-shadow: 0 0 12px rgba(49, 205, 255, 0.36);
}

.compute-platform-list {
  display: grid;
  gap: 6px;
  min-height: 0;
  overflow: hidden;
}

.compute-service-row {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  border: 1px solid rgba(42, 199, 255, 0.2);
  border-radius: 7px;
  padding: 6px 8px;
  background: rgba(4, 29, 47, 0.76);
}

.compute-service-row:nth-child(n + 3) {
  display: none;
}

.compute-service-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #8ca7b8;
  box-shadow: 0 0 10px rgba(140, 167, 184, 0.5);
}

.compute-service-row.is-running .compute-service-dot {
  background: #39e69f;
  box-shadow: 0 0 12px rgba(57, 230, 159, 0.7);
}

.compute-service-row.is-abnormal .compute-service-dot {
  background: #ffd064;
  box-shadow: 0 0 12px rgba(255, 208, 100, 0.65);
}

.compute-service-row.is-offline .compute-service-dot {
  background: #ff6b76;
  box-shadow: 0 0 12px rgba(255, 107, 118, 0.62);
}

.compute-service-main,
.compute-service-meta {
  min-width: 0;
}

.compute-service-main strong,
.compute-service-main span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compute-service-main strong {
  color: #f2fff8;
  font-size: 12px;
  line-height: 1.25;
}

.compute-service-main span {
  margin-top: 2px;
  color: rgba(164, 217, 238, 0.66);
  font-size: 10px;
  line-height: 1.2;
}

.compute-service-meta {
  text-align: right;
}

.compute-service-meta em,
.compute-service-meta small {
  display: block;
  font-style: normal;
  white-space: nowrap;
}

.compute-service-meta em {
  color: #6ff5ba;
  font-size: 11px;
  font-weight: 800;
}

.compute-service-meta small {
  margin-top: 2px;
  color: rgba(188, 225, 240, 0.68);
  font-size: 10px;
}

.compute-service-row.is-abnormal .compute-service-meta em {
  color: #ffd064;
}

.compute-service-row.is-offline .compute-service-meta em {
  color: #ff8b91;
}

.compute-empty {
  display: grid;
  place-items: center;
  min-height: 68px;
  color: rgba(178, 221, 238, 0.72);
  font-size: 12px;
  font-weight: 700;
}

.rice-bigscreen .map-panel {
  display: grid;
  grid-template-rows: 48px minmax(0, 1fr);
  min-height: 0;
}

.rice-bigscreen .map-head {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) 610px;
  gap: 10px;
  min-height: 0;
}

.rice-bigscreen .map-title .panel-title {
  height: 34px;
}

.rice-bigscreen .map-title p {
  display: none;
}

.rice-bigscreen .map-filters {
  grid-template-columns: 170px minmax(170px, 1fr) 120px;
  padding: 9px 12px 0 0;
}

.rice-bigscreen .map-filters :deep(.el-select__wrapper),
.rice-bigscreen .map-filters :deep(.el-input__wrapper) {
  min-height: 30px;
  color: #effff4;
  background: rgba(3, 20, 34, 0.9);
  box-shadow: 0 0 0 1px rgba(46, 190, 101, 0.28) inset;
}

.rice-bigscreen .field-map {
  min-height: 0;
  height: auto;
  margin: 0 12px 12px;
  border-color: rgba(46, 190, 101, 0.24);
  background:
    linear-gradient(145deg, rgba(7, 44, 58, 0.84), rgba(4, 24, 32, 0.98)),
    #041a24;
}

.rice-bigscreen .field-map::before {
  inset: 18px;
  border-color: rgba(84, 218, 131, 0.16);
  background:
    linear-gradient(130deg, rgba(46, 190, 101, 0.13), transparent 36%),
    linear-gradient(42deg, transparent 0%, transparent 47%, rgba(63, 216, 124, 0.12) 48%, rgba(63, 216, 124, 0.12) 52%, transparent 53%);
}

.rice-bigscreen .plot-hotspot {
  height: 28px;
  border-color: rgba(84, 218, 131, 0.72);
  background: rgba(4, 47, 74, 0.92);
}

.rice-bigscreen .plot-hotspot.active,
.rice-bigscreen .plot-hotspot:hover {
  background: rgba(8, 73, 112, 0.95);
  box-shadow: 0 0 0 3px rgba(63, 216, 124, 0.12), 0 0 20px rgba(84, 218, 131, 0.28);
}

.rice-bigscreen .map-detail {
  border-color: rgba(84, 218, 131, 0.24);
  background: rgba(3, 19, 31, 0.92);
}

.screen-chart-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  min-height: 0;
}

/* 实时环境监测标题跳转入口 */
.environment-record-title-link {
  display: block;
  cursor: pointer;
  outline: none;
}

.environment-record-title-link .panel-title {
  transition:
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.environment-record-title-link:hover .panel-title {
  background: rgba(79, 154, 90, 0.09);
  box-shadow: inset 0 -2px 0 rgba(79, 154, 90, 0.48);
}

.environment-record-title-link:focus-visible .panel-title {
  border-radius: 5px;
  box-shadow:
    inset 0 0 0 2px rgba(79, 154, 90, 0.48),
    inset 0 -2px 0 rgba(79, 154, 90, 0.48);
}

.environment-record-title-link .panel-title-main strong {
  position: relative;
}

.environment-record-title-link .panel-title-main strong::after {
  margin-left: 7px;
  color: #4f9a5a;
  content: '→';
  font-size: 14px;
  font-weight: 800;
  opacity: 0;
  transform: translateX(-3px);
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.environment-record-title-link:hover .panel-title-main strong::after,
.environment-record-title-link:focus-visible .panel-title-main strong::after {
  opacity: 1;
  transform: translateX(0);
}

/* 实时环境监测滚动轮播 */
.environment-record-card .panel-title {
  height: 42px;
  padding: 0 14px;
}

.environment-record-card .panel-title-main strong {
  font-size: 18px;
  font-weight: 800;
  color: #183d27;
}

.environment-record-card .panel-title-extra {
  font-size: 15px;
  font-weight: 700;
  color: #355f40;
}

.environment-record-card {
  grid-column: 1 / -1;
  width: 100%;
  --record-columns:
    minmax(82px, 1.12fr)
    minmax(108px, 1.38fr)
    minmax(58px, 0.72fr)
    minmax(58px, 0.72fr)
    minmax(58px, 0.72fr)
    minmax(62px, 0.82fr)
    minmax(66px, 0.82fr)
    minmax(72px, 0.92fr)
    minmax(54px, 0.62fr);
}

.environment-record-board {
  height: calc(100% - 42px);
  min-height: 136px;
  padding: 7px 12px 10px;
}

.environment-record-head,
.environment-record-row {
  display: grid;
  grid-template-columns: var(--record-columns);
  align-items: center;
  column-gap: 6px;
  min-width: 0;
  
}

.environment-record-head {
  height: 32px;
  padding: 0 11px;
  border-bottom: 1px solid rgba(195, 203, 197, 0.904);
  color: #4f6656;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
}

.environment-record-viewport {
  position: relative;
  height: calc(100% - 32px);
  min-height: 96px;
  overflow: hidden;
}

.environment-record-viewport::before,
.environment-record-viewport::after {
  position: absolute;
  right: 0;
  left: 0;
  z-index: 2;
  height: 12px;
  pointer-events: none;
  content: '';
}

.environment-record-viewport::before {
  top: 0;
  background: linear-gradient(180deg, rgba(5, 25, 33, 0.92), transparent);
}

.environment-record-viewport::after {
  bottom: 0;
  background: linear-gradient(0deg, rgba(5, 25, 33, 0.94), transparent);
}

.environment-record-track {
  will-change: transform;
}

.environment-record-track.is-scrolling {
  animation: environment-record-scroll var(--scroll-duration) linear infinite;
}

.environment-record-viewport:hover .environment-record-track.is-scrolling {
  animation-play-state: paused;
}

.environment-record-row {
  height: 36px;
  padding: 0 11px;
  border-bottom: 1px dashed rgba(79, 154, 90, 0.12);
  color: #3f5948;
  font-size: 12px;
  font-weight: 600;
  transition: background 0.18s ease;
}

.environment-record-row:hover {
  background: rgba(63, 216, 124, 0.055);
}

.environment-record-row time,
.environment-record-row strong,
.environment-record-row span,
.environment-record-row em {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.environment-record-row time {
  color: #64776b;
  font-size: 12px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.environment-record-row strong {
  color: #263f2e;
  font-size: 12.5px;
  font-weight: 750;
}

.environment-record-row span {
  color: #2f7d4a;
  font-size: 12px;
  font-weight: 750;
  font-variant-numeric: tabular-nums;
}

.environment-record-row span small {
  margin-left: 2px;
  color: #7699a8;
  font-size: 9px;
  font-weight: 600;
}

.environment-record-row em {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  gap: 4px;
  margin: 0;
  padding: 3px 6px;
  border: 1px solid rgba(120, 169, 183, 0.16);
  border-radius: 999px;
  color: #91adba;
  background: rgba(120, 169, 183, 0.06);
  font-size: 10px;
  line-height: 1;
  font-style: normal;
  font-weight: 700;
}

.environment-record-row em i {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 7px currentColor;
}

.environment-record-row em.online {
  color: #5fe2a0;
  border-color: rgba(95, 226, 160, 0.2);
  background: rgba(95, 226, 160, 0.06);
}

.environment-record-row em.warning {
  color: #f0c465;
  border-color: rgba(240, 196, 101, 0.22);
  background: rgba(240, 196, 101, 0.065);
}

.environment-record-row em.offline {
  color: #e77f7f;
  border-color: rgba(231, 127, 127, 0.22);
  background: rgba(231, 127, 127, 0.065);
}

@keyframes environment-record-scroll {
  from { transform: translateY(0); }
  to { transform: translateY(-50%); }
}

.rice-bigscreen .chart-card {
  min-height: 0;
}

.rice-bigscreen .trend-chart {
  height: calc(100% - 38px);
  min-height: 138px;
}

.rice-bigscreen .trend-chart.small {
  height: 138px;
  min-height: 138px;
}

.rice-bigscreen .right-side.has-task-panel .trend-chart.small {
  height: 80px;
  min-height: 80px;
}

.rice-bigscreen .env-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 10px;
}

.rice-bigscreen .env-grid article {
  padding: 10px 8px;
  background: rgba(4, 24, 39, 0.58);
}

.rice-bigscreen .env-grid strong {
  font-size: 18px;
}

.rice-bigscreen .disease-result {
  padding: 12px 14px;
}

.rice-bigscreen .disease-result dl {
  gap: 8px;
}

.rice-bigscreen .disease-result div {
  padding-bottom: 6px;
}

.rice-bigscreen .task-panel .empty-data,
.rice-bigscreen .source-panel .empty-data {
  min-height: 118px;
}

.rice-bigscreen .task-list {
  grid-template-columns: 1fr;
  gap: 8px;
  padding: 10px 12px;
  max-height: calc(100% - 38px);
  overflow: auto;
}

.rice-bigscreen .task-list article {
  padding: 9px 10px;
  background: rgba(4, 24, 39, 0.58);
}

.rice-bigscreen .source-list {
  gap: 0;
  padding: 8px 12px;
}

.rice-bigscreen .source-list article {
  padding: 8px 0;
}

.rice-bigscreen .empty-data {
  min-height: 132px;
  padding: 18px;
}

.rice-bigscreen .field-map > .empty-data {
  height: 100%;
}

.rice-bigscreen .data-note {
  margin: 4px 0 0;
  text-align: center;
}

@media (max-width: 1500px) {
  .bigscreen-shell {
    min-height: 820px;
    overflow: visible;
  }

  .rice-bigscreen {
    overflow: auto;
  }

  .screen-body {
    grid-template-columns: 270px minmax(0, 1fr) 330px;
  }

  .rice-bigscreen .map-head {
    grid-template-columns: 1fr;
  }

  .rice-bigscreen .map-filters {
    padding: 0 12px 10px;
  }

  .rice-bigscreen .map-panel {
    grid-template-rows: 110px minmax(0, 1fr);
  }
}

@media (max-width: 1180px) {
  .rice-bigscreen {
    overflow: auto;
  }

  .bigscreen-shell {
    height: auto;
    min-height: 0;
  }

  .screen-header,
  .screen-body {
    grid-template-columns: 1fr;
  }

  .screen-side,
  .screen-center,
  .left-side,
  .right-side {
    grid-template-rows: auto;
  }

  .kpi-strip {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .rice-bigscreen .map-panel {
    min-height: 520px;
  }
}

@media (max-width: 760px) {
  .screen-header,
  .kpi-strip,
  .screen-chart-row,
  .rice-bigscreen .map-filters,
  .rice-bigscreen .env-grid {
    grid-template-columns: 1fr;
  }
}

.rice-bigscreen {
  isolation: isolate;
  background-color: #061a11 !important;
}

.rice-bigscreen :deep(.el-loading-mask) {
  background-color: rgba(4, 18, 29, 0.88);
}

.bigscreen-shell,
.screen-body {
  background:
    linear-gradient(180deg, rgba(5, 18, 32, 0.98), rgba(4, 20, 26, 0.98)),
    #061a11;
}

.screen-body {
  padding: 0;
  border-radius: 8px;
}

.screen-side {
  padding: 8px;
  border: 1px solid rgba(46, 190, 101, 0.16);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(3, 18, 31, 0.96), rgba(4, 24, 28, 0.96));
}

.screen-center {
  background: transparent;
}

.screen-side .panel,
.screen-center .panel {
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.018);
}

:global(.app-main),
:global(.main-container),
:global(.layout-container) {
  background-color: #061a11;
}
/* 实时环境监测：表头与数据九列严格对齐 */
.environment-record-head > *,
.environment-record-row > * {
  width: 100%;
  min-width: 0;
  margin: 0;
  justify-self: stretch;
  text-align: center;
}

/* 表头全部居中 */
.environment-record-head > span {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* 采集时间、监测设备居中 */
.environment-record-row > time,
.environment-record-row > strong {
  display: block;
  width: 100%;
  text-align: center;
}

/* 数值和单位作为整体居中 */
.environment-record-row > span {
  display: flex;
  width: 100%;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  text-align: center;
}

.environment-record-row > span small {
  margin-left: 0;
}

/* 状态标签居中 */
.environment-record-row > em {
  width: max-content;
  max-width: 100%;
  justify-self: center;
}

/* 表头和数据左右边距完全一致 */
.environment-record-head,
.environment-record-row {
  padding-right: 11px;
  padding-left: 11px;
}

/* =========================================================
   田间温湿度趋势面板
========================================================= */
.environment-trend-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
}

.environment-trend-heading {
  border-bottom: 1px solid var(--line-soft);
}

.environment-trend-heading .panel-title {
  height: 36px;
  border-bottom: 0;
}

.environment-trend-controls {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 92px;
  gap: 7px;
  padding: 5px 9px 7px;
}

.environment-trend-controls :deep(.el-select__wrapper) {
  min-height: 28px;
  padding: 0 9px;
  color: #dff7ff;
  border-radius: 5px;
  background: rgba(3, 20, 34, 0.88);
  box-shadow: 0 0 0 1px rgba(84, 218, 131, 0.20) inset;
}

.environment-trend-controls :deep(.el-select__wrapper:hover),
.environment-trend-controls :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px rgba(98, 217, 211, 0.48) inset,
    0 0 12px rgba(98, 217, 211, 0.08);
}

.environment-trend-controls :deep(.el-select__selected-item),
.environment-trend-controls :deep(.el-select__placeholder),
.environment-trend-controls :deep(.el-select__caret) {
  color: #cfe8f0;
  font-size: 10px;
}

.environment-trend-content {
  display: grid;
  grid-template-rows: 38px minmax(0, 1fr);
  min-height: 0;
  padding: 0 8px 7px;
}

.environment-trend-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 76px 76px;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.trend-device-name,
.trend-current-value {
  min-width: 0;
}

.trend-device-name span,
.trend-current-value span {
  display: block;
  color: #759bad;
  font-size: 8px;
  line-height: 1.2;
}

.trend-device-name strong {
  display: block;
  margin-top: 3px;
  overflow: hidden;
  color: #e9f8fd;
  font-size: 10px;
  line-height: 1.2;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.trend-current-value {
  padding-left: 7px;
  border-left: 1px solid rgba(84, 218, 131, 0.13);
}

.trend-current-value strong {
  display: flex;
  align-items: baseline;
  gap: 2px;
  margin-top: 2px;
  font-size: 15px;
  line-height: 1;
  font-weight: 800;
}

.trend-current-value strong small {
  font-size: 8px;
  font-weight: 600;
}

.trend-current-value.temperature strong {
  color: #C88745;
}

.trend-current-value.humidity strong {
  color: #4E9982;
}

.environment-trend-chart {
  width: 100%;
  min-width: 0;
  min-height: 0;
}

.environment-trend-chart :deep(.el-loading-mask) {
  background: rgba(5, 24, 35, 0.62);
}

.environment-trend-chart :deep(.el-loading-spinner .circular) {
  width: 26px;
  height: 26px;
}

/* 为趋势图增加一点高度，同时保持右侧其他模块完整 */
.right-side {
  grid-template-rows: 250px 194px minmax(0, 1fr);
}

.right-side.has-task-panel {
  grid-template-rows: 215px 155px 105px minmax(128px, 1fr);
}

@media (max-width: 1500px) {
  .environment-trend-summary {
    grid-template-columns: minmax(0, 1fr) 68px 68px;
  }

  .trend-current-value strong {
    font-size: 14px;
  }
}

@media (max-width: 1180px) {
  .environment-trend-panel {
    min-height: 260px;
  }

  .environment-trend-chart {
    min-height: 150px;
  }
}

@media (max-width: 760px) {
  .environment-trend-controls {
    grid-template-columns: 1fr;
  }

  .trend-range-select {
    width: 100%;
  }

  .environment-trend-summary {
    grid-template-columns: minmax(0, 1fr) 72px 72px;
  }
}


/* =========================================================
   田间环境综合监测：一个设备选择控制全部环境图表
========================================================= */

.screen-center {
  grid-template-rows: minmax(0, 1fr) 310px;
}

.environment-dashboard-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  min-height: 0;
}

.environment-dashboard-header {
  border-bottom: 1px solid var(--line-soft);
  background: rgba(3, 20, 34, 0.30);
}

.environment-dashboard-title-link {
  display: block;
  cursor: pointer;
  outline: none;
}

.environment-dashboard-title-link .panel-title {
  height: 34px;
  border-bottom: 0;
}

.environment-dashboard-title-link:hover .panel-title,
.environment-dashboard-title-link:focus-visible .panel-title {
  background: rgba(63, 216, 124, 0.055);
}

.environment-global-controls {
  display: grid;
  grid-template-columns:
    minmax(230px, 1.45fr)
    110px
    minmax(132px, 0.62fr)
    minmax(150px, 0.76fr)
    66px;
  align-items: end;
  gap: 8px;
  padding: 5px 10px 8px;
}

.environment-control-item {
  display: grid;
  min-width: 0;
  gap: 4px;
}

.environment-control-item > span,
.environment-control-status small,
.environment-control-time small {
  color: #7399aa;
  font-size: 8px;
  line-height: 1;
  font-weight: 700;
}

.environment-global-controls :deep(.el-select) {
  width: 100%;
}

.environment-global-controls :deep(.el-select__wrapper) {
  min-height: 29px;
  padding: 0 9px;
  color: #e7f7fc;
  border-radius: 5px;
  background: rgba(3, 20, 34, 0.90);
  box-shadow: 0 0 0 1px rgba(84, 218, 131, 0.20) inset;
}

.environment-global-controls :deep(.el-select__wrapper:hover),
.environment-global-controls :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px rgba(98, 217, 211, 0.50) inset,
    0 0 12px rgba(98, 217, 211, 0.07);
}

.environment-global-controls :deep(.el-select__selected-item),
.environment-global-controls :deep(.el-select__placeholder),
.environment-global-controls :deep(.el-select__caret) {
  color: #cfe8f0;
  font-size: 10px;
}

.environment-control-status,
.environment-control-time {
  display: flex;
  align-items: center;
  min-width: 0;
  min-height: 29px;
  gap: 7px;
  padding: 0 9px;
  border: 1px solid rgba(84, 218, 131, 0.13);
  border-radius: 5px;
  background: rgba(3, 20, 34, 0.56);
}

.environment-control-status > div,
.environment-control-time {
  min-width: 0;
}

.environment-control-status > div {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 6px;
}

.environment-control-status strong,
.environment-control-time strong {
  display: block;
  margin-top: 0;
  overflow: hidden;
  color: #e2f3f8;
  font-size: 9px;
  line-height: 1;
  font-weight: 750;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.environment-status-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 7px;
  border-radius: 50%;
  background: #829ba6;
  box-shadow: 0 0 0 3px rgba(130, 155, 166, 0.10);
}

.environment-status-dot.online {
  background: #55d98b;
  box-shadow:
    0 0 0 3px rgba(85, 217, 139, 0.12),
    0 0 9px rgba(85, 217, 139, 0.28);
}

.environment-status-dot.warning {
  background: #f2c765;
  box-shadow:
    0 0 0 3px rgba(242, 199, 101, 0.12),
    0 0 9px rgba(242, 199, 101, 0.24);
}

.environment-status-dot.offline {
  background: #e26767;
  box-shadow:
    0 0 0 3px rgba(226, 103, 103, 0.12),
    0 0 9px rgba(226, 103, 103, 0.24);
}

.environment-refresh-button {
  width: 66px;
  min-height: 29px;
  margin: 0 !important;
}

.environment-chart-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  min-height: 0;
  gap: 7px;
  padding: 7px 9px 10px;
}

.environment-chart-cell {
  display: grid;
  grid-template-rows: 32px minmax(132px, 1fr);
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(84, 218, 131, 0.13);
  border-radius: 6px;
  background:
    linear-gradient(
      145deg,
      rgba(7, 34, 48, 0.80),
      rgba(3, 20, 32, 0.86)
    );
}

.environment-chart-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  gap: 7px;
  padding: 5px 7px;
  border-bottom: 1px solid rgba(84, 218, 131, 0.10);
}

.environment-chart-title > div {
  min-width: 0;
}

.environment-chart-title strong,
.environment-chart-title small {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.environment-chart-title strong {
  color: #e6f5fa;
  font-size: 10px;
  line-height: 1;
  font-weight: 750;
}

.environment-chart-title small {
  margin-top: 4px;
  color: #7399aa;
  font-size: 7px;
  line-height: 1;
}

.environment-chart-title > span {
  flex: 0 0 auto;
  color: #6fa8b9;
  font-size: 7px;
  font-weight: 700;
}

.environment-mini-chart {
  width: 100%;
  min-width: 0;
  min-height: 0;
}

.environment-chart-grid :deep(.el-loading-mask) {
  background: rgba(4, 22, 33, 0.64);
}

/* =========================================================
   右侧所选设备的 8 项实时指标
========================================================= */

.environment-metric-panel {
  display: grid;
  grid-template-rows: 38px minmax(0, 1fr);
  min-height: 0;
}

.environment-metric-content {
  display: grid;
  grid-template-rows: 42px minmax(0, 1fr);
  min-height: 0;
  padding: 6px 8px 8px;
}

.environment-device-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  gap: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(84, 218, 131, 0.11);
}

.environment-device-identity {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 7px;
}

.environment-device-identity > div {
  min-width: 0;
}

.environment-device-identity strong,
.environment-device-identity small {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.environment-device-identity strong {
  color: #e8f7fb;
  font-size: 10px;
  font-weight: 750;
}

.environment-device-identity small {
  margin-top: 4px;
  color: #789cab;
  font-size: 7px;
}

.environment-device-state-icon {
  display: grid;
  width: 25px;
  height: 25px;
  flex: 0 0 25px;
  place-items: center;
  border: 1px solid rgba(126, 157, 169, 0.18);
  border-radius: 6px;
  background: rgba(126, 157, 169, 0.06);
}

.environment-device-state-icon i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #829ba6;
}

.environment-device-state-icon.online i {
  background: #55d98b;
  box-shadow: 0 0 8px rgba(85, 217, 139, 0.42);
}

.environment-device-state-icon.warning i {
  background: #f2c765;
  box-shadow: 0 0 8px rgba(242, 199, 101, 0.38);
}

.environment-device-state-icon.offline i {
  background: #e26767;
  box-shadow: 0 0 8px rgba(226, 103, 103, 0.38);
}

.environment-data-quality {
  flex: 0 0 auto;
  padding: 4px 7px;
  color: #70cfa0;
  border: 1px solid rgba(85, 217, 139, 0.16);
  border-radius: 999px;
  background: rgba(85, 217, 139, 0.055);
  font-size: 7px;
  font-weight: 750;
}

.selected-environment-metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  min-height: 0;
  gap: 5px;
  padding-top: 6px;
}

.selected-environment-metric {
  --metric-color: #4E9982;

  position: relative;
  display: flex;
  min-width: 0;
  min-height: 0;
  padding: 6px 7px;
  overflow: hidden;
  flex-direction: column;
  justify-content: center;
  border: 1px solid rgba(84, 218, 131, 0.10);
  border-radius: 5px;
  background: rgba(3, 20, 34, 0.47);
}

.selected-environment-metric::before {
  position: absolute;
  top: 5px;
  bottom: 5px;
  left: 0;
  width: 2px;
  border-radius: 0 2px 2px 0;
  content: "";
  background: var(--metric-color);
  opacity: 0.78;
}

.selected-environment-metric > span {
  color: #789cab;
  font-size: 7px;
  line-height: 1;
}

.selected-environment-metric > strong {
  margin-top: 5px;
  overflow: hidden;
  color: var(--metric-color);
  font-size: 13px;
  line-height: 1;
  font-weight: 800;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.selected-environment-metric > strong small {
  margin-left: 2px;
  color: #8da8b3;
  font-size: 7px;
  font-weight: 600;
}

.selected-environment-metric > i {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #697f89;
}

.selected-environment-metric > i.available {
  background: #55d98b;
  box-shadow: 0 0 6px rgba(85, 217, 139, 0.36);
}

.selected-environment-metric.air-temperature {
  --metric-color: #C88745;
}

.selected-environment-metric.air-humidity {
  --metric-color: #4E9982;
}

.selected-environment-metric.soil-temperature {
  --metric-color: #B98952;
}

.selected-environment-metric.soil-moisture {
  --metric-color: #4E8FA6;
}

.selected-environment-metric.illuminance {
  --metric-color: #C5A13D;
}

.selected-environment-metric.co2 {
  --metric-color: #7484A5;
}

.selected-environment-metric.rainfall {
  --metric-color: #4C93A0;
}

.selected-environment-metric.battery {
  --metric-color: #5B9868;
}

/* 右侧布局：环境实时指标优先保证展示空间 */
.right-side {
  grid-template-rows: 248px 178px minmax(0, 1fr);
}

.right-side.has-task-panel {
  grid-template-rows: 226px 150px 104px minmax(118px, 1fr);
}

@media (max-width: 1500px) {
  .environment-global-controls {
    grid-template-columns:
      minmax(190px, 1.35fr)
      98px
      106px
      112px
      60px;
    gap: 6px;
  }

  .environment-chart-grid {
    gap: 5px;
  }

  .environment-chart-title small {
    display: none;
  }
}

@media (max-width: 1180px) {
  .screen-center {
    grid-template-rows: minmax(360px, 1fr) 560px;
  }

  .environment-global-controls {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .environment-control-status,
  .environment-control-time {
    min-height: 31px;
  }

  .environment-refresh-button {
    grid-column: span 2;
    width: 100%;
  }

  .environment-chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .environment-chart-cell {
    min-height: 205px;
  }
}

@media (max-width: 760px) {
  .environment-global-controls,
  .environment-chart-grid {
    grid-template-columns: 1fr;
  }

  .environment-refresh-button {
    grid-column: span 1;
  }

  .environment-chart-cell {
    min-height: 210px;
  }

  .selected-environment-metric-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}


/* =========================================================
   田间环境综合监测——浅色农业专业主题
   统一整个平台的白色、浅灰、稻叶绿视觉语言
========================================================= */

/* 综合监测模块整体 */
.environment-dashboard-panel {
  border-color: #d9e6dc !important;
  background: #ffffff !important;
  box-shadow:
    0 8px 24px rgba(39, 77, 49, 0.055),
    0 1px 2px rgba(39, 77, 49, 0.035) !important;
}

.environment-dashboard-header {
  border-bottom-color: #dfe9e2 !important;
  background: linear-gradient(180deg, #ffffff, #f8fbf8) !important;
}

.environment-dashboard-title-link:hover .panel-title,
.environment-dashboard-title-link:focus-visible .panel-title {
  background: #f0f7f1 !important;
}

/* 设备选择控制栏 */
.environment-global-controls {
  background: #f7faf7;
  border-top: 1px solid #edf2ee;
}

.environment-control-item > span,
.environment-control-status small,
.environment-control-time small {
  color: #6f8275 !important;
}

.environment-global-controls :deep(.el-select__wrapper) {
  color: #355441 !important;
  border: 1px solid #d4e2d7 !important;
  background: #ffffff !important;
  box-shadow: 0 1px 2px rgba(45, 78, 54, 0.035) !important;
}

.environment-global-controls :deep(.el-select__wrapper:hover) {
  border-color: #aac8b1 !important;
  box-shadow: 0 0 0 1px rgba(76, 143, 89, 0.04) !important;
}

.environment-global-controls :deep(.el-select__wrapper.is-focused) {
  border-color: #5d9a6d !important;
  box-shadow: 0 0 0 3px rgba(76, 143, 89, 0.10) !important;
}

.environment-global-controls :deep(.el-select__selected-item),
.environment-global-controls :deep(.el-select__placeholder),
.environment-global-controls :deep(.el-select__caret) {
  color: #355441 !important;
}

.environment-control-status,
.environment-control-time {
  border-color: #d8e5db !important;
  background: #ffffff !important;
}

.environment-control-status strong,
.environment-control-time strong {
  color: #294b35 !important;
}

.environment-refresh-button {
  border-color: #3f8f59 !important;
  color: #ffffff !important;
  background: linear-gradient(180deg, #4c9a62, #397f4f) !important;
  box-shadow: 0 5px 12px rgba(57, 127, 79, 0.15) !important;
}

/* 四张趋势图卡片 */
.environment-chart-grid {
  background: #f5f8f5;
}

.environment-chart-cell {
  border-color: #d9e5dc !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  box-shadow:
    0 5px 15px rgba(39, 77, 49, 0.045),
    0 1px 2px rgba(39, 77, 49, 0.025);
}

.environment-chart-title {
  border-bottom-color: #e4ece6 !important;
  background: linear-gradient(180deg, #fbfdfb, #f6faf7);
}

.environment-chart-title strong {
  color: #274a34 !important;
  font-size: 10px;
}

.environment-chart-title small {
  color: #7d8d82 !important;
}

.environment-chart-title > span {
  color: #789083 !important;
  padding: 3px 6px;
  border: 1px solid #dce7df;
  border-radius: 999px;
  background: #f1f7f2;
}

.environment-chart-grid :deep(.el-loading-mask) {
  background: rgba(247, 250, 247, 0.82) !important;
}

/* 右侧实时环境指标卡 */
.environment-metric-panel {
  border-color: #d9e6dc !important;
  background: #ffffff !important;
  box-shadow:
    0 8px 24px rgba(39, 77, 49, 0.055),
    0 1px 2px rgba(39, 77, 49, 0.03) !important;
}

.environment-metric-content {
  background: #ffffff;
}

.environment-device-summary {
  padding: 6px 8px 9px;
  border-bottom-color: #e3ebe5 !important;
  border-radius: 8px;
  background: #f4f9f5;
}

.environment-device-identity strong {
  color: #284b35 !important;
}

.environment-device-identity small {
  color: #788a7e !important;
}

.environment-device-state-icon {
  border-color: #cee0d2 !important;
  background: #eaf5ec !important;
}

.environment-data-quality {
  color: #39784d !important;
  border-color: #cde1d2 !important;
  background: #edf7ef !important;
}

/* 指标卡统一为浅色卡片，不再使用深灰背景 */
.selected-environment-metric {
  border-color: #dce7df !important;
  border-radius: 7px !important;
  background:
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--metric-color) 5%, #ffffff),
      #ffffff 72%
    ) !important;
  box-shadow: 0 2px 7px rgba(39, 77, 49, 0.035);
}

.selected-environment-metric::before {
  top: 7px;
  bottom: 7px;
  width: 3px;
  opacity: 0.82;
}

.selected-environment-metric > span {
  color: #687c6f !important;
  font-size: 8px;
  font-weight: 650;
}

.selected-environment-metric > strong {
  color: color-mix(in srgb, var(--metric-color) 78%, #294836) !important;
  font-size: 14px;
}

.selected-environment-metric > strong small {
  color: #78897e !important;
}

.selected-environment-metric > i {
  background: #bdc9c0 !important;
}

.selected-environment-metric > i.available {
  background: #4c9a62 !important;
  box-shadow: 0 0 0 3px rgba(76, 154, 98, 0.10) !important;
}

/* 低饱和专业配色 */
.selected-environment-metric.air-temperature {
  --metric-color: #C88745;
}

.selected-environment-metric.air-humidity {
  --metric-color: #4E9982;
}

.selected-environment-metric.soil-temperature {
  --metric-color: #B98952;
}

.selected-environment-metric.soil-moisture {
  --metric-color: #4E8FA6;
}

.selected-environment-metric.illuminance {
  --metric-color: #C5A13D;
}

.selected-environment-metric.co2 {
  --metric-color: #7484A5;
}

.selected-environment-metric.rainfall {
  --metric-color: #4C93A0;
}

.selected-environment-metric.battery {
  --metric-color: #5B9868;
}


/* =========================================================
   设备实时环境指标——可见性修复
   解决 8 项指标卡高度不足、数值被裁剪的问题
========================================================= */

/* 第一步：给右侧环境指标面板足够高度 */
.right-side {
  grid-template-rows: 335px 178px minmax(0, 1fr) !important;
}

.right-side.has-task-panel {
  grid-template-rows: 330px 150px 104px minmax(118px, 1fr) !important;
}

.environment-metric-panel {
  min-height: 335px !important;
  grid-template-rows: 42px minmax(0, 1fr) !important;
  overflow: visible !important;
}

/* 第二步：设备摘要区域稍微加高 */
.environment-metric-content {
  min-height: 0 !important;
  padding: 8px 10px 10px !important;
  grid-template-rows: 58px minmax(0, 1fr) !important;
  overflow: visible !important;
}

.environment-device-summary {
  min-height: 52px !important;
  padding: 8px 10px !important;
}

/* 第三步：8 个指标固定为两列四行，每行保证高度 */
.selected-environment-metric-grid {
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  grid-template-rows: repeat(4, minmax(50px, 1fr)) !important;
  gap: 7px !important;
  min-height: 218px !important;
  padding-top: 8px !important;
  overflow: visible !important;
}

/* 第四步：每张指标卡不再被压扁 */
.selected-environment-metric {
  min-height: 50px !important;
  padding: 8px 10px 8px 13px !important;
  overflow: hidden !important;
  justify-content: center !important;
}

/* 指标名称放大 */
.selected-environment-metric > span {
  display: block !important;
  color: #5f7466 !important;
  font-size: 10px !important;
  line-height: 1.2 !important;
  font-weight: 700 !important;
  white-space: nowrap !important;
}

/* 指标数值明显放大，并保证完整显示 */
.selected-environment-metric > strong {
  display: flex !important;
  align-items: baseline !important;
  min-height: 21px !important;
  margin-top: 7px !important;
  overflow: visible !important;
  font-size: 18px !important;
  line-height: 1.15 !important;
  font-weight: 800 !important;
  letter-spacing: -0.2px !important;
  white-space: nowrap !important;
  text-overflow: clip !important;
}

/* 单位字号同步放大 */
.selected-environment-metric > strong small {
  margin-left: 3px !important;
  font-size: 9px !important;
  line-height: 1 !important;
  font-weight: 650 !important;
}

/* 右上角有效状态点 */
.selected-environment-metric > i {
  top: 9px !important;
  right: 9px !important;
  width: 6px !important;
  height: 6px !important;
}

/* 左侧指标颜色条 */
.selected-environment-metric::before {
  top: 9px !important;
  bottom: 9px !important;
  width: 3px !important;
}

/* 设备名称和采集时间也放大 */
.environment-device-identity strong {
  font-size: 12px !important;
  line-height: 1.2 !important;
}

.environment-device-identity small {
  margin-top: 5px !important;
  font-size: 9px !important;
  line-height: 1.2 !important;
}

.environment-data-quality {
  padding: 5px 8px !important;
  font-size: 9px !important;
}

/* 1366 等较窄屏幕仍保持可读 */
@media (max-width: 1500px) {
  .right-side {
    grid-template-rows: 325px 170px minmax(0, 1fr) !important;
  }

  .environment-metric-panel {
    min-height: 325px !important;
  }

  .selected-environment-metric-grid {
    grid-template-rows: repeat(4, minmax(48px, 1fr)) !important;
    min-height: 210px !important;
  }

  .selected-environment-metric {
    min-height: 48px !important;
  }

  .selected-environment-metric > strong {
    font-size: 16px !important;
  }
}


/* =========================================================
   可视化大屏中央 Leaflet 地图
========================================================= */

.dashboard-map-panel {
  position: relative;
  display: grid !important;
  grid-template-rows: auto minmax(0, 1fr) !important;
  overflow: hidden !important;
}

.dashboard-map-panel .map-head {
  position: relative;
  z-index: 1200;
  isolation: isolate;
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: auto auto;
  min-height: 82px;
  border-bottom: 1px solid #dce8df !important;
  background: linear-gradient(180deg, #ffffff, #f8fbf8) !important;
}

.dashboard-map-panel .map-title {
  min-width: 0;
}

.dashboard-map-panel .map-title .panel-title {
  height: 36px;
  border-bottom: 0;
  background: transparent !important;
}

.dashboard-map-panel .map-filters {
  position: relative;
  z-index: 1201;
  pointer-events: auto;
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  padding: 0 10px 10px;
  overflow: hidden;
  border-top: 1px solid rgba(211, 225, 214, 0.72);
}

.dashboard-map-mode-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 11px;
  border: 1px solid rgba(63, 143, 89, 0.26);
  border-radius: 7px;
  color: #2f6f45;
  background: rgba(238, 248, 241, 0.90);
  font-size: 10px;
  font-weight: 700;
  white-space: nowrap;
}

.dashboard-map-panel .map-filters .dashboard-map-mode-badge {
  flex: 0 0 136px;
}

.dashboard-map-panel .map-filters .dashboard-basemap-switch {
  flex: 0 0 auto;
}

.dashboard-map-panel .map-filters .dashboard-layer-switch {
  flex: 0 0 auto;
}

.dashboard-map-panel .map-filters .dashboard-base-filter {
  flex: 0 0 116px;
  min-width: 116px;
}

.dashboard-map-panel .map-filters .dashboard-node-filter {
  flex: 1 1 150px;
  min-width: 120px;
}

.dashboard-map-panel .map-filters .dashboard-refresh-button {
  flex: 0 0 86px;
  min-width: 86px;
}

.dashboard-map-panel .map-filters :deep(.el-select__wrapper),
.dashboard-map-panel .map-filters :deep(.el-input__wrapper) {
  min-height: 34px;
  color: #355441 !important;
  border: 1px solid #d3e1d6 !important;
  border-radius: 7px;
  background: #ffffff !important;
  box-shadow: none !important;
}

.dashboard-map-panel .map-filters :deep(.el-select__wrapper:hover),
.dashboard-map-panel .map-filters :deep(.el-input__wrapper:hover) {
  border-color: #a8c6af !important;
}

.dashboard-map-panel .map-filters :deep(.el-select__selected-item),
.dashboard-map-panel .map-filters :deep(.el-select__placeholder),
.dashboard-map-panel .map-filters :deep(.el-input__inner),
.dashboard-map-panel .map-filters :deep(.el-select__caret),
.dashboard-map-panel .map-filters :deep(.el-input__icon) {
  color: #476052 !important;
  font-size: 10px;
}

.dashboard-map-panel .map-filters :deep(.el-button) {
  min-height: 34px;
  margin: 0;
  border-color: #3f8f59 !important;
  border-radius: 7px;
  color: #ffffff !important;
  background: linear-gradient(180deg, #4d9b63, #387d4e) !important;
  box-shadow: 0 5px 12px rgba(56, 125, 78, 0.14);
  font-size: 10px;
  font-weight: 700;
}

.dashboard-map-stage {
  position: relative;
  z-index: 1;
  min-width: 0;
  min-height: 420px;
  margin: 0;
  overflow: hidden;
  background: #eaf0eb;
}

.dashboard-leaflet-map {
  position: absolute;
  inset: 0;
  z-index: 1;
  width: 100%;
  height: 100%;
  min-height: 420px;
  background: #eaf0eb;
}

/* 地图图例 */
.dashboard-map-legend {
  position: absolute;
  top: 12px;
  left: 54px;
  z-index: 510;
  pointer-events: auto;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px;
  max-width: calc(100% - 430px);
  padding: 7px 10px;
  border: 1px solid rgba(72, 124, 84, 0.17);
  border-radius: 8px;
  color: #52695a;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 18px rgba(39, 77, 49, 0.09);
  backdrop-filter: blur(10px);
  font-size: 9px;
}

.dashboard-map-legend span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.map-legend-symbol {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 3px;
  background: #4f9a62;
}

.map-legend-symbol.base {
  border-radius: 50% 50% 50% 0;
  background: #347d4c;
  transform: rotate(-45deg);
}

.map-legend-symbol.low {
  background: #8fb764;
}

.map-legend-symbol.medium {
  background: #c6a145;
}

.map-legend-symbol.high {
  background: #c76565;
}

.map-legend-symbol.county {
  border-radius: 2px;
  background: rgba(35, 209, 139, 0.72);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45);
}

.dashboard-map-stage :deep(.leaflet-control-container),
.dashboard-map-stage :deep(.leaflet-control-zoom),
.dashboard-map-stage :deep(.leaflet-popup-pane),
.dashboard-map-stage :deep(.leaflet-tooltip-pane) {
  z-index: 730 !important;
}

.map-legend-symbol.boundary {
  width: 14px;
  height: 0;
  border-top: 2px dashed #58d8ff;
  border-radius: 0;
  background: transparent;
}

.dashboard-basemap-floating {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 514;
  display: inline-flex;
}

.dashboard-layer-switch {
  position: static;
  z-index: auto;
  display: inline-flex;
  padding: 4px;
  border: 1px solid rgba(72, 124, 84, 0.17);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 6px 18px rgba(39, 77, 49, 0.09);
  backdrop-filter: blur(10px);
}

.dashboard-layer-switch :deep(.el-checkbox-button__inner) {
  height: 26px;
  min-width: 70px;
  padding: 0 10px;
  border: 0 !important;
  border-radius: 6px !important;
  color: #476052 !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 10px;
  font-weight: 700;
  line-height: 26px;
}

.dashboard-layer-switch :deep(.el-checkbox-button.is-checked .el-checkbox-button__inner) {
  color: #ffffff !important;
  background: linear-gradient(180deg, #4d9b63, #387d4e) !important;
  box-shadow: 0 5px 12px rgba(56, 125, 78, 0.14) !important;
}

.map-legend-symbol.device {
  border-radius: 50%;
  background: #4c93a0;
}

/* Leaflet 原生控件浅色化 */
.dashboard-map-stage :deep(.leaflet-control-zoom) {
  overflow: hidden;
  border: 1px solid #d4e1d7;
  border-radius: 8px;
  box-shadow: 0 5px 15px rgba(39, 77, 49, 0.10);
}

.dashboard-map-stage :deep(.leaflet-control-zoom a) {
  color: #376a49;
  border-bottom-color: #e1e9e3;
  background: rgba(255, 255, 255, 0.96);
}

.dashboard-map-stage :deep(.leaflet-control-zoom a:hover) {
  color: #245538;
  background: #eef6f0;
}

.dashboard-map-stage :deep(.leaflet-control-attribution) {
  color: #73857a;
  background: rgba(255, 255, 255, 0.82);
  font-size: 7px;
}

/* 基地标记 */
.dashboard-map-stage :deep(.dashboard-base-marker-wrapper),
.dashboard-map-stage :deep(.dashboard-node-marker-wrapper),
.dashboard-map-stage :deep(.dashboard-sensor-marker-wrapper) {
  border: 0;
  background: transparent;
}

.dashboard-map-stage :deep(.dashboard-base-marker),
.dashboard-map-stage :deep(.dashboard-node-marker) {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 7px;
  color: #234932;
  font-size: 10px;
  white-space: nowrap;
}

.dashboard-map-stage :deep(.dashboard-base-marker > span) {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  border: 3px solid #ffffff;
  border-radius: 50% 50% 50% 0;
  background: #3f8f59;
  box-shadow:
    0 0 0 4px rgba(63, 143, 89, 0.14),
    0 5px 12px rgba(39, 77, 49, 0.22);
  transform: rotate(-45deg);
}

.dashboard-map-stage :deep(.dashboard-base-marker b),
.dashboard-map-stage :deep(.dashboard-node-marker b) {
  max-width: 118px;
  overflow: hidden;
  padding: 5px 8px;
  border: 1px solid rgba(69, 122, 80, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 4px 12px rgba(39, 77, 49, 0.10);
  font-weight: 750;
  text-overflow: ellipsis;
}

/* 真实节点标记 */
.dashboard-map-stage :deep(.dashboard-node-marker > span) {
  width: 11px;
  height: 11px;
  flex: 0 0 11px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  background: #89988e;
  box-shadow: 0 0 0 4px rgba(137, 152, 142, 0.13);
}

.dashboard-map-stage :deep(.dashboard-node-marker.online > span) {
  background: #4f9a62;
  box-shadow: 0 0 0 4px rgba(79, 154, 98, 0.13);
}

.dashboard-map-stage :deep(.dashboard-node-marker.warning > span) {
  background: #c6a145;
  box-shadow: 0 0 0 4px rgba(198, 161, 69, 0.13);
}

.dashboard-map-stage :deep(.dashboard-node-marker.offline > span) {
  background: #c76565;
  box-shadow: 0 0 0 4px rgba(199, 101, 101, 0.13);
}

/* 监测设备点 */
.dashboard-map-stage :deep(.dashboard-sensor-marker) {
  display: grid;
  width: 15px;
  height: 15px;
  place-items: center;
  border: 2px solid #ffffff;
  border-radius: 50%;
  background: #4c93a0;
  box-shadow:
    0 0 0 4px rgba(76, 147, 160, 0.13),
    0 4px 10px rgba(45, 92, 100, 0.22);
}

.dashboard-map-stage :deep(.dashboard-sensor-marker span) {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #ffffff;
}

/* 地块永久标签 */
.dashboard-map-stage :deep(.dashboard-plot-label) {
  padding: 3px 6px;
  color: #365441;
  border: 1px solid rgba(66, 119, 77, 0.18);
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.89);
  box-shadow: none;
  font-size: 8px;
  font-weight: 750;
}

.dashboard-map-stage :deep(.dashboard-plot-label::before) {
  display: none;
}

/* Popup */
.dashboard-map-stage :deep(.leaflet-popup-content-wrapper) {
  border: 1px solid #d9e5dc;
  border-radius: 9px;
  color: #53695a;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 9px 24px rgba(39, 77, 49, 0.13);
}

.dashboard-map-stage :deep(.leaflet-popup-content) {
  margin: 10px 12px;
}

.dashboard-map-stage :deep(.dashboard-map-popup) {
  display: grid;
  gap: 4px;
}

.dashboard-map-stage :deep(.dashboard-map-popup strong) {
  color: #244832;
  font-size: 11px;
}

.dashboard-map-stage :deep(.dashboard-map-popup span) {
  color: #718278;
  font-size: 9px;
}

.dashboard-map-stage :deep(.leaflet-popup-tip) {
  background: #ffffff;
}

/* 适配常见屏幕 */
@media (max-width: 1500px) {
  .dashboard-map-panel .map-head {
    grid-template-columns: 1fr;
  }

  .dashboard-map-panel .map-filters {
    gap: 6px;
  }

  .dashboard-map-legend {
    max-width: calc(100% - 220px);
  }

  .dashboard-map-stage,
  .dashboard-leaflet-map {
    min-height: 390px;
  }
}

@media (max-width: 1180px) {
  .dashboard-map-panel .map-head {
    grid-template-columns: 1fr;
  }

  .dashboard-map-panel .map-filters {
    flex-wrap: wrap;
    padding: 0 10px 10px;
  }

  .dashboard-map-panel .map-filters .dashboard-basemap-switch,
  .dashboard-map-panel .map-filters .dashboard-layer-switch {
    flex: 1 1 180px;
  }

  .dashboard-map-legend {
    right: 12px;
    left: 54px;
    max-width: none;
  }
}

@media (max-width: 760px) {
  .dashboard-map-panel .map-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .dashboard-map-legend {
    display: none;
  }

  .dashboard-map-detail {
    right: 9px;
    bottom: 9px;
    min-width: 180px;
  }

  .dashboard-map-source-note {
    display: none;
  }

  .dashboard-map-stage,
  .dashboard-leaflet-map {
    min-height: 360px;
  }
}


/* 地图版权信息保留，并降低视觉占用 */
.dashboard-map-stage :deep(.leaflet-control-attribution) {
  right: 4px !important;
  bottom: 2px !important;
  padding: 1px 4px !important;
  color: #87958c !important;
  border-radius: 4px 0 0 0 !important;
  background: rgba(255, 255, 255, 0.72) !important;
  font-size: 6px !important;
  line-height: 1.2 !important;
}

.dashboard-map-stage :deep(.leaflet-control-attribution a) {
  color: #697b6f !important;
}

/* =========================================================
   可视化大屏深色指挥中心主题
   覆盖前面的浅色农业主题，使首页真正呈现大屏风格
========================================================= */
.rice-bigscreen {
  min-height: 100vh !important;
  color: #dff8ff !important;
  background:
    radial-gradient(circle at 50% 0%, rgba(34, 151, 208, 0.24), transparent 30%),
    radial-gradient(circle at 8% 18%, rgba(51, 224, 152, 0.16), transparent 28%),
    linear-gradient(180deg, #04101e 0%, #061827 45%, #03101b 100%) !important;
}

.rice-bigscreen::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(93, 218, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(93, 218, 255, 0.035) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.86), rgba(0, 0, 0, 0.18));
}

.rice-bigscreen,
.rice-bigscreen .bigscreen-shell,
.rice-bigscreen .screen-body {
  background-color: transparent !important;
}

.rice-bigscreen .bigscreen-shell {
  gap: 10px !important;
  padding: 10px !important;
}

.rice-bigscreen .screen-header {
  min-height: 50px !important;
  border: 1px solid rgba(63, 204, 255, 0.34) !important;
  border-radius: 6px !important;
  background:
    linear-gradient(90deg, rgba(4, 18, 35, 0.98), rgba(8, 40, 64, 0.90), rgba(4, 18, 35, 0.98)) !important;
  box-shadow:
    inset 0 0 24px rgba(63, 204, 255, 0.09),
    0 0 28px rgba(0, 0, 0, 0.28) !important;
}

.rice-bigscreen .screen-title {
  width: min(560px, 48vw) !important;
  height: 34px !important;
  border: 1px solid rgba(120, 232, 255, 0.36) !important;
  border-radius: 999px !important;
  background:
    linear-gradient(90deg, transparent, rgba(61, 188, 255, 0.22), transparent),
    rgba(6, 30, 52, 0.84) !important;
  box-shadow:
    inset 0 0 16px rgba(72, 218, 255, 0.16),
    0 0 18px rgba(51, 224, 152, 0.08) !important;
}

.rice-bigscreen .screen-title h1 {
  color: #f3fdff !important;
  font-size: 22px !important;
  line-height: 34px !important;
  letter-spacing: 0 !important;
  text-shadow:
    0 0 10px rgba(70, 212, 255, 0.70),
    0 0 18px rgba(51, 224, 152, 0.32) !important;
}

.rice-bigscreen .admin-entry {
  border: 1px solid rgba(71, 211, 255, 0.46) !important;
  color: #e8fbff !important;
  background: linear-gradient(180deg, rgba(14, 99, 149, 0.92), rgba(8, 55, 92, 0.94)) !important;
  box-shadow:
    inset 0 0 12px rgba(96, 224, 255, 0.14),
    0 0 18px rgba(55, 190, 255, 0.18) !important;
}

.rice-bigscreen .kpi-strip {
  gap: 10px !important;
}

.rice-bigscreen .kpi-card {
  min-height: 64px !important;
  border: 1px solid rgba(63, 204, 255, 0.24) !important;
  border-radius: 6px !important;
  color: #bcecff !important;
  background:
    linear-gradient(180deg, rgba(8, 37, 61, 0.92), rgba(5, 22, 39, 0.96)) !important;
  box-shadow:
    inset 0 1px 0 rgba(152, 236, 255, 0.12),
    inset 0 -18px 32px rgba(43, 146, 209, 0.08),
    0 10px 28px rgba(0, 0, 0, 0.24) !important;
}

.rice-bigscreen .kpi-card::before {
  background: linear-gradient(90deg, transparent, rgba(60, 218, 255, 0.68), transparent) !important;
}

.rice-bigscreen .kpi-card span {
  color: #9bcde0 !important;
  font-size: 11px !important;
}

.rice-bigscreen .kpi-card strong {
  color: #5effbd !important;
  font-size: 24px !important;
  text-shadow: 0 0 14px rgba(82, 255, 188, 0.42) !important;
}

.rice-bigscreen .kpi-card small {
  color: #dff8ff !important;
}

.rice-bigscreen .screen-body {
  grid-template-columns: 292px minmax(0, 1fr) 360px !important;
  gap: 10px !important;
}

.rice-bigscreen .screen-side {
  gap: 10px !important;
  background: transparent !important;
}

.rice-bigscreen .screen-side .panel,
.rice-bigscreen .screen-center .panel,
.rice-bigscreen .environment-dashboard-panel,
.rice-bigscreen .environment-metric-panel,
.rice-bigscreen .dashboard-map-panel {
  border: 1px solid rgba(63, 204, 255, 0.26) !important;
  border-radius: 6px !important;
  color: #dff8ff !important;
  background:
    linear-gradient(145deg, rgba(6, 27, 48, 0.94), rgba(4, 18, 32, 0.98)) !important;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.025),
    inset 0 0 34px rgba(43, 146, 209, 0.08),
    0 10px 28px rgba(0, 0, 0, 0.26) !important;
}

.rice-bigscreen .panel-title {
  min-height: 38px !important;
  border-bottom: 1px solid rgba(63, 204, 255, 0.18) !important;
  background: linear-gradient(90deg, rgba(12, 58, 91, 0.62), rgba(5, 24, 42, 0.24)) !important;
}

.rice-bigscreen .panel-title-main strong,
.rice-bigscreen .map-title .panel-title-main strong,
.rice-bigscreen .environment-dashboard-title-link .panel-title-main strong {
  color: #f1fcff !important;
  font-size: 16px !important;
  text-shadow: 0 0 8px rgba(70, 212, 255, 0.44) !important;
}

.rice-bigscreen .panel-title-icon {
  background: linear-gradient(180deg, #46d4ff, #167eba) !important;
  box-shadow: 0 0 16px rgba(70, 212, 255, 0.38) !important;
}

.rice-bigscreen .side-chart {
  min-height: 170px !important;
}

.rice-bigscreen .dashboard-map-panel .map-head,
.rice-bigscreen .environment-dashboard-header {
  border-bottom: 1px solid rgba(63, 204, 255, 0.20) !important;
  background:
    linear-gradient(180deg, rgba(8, 38, 62, 0.80), rgba(4, 18, 32, 0.40)) !important;
}

.rice-bigscreen .dashboard-map-panel .map-title p {
  color: #91c7da !important;
}

.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-select__wrapper),
.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-input__wrapper),
.rice-bigscreen .environment-global-controls :deep(.el-select__wrapper) {
  border-color: rgba(70, 212, 255, 0.28) !important;
  color: #dff8ff !important;
  background: rgba(2, 15, 27, 0.76) !important;
  box-shadow: inset 0 0 12px rgba(70, 212, 255, 0.05) !important;
}

.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-select__selected-item),
.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-select__placeholder),
.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-input__inner),
.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-select__caret),
.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-input__icon),
.rice-bigscreen .environment-global-controls :deep(.el-select__selected-item),
.rice-bigscreen .environment-global-controls :deep(.el-select__placeholder),
.rice-bigscreen .environment-global-controls :deep(.el-select__caret) {
  color: #bcecff !important;
}

.rice-bigscreen .dashboard-map-panel .map-filters :deep(.el-button),
.rice-bigscreen .environment-refresh-button {
  border-color: rgba(70, 212, 255, 0.52) !important;
  color: #ffffff !important;
  background: linear-gradient(180deg, #1597df, #075f9f) !important;
  box-shadow: 0 0 16px rgba(21, 151, 223, 0.28) !important;
}

.rice-bigscreen .dashboard-map-stage,
.rice-bigscreen .dashboard-leaflet-map {
  min-height: 456px !important;
  background: #051321 !important;
}

.rice-bigscreen .dashboard-map-stage {
  border-top: 1px solid rgba(63, 204, 255, 0.12);
}

.rice-bigscreen .dashboard-map-stage::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 500;
  pointer-events: none;
  background:
    radial-gradient(circle at 50% 50%, transparent 0 42%, rgba(1, 9, 17, 0.26) 76%),
    linear-gradient(180deg, rgba(4, 18, 32, 0.12), rgba(4, 18, 32, 0.22));
}

.rice-bigscreen .dashboard-map-legend {
  border-color: rgba(70, 212, 255, 0.28) !important;
  color: #dff8ff !important;
  background: rgba(3, 18, 31, 0.82) !important;
  box-shadow: 0 0 18px rgba(70, 212, 255, 0.12) !important;
}

.rice-bigscreen .map-legend-symbol {
  box-shadow: 0 0 8px currentColor;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-control-zoom) {
  border-color: rgba(70, 212, 255, 0.32) !important;
  box-shadow: 0 0 18px rgba(70, 212, 255, 0.13) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-control-zoom a) {
  color: #dff8ff !important;
  border-bottom-color: rgba(70, 212, 255, 0.16) !important;
  background: rgba(3, 18, 31, 0.94) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-control-zoom a:hover) {
  color: #ffffff !important;
  background: rgba(14, 99, 149, 0.95) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-control-attribution) {
  color: rgba(188, 236, 255, 0.70) !important;
  background: rgba(3, 18, 31, 0.72) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-control-attribution a) {
  color: rgba(133, 223, 255, 0.86) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.dashboard-base-marker),
.rice-bigscreen .dashboard-map-stage :deep(.dashboard-node-marker) {
  color: #effcff !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.dashboard-base-marker > span),
.rice-bigscreen .dashboard-map-stage :deep(.dashboard-node-marker > span),
.rice-bigscreen .dashboard-map-stage :deep(.dashboard-sensor-marker) {
  border-color: rgba(230, 252, 255, 0.96) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.dashboard-base-marker b),
.rice-bigscreen .dashboard-map-stage :deep(.dashboard-node-marker b),
.rice-bigscreen .dashboard-map-stage :deep(.dashboard-plot-label) {
  border-color: rgba(70, 212, 255, 0.28) !important;
  color: #e9fbff !important;
  background: rgba(3, 18, 31, 0.86) !important;
  box-shadow: 0 0 14px rgba(70, 212, 255, 0.14) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.leaflet-popup-content-wrapper),
.rice-bigscreen .dashboard-map-stage :deep(.leaflet-popup-tip) {
  border-color: rgba(70, 212, 255, 0.30) !important;
  color: #dff8ff !important;
  background: rgba(3, 18, 31, 0.96) !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.dashboard-map-popup strong) {
  color: #ffffff !important;
}

.rice-bigscreen .dashboard-map-stage :deep(.dashboard-map-popup span) {
  color: #a9d8e8 !important;
}

.rice-bigscreen .environment-dashboard-panel {
  min-height: 306px !important;
}

.rice-bigscreen .environment-global-controls {
  border-top: 1px solid rgba(63, 204, 255, 0.14) !important;
  background: rgba(3, 18, 31, 0.36) !important;
}

.rice-bigscreen .environment-control-item > span,
.rice-bigscreen .environment-control-status small,
.rice-bigscreen .environment-control-time small {
  color: #91c7da !important;
}

.rice-bigscreen .environment-control-status,
.rice-bigscreen .environment-control-time {
  border-color: rgba(70, 212, 255, 0.22) !important;
  background: rgba(2, 15, 27, 0.66) !important;
}

.rice-bigscreen .environment-control-status strong,
.rice-bigscreen .environment-control-time strong {
  color: #f0fcff !important;
}

.rice-bigscreen .environment-chart-grid {
  background: rgba(2, 13, 24, 0.36) !important;
}

.rice-bigscreen .environment-chart-cell {
  border-color: rgba(70, 212, 255, 0.18) !important;
  background:
    linear-gradient(145deg, rgba(6, 30, 50, 0.72), rgba(3, 18, 31, 0.90)) !important;
  box-shadow: inset 0 0 18px rgba(70, 212, 255, 0.045) !important;
}

.rice-bigscreen .environment-chart-title {
  border-bottom-color: rgba(70, 212, 255, 0.14) !important;
  background: rgba(3, 18, 31, 0.36) !important;
}

.rice-bigscreen .environment-chart-title strong {
  color: #f0fcff !important;
}

.rice-bigscreen .environment-chart-title small,
.rice-bigscreen .environment-chart-title > span {
  color: #9bcde0 !important;
}

.rice-bigscreen .environment-chart-title > span {
  border-color: rgba(70, 212, 255, 0.22) !important;
  background: rgba(70, 212, 255, 0.07) !important;
}

.rice-bigscreen .environment-metric-panel {
  min-height: 354px !important;
}

.rice-bigscreen .environment-metric-content {
  background: rgba(2, 13, 24, 0.18) !important;
}

.rice-bigscreen .environment-device-summary {
  border-color: rgba(70, 212, 255, 0.16) !important;
  background: rgba(3, 18, 31, 0.56) !important;
}

.rice-bigscreen .environment-device-identity strong {
  color: #f3fdff !important;
}

.rice-bigscreen .environment-device-identity small {
  color: #9bcde0 !important;
}

.rice-bigscreen .environment-device-state-icon {
  border-color: rgba(70, 212, 255, 0.24) !important;
  background: rgba(70, 212, 255, 0.08) !important;
}

.rice-bigscreen .environment-data-quality {
  border-color: rgba(95, 255, 189, 0.24) !important;
  color: #5effbd !important;
  background: rgba(51, 224, 152, 0.08) !important;
}

.rice-bigscreen .selected-environment-metric {
  border-color: rgba(70, 212, 255, 0.16) !important;
  color: #dff8ff !important;
  background:
    linear-gradient(145deg, rgba(7, 34, 55, 0.76), rgba(3, 18, 31, 0.92)) !important;
  box-shadow: inset 0 0 16px rgba(70, 212, 255, 0.04) !important;
}

.rice-bigscreen .selected-environment-metric > span {
  color: #a9d8e8 !important;
}

.rice-bigscreen .selected-environment-metric > strong {
  color: var(--metric-color) !important;
  text-shadow: 0 0 12px color-mix(in srgb, var(--metric-color) 42%, transparent) !important;
}

.rice-bigscreen .selected-environment-metric > strong small {
  color: #c7e9f5 !important;
}

.rice-bigscreen .source-list article,
.rice-bigscreen .task-list article {
  border-color: rgba(70, 212, 255, 0.12) !important;
  background: rgba(3, 18, 31, 0.54) !important;
}

.rice-bigscreen .source-list strong,
.rice-bigscreen .task-list strong,
.rice-bigscreen .disease-result dt {
  color: #f0fcff !important;
}

.rice-bigscreen .source-list small,
.rice-bigscreen .task-list small,
.rice-bigscreen .empty-data,
.rice-bigscreen .data-note {
  color: #9bcde0 !important;
}

@media (max-width: 1500px) {
  .rice-bigscreen .screen-body {
    grid-template-columns: 292px minmax(0, 1fr) 354px !important;
  }

  .rice-bigscreen .dashboard-map-stage,
  .rice-bigscreen .dashboard-leaflet-map {
    min-height: 430px !important;
  }
}

@media (max-width: 1180px) {
  .rice-bigscreen .screen-body {
    grid-template-columns: 1fr !important;
  }

  .rice-bigscreen .screen-title {
    width: min(620px, calc(100vw - 190px)) !important;
  }
}

/* 最终兜底：清除首页大屏残留浅色主题 */
:global(html),
:global(body),
:global(#app),
:global(.app-wrapper),
:global(.main-container),
:global(.app-main),
:global(.layout-container) {
  background: #030d19 !important;
}

:global(.rice-screen.rice-bigscreen),
:global(.rice-screen.rice-bigscreen.public-display) {
  color: #dff8ff !important;
  background:
    radial-gradient(circle at 50% -12%, rgba(68, 203, 255, 0.25), transparent 32%),
    radial-gradient(circle at 10% 18%, rgba(73, 255, 181, 0.13), transparent 26%),
    linear-gradient(180deg, #030d19 0%, #06192a 48%, #030d19 100%) !important;
}

:global(.rice-screen.rice-bigscreen .bigscreen-shell) {
  background:
    linear-gradient(rgba(88, 214, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(88, 214, 255, 0.035) 1px, transparent 1px),
    linear-gradient(180deg, rgba(2, 12, 22, 0.20), rgba(2, 12, 22, 0.08)) !important;
  background-size: 32px 32px, 32px 32px, auto !important;
}

:global(.rice-screen.rice-bigscreen .screen-header),
:global(.rice-screen.rice-bigscreen .kpi-card),
:global(.rice-screen.rice-bigscreen .screen-side),
:global(.rice-screen.rice-bigscreen .screen-side .panel),
:global(.rice-screen.rice-bigscreen .screen-center .panel),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel),
:global(.rice-screen.rice-bigscreen .environment-dashboard-panel),
:global(.rice-screen.rice-bigscreen .environment-metric-panel),
:global(.rice-screen.rice-bigscreen .disease-result-panel),
:global(.rice-screen.rice-bigscreen .ndvi-panel),
:global(.rice-screen.rice-bigscreen .task-panel),
:global(.rice-screen.rice-bigscreen .source-panel),
:global(.rice-screen.rice-bigscreen .side-panel) {
  border-color: rgba(69, 209, 255, 0.30) !important;
  color: #dff8ff !important;
  background:
    linear-gradient(145deg, rgba(8, 35, 59, 0.94), rgba(3, 17, 31, 0.98)) !important;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.025),
    inset 0 0 30px rgba(68, 203, 255, 0.075),
    0 12px 28px rgba(0, 0, 0, 0.28) !important;
}

:global(.rice-screen.rice-bigscreen .screen-header) {
  min-height: 54px !important;
  background:
    linear-gradient(90deg, rgba(3, 13, 25, 0.98), rgba(10, 48, 77, 0.94), rgba(3, 13, 25, 0.98)) !important;
}

:global(.rice-screen.rice-bigscreen .screen-title) {
  border-color: rgba(123, 230, 255, 0.42) !important;
  background:
    linear-gradient(90deg, transparent, rgba(44, 184, 255, 0.25), transparent),
    rgba(6, 30, 52, 0.92) !important;
  box-shadow:
    inset 0 0 18px rgba(72, 218, 255, 0.18),
    0 0 22px rgba(56, 217, 150, 0.10) !important;
}

:global(.rice-screen.rice-bigscreen .screen-title h1) {
  color: #f5fdff !important;
  text-shadow:
    0 0 10px rgba(75, 218, 255, 0.82),
    0 0 20px rgba(77, 255, 187, 0.34) !important;
}

:global(.rice-screen.rice-bigscreen .kpi-card span),
:global(.rice-screen.rice-bigscreen .panel-title-main span),
:global(.rice-screen.rice-bigscreen .map-title p),
:global(.rice-screen.rice-bigscreen .empty-data),
:global(.rice-screen.rice-bigscreen .data-note) {
  color: #9bcde0 !important;
}

:global(.rice-screen.rice-bigscreen .kpi-card strong) {
  color: #5effbd !important;
  text-shadow: 0 0 15px rgba(94, 255, 189, 0.44) !important;
}

:global(.rice-screen.rice-bigscreen .kpi-card small),
:global(.rice-screen.rice-bigscreen .panel-title-main strong),
:global(.rice-screen.rice-bigscreen .source-list strong),
:global(.rice-screen.rice-bigscreen .task-list strong),
:global(.rice-screen.rice-bigscreen .disease-result strong) {
  color: #f0fcff !important;
}

:global(.rice-screen.rice-bigscreen .panel-title),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-head),
:global(.rice-screen.rice-bigscreen .environment-dashboard-header) {
  position: relative !important;
  z-index: 1200 !important;
  border-bottom-color: rgba(69, 209, 255, 0.20) !important;
  background:
    linear-gradient(90deg, rgba(12, 61, 96, 0.70), rgba(4, 18, 32, 0.28)) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters),
:global(.rice-screen.rice-bigscreen .environment-global-controls) {
  position: relative !important;
  z-index: 1201 !important;
  pointer-events: auto !important;
  background: rgba(3, 17, 31, 0.56) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-select__wrapper),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-input__wrapper),
:global(.rice-screen.rice-bigscreen .environment-global-controls .el-select__wrapper) {
  border-color: rgba(69, 209, 255, 0.30) !important;
  color: #dff8ff !important;
  background: rgba(2, 12, 22, 0.86) !important;
  box-shadow: inset 0 0 14px rgba(69, 209, 255, 0.06) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-input__inner),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-select__selected-item),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-select__placeholder),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-select__caret),
:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-input__icon),
:global(.rice-screen.rice-bigscreen .environment-global-controls .el-select__selected-item),
:global(.rice-screen.rice-bigscreen .environment-global-controls .el-select__placeholder),
:global(.rice-screen.rice-bigscreen .environment-global-controls .el-select__caret) {
  color: #bcecff !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .el-button),
:global(.rice-screen.rice-bigscreen .environment-refresh-button),
:global(.rice-screen.rice-bigscreen .admin-entry) {
  border-color: rgba(69, 209, 255, 0.55) !important;
  color: #ffffff !important;
  background: linear-gradient(180deg, #1597df, #075f9f) !important;
  box-shadow: 0 0 18px rgba(21, 151, 223, 0.30) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage),
:global(.rice-screen.rice-bigscreen .dashboard-leaflet-map),
:global(.rice-screen.rice-bigscreen .environment-chart-grid),
:global(.rice-screen.rice-bigscreen .environment-metric-content) {
  background: #061524 !important;
}

:global(.rice-screen.rice-bigscreen .environment-chart-cell),
:global(.rice-screen.rice-bigscreen .environment-device-summary),
:global(.rice-screen.rice-bigscreen .selected-environment-metric),
:global(.rice-screen.rice-bigscreen .source-list article),
:global(.rice-screen.rice-bigscreen .task-list article) {
  border-color: rgba(69, 209, 255, 0.18) !important;
  background:
    linear-gradient(145deg, rgba(8, 35, 59, 0.78), rgba(3, 17, 31, 0.94)) !important;
}

:global(.rice-screen.rice-bigscreen .environment-chart-title),
:global(.rice-screen.rice-bigscreen .environment-control-status),
:global(.rice-screen.rice-bigscreen .environment-control-time) {
  border-color: rgba(69, 209, 255, 0.18) !important;
  background: rgba(3, 17, 31, 0.68) !important;
}

:global(.rice-screen.rice-bigscreen .environment-chart-title strong),
:global(.rice-screen.rice-bigscreen .environment-device-identity strong),
:global(.rice-screen.rice-bigscreen .environment-control-status strong),
:global(.rice-screen.rice-bigscreen .environment-control-time strong) {
  color: #f0fcff !important;
}

:global(.rice-screen.rice-bigscreen .environment-chart-title small),
:global(.rice-screen.rice-bigscreen .environment-chart-title > span),
:global(.rice-screen.rice-bigscreen .environment-device-identity small),
:global(.rice-screen.rice-bigscreen .environment-control-item > span),
:global(.rice-screen.rice-bigscreen .environment-control-status small),
:global(.rice-screen.rice-bigscreen .environment-control-time small),
:global(.rice-screen.rice-bigscreen .source-list small),
:global(.rice-screen.rice-bigscreen .source-list time) {
  color: #9bcde0 !important;
}

:global(.rice-screen.rice-bigscreen .right-side .panel),
:global(.rice-screen.rice-bigscreen .left-side .panel) {
  overflow: hidden !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-legend),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-popup-content-wrapper),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-popup-tip),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-base-marker b),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-node-marker b),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-plot-label) {
  border-color: rgba(69, 209, 255, 0.30) !important;
  color: #e9fbff !important;
  background: rgba(3, 17, 31, 0.90) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-control-zoom a),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-control-attribution) {
  color: #dff8ff !important;
  background: rgba(3, 17, 31, 0.86) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-tile-pane) {
  filter: saturate(1.15) contrast(1.06) brightness(0.78) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-control-container),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-control-zoom),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-popup-pane),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .leaflet-tooltip-pane) {
  z-index: 730 !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-map-mode-badge) {
  border-color: rgba(69, 209, 255, 0.30) !important;
  color: #c9f4ff !important;
  background: rgba(3, 17, 31, 0.78) !important;
  box-shadow: inset 0 0 14px rgba(69, 209, 255, 0.05) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-layer-switch) {
  position: static !important;
  top: auto !important;
  right: auto !important;
  z-index: auto !important;
  border-color: rgba(69, 209, 255, 0.30) !important;
  background: rgba(3, 17, 31, 0.88) !important;
  box-shadow: 0 0 18px rgba(69, 209, 255, 0.14) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-layer-switch .el-checkbox-button__inner) {
  color: #bcecff !important;
  background: transparent !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-layer-switch .el-checkbox-button.is-checked .el-checkbox-button__inner) {
  color: #ffffff !important;
  background: linear-gradient(180deg, #1597df, #075f9f) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-county-label),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-boundary-label-wrapper) {
  border: 0 !important;
  background: transparent !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-county-label) {
  padding: 5px 8px !important;
  border: 1px solid rgba(35, 209, 139, 0.42) !important;
  border-radius: 6px !important;
  color: #eafff7 !important;
  background: rgba(5, 25, 38, 0.84) !important;
  box-shadow: 0 0 18px rgba(35, 209, 139, 0.20) !important;
  font-size: 10px !important;
  font-weight: 700 !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-county-label small) {
  display: block !important;
  margin-top: 2px !important;
  color: #a8d9e8 !important;
  font-size: 8px !important;
  font-weight: 600 !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-boundary-label) {
  display: inline-flex !important;
  align-items: center !important;
  max-width: 150px !important;
  height: 22px !important;
  padding: 0 8px !important;
  overflow: hidden !important;
  border: 1px dashed rgba(88, 216, 255, 0.52) !important;
  border-radius: 999px !important;
  color: #c8f5ff !important;
  background: rgba(4, 22, 38, 0.72) !important;
  box-shadow: 0 0 14px rgba(88, 216, 255, 0.14) !important;
  font-size: 9px !important;
  font-weight: 700 !important;
  white-space: nowrap !important;
  text-overflow: ellipsis !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage .dashboard-boundary-hover-label) {
  padding: 4px 7px !important;
  border: 1px solid rgba(88, 216, 255, 0.44) !important;
  border-radius: 999px !important;
  color: #e9fbff !important;
  background: rgba(4, 22, 38, 0.86) !important;
  box-shadow: 0 0 14px rgba(88, 216, 255, 0.16) !important;
  font-size: 9px !important;
  font-weight: 700 !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters) {
  display: flex !important;
  align-items: center !important;
  flex-wrap: nowrap !important;
  gap: 8px !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-basemap-switch) {
  display: inline-flex !important;
  min-width: 0;
  padding: 3px;
  border: 1px solid rgba(69, 209, 255, 0.26);
  border-radius: 8px;
  background: rgba(2, 12, 22, 0.78);
  box-shadow: inset 0 0 14px rgba(69, 209, 255, 0.05);
}

:global(.rice-screen.rice-bigscreen .dashboard-basemap-switch .el-radio-button__inner) {
  min-width: 56px;
  height: 26px;
  padding: 0 8px;
  border: 0 !important;
  border-radius: 6px !important;
  color: #bcecff !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 10px;
  font-weight: 700;
  line-height: 26px;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-map-mode-badge) {
  flex: 0 0 132px !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-base-filter) {
  flex: 0 0 108px !important;
  min-width: 108px !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-node-filter) {
  flex: 1 1 140px !important;
  min-width: 120px !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-panel .map-filters .dashboard-refresh-button) {
  flex: 0 0 86px !important;
  min-width: 86px !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-basemap-switch .el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #ffffff !important;
  background: linear-gradient(180deg, rgba(28, 169, 239, 0.92), rgba(8, 96, 160, 0.96)) !important;
  box-shadow: 0 0 14px rgba(69, 209, 255, 0.24) !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage.basemap-terrain .leaflet-tile-pane),
:global(.rice-screen.rice-bigscreen .dashboard-map-stage.basemap-vector .leaflet-tile-pane) {
  filter: saturate(1.06) contrast(1.02) brightness(0.96) !important;
  opacity: 0.98 !important;
}

:global(.rice-screen.rice-bigscreen .dashboard-map-stage.basemap-satellite .leaflet-tile-pane) {
  filter: saturate(1.08) contrast(1.04) brightness(0.88) !important;
  opacity: 0.98 !important;
}

.rice-bigscreen .source-panel.dashboard-disease-panel {
  min-height: 0;
  overflow: hidden;
}

.rice-bigscreen .source-panel.dashboard-disease-panel .latest-file-list,
.rice-bigscreen .source-panel.dashboard-disease-panel > .empty-data {
  display: none !important;
}

.rice-bigscreen .dashboard-disease-panel .disease-dashboard-content {
  display: flex;
  min-height: 0;
  height: calc(100% - 38px);
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px 10px;
  overflow: hidden;
}

.rice-bigscreen .disease-stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 5px;
}

.rice-bigscreen .disease-stat-card {
  min-width: 0;
  padding: 6px 4px 5px;
  border: 1px solid rgba(69, 209, 255, 0.20);
  border-radius: 6px;
  background: rgba(5, 31, 51, 0.72);
  text-align: center;
}

.rice-bigscreen .disease-stat-card span,
.rice-bigscreen .disease-stat-card small {
  display: block;
  overflow: hidden;
  color: #9bc8d8;
  font-size: 9px;
  line-height: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rice-bigscreen .disease-stat-card strong {
  display: inline-block;
  margin: 1px 2px 0;
  color: #e7fbff;
  font-size: 16px;
  line-height: 19px;
}

.rice-bigscreen .disease-stat-card small {
  display: inline-block;
  color: #79b8cb;
}

.rice-bigscreen .disease-stat-card.red strong {
  color: #ff7e82;
}

.rice-bigscreen .disease-stat-card.orange strong {
  color: #ffc65d;
}

.rice-bigscreen .disease-stat-card.green strong {
  color: #72e5a7;
}

.rice-bigscreen .disease-risk-section {
  min-height: 0;
  padding: 7px 8px 6px;
  border-top: 1px solid rgba(69, 209, 255, 0.17);
  border-bottom: 1px solid rgba(69, 209, 255, 0.17);
}

.rice-bigscreen .disease-section-heading,
.rice-bigscreen .disease-risk-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 42px 16px;
  align-items: center;
  gap: 5px;
}

.rice-bigscreen .disease-section-heading {
  margin-bottom: 5px;
  color: #d9f8ff;
  font-size: 10px;
  font-weight: 700;
}

.rice-bigscreen .disease-section-heading small {
  grid-column: 3 / 5;
  color: #78b5c8;
  font-size: 9px;
  font-weight: 400;
  text-align: right;
}

.rice-bigscreen .disease-risk-row {
  min-height: 18px;
  color: #a7d4df;
  font-size: 9px;
}

.rice-bigscreen .disease-risk-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(90, 145, 166, 0.20);
}

.rice-bigscreen .disease-risk-track i {
  display: block;
  height: 100%;
  min-width: 0;
  border-radius: inherit;
  transition: width 0.25s ease;
}

.rice-bigscreen .disease-risk-row em,
.rice-bigscreen .disease-risk-row strong {
  color: #9dcbd8;
  font-size: 9px;
  font-style: normal;
  text-align: right;
}

.rice-bigscreen .disease-risk-row strong {
  color: #e3f9ff;
}

.rice-bigscreen .disease-summary-line {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  overflow: hidden;
  color: #9fcbd7;
  font-size: 9px;
  line-height: 18px;
  white-space: nowrap;
}

.rice-bigscreen .disease-summary-line span {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rice-bigscreen .disease-summary-line strong {
  color: #69e3a4;
}

.rice-bigscreen .disease-summary-line strong.warning {
  color: #ffc65d;
}

.rice-bigscreen .right-side.has-task-panel {
  grid-template-rows: 330px minmax(0, 1fr) minmax(0, 1fr) !important;
}

.rice-bigscreen .right-side .task-panel {
  min-height: 0;
  overflow: hidden;
}

.rice-bigscreen .right-side .task-panel .task-list {
  max-height: calc(100% - 38px);
  overflow: auto;
}

.rice-bigscreen .right-side .ndvi-panel {
  display: grid !important;
  grid-template-rows: 38px minmax(0, 1fr) !important;
  min-height: 0 !important;
  overflow: hidden;
}

.rice-bigscreen .right-side .ndvi-panel .trend-chart.small {
  height: 100% !important;
  min-height: 0 !important;
  margin: 0 8px 8px !important;
}

</style>
