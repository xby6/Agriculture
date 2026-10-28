export const baseOptions = [
  { value: 'qingyuan', label: '清原实验基地' },
  { value: 'donggang', label: '丹东东港实验基地' },
  { value: 'dandong_academy', label: '丹东农科院实验基地' },
  { value: 'haicheng', label: '海城实验基地' }
]
export const fieldOptions = [
  { value: 'A01', label: 'A01 地块' },
  { value: 'A02', label: 'A02 地块' },
  { value: 'B01', label: 'B01 地块' },
  { value: 'B02', label: 'B02 地块' }
]

export const riskTypeMap = {
  healthy: { label: '健康', type: 'success' },
  low: { label: '低风险', type: 'success' },
  medium: { label: '中风险', type: 'warning' },
  high: { label: '高风险', type: 'danger' }
}

export const farmingTypes = ['育秧', '插秧', '施肥', '灌溉', '排水', '打药', '田间调查', '无人机采样', '收获']

export const dataSourcePipelines = [
  {
    source: '环境传感器',
    method: 'HTTP / MQTT',
    frequency: '10 分钟',
    payload: '空气温湿度、土壤温湿度、光照、CO₂、降雨、风速',
    status: '已接入',
    type: 'success',
    progress: 92
  },
  {
    source: '无人机多光谱',
    method: '文件上传 / 结果导入',
    frequency: '按飞行日期',
    payload: '正射影像、NDVI、NDRE、GNDVI、采样范围',
    status: '试运行',
    type: 'warning',
    progress: 68
  },
  {
    source: '人工调查',
    method: '网页表单 / Excel 导入',
    frequency: '按调查日期',
    payload: '病级、病株数、总株数、DI、采样点位、农事备注',
    status: '已接入',
    type: 'success',
    progress: 86
  },
  {
    source: '外部天气',
    method: 'API 定时同步',
    frequency: '1 小时',
    payload: '降雨预报、风速风向、气压、连续高湿时长',
    status: '待联调',
    type: 'info',
    progress: 45
  }
]

export const algorithmServices = [
  {
    name: '稻瘟病图像检测',
    version: 'DCDW-YOLOv11',
    input: '叶片图片 / 田间照片',
    output: '病斑框、病害类型、置信度',
    status: '在线',
    latency: '0.8s',
    type: 'success'
  },
  {
    name: '病情指数预测',
    version: 'Rule + SEIR 预留',
    input: '历史 DI / 环境 / 降雨 / 光照',
    output: '未来 7 天 DI 与风险等级',
    status: '在线',
    latency: '1.2s',
    type: 'success'
  },
  {
    name: '遥感长势评估',
    version: 'NDVI/NDRE/GNDVI',
    input: '无人机指数栅格 / 地块边界',
    output: '长势等级、异常地块、变化趋势',
    status: '试运行',
    latency: '批处理',
    type: 'warning'
  },
  {
    name: '综合报告生成',
    version: 'ReportFlow v1',
    input: '环境、病害、遥感、农事、模型结果',
    output: '周报、病害预测报告、遥感分析报告',
    status: '待优化',
    latency: '3-5s',
    type: 'info'
  }
]

export const dataAssetTypes = [
  { name: '环境监测数据', count: 24860, unit: '条', quality: 98.6 },
  { name: '遥感影像与指数', count: 46, unit: '批', quality: 94.2 },
  { name: '病害图片样本', count: 1280, unit: '张', quality: 91.8 },
  { name: '田间调查记录', count: 328, unit: '条', quality: 96.4 },
  { name: '农事作业记录', count: 216, unit: '条', quality: 97.1 },
  { name: '模型输出结果', count: 584, unit: '份', quality: 95.3 }
]
