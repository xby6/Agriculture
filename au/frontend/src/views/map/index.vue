<template>
  <div class="agri-map-page">
    <header class="page-header">
      <div>
        <span class="eyebrow">FIELD SPATIAL MONITORING</span>
        <h1>水稻基地与地块空间监测</h1>
        <p>展示基地位置、示例地块边界、传感器布点、病害风险与无人机采样任务。</p>
      </div>
      <div class="header-tools">
        <el-select v-model="selectedBaseId" class="base-select" @change="focusSelectedBase">
          <el-option v-for="base in bases" :key="base.id" :label="base.name" :value="base.id" />
        </el-select>
        <el-button type="success" plain @click="showAllBases">
          <el-icon><Location /></el-icon>
          查看全部基地
        </el-button>
      </div>
    </header>

    <section class="map-layout">
      <article class="map-panel">
        <div class="map-toolbar">
          <div class="map-toolbar-head">
            <div class="legend-group">
              <span><i class="legend-dot county"></i>典型区县</span>
              <span><i class="legend-dot boundary"></i>行政边界</span>
              <span><i class="legend-dot healthy"></i>健康</span>
              <span><i class="legend-dot low"></i>轻度</span>
              <span><i class="legend-dot medium"></i>中度</span>
              <span><i class="legend-dot high"></i>重度</span>
              <span><i class="legend-dot sensor"></i>监测设备</span>
            </div>
            <span class="data-note">地块范围为界面示例，接入 GeoJSON/PostGIS 后替换为真实边界</span>
          </div>

          <div class="spatial-map-filters">
            <span class="map-mode-badge">示例基地模式</span>

            <el-radio-group
              v-model="mapBaseLayer"
              size="small"
              class="map-basemap-switch"
            >
              <el-radio-button
                v-for="item in baseMapOptions"
                :key="item.value"
                :label="item.value"
              >
                {{ item.label }}
              </el-radio-button>
            </el-radio-group>

            <el-checkbox-group
              v-model="mapVisibleLayers"
              size="small"
              class="map-layer-switch"
            >
              <el-checkbox-button
                v-for="item in mapLayerOptions"
                :key="item.value"
                :label="item.value"
              >
                {{ item.label }}
              </el-checkbox-button>
            </el-checkbox-group>

            <el-select
              v-model="selectedBaseId"
              class="map-base-filter"
              size="small"
              @change="focusSelectedBase"
            >
              <el-option v-for="base in bases" :key="base.id" :label="base.name" :value="base.id" />
            </el-select>

            <el-input
              v-model="mapKeyword"
              class="map-node-filter"
              size="small"
              placeholder="搜索基地、地块或节点"
              clearable
            >
              <template #suffix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>

            <el-button
              class="map-refresh-button"
              size="small"
              type="primary"
              plain
              @click="refreshMap"
            >
              刷新地图
            </el-button>
          </div>
        </div>
        <div class="leaflet-map-stage" :class="`basemap-${mapBaseLayer}`">
          <div ref="mapContainer" class="leaflet-map"></div>
        </div>
      </article>

      <aside class="side-panel">
        <article class="info-card selected-base-card">
          <div class="card-title">
            <div>
              <span class="eyebrow">SELECTED BASE</span>
              <h2>{{ selectedBase.name }}</h2>
            </div>
            <span class="status-tag">运行正常</span>
          </div>
          <div class="base-location">
            <el-icon><LocationFilled /></el-icon>
            <span>{{ selectedBase.location }}</span>
          </div>
          <div class="base-metrics">
            <div><span>地块</span><strong>{{ selectedBase.plots.length }}<small>块</small></strong></div>
            <div><span>面积</span><strong>{{ selectedBase.area }}<small>亩</small></strong></div>
            <div><span>设备</span><strong>{{ selectedBase.online }}/{{ selectedBase.devices }}</strong></div>
            <div><span>平均 DI</span><strong>{{ averageDi }}</strong></div>
          </div>
        </article>

        <article class="info-card plot-list-card">
          <div class="card-title compact">
            <div>
              <span class="eyebrow">PLOT RISK LIST</span>
              <h2>地块病害风险</h2>
            </div>
          </div>
          <div class="plot-list">
            <button
              v-for="plot in selectedBase.plots"
              :key="plot.id"
              type="button"
              class="plot-row"
              :class="{ active: selectedPlotId === plot.id }"
              @click="selectPlot(plot.id)"
            >
              <span class="risk-bar" :class="plot.risk"></span>
              <div>
                <strong>{{ plot.code }}</strong>
                <small>{{ plot.disease }}</small>
              </div>
              <div class="plot-di">
                <span>DI</span>
                <strong>{{ plot.di.toFixed(1) }}</strong>
              </div>
              <span class="risk-tag" :class="plot.risk">{{ riskLabel[plot.risk] }}</span>
            </button>
          </div>
        </article>

        <article class="info-card plot-detail-card">
          <div class="card-title compact">
            <div>
              <span class="eyebrow">PLOT DETAIL</span>
              <h2>{{ selectedPlot.code }} 地块详情</h2>
            </div>
            <span class="risk-tag" :class="selectedPlot.risk">{{ riskLabel[selectedPlot.risk] }}</span>
          </div>
          <div class="detail-grid">
            <div><span>当前 DI</span><strong>{{ selectedPlot.di.toFixed(1) }}</strong></div>
            <div><span>预测 DI（7 d）</span><strong>{{ selectedPlot.predictedDi.toFixed(1) }}</strong></div>
            <div><span>空气温度</span><strong>{{ selectedPlot.temperature }}℃</strong></div>
            <div><span>空气湿度</span><strong>{{ selectedPlot.humidity }}%</strong></div>
            <div><span>NDVI</span><strong>{{ selectedPlot.ndvi.toFixed(2) }}</strong></div>
            <div><span>最近调查</span><strong>{{ selectedPlot.survey }}</strong></div>
          </div>
          <div class="advice-box">
            <el-icon><WarningFilled /></el-icon>
            <p><strong>处理建议：</strong>{{ selectedPlot.advice }}</p>
          </div>
        </article>
      </aside>
    </section>

    <section class="bottom-grid">
      <article class="info-card chart-card">
        <div class="card-title compact">
          <div>
            <span class="eyebrow">RISK DISTRIBUTION</span>
            <h2>风险等级分布</h2>
          </div>
        </div>
        <div ref="riskChart" class="chart"></div>
      </article>
      <article class="info-card chart-card wide">
        <div class="card-title compact">
          <div>
            <span class="eyebrow">ENVIRONMENT HISTORY</span>
            <h2>选中地块环境变化</h2>
          </div>
          <span class="status-tag">近 24 小时</span>
        </div>
        <div ref="environmentChart" class="chart"></div>
      </article>
      <article class="info-card task-card">
        <div class="card-title compact">
          <div>
            <span class="eyebrow">UAV TASK</span>
            <h2>无人机采样任务</h2>
          </div>
        </div>
        <div class="task-content">
          <div class="task-progress">
            <span>本次任务完成度</span>
            <strong>72%</strong>
          </div>
          <div class="progress-track"><div class="progress-fill"></div></div>
          <div class="task-meta">
            <span>计划航线：6 条</span>
            <span>已采样：4 条</span>
            <span>影像：186 张</span>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup name="AgricultureMap">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { Location, LocationFilled, Search, WarningFilled } from '@element-plus/icons-vue'

