<template>
  <div class="app-container agri-page">
    <AgriPageHeader
      title="农业分析报告中心"
      eyebrow="ANALYSIS REPORTS"
      icon="Document"
      description="集中生成和归档环境监测、病害检测、病情预测、遥感长势与农事生产报告，支持复核、下载和共享。"
    >
      <el-button type="primary" icon="DocumentAdd" @click="dialogOpen=true">生成新报告</el-button>
    </AgriPageHeader>

    <section class="report-grid">
      <article v-for="item in reportTypes" :key="item.title" class="report-type-card">
        <div class="report-icon"><el-icon><component :is="item.icon" /></el-icon></div>
        <div class="report-info"><strong>{{ item.title }}</strong><p>{{ item.description }}</p><span>最近生成：{{ item.lastTime }}</span></div>
        <el-button link type="primary" @click="quickGenerate(item.title)">快速生成</el-button>
      </article>
    </section>

    <section class="summary-grid">
      <el-card shadow="never">
        <template #header><div class="card-title"><span>报告生成情况</span><el-tag type="success">本月</el-tag></div></template>
        <div class="stats"><div><strong>36</strong><span>已生成</span></div><div><strong>31</strong><span>已审核</span></div><div><strong>28</strong><span>已下载</span></div><div><strong>5</strong><span>待处理</span></div></div>
      </el-card>
      <el-card shadow="never">
        <template #header><div class="card-title"><span>本周重点结论</span><el-button link type="primary">查看详情</el-button></div></template>
        <ul class="conclusion-list"><li>海城 A02 地块稻瘟病风险升至中风险。</li><li>铁岭 B03 地块 NDVI 较上期下降 8.2%。</li><li>连续高湿时长增加，需缩短田间积水时间。</li></ul>
      </el-card>
    </section>

    <el-card shadow="never" class="table-card">
      <template #header><div class="card-title"><span>历史报告</span><div class="filters"><el-select v-model="typeFilter" placeholder="报告类型" clearable><el-option v-for="item in reportTypes" :key="item.title" :label="item.title" :value="item.title" /></el-select><el-input v-model="keyword" placeholder="搜索报告名称" clearable prefix-icon="Search" /></div></div></template>
      <el-table :data="filteredReports" stripe>
        <el-table-column prop="name" label="报告名称" min-width="260" />
        <el-table-column prop="type" label="报告类型" width="150" />
        <el-table-column prop="base" label="所属基地" min-width="160" />
        <el-table-column prop="period" label="数据周期" width="190" />
        <el-table-column prop="creator" label="生成人" width="100" />
        <el-table-column prop="time" label="生成时间" width="170" />
        <el-table-column label="审核状态" width="100" align="center"><template #default="scope"><el-tag :type="scope.row.status==='已审核'?'success':'warning'">{{ scope.row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="180" fixed="right"><template #default><el-button link type="primary">预览</el-button><el-button link type="primary">下载</el-button><el-button link type="primary">分享</el-button></template></el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogOpen" title="生成农业分析报告" width="650px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报告类型"><el-select v-model="form.type"><el-option v-for="item in reportTypes" :key="item.title" :label="item.title" :value="item.title" /></el-select></el-form-item>
        <el-form-item label="所属基地"><el-select v-model="form.base"><el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
        <el-form-item label="分析周期"><el-date-picker v-model="form.range" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" /></el-form-item>
        <el-form-item label="报告内容"><el-checkbox-group v-model="form.sections"><el-checkbox label="基地概况" /><el-checkbox label="环境统计" /><el-checkbox label="病害检测" /><el-checkbox label="病情预测" /><el-checkbox label="遥感长势" /><el-checkbox label="农事记录" /><el-checkbox label="防控建议" /></el-checkbox-group></el-form-item>
        <el-form-item label="输出格式"><el-radio-group v-model="form.format"><el-radio label="PDF" /><el-radio label="Word" /><el-radio label="Excel" /></el-radio-group></el-form-item>
      </el-form>
      <template #footer><el-button @click="dialogOpen=false">取消</el-button><el-button type="primary" @click="generate">开始生成</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup name="ReportCenter">
