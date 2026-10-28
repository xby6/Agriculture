import test from 'node:test'
import assert from 'node:assert/strict'
import { diseaseRecordsCsv, fetchDiseaseTasks, filterDiseaseRecords } from '../src/utils/diseaseRecords.js'

const records = [
  { taskId: 101, date: '2026-10-01 08:00', disease: '稻瘟病、纹枯病', source: '图像检测', note: '已完成' },
  { taskId: 102, date: '2026-10-08 23:59', disease: '未检出', source: '图像检测', note: '已完成' },
  { taskId: 103, date: '--', disease: '稻瘟病', source: '图像检测', note: '已完成' }
]

test('combines keyword, disease and inclusive dates without changing the source', () => {
  assert.deepEqual(filterDiseaseRecords(records, {
    keyword: ' 101 ', disease: '纹枯病', dateRange: ['2026-10-01', '2026-10-08']
  }), [records[0]])
  assert.deepEqual(filterDiseaseRecords(records, { dateRange: ['2026-10-01', '2026-10-08'] }), records.slice(0, 2))
  assert.deepEqual(filterDiseaseRecords(records, { keyword: '999' }), [])
  assert.deepEqual(filterDiseaseRecords(records, { disease: '稻瘟病' }), [records[0], records[2]])
  assert.equal(filterDiseaseRecords(records, { dateRange: null }).length, 3)
  assert.equal(records.length, 3)
})

test('CSV preserves Chinese, commas, quotes and newlines, and neutralizes formulas', () => {
  const csv = diseaseRecordsCsv([
    { taskId: 101, disease: '稻瘟病', note: '田块,"A"\n复查', operator: ' =HYPERLINK("example")' },
    { taskId: 102, note: '@SUM(1,2)' }
  ])
  assert.ok(csv.startsWith('\uFEFF"任务编号","调查日期"'))
  assert.ok(csv.includes('"田块,""A""\n复查"'))
  assert.ok(csv.includes('"\' =HYPERLINK(""example"")"'))
  assert.ok(csv.includes('"\'@SUM(1,2)"'))
  assert.ok(csv.endsWith('\r\n'))
  assert.ok(!csv.includes('undefined'))
})

test('history retrieves more than 100 tasks and exports every filtered row', async () => {
  const tasks = Array.from({ length: 205 }, (_, index) => ({
    id: index + 1, result: index + 10, remark: '水稻病害检测页面提交'
  }))
  tasks[0].result = 0
  tasks[1].remark = '其他任务'
  const requested = []
  const loaded = await fetchDiseaseTasks(async query => {
    requested.push(query.pageNum)
    return { rows: tasks.slice((query.pageNum - 1) * query.pageSize, query.pageNum * query.pageSize), total: 205, hasNext: query.pageNum < 3 }
  })
  assert.deepEqual(requested, [1, 2, 3])
  assert.equal(loaded.length, 203)
  assert.equal(loaded.at(-1).id, 205)
  const filtered = filterDiseaseRecords(loaded.map(task => ({ taskId: task.id, disease: '稻瘟病' })), { disease: '稻瘟病' })
  assert.equal(diseaseRecordsCsv(filtered).split('\r\n').length - 2, 203)
})

test('accepts nested pagination and detects a repeated page', async () => {
  const task = { id: 1, result: 10, remark: '水稻病害检测页面提交' }
  assert.deepEqual(await fetchDiseaseTasks(async () => ({ data: { rows: [task], hasNext: false } })), [task])
  await assert.rejects(fetchDiseaseTasks(async () => ({ rows: [task], hasNext: true })), /下一页/)
})

test('a page failure propagates instead of returning a partial history', async () => {
  await assert.rejects(fetchDiseaseTasks(async ({ pageNum }) => {
    if (pageNum === 2) throw new Error('network unavailable')
    return { rows: [{ id: 1, result: 10, remark: '水稻病害检测页面提交' }], hasNext: true }
  }), /network unavailable/)
})
