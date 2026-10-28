import request from '@/utils/request'

// 查询农业岗位列表
export function listPost(query) {
  return request({
    url: '/system/post/list',
    method: 'get',
    params: query
  })
}

// 查询农业岗位详细
export function getPost(postId) {
  return request({
    url: '/system/post/' + postId,
    method: 'get'
  })
}

// 新增农业岗位
export function addPost(data) {
  return request({
    url: '/system/post',
    method: 'post',
    data: data
  })
}

// 修改农业岗位
export function updatePost(data) {
  return request({
    url: '/system/post',
    method: 'put',
    data: data
  })
}

// 删除农业岗位
export function delPost(postId) {
  return request({
    url: '/system/post/' + postId,
    method: 'delete'
  })
}