const mapContainer = ref(null)
const riskChart = ref(null)
const environmentChart = ref(null)
const selectedBaseId = ref('qingyuan')
const selectedPlotId = ref('Q03')
const mapBaseLayer = ref('terrain')
const mapVisibleLayers = ref(['typicalCounty', 'adminBoundary'])
const mapKeyword = ref('')
const riskLabel = { healthy: '健康', low: '轻度', medium: '中度', high: '重度' }
let map = null
let mapLayers = []
let mapTileLayer = null
let mapTileLabelLayer = null
let administrativeBoundaryPromise = null
let administrativeBoundaryCollection = null
let administrativeBoundaryRenderToken = 0
let charts = []

const tiandituToken = import.meta.env.VITE_TIANDITU_TOKEN || import.meta.env.VITE_TDT_TOKEN || ''
const tiandituSubdomains = ['0', '1', '2', '3', '4', '5', '6', '7']

function createTiandituUrl(layer) {
  return `https://t{s}.tianditu.gov.cn/${layer}_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=${layer}&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=${tiandituToken}`
}

const baseMapOptions = [
  { label: '地形图', value: 'terrain' },
  { label: '矢量地图', value: 'vector' },
  { label: '卫星地图', value: 'satellite' }
]

const baseMapConfigs = {
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
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        options: {
          attribution: '&copy; OpenStreetMap contributors'
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

const mapLayerOptions = [
  { label: '典型区县', value: 'typicalCounty' },
  { label: '行政边界', value: 'adminBoundary' }
]

const typicalCountyAreas = [
  {
    id: 'qingyuan-county',
    name: '清原典型区',
    location: '辽宁省抚顺市清原满族自治县',
    center: [42.10872154, 124.96911137],
    color: '#23d18b',
    radius: [0.22, 0.30],
    baseId: 'qingyuan'
  },
  {
    id: 'donggang-county',
    name: '丹东东港典型区',
    location: '辽宁省丹东市东港市',
    center: [39.92638130, 124.13124693],
    color: '#35a7ff',
    radius: [0.24, 0.32],
    baseId: 'donggang'
  },
  {
    id: 'dandong-academy-county',
    name: '丹东农科院典型区',
    location: '辽宁省丹东市农科院试验区',
    center: [40.47411023, 124.11777270],
    color: '#ffb84d',
    radius: [0.20, 0.28],
    baseId: 'dandong_academy'
  },
  {
    id: 'haicheng-county',
    name: '海城典型区',
    location: '辽宁省鞍山市海城市',
    center: [40.97812011, 122.72505471],
    color: '#ff6b6b',
    radius: [0.22, 0.30],
    baseId: 'haicheng'
  }
]
const administrativeBoundarySources = [
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
  }
]

const bases = ref([
  {
    id: 'qingyuan',
    name: '清原实验基地',
    location: '辽宁省抚顺市清原满族自治县',
    coordinate: [42.10872154, 124.96911137],
    area: 18.6,
    devices: 12,
    online: 11,
    plots: [
      { id: 'Q01', code: 'Q01', risk: 'healthy', di: 4.8, predictedDi: 6.2, disease: '未检出', temperature: 26.4, humidity: 86.1, ndvi: 0.84, survey: '08-07', advice: '维持常规巡田与环境监测。', offset: [-0.0020, -0.0024] },
      { id: 'Q02', code: 'Q02', risk: 'low', di: 9.5, predictedDi: 11.8, disease: '叶瘟疑似', temperature: 26.8, humidity: 88.3, ndvi: 0.81, survey: '08-07', advice: '加强复查，关注连续高湿时段。', offset: [-0.0010, 0.0002] },
      { id: 'Q03', code: 'Q03', risk: 'medium', di: 17.9, predictedDi: 24.6, disease: '稻瘟病', temperature: 27.1, humidity: 90.2, ndvi: 0.78, survey: '08-07', advice: '24小时内重点复查，控制田间湿度。', offset: [-0.0018, 0.0028] },
      { id: 'Q04', code: 'Q04', risk: 'healthy', di: 5.2, predictedDi: 6.9, disease: '未检出', temperature: 26.5, humidity: 84.9, ndvi: 0.86, survey: '08-07', advice: '保持常规管理。', offset: [0.0012, -0.0022] }
    ]
  },
  {
    id: 'donggang',
    name: '丹东东港实验基地',
    location: '辽宁省丹东市东港市',
    coordinate: [39.92638130, 124.13124693],
    area: 9.6,
    devices: 18,
    online: 16,
    plots: [
      { id: 'DG01', code: 'DG01', risk: 'low', di: 8.6, predictedDi: 10.2, disease: '叶瘟疑似', temperature: 25.0, humidity: 92.0, ndvi: 0.82, survey: '08-07', advice: '持续观察并关注降雨后病情变化。', offset: [-0.0018, -0.0022] },
      { id: 'DG02', code: 'DG02', risk: 'medium', di: 19.2, predictedDi: 27.3, disease: '稻瘟病', temperature: 25.1, humidity: 94.2, ndvi: 0.76, survey: '08-07', advice: '加密巡查，重点关注高湿区域。', offset: [-0.0010, 0.0004] },
      { id: 'DG03', code: 'DG03', risk: 'low', di: 10.1, predictedDi: 13.8, disease: '叶瘟疑似', temperature: 24.9, humidity: 91.4, ndvi: 0.80, survey: '08-07', advice: '改善田间通风。', offset: [-0.0016, 0.0028] },
      { id: 'DG04', code: 'DG04', risk: 'healthy', di: 3.9, predictedDi: 5.0, disease: '未检出', temperature: 25.3, humidity: 87.1, ndvi: 0.85, survey: '08-07', advice: '保持常规管理。', offset: [0.0012, -0.0020] }
    ]
  },
  {
    id: 'dandong_academy',
    name: '丹东农科院实验基地',
    location: '辽宁省丹东市农科院',
    coordinate: [40.47411023, 124.11777270],
    area: 12.8,
    devices: 16,
    online: 15,
    plots: [
      { id: 'DK01', code: 'DK01', risk: 'healthy', di: 3.6, predictedDi: 4.4, disease: '未检出', temperature: 26.7, humidity: 83.4, ndvi: 0.87, survey: '08-07', advice: '保持常规管理。', offset: [-0.0018, -0.0022] },
      { id: 'DK02', code: 'DK02', risk: 'healthy', di: 4.4, predictedDi: 5.6, disease: '未检出', temperature: 26.9, humidity: 84.1, ndvi: 0.86, survey: '08-07', advice: '保持常规管理。', offset: [-0.0010, 0.0004] },
      { id: 'DK03', code: 'DK03', risk: 'low', di: 8.3, predictedDi: 10.1, disease: '叶瘟疑似', temperature: 27.2, humidity: 86.8, ndvi: 0.82, survey: '08-07', advice: '持续观察。', offset: [-0.0016, 0.0028] },
      { id: 'DK04', code: 'DK04', risk: 'medium', di: 15.8, predictedDi: 19.6, disease: '稻瘟病', temperature: 27.4, humidity: 88.6, ndvi: 0.79, survey: '08-07', advice: '控制高湿并复查。', offset: [0.0012, -0.0020] }
    ]
  },
  {
    id: 'haicheng',
    name: '海城实验基地',
    location: '辽宁省鞍山市海城市',
    coordinate: [40.97812011, 122.72505471],
    area: 15.2,
    devices: 20,
    online: 18,
    plots: [
      { id: 'HC01', code: 'HC01', risk: 'healthy', di: 4.2, predictedDi: 5.8, disease: '未检出', temperature: 27.1, humidity: 88.4, ndvi: 0.84, survey: '08-07', advice: '维持常规巡田与环境监测。', offset: [-0.0020, -0.0024] },
      { id: 'HC02', code: 'HC02', risk: 'low', di: 9.8, predictedDi: 12.3, disease: '叶瘟疑似', temperature: 27.3, humidity: 90.1, ndvi: 0.81, survey: '08-07', advice: '加强复查，关注连续高湿时段。', offset: [-0.0010, 0.0002] },
      { id: 'HC03', code: 'HC03', risk: 'medium', di: 18.6, predictedDi: 25.4, disease: '稻瘟病', temperature: 27.4, humidity: 91.6, ndvi: 0.78, survey: '08-07', advice: '24小时内重点复查并评估防控措施。', offset: [-0.0018, 0.0028] },
      { id: 'HC04', code: 'HC04', risk: 'high', di: 31.8, predictedDi: 38.9, disease: '稻瘟病', temperature: 27.6, humidity: 94.0, ndvi: 0.72, survey: '08-07', advice: '优先现场核查，加密病情调查和环境监测。', offset: [0.0014, 0.0030] }
    ]
  }
])
const selectedBase = computed(() => bases.value.find(item => item.id === selectedBaseId.value) || bases.value[0])
const selectedPlot = computed(() => selectedBase.value.plots.find(item => item.id === selectedPlotId.value) || selectedBase.value.plots[0])
const averageDi = computed(() => (selectedBase.value.plots.reduce((sum, item) => sum + item.di, 0) / selectedBase.value.plots.length).toFixed(1))
const filteredBases = computed(() => {
  const keyword = mapKeyword.value.trim().toLowerCase()
  if (!keyword) return bases.value

  return bases.value.filter(base => {
    const baseText = [base.name, base.location, base.id].join(' ').toLowerCase()
    const plotText = base.plots
      .map(plot => [plot.code, plot.disease, plot.risk].join(' '))
      .join(' ')
      .toLowerCase()

    return `${baseText} ${plotText}`.includes(keyword)
  })
})

const riskColors = {
  healthy: '#49b978',
  low: '#9acb61',
  medium: '#e4bd55',
  high: '#dc6b6b'
}

function clearMapLayers() {
  mapLayers.forEach(layer => {
    if (map?.hasLayer(layer)) {
      map.removeLayer(layer)
    } else {
      layer.remove?.()
    }
  })
  mapLayers = []
}

function createTileLayer(config, zIndex = 1) {
  return L.tileLayer(config.url, {
    minZoom: 3,
    maxZoom: 18,
    zIndex,
    ...config.options
  })
}

function applyBaseMapLayer() {
  if (!map) return

  const config = baseMapConfigs[mapBaseLayer.value] || baseMapConfigs.terrain

  if (mapTileLayer && map.hasLayer(mapTileLayer)) {
    map.removeLayer(mapTileLayer)
  }

  if (mapTileLabelLayer && map.hasLayer(mapTileLabelLayer)) {
    map.removeLayer(mapTileLabelLayer)
  }

  mapTileLayer = createTileLayer(config, 1).addTo(map)
  mapTileLayer.bringToBack()

  if (config.labelUrl) {
    mapTileLabelLayer = createTileLayer(
      {
        url: config.labelUrl,
        options: config.options
      },
      2
    ).addTo(map)
  } else {
    mapTileLabelLayer = null
  }
}

function ensureMapPanes() {
  if (!map) return

  const panes = [
    ['agri-boundary-pane', 430],
    ['agri-county-pane', 440],
    ['agri-plot-pane', 450],
    ['agri-sensor-pane', 610],
    ['agri-base-pane', 620],
    ['agri-label-pane', 700],
    ['agri-popup-pane', 720]
  ]

  panes.forEach(([name, zIndex]) => {
    const pane = map.getPane(name) || map.createPane(name)
    pane.style.zIndex = String(zIndex)
  })
}

function isMapLayerVisible(layer) {
  return mapVisibleLayers.value.includes(layer)
}

function escapeMapHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function createAreaBounds(center, radius) {
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

function renderAdministrativeBoundaries() {
  if (!isMapLayerVisible('adminBoundary')) return

  const renderToken = ++administrativeBoundaryRenderToken

  loadAdministrativeBoundaries()
    .then(collection => {
      if (
        !map ||
        renderToken !== administrativeBoundaryRenderToken ||
        !isMapLayerVisible('adminBoundary')
      ) {
        return
      }

      const layer = L.geoJSON(collection, {
        pane: 'agri-boundary-pane',
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
              `${escapeMapHtml(name)}${sourceName ? ` · ${escapeMapHtml(sourceName)}` : ''}`,
              {
                sticky: true,
                className: 'boundary-hover-label',
                pane: 'agri-label-pane'
              }
            )
          }
        }
      }).addTo(map)

      mapLayers.push(layer)
    })
    .catch(() => {
      renderFallbackAdministrativeBoundaries(renderToken)
    })
}

