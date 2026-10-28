<template>
  <div class="app-container agri-page">
    <AgriPageHeader
      title="无人机遥感与长势分析"
      eyebrow="UAV REMOTE SENSING"
      icon="Position"
      description="管理无人机多光谱影像与植被指数结果，展示 NDVI、NDRE、GNDVI、OSAVI、RDVI 和 GDVI 的时空变化。"
    >
      <el-button icon="UploadFilled" @click="uploadOpen=true">上传遥感数据</el-button>
      <el-button type="primary" icon="MagicStick" @click="startAnalysis">启动长势分析</el-button>
    </AgriPageHeader>

    <section class="metric-grid">
      <article v-for="item in metrics" :key="item.label" class="metric-card">
        <span>{{ item.label }}</span><strong>{{ item.value }}</strong><p>{{ item.note }}</p>
      </article>
    </section>

    <section class="main-grid">
      <el-card shadow="never" class="map-card">
        <template #header><div class="card-title"><span>地块长势空间分布</span><div><el-radio-group v-model="selectedIndex" size="small"><el-radio-button label="NDVI" /><el-radio-button label="NDRE" /><el-radio-button label="GNDVI" /></el-radio-group></div></div></template>
        <div class="field-map">
          <div v-for="plot in plots" :key="plot.code" class="plot" :class="plot.level" :style="plot.style">
            <strong>{{ plot.code }}</strong><span>{{ selectedIndex }} {{ plot[selectedIndex.toLowerCase()] }}</span>
          </div>
          <div class="map-legend"><span><i class="excellent"></i>长势优</span><span><i class="good"></i>长势良</span><span><i class="normal"></i>长势中</span><span><i class="weak"></i>长势弱</span></div>
        </div>
      </el-card>

      <el-card shadow="never" class="ranking-card">
        <template #header><div class="card-title"><span>地块长势排序</span><el-tag type="success">2026-07-18 航次</el-tag></div></template>
        <div v-for="(item,index) in ranking" :key="item.field" class="ranking-row">
          <span class="rank">{{ index+1 }}</span>
          <div class="ranking-info"><strong>{{ item.field }}</strong><p>{{ item.base }}</p></div>
          <el-progress :percentage="item.score" :stroke-width="8" :show-text="false" />
          <b>{{ item.score }}</b>
        </div>
      </el-card>

      <el-card shadow="never" class="trend-card wide">
        <template #header><div class="card-title"><span>植被指数时序变化</span><el-select v-model="selectedField" size="small" style="width:150px"><el-option v-for="item in fieldOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></div></template>
        <div ref="trendChartRef" class="chart"></div>
      </el-card>

      <el-card shadow="never" class="feature-card">
        <template #header><div class="card-title"><span>病害相关关键光谱因子</span><span class="subtle">特征筛选结果</span></div></template>
        <div v-for="item in spectralFactors" :key="item.name" class="factor-row">
          <div><strong>{{ item.name }}</strong><span>{{ item.description }}</span></div>
          <el-progress :percentage="item.importance" :stroke-width="10" />
        </div>
      </el-card>
    </section>

    <el-card shadow="never" class="flight-card">
      <template #header><div class="card-title"><span>无人机航次与数据产品</span><el-button link type="primary">查看数据目录</el-button></div></template>
      <el-table :data="flights" stripe>
        <el-table-column prop="date" label="飞行日期" width="120" />
        <el-table-column prop="base" label="基地" min-width="160" />
        <el-table-column prop="area" label="覆盖面积" width="110" />
        <el-table-column prop="height" label="飞行高度" width="100" />
        <el-table-column prop="overlap" label="航向/旁向重叠" width="140" />
        <el-table-column prop="products" label="数据产品" min-width="220" />
        <el-table-column label="处理状态" width="100" align="center"><template #default="scope"><el-tag :type="scope.row.status==='已完成'?'success':'warning'">{{ scope.row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="150"><template #default><el-button link type="primary">查看</el-button><el-button link type="primary">下载</el-button></template></el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="uploadOpen" title="上传无人机遥感数据" width="620px">
      <el-form label-width="110px">
        <el-form-item label="所属基地"><el-select v-model="uploadForm.base"><el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
        <el-form-item label="飞行日期"><el-date-picker v-model="uploadForm.date" type="date" /></el-form-item>
        <el-form-item label="数据类型"><el-checkbox-group v-model="uploadForm.types"><el-checkbox label="正射影像" /><el-checkbox label="多光谱影像" /><el-checkbox label="植被指数结果" /><el-checkbox label="地块统计表" /></el-checkbox-group></el-form-item>
        <el-form-item label="选择文件"><el-upload drag action="#" :auto-upload="false" multiple><el-icon class="el-icon--upload"><UploadFilled /></el-icon><div class="el-upload__text">拖拽文件到此处或<em>点击上传</em></div></el-upload></el-form-item>
      </el-form>
      <template #footer><el-button @click="uploadOpen=false">取消</el-button><el-button type="primary" @click="saveUpload">开始上传</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup name="RemoteSensing">
