import request from '@/utils/request'

// 查询基地组织列表
export function listDept(query) {
  return request({
    url: '/system/dept/list',
    method: 'get',
    params: query
  })
}

// 查询基地组织列表（排除节点）
export function listDeptExcludeChild(deptId) {
  return request({
    url: '/system/dept/list/exclude/' + deptId,
    method: 'get'
  })
}

// 查询基地组织详细
export function getDept(deptId) {
  return request({
    url: '/system/dept/' + deptId,
    method: 'get'
  })
}

// 新增基地组织
export function addDept(data) {
  return request({
    url: '/system/dept',
    method: 'post',
    data: data
  })
}

// 修改基地组织
export function updateDept(data) {
  return request({
    url: '/system/dept',
    method: 'put',
    data: data
  })
}

// 删除基地组织
export function delDept(deptId) {
  return request({
    url: '/system/dept/' + deptId,
    method: 'delete'
  })
}