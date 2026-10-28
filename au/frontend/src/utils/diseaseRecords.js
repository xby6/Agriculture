const recordColumns = [
  ['taskId', '任务编号'],
  ['date', '调查日期'],
  ['base', '基地'],
  ['field', '地块'],
  ['disease', '病害类型'],
  ['detectionCount', '检测目标数'],
  ['confidence', '最高置信度'],
  ['di', '病情指数 DI'],
  ['risk', '风险等级'],
  ['source', '数据来源'],
  ['operator', '调查人员'],
  ['note', '处理状态']
]

export function filterDiseaseRecords(records, filters = {}) {
  const keyword = String(filters.keyword || '').trim().toLowerCase()
  const [start, end] = filters.dateRange || []
  return records.filter(record => {
    const date = String(record.date || '').slice(0, 10)
    if (start && (!/^\d{4}-\d{2}-\d{2}$/.test(date) || date < start || date > end)) return false
    if (filters.disease && !String(record.disease || '').split('、').includes(filters.disease)) return false
    return !keyword || ['taskId', 'date', 'base', 'field', 'disease', 'source', 'operator', 'note']
      .some(key => String(record[key] ?? '').toLowerCase().includes(keyword))
  })
}

function csvCell(value) {
  let text = String(value ?? '')
  // Keep user-provided text as text when opened in Excel or another spreadsheet.
  if (/^[\s\uFEFF]*[=+\-@]/.test(text)) text = `'${text}`
  return `"${text.replace(/"/g, '""')}"`
}

export function diseaseRecordsCsv(records) {
  const rows = [recordColumns.map(([, label]) => label)]
  records.forEach(record => rows.push(recordColumns.map(([key]) => record[key])))
  // UTF-8 BOM preserves Chinese headers in Excel; CRLF is compatible with CSV readers.
  return '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n') + '\r\n'
}

export async function fetchDiseaseTasks(fetchPage) {
  const tasks = new Map()
  const pageSize = 100
  for (let pageNum = 1; ; pageNum += 1) {
    const response = await fetchPage({ pageNum, pageSize, remark: '水稻病害检测页面提交' })
    const page = Array.isArray(response?.rows) ? response : response?.data || response
    const rows = Array.isArray(page?.rows) ? page.rows : Array.isArray(page) ? page : []
    let added = 0
    rows.forEach(task => {
      if (!tasks.has(task.id)) added += 1
      tasks.set(task.id, task)
    })
    const hasNext = page?.hasNext ?? page?.has_next
    const total = Number(page?.total)
    if (!rows.length || hasNext === false || (Number.isFinite(total) && pageNum * pageSize >= total)) break
    if (hasNext == null && !Number.isFinite(total) && rows.length < pageSize) break
    if (!added) throw new Error('任务接口未返回下一页记录，请稍后重试')
  }
  return [...tasks.values()].filter(task => (
    String(task.remark || '').includes('水稻病害检测页面提交') && Number(task.result) > 0
  ))
}