import * as echarts from 'echarts'
import AgriPageHeader from '@/components/AgriPageHeader'
import { baseOptions, fieldOptions } from '@/data/agriculture'

const { proxy } = getCurrentInstance()
const selectedIndex = ref('NDVI')
const selectedField = ref('A01')
const trendChartRef = ref()
const uploadOpen = ref(false)
const uploadForm = reactive({ base: 'haicheng', date: new Date(), types: ['多光谱影像', '植被指数结果'] })
let chart
const chartTextColor = '#3f5948'
const chartMutedColor = '#718177'
const chartGridLine = 'rgba(74, 128, 82, 0.16)'
const trendColors = ['#2f7d4a', '#5ea98a', '#d7a12e', '#8b77b5']
const tooltipStyle = {
  backgroundColor: 'rgba(255, 255, 255, 0.98)',
  borderColor: 'rgba(74, 128, 82, 0.24)',
  textStyle: { color: '#3f5948' }
}
const metrics = [
  { label: '本季飞行航次', value: '18 次', note: '最近一次 07-18' },
  { label: '遥感覆盖面积', value: '42.6 hm²', note: '覆盖 12 个地块' },
  { label: '平均 NDVI', value: '0.76', note: '较上次 +0.03' },
  { label: '长势异常地块', value: '2 块', note: 'A02、B03 待核查' }
]
const plots = [
  { code: 'A01', level: 'excellent', ndvi: 0.82, ndre: 0.47, gndvi: 0.73, style: { left:'8%', top:'10%', width:'27%', height:'30%' } },
  { code: 'A02', level: 'normal', ndvi: 0.68, ndre: 0.34, gndvi: 0.61, style: { left:'38%', top:'8%', width:'25%', height:'35%' } },
  { code: 'A03', level: 'good', ndvi: 0.76, ndre: 0.42, gndvi: 0.69, style: { left:'66%', top:'13%', width:'25%', height:'27%' } },
  { code: 'B01', level: 'excellent', ndvi: 0.84, ndre: 0.49, gndvi: 0.75, style: { left:'10%', top:'48%', width:'24%', height:'35%' } },
  { code: 'B02', level: 'good', ndvi: 0.78, ndre: 0.44, gndvi: 0.70, style: { left:'38%', top:'50%', width:'27%', height:'31%' } },
  { code: 'B03', level: 'weak', ndvi: 0.59, ndre: 0.28, gndvi: 0.53, style: { left:'69%', top:'47%', width:'22%', height:'36%' } }
]
const ranking = [
  { field: 'B01 地块', base: '海城基地', score: 92 }, { field: 'A01 地块', base: '海城基地', score: 90 }, { field: 'B02 地块', base: '铁岭基地', score: 85 }, { field: 'A03 地块', base: '东港基地', score: 82 }, { field: 'A02 地块', base: '海城基地', score: 71 }, { field: 'B03 地块', base: '铁岭基地', score: 63 }
]
const spectralFactors = [
  { name: 'OSAVI', description: '优化土壤调节植被指数', importance: 91 },
  { name: 'RDVI', description: '再归一化差值植被指数', importance: 86 },
  { name: 'GDVI', description: '绿光差值植被指数', importance: 79 }
]
const flights = [
  { date: '2026-07-18', base: '海城水稻试验基地', area: '12.4 hm²', height: '30 m', overlap: '80% / 75%', products: '正射影像、NDVI、NDRE、GNDVI', status: '已完成' },
  { date: '2026-07-12', base: '铁岭水稻试验基地', area: '9.8 hm²', height: '30 m', overlap: '80% / 75%', products: '多光谱影像、OSAVI、RDVI、GDVI', status: '已完成' },
  { date: '2026-07-05', base: '东港水稻试验基地', area: '8.6 hm²', height: '30 m', overlap: '78% / 75%', products: '正射影像、地块统计表', status: '已完成' },
  { date: '2026-07-20', base: '海城水稻试验基地', area: '12.4 hm²', height: '30 m', overlap: '80% / 75%', products: '计划采集', status: '待执行' }
]
function initChart(){
  chart=echarts.init(trendChartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis', ...tooltipStyle },
    color: trendColors,
    legend: { data: ['NDVI','NDRE','GNDVI','OSAVI'], top: 0, textStyle: { color: chartTextColor, fontSize: 13 } },
    grid: { left: 45, right: 25, top: 42, bottom: 28 },
    xAxis: {
      type: 'category',
      data: ['05-30','06-08','06-18','06-28','07-05','07-12','07-18'],
      axisLabel: { color: chartMutedColor, fontSize: 12 },
      axisLine: { lineStyle: { color: 'rgba(74, 128, 82, 0.28)' } },
      axisTick: { lineStyle: { color: 'rgba(74, 128, 82, 0.22)' } }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: { color: chartMutedColor, fontSize: 12 },
      splitLine: { lineStyle: { type: 'dashed', color: chartGridLine } }
    },
    series: [
      { name: 'NDVI', type: 'line', smooth: true, symbolSize: 7, lineStyle: { width: 3, color: trendColors[0] }, itemStyle: { color: trendColors[0] }, data: [0.36,0.48,0.58,0.67,0.73,0.79,0.82] },
      { name: 'NDRE', type: 'line', smooth: true, symbolSize: 7, lineStyle: { width: 3, color: trendColors[1] }, itemStyle: { color: trendColors[1] }, data: [0.18,0.25,0.31,0.36,0.40,0.44,0.47] },
      { name: 'GNDVI', type: 'line', smooth: true, symbolSize: 7, lineStyle: { width: 3, color: trendColors[2] }, itemStyle: { color: trendColors[2] }, data: [0.31,0.41,0.50,0.59,0.65,0.70,0.73] },
      { name: 'OSAVI', type: 'line', smooth: true, symbolSize: 7, lineStyle: { width: 3, color: trendColors[3] }, itemStyle: { color: trendColors[3] }, data: [0.29,0.39,0.49,0.58,0.64,0.69,0.72] }
    ]
  })
}
function startAnalysis(){proxy.$modal.msgSuccess('长势分析任务已提交至模型服务')}
function saveUpload(){uploadOpen.value=false;proxy.$modal.msgSuccess('遥感数据上传任务已创建')}
function resize(){chart?.resize()}
onMounted(()=>{nextTick(initChart);window.addEventListener('resize',resize)})
onBeforeUnmount(()=>{window.removeEventListener('resize',resize);chart?.dispose()})
</script>