async function loadAdministrativeBoundaries() {
  if (administrativeBoundaryCollection) {
    return administrativeBoundaryCollection
  }

  if (administrativeBoundaryPromise) {
    return administrativeBoundaryPromise
  }

  administrativeBoundaryPromise = Promise.allSettled(
    administrativeBoundarySources.map(async source => {
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

      administrativeBoundaryCollection = {
        type: 'FeatureCollection',
        features
      }

      return administrativeBoundaryCollection
    })
    .finally(() => {
      administrativeBoundaryPromise = null
    })

  return administrativeBoundaryPromise
}

function renderFallbackAdministrativeBoundaries(renderToken) {
  if (
    !map ||
    renderToken !== administrativeBoundaryRenderToken ||
    !isMapLayerVisible('adminBoundary')
  ) {
    return
  }

  const fallbackBoundaries = [
    { name: '辽宁省界', level: 'province', coordinates: [[43.0, 121.0], [42.6, 125.2], [40.2, 125.0], [38.9, 123.1], [40.1, 120.4], [42.1, 119.8], [43.0, 121.0]] },
    { name: '吉林省界', level: 'province', coordinates: [[46.3, 121.5], [46.0, 130.6], [42.6, 131.0], [41.8, 125.0], [43.9, 121.5], [46.3, 121.5]] },
    { name: '黑龙江省界', level: 'province', coordinates: [[53.4, 121.0], [53.2, 135.1], [47.0, 134.4], [44.1, 129.0], [45.2, 121.0], [53.4, 121.0]] },
    { name: '沈阳市界', level: 'city', coordinates: createAreaBounds([41.80, 123.43], [0.42, 0.55]) },
    { name: '鞍山市界', level: 'city', coordinates: createAreaBounds([41.10, 122.98], [0.32, 0.45]) },
    { name: '铁岭市界', level: 'city', coordinates: createAreaBounds([42.29, 123.84], [0.36, 0.50]) },
    { name: '丹东市界', level: 'city', coordinates: createAreaBounds([40.12, 124.39], [0.34, 0.48]) }
  ]

  const layers = fallbackBoundaries.map(boundary => L.polyline(
    boundary.coordinates,
    {
      color: boundary.level === 'province' ? '#58d8ff' : '#ffce64',
      weight: boundary.level === 'province' ? 1.8 : 1,
      opacity: boundary.level === 'province' ? 0.78 : 0.48,
      dashArray: boundary.level === 'province' ? '10 7' : '5 6',
      interactive: true,
      pane: 'agri-boundary-pane'
    }
  ).bindTooltip(boundary.name, {
    sticky: true,
    className: 'boundary-hover-label',
    pane: 'agri-label-pane'
  }))

  const group = L.layerGroup(layers).addTo(map)
  mapLayers.push(group)
}

function renderTypicalCounties() {
  if (!isMapLayerVisible('typicalCounty')) return

  typicalCountyAreas.forEach(area => {
    const polygon = L.polygon(
      createAreaBounds(area.center, area.radius),
      {
        color: area.color,
        weight: 2,
        opacity: 0.90,
        fillColor: area.color,
        fillOpacity: 0.18,
        pane: 'agri-county-pane'
      }
    ).addTo(map)

    polygon.bindTooltip(
      `<strong>${escapeMapHtml(area.name)}</strong><small>${escapeMapHtml(area.location)}</small>`,
      {
        permanent: true,
        direction: 'center',
        className: 'county-label',
        pane: 'agri-label-pane'
      }
    )

    polygon.on('click', () => {
      const base = bases.value.find(item => item.id === area.baseId)
      if (!base) return
      selectedBaseId.value = base.id
      selectedPlotId.value = base.plots[0]?.id || ''
      renderSelectedBase({ preserveView: true })
    })

    mapLayers.push(polygon)
  })
}

function createPlotBounds(base, plot) {
  const [lat, lng] = base.coordinate
  const [dLat, dLng] = plot.offset
  const centerLat = lat + dLat
  const centerLng = lng + dLng
  const h = 0.00075
  const w = 0.00105
  return [
    [centerLat - h, centerLng - w],
    [centerLat - h * 0.85, centerLng + w],
    [centerLat + h, centerLng + w * 0.9],
    [centerLat + h * 0.9, centerLng - w]
  ]
}

function createBaseMarker(base) {
  const icon = L.divIcon({
    className: 'agri-base-icon-wrapper',
    html: `<div class="agri-base-icon"><span></span><b>${escapeMapHtml(base.name.replace('水稻试验基地', '').replace('水稻示范基地', '').replace('实验基地', ''))}</b></div>`,
    iconSize: [120, 36],
    iconAnchor: [18, 18]
  })
  const marker = L.marker(base.coordinate, { icon, pane: 'agri-base-pane' }).addTo(map)
  marker.bindPopup(`<strong>${escapeMapHtml(base.name)}</strong><br/>${escapeMapHtml(base.location)}<br/>地块：${base.plots.length} 块<br/>设备在线：${base.online}/${base.devices}`, { pane: 'agri-popup-pane' })
  marker.on('click', () => {
    selectedBaseId.value = base.id
    selectedPlotId.value = base.plots[0].id
    renderSelectedBase()
  })
  mapLayers.push(marker)
  return marker
}

function renderSelectedBase(options = {}) {
  if (!map) return
  clearMapLayers()
  renderAdministrativeBoundaries()
  renderTypicalCounties()

  const base = selectedBase.value
  const markerBases = filteredBases.value.length ? filteredBases.value : bases.value
  const baseMarkers = markerBases.map(createBaseMarker).filter(Boolean)

  base.plots.forEach(plot => {
    const polygon = L.polygon(createPlotBounds(base, plot), {
      color: riskColors[plot.risk],
      weight: selectedPlotId.value === plot.id ? 4 : 2,
      fillColor: riskColors[plot.risk],
      fillOpacity: selectedPlotId.value === plot.id ? 0.56 : 0.36,
      pane: 'agri-plot-pane'
    }).addTo(map)
    polygon.bindTooltip(`${escapeMapHtml(plot.code)} · ${escapeMapHtml(riskLabel[plot.risk])} · DI ${plot.di.toFixed(1)}`, { permanent: true, direction: 'center', className: 'plot-label', pane: 'agri-label-pane' })
    polygon.on('click', () => selectPlot(plot.id))
    mapLayers.push(polygon)
  })

  const sensorOffsets = [[-0.0007, -0.0013], [0.0004, 0.0015], [0.0016, -0.0006]]
  sensorOffsets.forEach((offset, index) => {
    const icon = L.divIcon({
      className: 'sensor-icon-wrapper',
      html: `<div class="sensor-icon"><span></span></div>`,
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    })
    const marker = L.marker([base.coordinate[0] + offset[0], base.coordinate[1] + offset[1]], { icon, pane: 'agri-sensor-pane' }).addTo(map)
    marker.bindTooltip(`监测设备 S0${index + 1}`, { pane: 'agri-label-pane' })
    mapLayers.push(marker)
  })

  if (options.forceFit && baseMarkers.length) {
    const group = L.featureGroup(baseMarkers)
    map.fitBounds(group.getBounds().pad(0.22), {
      maxZoom: 8,
      animate: true
    })
  } else if (!options.preserveView) {
    map.setView(base.coordinate, 16, { animate: true })
  }

  window.setTimeout(() => {
    map?.invalidateSize({ pan: false })
  }, 80)
  nextTick(initCharts)
}

function selectPlot(plotId) {
  selectedPlotId.value = plotId
  renderSelectedBase()
}

function focusSelectedBase() {
  selectedPlotId.value = selectedBase.value.plots[0].id
  renderSelectedBase()
}

function showAllBases() {
  renderSelectedBase({ forceFit: true })
}

function refreshMap() {
  renderSelectedBase({ forceFit: true })
}

function initMap() {
  map = L.map(mapContainer.value, {
    zoomControl: true,
    attributionControl: true
  }).setView([41.2, 123.2], 7)

  ensureMapPanes()
  applyBaseMapLayer()

  renderSelectedBase({ forceFit: true })
}

function disposeCharts() {
  charts.forEach(chart => chart?.dispose())
  charts = []
}

function initRiskChart() {
  if (!riskChart.value) return
  const counts = selectedBase.value.plots.reduce((acc, plot) => {
    acc[plot.risk] = (acc[plot.risk] || 0) + 1
    return acc
  }, {})
  const chart = echarts.init(riskChart.value)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}：{c} 块（{d}%）' },
    legend: { bottom: 4, textStyle: { color: '#718177', fontSize: 10 }, itemWidth: 10, itemHeight: 10 },
    series: [{
      type: 'pie',
      radius: ['42%', '67%'],
      center: ['50%', '44%'],
      label: { show: false },
      itemStyle: { borderColor: '#ffffff', borderWidth: 3, borderRadius: 6 },
      data: [
        { name: '健康', value: counts.healthy || 0, itemStyle: { color: riskColors.healthy } },
        { name: '轻度', value: counts.low || 0, itemStyle: { color: riskColors.low } },
        { name: '中度', value: counts.medium || 0, itemStyle: { color: riskColors.medium } },
        { name: '重度', value: counts.high || 0, itemStyle: { color: riskColors.high } }
      ]
    }]
  })
  charts.push(chart)
}

