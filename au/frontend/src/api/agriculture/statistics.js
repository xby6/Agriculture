import request from '@/utils/request'

export function getAgricultureOverview() {
  return request({
    url: '/statistics/agriculture/overview',
    method: 'get'
  })
}
