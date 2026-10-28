import request from '@/utils/request'

export function listAgriDevices(query) {
  return request({
    url: '/agri/devices',
    method: 'get',
    params: query
  })
}

export function getEnvironmentLatest(query) {
  return request({
    url: '/agri/environment/latest',
    method: 'get',
    params: query
  })
}

export function getEnvironmentHistory(query) {
  return request({
    url: '/agri/environment/history',
    method: 'get',
    params: query
  })
}

export function getEnvironmentAlerts(query) {
  return request({
    url: '/agri/environment/alerts',
    method: 'get',
    params: query
  })
}

export function syncAgriRealtime(data) {
  return request({
    url: '/agri/iot/sync/realtime',
    method: 'post',
    data
  })
}

export function syncAgriHistory(data) {
  return request({
    url: '/agri/iot/sync/history',
    method: 'post',
    data
  })
}