function initEnvironmentChart() {
  if (!environmentChart.value) return
  const chart = echarts.init(environmentChart.value)
  chart.setOption({
    grid: { left: 45, right: 45, top: 24, bottom: 32 },
    tooltip: { trigger: 'axis' },
    legend: { top: 0, right: 0, textStyle: { color: '#718177' } },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00', '24:00'],
      axisLabel: { color: '#718177', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(74,128,82,.18)' } }
    },
    yAxis: [
      { type: 'value', min: 20, max: 34, axisLabel: { color: '#718177', formatter: '{value}℃' }, splitLine: { lineStyle: { color: 'rgba(74,128,82,.12)' } } },
      { type: 'value', min: 60, max: 100, axisLabel: { color: '#718177', formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      { name: '温度', type: 'line', smooth: true, symbol: 'none', data: [23.4, 22.8, 22.3, 25.1, 28.6, 30.2, 28.8, 26.1, 24.7], lineStyle: { width: 3, color: '#ec9b61' }, areaStyle: { color: 'rgba(236,155,97,.10)' } },
      { name: '湿度', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'none', data: [93, 95, 96, 91, 82, 76, 84, 90, 92], lineStyle: { width: 3, color: '#63abe5' }, areaStyle: { color: 'rgba(99,171,229,.08)' } }
    ]
  })
  charts.push(chart)
}

function initCharts() {
  disposeCharts()
  initRiskChart()
  initEnvironmentChart()
}

function resizeAll() {
  map?.invalidateSize()
  charts.forEach(chart => chart?.resize())
}

watch(mapBaseLayer, () => {
  applyBaseMapLayer()
})

watch(
  mapVisibleLayers,
  () => {
    renderSelectedBase({ preserveView: true })
  },
  { deep: true }
)

watch(mapKeyword, () => {
  renderSelectedBase({ preserveView: true })
})

onMounted(() => {
  nextTick(() => {
    initMap()
    initCharts()
  })
  window.addEventListener('resize', resizeAll)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeAll)
  disposeCharts()
  administrativeBoundaryRenderToken += 1
  map?.remove()
  map = null
  mapTileLayer = null
  mapTileLabelLayer = null
})
</script>

<style scoped lang="scss">
.agri-map-page {
  min-height: calc(100vh - 84px);
  padding: 18px;
  color: #effff4;
  background:
    linear-gradient(180deg, rgba(5, 38, 23, 0.96), rgba(4, 31, 19, 0.98)),
    #061a11;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 14px;

  h1 {
    margin: 3px 0 5px;
    font-size: 25px;
  }

  p {
    margin: 0;
    color: #88a894;
    font-size: 12px;
  }
}

.eyebrow {
  color: #72c891;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
}

.header-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.base-select {
  width: 210px;

  :deep(.el-select__wrapper) {
    min-height: 40px;
    background: rgba(16, 42, 29, 0.94);
    box-shadow: 0 0 0 1px rgba(128, 189, 151, 0.2) inset;
  }
}

.map-layout {
  display: grid;
  grid-template-columns: minmax(620px, 1.9fr) minmax(300px, .85fr);
  gap: 12px;
}

.map-panel,
.info-card {
  overflow: hidden;
  border: 1px solid rgba(128, 189, 151, 0.18);
  border-radius: 14px;
  background: linear-gradient(145deg, rgba(15, 38, 26, 0.96), rgba(10, 27, 18, 0.98));
}

.map-toolbar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(128, 189, 151, 0.12);
}

