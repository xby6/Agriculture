import request from '@/utils/request'

// 查询任务列表
export function listTask(query) {
  return request({
    url: '/task/task/list',
    method: 'get',
    params: query
  })
}
// 执行任务
export function executeTask(taskId) {
  return request({
    url: '/task/task/process',
    method: 'post',
    params: {
      task_id: taskId
    }
  })
}

export function getRunningTasks(containerId) {
  return request({
    url: '/container/container/running-tasks/' + containerId,
    method: 'get'
  })
}
// 查询任务详细
export function getTask(id) {
  return request({
    url: '/task/task/' + id,
    method: 'get'
  })
}

// 新增任务
export function addTask(data) {
  return request({
    url: '/task/task',
    method: 'post',
    data: data
  })
}

// 修改任务
export function updateTask(data) {
  return request({
    url: '/task/task',
    method: 'put',
    data: data
  })
}

// 删除任务
export function delTask(id) {
  return request({
    url: '/task/task/' + id,
    method: 'delete'
  })
}

