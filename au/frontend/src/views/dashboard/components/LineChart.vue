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
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '趋势',
        type: 'line',
        stack: 'Total',
        smooth: true,
        lineStyle: {
          width: 3
        },
        showSymbol: false,
        areaStyle: {
          opacity: 0.8,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(79, 154, 90, 0.58)'
            },
            {
              offset: 1,
              color: 'rgba(94, 169, 138, 0.10)'
            }
          ])
        },
        emphasis: {
          focus: 'series'
        },
        data: seriesData
      }
    ]
  }
  
  chart.value.setOption(option)
}
</script>
