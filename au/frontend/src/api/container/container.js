import request from '@/utils/request'

// 查询容器列表
export function listModel(containerId) {
  return request({
    url: '/container/container/model/list',
    method: 'get',
    params: {
container_id: containerId
}
  })
}


export function getLog(container_id){
  return request({
    url:'/container/container/logs/'+container_id,
    method:'get'
  })
}

export function getTasking(container_id){
  return request({
    url:'/container/container/running-tasks/'+container_id,
    method:'get',
  })
}


export function listAlgorithm(containerId) {
return request({
url: '/container/container/algorithm/list',
method: 'get',
params: {
container_id: containerId
}
})
}

// 删除模型 

export function delModel(containerId, modelName) {
  const formData = new FormData()
  formData.append('model_name', modelName)
  formData.append('container_id', containerId.toString())
  
  return request({
    url: '/container/container/model/delete',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 新增模型算法
export function addModel(data) {
  return request({
    url: '/container/container/model/create',
    method: 'post',
    data: data,
     headers: {
      'Content-Type': 'multipart/form-data'
    }
    
  })

}
// 新增算法
export function addAlgorithm(data) {
  return request({
    url: '/container/container/algorithm/create',
    method: 'post',
    data: data,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 删除算法 
export function delAlgorithm(containerId, algoName) {
  const formData = new FormData()
  formData.append('container_id', containerId.toString())
  formData.append('algo_name', algoName)
  
  return request({
    url: '/container/container/algorithm/delete',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
// 查询模型算法详细
export function getContainer(id) {
  return request({
    url: '/container/container/' + id,
    method: 'get'
  })
}

// 修改模型算法
export function updateAlgorithm(data) {
  return request({
    url: '/container/container/algorithm/update',
    method: 'post',
    data: data
  })
}

// 修改模型算法
export function updateModel(data) {
  return request({
    url: '/container/container',
    method: 'put',
    data: data
  })
}



// 查询容器列表
export function listContainer(query) {
  return request({
    url: '/container/container/list',
    method: 'get',
    params: query
  })
}



// 新增容器
export function addContainer(data) {
  return request({
    url: '/container/container',
    method: 'post',
    data: data
  })
}

// 修改容器
export function updateContainer(data) {
  return request({
    url: '/container/container',
    method: 'put',
    data: data
  })
}

// 删除容器
export function delContainer(id) {
  return request({
    url: '/container/container/' + id,
    method: 'delete'
  })
}


