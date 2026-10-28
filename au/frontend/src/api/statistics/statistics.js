import request from '@/utils/request'

// 获取所有统计数据
export function getAllStatistics() {
  return request({
    url: '/statistics/all',
    method: 'get'
  })
}

// 获取任务统计数据
export function getTaskStatistics() {
  return request({
    url: '/statistics/tasks',
    method: 'get'
  })
}

// 获取文件统计数据
export function getFileStatistics() {
  return request({
    url: '/statistics/files',
    method: 'get'
  })
}

// 获取容器统计数据
export function getContainerStatistics() {
  return request({
    url: '/statistics/containers',
    method: 'get'
  })
}

// 获取节点统计数据
export function getNodeStatistics() {
  return request({
    url: '/statistics/nodes',
    method: 'get'
  })
}