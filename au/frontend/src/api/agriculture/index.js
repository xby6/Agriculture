import request from '@/utils/request'

// 基地与地块
export function listRiceBases(params) {
  return request({ url: '/agriculture/base/list', method: 'get', params })
}
export function listRiceFields(params) {
  return request({ url: '/agriculture/field/list', method: 'get', params })
}

// 环境监测
export function getRealtimeEnvironment(params) {
  return request({ url: '/agriculture/environment/realtime', method: 'get', params })
}
export function getEnvironmentHistory(params) {
  return request({ url: '/agriculture/environment/history', method: 'get', params })
}
export function exportEnvironment(params) {
  return request({ url: '/agriculture/environment/export', method: 'post', data: params, responseType: 'blob' })
}

// 病害检测、调查与预测
export function detectRiceDisease(data) {
  return request({ url: '/agriculture/disease/detect', method: 'post', data, headers: { 'Content-Type': 'multipart/form-data' } })
}
export function saveDiseaseSurvey(data) {
  return request({ url: '/agriculture/disease/survey', method: 'post', data })
}
export function getDiseasePrediction(params) {
  return request({ url: '/agriculture/disease/prediction', method: 'get', params })
}

// 农事全过程
export function listFarmingRecords(params) {
  return request({ url: '/agriculture/farming/list', method: 'get', params })
}
export function saveFarmingRecord(data) {
  return request({ url: '/agriculture/farming', method: 'post', data })
}

// 无人机遥感与长势
export function listRemoteSensingFlights(params) {
  return request({ url: '/agriculture/remote-sensing/flight/list', method: 'get', params })
}
export function getVegetationIndexTrend(params) {
  return request({ url: '/agriculture/remote-sensing/index-trend', method: 'get', params })
}
export function uploadRemoteSensingData(data) {
  return request({ url: '/agriculture/remote-sensing/upload', method: 'post', data, headers: { 'Content-Type': 'multipart/form-data' } })
}

// 报告中心
export function listAgricultureReports(params) {
  return request({ url: '/agriculture/report/list', method: 'get', params })
}
export function generateAgricultureReport(data) {
  return request({ url: '/agriculture/report/generate', method: 'post', data })
}