import AgriPageHeader from '@/components/AgriPageHeader'
import { baseOptions } from '@/data/agriculture'
const { proxy } = getCurrentInstance()
const dialogOpen=ref(false),typeFilter=ref(''),keyword=ref('')
const form=reactive({type:'水稻病害预测报告',base:'haicheng',range:[],sections:['基地概况','环境统计','病害检测','病情预测','防控建议'],format:'PDF'})
const reportTypes=[
  {title:'基地运行周报',description:'基地、设备、环境、农事和风险总体情况。',lastTime:'2026-07-18',icon:'DataBoard'},
  {title:'水稻病害预测报告',description:'当前 DI、未来趋势、风险地块和防控建议。',lastTime:'2026-07-18',icon:'TrendCharts'},
  {title:'无人机长势分析报告',description:'植被指数、空间差异和异常地块诊断。',lastTime:'2026-07-17',icon:'Position'},
  {title:'田间环境统计报告',description:'温湿度、土壤、降雨和连续高湿统计。',lastTime:'2026-07-18',icon:'Sunny'}
]
const reports=ref([
  {name:'海城基地第29周水稻病害监测与预测报告',type:'水稻病害预测报告',base:'海城水稻试验基地',period:'2026-07-12 至 07-18',creator:'系统',time:'2026-07-18 20:55',status:'已审核'},
  {name:'铁岭基地7月中旬无人机长势分析报告',type:'无人机长势分析报告',base:'铁岭水稻试验基地',period:'2026-07-10 至 07-17',creator:'遥感组',time:'2026-07-17 16:30',status:'已审核'},
  {name:'东港基地田间环境监测周报',type:'田间环境统计报告',base:'东港水稻试验基地',period:'2026-07-08 至 07-14',creator:'系统',time:'2026-07-15 08:10',status:'待审核'},
  {name:'三基地水稻生产运行月报',type:'基地运行周报',base:'全部基地',period:'2026-06-01 至 06-30',creator:'管理员',time:'2026-07-01 09:20',status:'已审核'}
])
const filteredReports=computed(()=>reports.value.filter(i=>(!typeFilter.value||i.type===typeFilter.value)&&(!keyword.value||i.name.includes(keyword.value))))
function quickGenerate(type){form.type=type;dialogOpen.value=true}
function generate(){dialogOpen.value=false;proxy.$modal.msgSuccess('报告生成任务已创建')}
</script>

<style lang="scss" scoped>
.agri-page {
  min-height: calc(100vh - 84px);
  background: linear-gradient(180deg, #eff9f2 0%, #e2f3e7 100%) !important;
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}

.report-type-card {
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  position: relative;
  padding: 20px;
  border: 1px solid #d7e7dc !important;
  border-radius: 14px;
  background: linear-gradient(145deg, #ffffff 0%, #f1faf4 100%) !important;
  box-shadow: 0 8px 22px rgba(19, 108, 56, 0.07) !important;
}

.report-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 14px;
  color: #2f7d4a !important;
  background: #edf5ee !important;
  font-size: 24px;
}

.report-info strong {
  color: #294432 !important;
}

.report-info p {
  margin: 7px 0;
  color: #506756 !important;
  font-size: 13px;
  line-height: 1.55;
}

.report-info span {
  color: #718177 !important;
  font-size: 12px;
}

.report-type-card > .el-button {
  grid-column: 2;
  justify-self: start;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.summary-grid .el-card,
.table-card {
  border: 1px solid #d7e7dc !important;
  border-radius: 14px;
  background: #ffffff !important;
  box-shadow: 0 8px 22px rgba(19, 108, 56, 0.07) !important;
}

.summary-grid :deep(.el-card__body),
.summary-grid :deep(.el-card__header),
.table-card :deep(.el-card__body),
.table-card :deep(.el-card__header) {
  background: transparent !important;
}

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  color: #183322 !important;
  font-weight: 700;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
}

.stats div {
  text-align: center;
  border-right: 1px solid #dce8dc;
}

.stats div:last-child {
  border-right: 0;
}

.stats strong {
  display: block;
  color: #2d7540 !important;
  font-size: 28px;
}

.stats span {
  color: #6f8376 !important;
  font-size: 12px;
}

.conclusion-list {
  margin: 0;
  padding-left: 20px;
  color: #506756 !important;
}

.conclusion-list li {
  margin: 10px 0;
  line-height: 1.6;
}

.filters {
  display: flex;
  gap: 10px;
}

.filters .el-select {
  width: 180px;
}

.filters .el-input {
  width: 250px;
}

@media (max-width: 1250px) {
  .report-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 760px) {
  .report-grid,
  .summary-grid { grid-template-columns: 1fr; }
  .card-title {
    align-items: flex-start;
    flex-direction: column;
  }
  .filters {
    width: 100%;
    flex-direction: column;
  }
  .filters .el-select,
  .filters .el-input { width: 100%; }
}
</style>
