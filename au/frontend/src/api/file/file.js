import request from '@/utils/request'

// 查询文件列表
export function listFile(query) {
  return request({
    url: '/file/file/list',
    method: 'get',
    params: query
  })
}

// 查询文件详细
export function getFile(id) {
  return request({
    url: '/file/file/' + id,
    method: 'get'
  })
}

// 新增文件
export function addFileFile(data) {
  return request({
    url: '/file/file',
    method: 'post',
    data: data,
    timeout: 300000,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 修改文件
export function updateFile(data) {
  return request({
    url: '/file/file',
    method: 'put',
    data: data
  })
}

// 删除文件
export function delFile(id) {
  return request({
    url: '/file/file/' + id,
    method: 'delete'
  })
}

export function UpzipFile(){
  return request({
    url:'/file/file/unzip',
    method:'post'
  })
}
//下载文件
export function down(id) {
  return request({
    url: '/file/file/' + id,
    method: 'get',
    responseType: 'blob', 
    timeout: 30000 
  })
}
