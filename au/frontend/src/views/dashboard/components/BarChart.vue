<template>
  <div :style="{ height: height, width: width }" />
</template>

<script setup>
import * as echarts from 'echarts'
import { debounce } from '@/utils'

const props = defineProps({
  data: {
    type: Array,
    required: true
  },
  height: {
    type: String,
    default: '300px'
  },
  width: {
    type: String,
    default: '100%'
  }
})

const chart = ref(null)
const { width, height } = toRefs(props)

// 监听数据变化
watch(() => props.data, () => {
  setOptions()
})

// 监听窗口大小变化
const resizeHandler = debounce(() => {
  if (chart.value) {
    chart.value.resize()
  }
}, 100)

onMounted(() => {
  initChart()
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  if (!chart.value) {
    return
  }
  window.removeEventListener('resize', resizeHandler)
  chart.value.dispose()
  chart.value = null
})

function initChart() {
  const chartDom = document.querySelector('.dashboard-container .chart-box')
  if (!chartDom) return
  
  chart.value = echarts.init(chartDom)
  setOptions()
}

function setOptions() {
  if (!chart.value) {
    return
  }
  
  const xAxisData = props.data.map(item => item.name)
  const seriesData = props.data.map(item => item.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: xAxisData,
        axisTick: {
          alignWithLabel: true
        }
      }
    ],
    yAxis: [
      {
        type: 'value'
      }
    ],
    series: [
      {
        name: '数量',
        type: 'bar',
        barWidth: '60%',
        data: seriesData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#7eb78a' },
            { offset: 0.5, color: '#4f9a5a' },
            { offset: 1, color: '#2f7d4a' }
          ])
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#2f7d4a' },
              { offset: 0.7, color: '#4f9a5a' },
              { offset: 1, color: '#97c39f' }
            ])
          }
        }
      }
    ]
  }
  
  chart.value.setOption(option)
}
</script>
