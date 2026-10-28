<template>
  <div class="app-container agri-page">
    <AgriPageHeader
      title="水稻农事全过程管理"
      eyebrow="FARMING OPERATIONS"
      icon="Calendar"
      description="记录育秧、插秧、施肥、灌溉、排水、打药、调查、采样和收获全过程，形成可追溯的地块生产档案。"
    >
      <el-button type="primary" icon="Plus" @click="openAdd">新增农事记录</el-button>
    </AgriPageHeader>

    <section class="summary-grid">
      <article v-for="item in summaries" :key="item.label" class="summary-card">
        <div class="icon-wrap"><el-icon><component :is="item.icon" /></el-icon></div>
        <div><span>{{ item.label }}</span><strong>{{ item.value }}</strong><p>{{ item.note }}</p></div>
      </article>
    </section>

    <section class="main-grid">
      <el-card shadow="never" class="calendar-card">
        <template #header><div class="card-title"><span>本月农事安排</span><el-date-picker v-model="calendarMonth" type="month" /></div></template>
        <div class="schedule-list">
          <div v-for="item in schedules" :key="item.date + item.title" class="schedule-item">
            <div class="date-box"><strong>{{ item.day }}</strong><span>{{ item.week }}</span></div>
            <div class="schedule-dot" :class="item.status"></div>
            <div class="schedule-content">
              <div><strong>{{ item.title }}</strong><el-tag :type="item.tagType" size="small">{{ item.statusText }}</el-tag></div>
              <p>{{ item.base }} · {{ item.field }} · {{ item.detail }}</p>
              <span>负责人：{{ item.owner }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="progress-card">
        <template #header><div class="card-title"><span>生育期与作业完成度</span><el-tag type="success">孕穗期</el-tag></div></template>
        <div class="stage-track">
          <div v-for="(item, index) in stages" :key="item.name" class="stage-item" :class="{ active: index <= 4 }">
            <span>{{ index + 1 }}</span><p>{{ item.name }}</p><small>{{ item.date }}</small>
          </div>
        </div>
        <div class="workload">
          <div v-for="item in workloads" :key="item.name" class="workload-row">
            <div><span>{{ item.name }}</span><strong>{{ item.done }}/{{ item.total }}</strong></div>
            <el-progress :percentage="Math.round(item.done / item.total * 100)" :stroke-width="10" />
          </div>
        </div>
      </el-card>
    </section>

    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-title table-title">
          <span>农事记录台账</span>
          <div class="filters">
            <el-select v-model="filters.base" placeholder="选择基地" clearable><el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select>
            <el-select v-model="filters.type" placeholder="农事类型" clearable><el-option v-for="item in farmingTypes" :key="item" :label="item" :value="item" /></el-select>
            <el-input v-model="filters.keyword" placeholder="搜索操作人或备注" clearable prefix-icon="Search" />
          </div>
        </div>
      </template>
      <el-table :data="filteredRecords" stripe>
        <el-table-column prop="date" label="作业日期" width="120" />
        <el-table-column prop="base" label="基地" min-width="150" />
        <el-table-column prop="field" label="地块" width="90" />
        <el-table-column label="农事类型" width="110"><template #default="scope"><el-tag>{{ scope.row.type }}</el-tag></template></el-table-column>
        <el-table-column prop="content" label="作业内容" min-width="220" />
        <el-table-column prop="amount" label="用量/规模" width="130" />
        <el-table-column prop="owner" label="操作人" width="100" />
        <el-table-column prop="weather" label="作业环境" width="150" />
        <el-table-column label="状态" width="100" align="center"><template #default="scope"><el-tag :type="scope.row.status === '已完成' ? 'success' : 'warning'">{{ scope.row.status }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="130" fixed="right"><template #default><el-button link type="primary">详情</el-button><el-button link type="primary">编辑</el-button></template></el-table-column>
      </el-table>
      <pagination :total="records.length" v-model:page="pageNum" v-model:limit="pageSize" />
    </el-card>

    <el-dialog v-model="dialogOpen" title="新增农事记录" width="680px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="18">
          <el-col :span="12"><el-form-item label="水稻基地" prop="base"><el-select v-model="form.base"><el-option v-for="item in baseOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="作业地块" prop="field"><el-select v-model="form.field"><el-option v-for="item in fieldOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="农事类型" prop="type"><el-select v-model="form.type"><el-option v-for="item in farmingTypes" :key="item" :label="item" :value="item" /></el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="作业日期" prop="date"><el-date-picker v-model="form.date" type="datetime" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="操作人员" prop="owner"><el-input v-model="form.owner" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="用量/规模"><el-input v-model="form.amount" placeholder="如 12 kg/亩" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="作业内容" prop="content"><el-input v-model="form.content" type="textarea" :rows="3" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注"><el-input v-model="form.note" type="textarea" :rows="2" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer><el-button @click="dialogOpen=false">取消</el-button><el-button type="primary" @click="submit">保存记录</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup name="FarmingManagement">
import AgriPageHeader from '@/components/AgriPageHeader'
import { baseOptions, fieldOptions, farmingTypes } from '@/data/agriculture'

const { proxy } = getCurrentInstance()
const calendarMonth = ref(new Date())
const pageNum = ref(1)
const pageSize = ref(10)
const dialogOpen = ref(false)
const formRef = ref()
const filters = reactive({ base: '', type: '', keyword: '' })
const form = reactive({ base: 'haicheng', field: 'A01', type: '田间调查', date: new Date(), owner: '', amount: '', content: '', note: '' })
const rules = { base: [{ required: true, message: '请选择基地', trigger: 'change' }], field: [{ required: true, message: '请选择地块', trigger: 'change' }], type: [{ required: true, message: '请选择农事类型', trigger: 'change' }], date: [{ required: true, message: '请选择日期', trigger: 'change' }], owner: [{ required: true, message: '请输入操作人员', trigger: 'blur' }], content: [{ required: true, message: '请输入作业内容', trigger: 'blur' }] }

const summaries = [
  { label: '今日待办', value: '5 项', note: '2 项为病害复查', icon: 'Bell' },
  { label: '本月已完成', value: '38 项', note: '完成率 86.4%', icon: 'CircleCheck' },
  { label: '在管地块', value: '12 块', note: '覆盖 3 个基地', icon: 'MapLocation' },
  { label: '待复查任务', value: '3 项', note: '均来自病害预警', icon: 'Warning' }
]
const schedules = [
  { day: '18', week: '周六', title: 'A02 地块稻瘟病复查', base: '海城基地', field: 'A02', detail: '重新调查 DI 并上传叶片图片', owner: '张老师', status: 'doing', statusText: '进行中', tagType: 'warning' },
  { day: '19', week: '周日', title: 'B01 地块排水作业', base: '铁岭基地', field: 'B01', detail: '降低田间湿度，改善通风', owner: '李同学', status: 'todo', statusText: '待执行', tagType: 'info' },
  { day: '20', week: '周一', title: '无人机多光谱采样', base: '海城基地', field: 'A01-A04', detail: '获取 NDVI、NDRE、GNDVI', owner: '遥感组', status: 'todo', statusText: '待执行', tagType: 'info' },
  { day: '21', week: '周二', title: '穗肥施用', base: '东港基地', field: 'A03', detail: '按方案进行定量施肥', owner: '王师傅', status: 'todo', statusText: '待执行', tagType: 'info' }
]
const stages = [{ name: '育秧', date: '04-20' }, { name: '插秧', date: '05-26' }, { name: '分蘖', date: '06-15' }, { name: '拔节', date: '07-05' }, { name: '孕穗', date: '07-18' }, { name: '抽穗', date: '08-01' }, { name: '灌浆', date: '08-20' }, { name: '成熟', date: '09-25' }]
const workloads = [{ name: '病害调查', done: 16, total: 18 }, { name: '环境设备巡检', done: 11, total: 12 }, { name: '无人机采样', done: 5, total: 8 }, { name: '水肥管理', done: 14, total: 15 }]
const records = ref([
  { date: '2026-07-18', base: '海城水稻试验基地', field: 'A02', type: '田间调查', content: '调查 5 个样点并计算稻瘟病 DI', amount: '250 叶片', owner: '张老师', weather: '24.8℃ / RH 91%', status: '已完成' },
  { date: '2026-07-18', base: '海城水稻试验基地', field: 'A01', type: '排水', content: '降低田间水层并清理排水沟', amount: '0.39 hm²', owner: '王师傅', weather: '阴 / 微风', status: '已完成' },
  { date: '2026-07-17', base: '铁岭水稻试验基地', field: 'B01', type: '打药', content: '依据预警结果开展稻瘟病防治', amount: '45 L', owner: '李同学', weather: '无雨 / 风速 1.8m/s', status: '已完成' },
  { date: '2026-07-20', base: '海城水稻试验基地', field: 'A01-A04', type: '无人机采样', content: '获取多光谱影像与植被指数', amount: '4 个地块', owner: '遥感组', weather: '待确认', status: '待执行' }
])
const filteredRecords = computed(() => records.value.filter(item => (!filters.type || item.type === filters.type) && (!filters.keyword || `${item.owner}${item.content}`.includes(filters.keyword))))

function openAdd() { dialogOpen.value = true }
function submit() { formRef.value.validate(valid => { if (!valid) return; dialogOpen.value = false; proxy.$modal.msgSuccess('农事记录已保存') }) }
</script>

<style lang="scss" scoped>
.agri-page{background:#061323;min-height:calc(100vh - 84px)}.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}.summary-card{display:flex;gap:14px;padding:18px;border:1px solid #e0eae2;border-radius:14px;background:rgba(6,29,47,.92)}.icon-wrap{display:grid;width:44px;height:44px;flex:0 0 44px;place-items:center;border-radius:13px;color:#2f7c45;background:rgba(5,24,40,.86);font-size:22px}.summary-card span{color:#78837b;font-size:13px}.summary-card strong{display:block;margin:4px 0;color:#24402c;font-size:24px}.summary-card p{margin:0;color:#738078;font-size:12px}.main-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:16px;margin-bottom:16px}.main-grid .el-card,.table-card{border:1px solid #e0eae2;border-radius:14px}.card-title{display:flex;align-items:center;justify-content:space-between;color:#2a4432;font-weight:700}.schedule-item{display:grid;grid-template-columns:50px 10px 1fr;gap:13px;align-items:start;padding:14px 0;border-bottom:1px dashed #e0e8e1}.date-box{text-align:center}.date-box strong{display:block;color:#2c6f3e;font-size:24px}.date-box span{color:#8a958d;font-size:12px}.schedule-dot{width:10px;height:10px;margin-top:9px;border-radius:50%;background:#9ba59e}.schedule-dot.doing{background:#e6a23c}.schedule-content>div{display:flex;align-items:center;justify-content:space-between;gap:10px}.schedule-content strong{color:#304a37}.schedule-content p{margin:6px 0;color:#6b786f;font-size:13px}.schedule-content>span{color:#929b94;font-size:12px}.stage-track{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.stage-item{padding:12px 6px;text-align:center;border:1px solid #e1e8e2;border-radius:12px;background:rgba(5,24,40,.86)}.stage-item span{display:grid;width:28px;height:28px;margin:auto;place-items:center;border-radius:50%;color:#8b958d;background:rgba(5,24,40,.86)}.stage-item p{margin:7px 0 3px;color:#637068}.stage-item small{color:#a0a8a2}.stage-item.active{border-color:#a9cdb0;background:rgba(5,24,40,.86)}.stage-item.active span{color:#fff;background:#4c9659}.stage-item.active p{color:#2d6f3e;font-weight:700}.workload{margin-top:24px}.workload-row{margin-top:16px}.workload-row>div{display:flex;justify-content:space-between;margin-bottom:8px;color:#5f6f64;font-size:13px}.table-title{gap:20px}.filters{display:flex;gap:10px}.filters .el-select{width:170px}.filters .el-input{width:220px}@media(max-width:1150px){.summary-grid{grid-template-columns:repeat(2,1fr)}.main-grid{grid-template-columns:1fr}}@media(max-width:720px){.summary-grid{grid-template-columns:1fr}.table-title{align-items:flex-start;flex-direction:column}.filters{width:100%;flex-direction:column}.filters .el-select,.filters .el-input{width:100%}}
</style>