<style lang="scss" scoped>
.agri-page{background:#061323;min-height:calc(100vh - 84px)}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}.metric-card{padding:18px 20px;border:1px solid #e0eae2;border-radius:14px;background:rgba(6,29,47,.92)}.metric-card span{color:#77827a;font-size:13px}.metric-card strong{display:block;margin:7px 0;color:#24402d;font-size:27px}.metric-card p{margin:0;color:#748178;font-size:12px}.main-grid{display:grid;grid-template-columns:1.5fr .8fr;gap:16px;margin-bottom:16px}.main-grid .el-card,.flight-card{border:1px solid #e0eae2;border-radius:14px}.wide{grid-column:span 1}.card-title{display:flex;align-items:center;justify-content:space-between;color:#294431;font-weight:700}.subtle{color:#8c968e;font-size:12px;font-weight:400}.field-map{position:relative;height:430px;overflow:hidden;border-radius:13px;background:linear-gradient(145deg,rgba(7,44,58,.84),rgba(4,24,32,.98))}.field-map:before{content:"";position:absolute;inset:0;background-image:linear-gradient(rgba(53,200,255,.16) 1px,transparent 1px),linear-gradient(90deg,rgba(53,200,255,.16) 1px,transparent 1px);background-size:32px 32px}.plot{position:absolute;display:flex;align-items:center;justify-content:center;flex-direction:column;border:2px solid rgba(255,255,255,.8);border-radius:12px;color:#fff;box-shadow:0 5px 14px rgba(35,65,40,.15)}.plot.excellent{background:#3e9252}.plot.good{background:#78a955}.plot.normal{background:#d1ab45}.plot.weak{background:#c56e57}.plot strong{font-size:17px}.plot span{margin-top:5px;font-size:12px}.map-legend{position:absolute;right:14px;bottom:14px;display:flex;gap:12px;padding:9px 12px;border-radius:9px;background:rgba(6,29,47,.92);font-size:12px}.map-legend i{display:inline-block;width:9px;height:9px;margin-right:4px;border-radius:2px}.map-legend .excellent{background:#3e9252}.map-legend .good{background:#78a955}.map-legend .normal{background:#d1ab45}.map-legend .weak{background:#c56e57}.ranking-row{display:grid;grid-template-columns:28px 95px 1fr 30px;gap:10px;align-items:center;padding:15px 0;border-bottom:1px dashed #e1e8e2}.rank{display:grid;width:25px;height:25px;place-items:center;border-radius:50%;color:#2f7541;background:rgba(5,24,40,.86);font-weight:700}.ranking-info strong{color:#344b3b}.ranking-info p{margin:3px 0 0;color:#8c968f;font-size:12px}.ranking-row b{color:#3a5b43;text-align:right}.chart{height:360px}.factor-row{margin-bottom:20px}.factor-row>div{display:flex;justify-content:space-between;margin-bottom:8px}.factor-row strong{color:#33513c}.factor-row span{color:#87928a;font-size:12px}@media(max-width:1150px){.metric-grid{grid-template-columns:repeat(2,1fr)}.main-grid{grid-template-columns:1fr}}@media(max-width:680px){.metric-grid{grid-template-columns:1fr}.map-legend{flex-wrap:wrap;left:10px;right:10px}}
</style>