.map-toolbar-head,
.spatial-map-filters {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.spatial-map-filters {
  flex-wrap: nowrap;
  padding: 8px;
  border: 1px solid rgba(84, 218, 131, 0.16);
  border-radius: 8px;
  background: rgba(3, 18, 31, 0.72);
}

.map-mode-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 132px;
  height: 30px;
  padding: 0 12px;
  border: 1px solid rgba(70, 212, 255, 0.22);
  border-radius: 7px;
  color: #bcecff;
  background: rgba(3, 18, 31, 0.76);
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.map-basemap-switch,
.map-layer-switch {
  flex: 0 0 auto;
  padding: 3px;
  border: 1px solid rgba(70, 212, 255, 0.18);
  border-radius: 8px;
  background: rgba(2, 14, 26, 0.86);
}

.map-base-filter {
  flex: 0 0 150px;
}

.map-node-filter {
  flex: 1 1 180px;
  min-width: 150px;
}

.map-refresh-button {
  flex: 0 0 92px;
  min-width: 92px;
}

.legend-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #87a994;
  font-size: 10px;

  span {
    display: flex;
    align-items: center;
    gap: 5px;
  }
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: #49b978;

  &.county { background: #26f2a0; }
  &.boundary { background: #58d8ff; }
  &.low { background: #9acb61; }
  &.medium { background: #e4bd55; }
  &.high { background: #dc6b6b; }
  &.sensor { border-radius: 50%; background: #62d9d3; }
}

.data-note {
  color: #648573;
  font-size: 9px;
  text-align: right;
}

.leaflet-map {
  height: 660px;
  background: #10261a;
}

.leaflet-map-stage {
  position: relative;
  overflow: hidden;
  background: #061a11;
}

.side-panel {
  display: grid;
  gap: 12px;
  grid-template-rows: auto 1fr auto;
}

.info-card {
  position: relative;
}

.info-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 72px;
  height: 2px;
  z-index: 2;
  background: linear-gradient(90deg, #2fbd69, transparent);
}

.card-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 15px 15px 11px;
  border-bottom: 1px solid rgba(128, 189, 151, 0.1);

  &.compact { padding-bottom: 10px; }

  h2 {
    margin: 2px 0 0;
    font-size: 14px;
  }
}

.status-tag,
.risk-tag {
  padding: 4px 8px;
  border-radius: 999px;
  color: #7fd39e;
  background: rgba(88, 202, 131, 0.1);
  border: 1px solid rgba(88, 202, 131, 0.16);
  font-size: 9px;
  white-space: nowrap;
}

.risk-tag {
  &.healthy { color: #69d292; background: rgba(73, 185, 120, .12); }
  &.low { color: #b6d97f; background: rgba(154, 203, 97, .12); }
  &.medium { color: #edd070; background: rgba(228, 189, 85, .12); }
  &.high { color: #ef8a8a; background: rgba(220, 107, 107, .12); }
}

.base-location {
  display: flex;
  gap: 7px;
  align-items: center;
  padding: 12px 15px 8px;
  color: #87a994;
  font-size: 10px;

  .el-icon { color: #4fe088; }
}

.base-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  margin: 7px 15px 15px;
  overflow: hidden;
  border: 1px solid rgba(128, 189, 151, 0.11);
  border-radius: 9px;
  background: rgba(128, 189, 151, 0.1);

  div {
    padding: 10px 7px;
    text-align: center;
    background: rgba(19, 46, 32, 0.92);
  }

  span,
  strong { display: block; }
  span { color: #799884; font-size: 8px; }
  strong { margin-top: 4px; font-size: 15px; }
  small { margin-left: 2px; color: #799884; font-size: 8px; }
}

.plot-list {
  max-height: 314px;
  padding: 7px 10px 10px;
  overflow: auto;
}

.plot-row {
  display: grid;
  grid-template-columns: 4px 1fr auto auto;
  align-items: center;
  gap: 9px;
  width: 100%;
  margin: 5px 0;
  padding: 9px;
  cursor: pointer;
  color: #eaf7ee;
  text-align: left;
  border: 1px solid rgba(128, 189, 151, 0.08);
  border-radius: 9px;
  background: rgba(24, 51, 36, 0.55);
  transition: .2s ease;

  &:hover,
  &.active {
    border-color: rgba(88, 202, 131, 0.42);
    background: rgba(29, 68, 45, 0.72);
  }

  div:nth-child(2) {
    min-width: 0;
  }

  strong,
  small { display: block; }
  strong { font-size: 11px; }
  small { margin-top: 2px; color: #769682; font-size: 8px; }
}

.risk-bar {
  width: 4px;
  height: 30px;
  border-radius: 999px;
  background: #49b978;

  &.low { background: #9acb61; }
  &.medium { background: #e4bd55; }
  &.high { background: #dc6b6b; }
}

.plot-di {
  text-align: right;

  span { color: #789884; font-size: 8px; }
  strong { font-size: 13px; }
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 7px;
  padding: 11px 13px;

  div {
    padding: 9px;
    border: 1px solid rgba(128, 189, 151, 0.09);
    border-radius: 8px;
    background: rgba(24, 51, 36, 0.55);
  }

  span,
  strong { display: block; }
  span { color: #789884; font-size: 8px; }
  strong { margin-top: 4px; font-size: 12px; }
}

.advice-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 13px 13px;
  padding: 9px 10px;
  border: 1px solid rgba(228, 189, 85, 0.14);
  border-radius: 8px;
  color: #d8d1ad;
  background: rgba(228, 189, 85, 0.07);

  .el-icon { color: #e4bd55; flex: 0 0 auto; margin-top: 1px; }
  p { margin: 0; font-size: 9px; line-height: 1.6; }
}

.bottom-grid {
  display: grid;
  grid-template-columns: .75fr 1.7fr .8fr;
  gap: 12px;
  margin-top: 12px;
}

.chart-card,
.task-card {
  min-height: 262px;
}

.chart {
  width: 100%;
  height: 205px;
}

.task-content {
  padding: 18px;
}

.task-progress {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  color: #88a894;
  font-size: 10px;

  strong { color: #eaf7ee; font-size: 24px; }
}

.progress-track {
  height: 9px;
  margin: 10px 0 15px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(128, 189, 151, 0.11);
}

.progress-fill {
  width: 72%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #4dbb78, #92d36e);
}

.task-meta {
  display: grid;
  gap: 8px;
  color: #85a68f;
  font-size: 10px;
}

:deep(.leaflet-control-zoom a) {
  color: #dff5e7;
  background: #123020;
  border-bottom-color: rgba(128, 189, 151, 0.18);
}

:deep(.leaflet-control-attribution) {
  color: #5c7866;
  background: rgba(9, 27, 17, 0.76);
}

:deep(.plot-label) {
  color: #effff4;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(10, 29, 19, 0.82);
  box-shadow: none;
  font-size: 9px;
}

:deep(.plot-label::before) { display: none; }

:deep(.county-label),
:deep(.boundary-hover-label) {
  color: #e9fbff;
  border: 1px solid rgba(70, 212, 255, 0.28);
  border-radius: 8px;
  background: rgba(3, 18, 31, 0.84);
  box-shadow: 0 0 14px rgba(70, 212, 255, 0.18);
  font-size: 10px;
  font-weight: 700;
}

:deep(.county-label::before),
:deep(.boundary-hover-label::before) {
  display: none;
}

:deep(.county-label small) {
  display: block;
  margin-top: 2px;
  color: #a7dff1;
  font-size: 8px;
  font-weight: 500;
}

:deep(.map-basemap-switch .el-radio-button__inner),
:deep(.map-layer-switch .el-checkbox-button__inner) {
  min-width: 56px;
  height: 26px;
  padding: 0 8px;
  border: 0 !important;
  border-radius: 6px !important;
  color: #bcecff !important;
  background: transparent !important;
  box-shadow: none !important;
  font-size: 11px;
  font-weight: 700;
  line-height: 26px;
}

:deep(.map-basemap-switch .el-radio-button__original-radio:checked + .el-radio-button__inner),
:deep(.map-layer-switch .el-checkbox-button.is-checked .el-checkbox-button__inner) {
  color: #ffffff !important;
  background: linear-gradient(180deg, rgba(28, 169, 239, 0.92), rgba(8, 96, 160, 0.96)) !important;
  box-shadow: 0 0 14px rgba(44, 187, 255, 0.24) !important;
}

.spatial-map-filters {
  :deep(.el-select__wrapper),
  :deep(.el-input__wrapper) {
    min-height: 30px;
    border-radius: 7px;
    background: rgba(2, 14, 26, 0.88) !important;
    box-shadow: 0 0 0 1px rgba(70, 212, 255, 0.22) inset !important;
  }

  :deep(.el-input__inner),
  :deep(.el-select__selected-item),
  :deep(.el-select__placeholder),
  :deep(.el-select__caret),
  :deep(.el-input__icon) {
    color: #c7ecf8 !important;
    font-size: 12px;
  }

  :deep(.el-button) {
    height: 30px;
    color: #ffffff !important;
    border-color: rgba(70, 212, 255, 0.52) !important;
    border-radius: 7px;
    background: linear-gradient(180deg, rgba(28, 169, 239, 0.92), rgba(8, 96, 160, 0.96)) !important;
  }
}

.leaflet-map-stage.basemap-terrain :deep(.leaflet-tile-pane),
.leaflet-map-stage.basemap-vector :deep(.leaflet-tile-pane) {
  filter: saturate(0.96) contrast(1.02) brightness(0.84);
}

.leaflet-map-stage.basemap-satellite :deep(.leaflet-tile-pane) {
  filter: saturate(1.06) contrast(1.03) brightness(0.82);
}

:deep(.agri-base-icon-wrapper),
:deep(.sensor-icon-wrapper) {
  background: transparent;
  border: 0;
}

:deep(.agri-base-icon) {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #effff4;
  font-size: 10px;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.8);
}

:deep(.agri-base-icon span) {
  width: 17px;
  height: 17px;
  border: 3px solid #effff4;
  border-radius: 50% 50% 50% 0;
  transform: rotate(-45deg);
  background: #4fc47d;
  box-shadow: 0 0 0 5px rgba(79, 196, 125, 0.16), 0 0 15px rgba(79, 196, 125, 0.5);
}

:deep(.sensor-icon) {
  position: relative;
  width: 14px;
  height: 14px;
  border: 2px solid #efffff;
  border-radius: 50%;
  background: #62d9d3;
  box-shadow: 0 0 0 5px rgba(98, 217, 211, .14), 0 0 12px rgba(98, 217, 211, .55);
}

/* 统一为可视化大屏深绿底色，去掉空间监测页残留绿底和浅色地图底。 */
.agri-map-page {
  color: #effff4;
  background:
    linear-gradient(180deg, rgba(5, 38, 23, 0.96), rgba(4, 31, 19, 0.98)),
    #061a11;
}

.page-header {
  padding: 12px 16px;
  border: 1px solid rgba(42, 174, 91, 0.24);
  border-radius: 8px;
  background: linear-gradient(90deg, rgba(6, 49, 29, 0.86), rgba(5, 40, 24, 0.72));

  h1 { color: #effff4; }
  p { color: #91c7a3; }
}

.eyebrow {
  color: #4fe088;
  letter-spacing: 0;
}

.base-select {
  :deep(.el-select__wrapper) {
    background: rgba(3, 32, 18, 0.9) !important;
    box-shadow: 0 0 0 1px rgba(42, 174, 91, 0.28) inset !important;
  }
}

.header-tools {
  :deep(.el-button--success.is-plain) {
    color: #e5ffed;
    border-color: rgba(42, 174, 91, 0.46);
    background: rgba(13, 143, 215, 0.16);
  }
}

.map-panel,
.info-card {
  border-color: rgba(42, 174, 91, 0.28);
  border-radius: 8px;
  background:
    linear-gradient(145deg, rgba(6, 49, 29, 0.92), rgba(5, 40, 24, 0.96)),
    #061a11;
}

.map-toolbar,
.card-title {
  border-bottom-color: rgba(84, 218, 131, 0.14);
}

.legend-group,
.base-location,
.task-progress,
.task-meta {
  color: #91c7a3;
}

.data-note,
.plot-row small,
.base-metrics span,
.base-metrics small,
.detail-grid span,
.plot-di span {
  color: #78a98a;
}

.info-card::before {
  background: linear-gradient(90deg, #2fbd69, transparent);
}

.leaflet-map,
:deep(.leaflet-container) {
  background: #061a11;
}

.status-tag {
  color: #83edaa;
  border-color: rgba(84, 218, 131, 0.2);
  background: rgba(42, 174, 91, 0.12);
}

.base-location .el-icon {
  color: #4fe088;
}

.base-metrics {
  border-color: rgba(84, 218, 131, 0.14);
  background: rgba(84, 218, 131, 0.08);

  div {
    background: rgba(3, 32, 18, 0.88);
  }
}

.plot-row,
.detail-grid div {
  color: #effff4;
  border-color: rgba(84, 218, 131, 0.12);
  background: rgba(3, 32, 18, 0.62);
}

.plot-row:hover,
.plot-row.active {
  border-color: rgba(84, 218, 131, 0.42);
  background: rgba(8, 72, 39, 0.76);
}

.progress-track {
  background: rgba(84, 218, 131, 0.12);
}

.progress-fill {
  background: linear-gradient(90deg, #168b4c, #4fe088);
}

:deep(.leaflet-control-zoom a) {
  color: #effff4;
  background: rgba(3, 32, 18, 0.92);
  border-bottom-color: rgba(84, 218, 131, 0.18);
}

:deep(.leaflet-control-attribution) {
  color: #78a98a;
  background: rgba(3, 32, 18, 0.78);
}

:deep(.plot-label) {
  color: #effff4;
  border-color: rgba(84, 218, 131, 0.26);
  background: rgba(3, 32, 18, 0.86);
}

:deep(.agri-base-icon span) {
  background: #28ad61;
  box-shadow: 0 0 0 5px rgba(24, 168, 229, 0.16), 0 0 15px rgba(104, 223, 255, 0.45);
}

@media (max-width: 1180px) {
  .map-layout { grid-template-columns: 1fr; }
  .side-panel { grid-template-columns: repeat(2, 1fr); grid-template-rows: auto auto; }
  .plot-list-card { grid-row: span 2; }
  .bottom-grid { grid-template-columns: 1fr 1fr; }
  .task-card { grid-column: 1 / -1; }
}

@media (max-width: 780px) {
  .agri-map-page { padding: 12px; }
  .page-header { align-items: flex-start; flex-direction: column; }
  .header-tools { width: 100%; flex-wrap: wrap; }
  .base-select { flex: 1; }
  .map-toolbar { align-items: flex-start; flex-direction: column; }
  .data-note { text-align: left; }
  .leaflet-map { height: 520px; }
  .side-panel,
  .bottom-grid { grid-template-columns: 1fr; }
  .plot-list-card,
  .task-card { grid-row: auto; grid-column: auto; }
}
</style>
