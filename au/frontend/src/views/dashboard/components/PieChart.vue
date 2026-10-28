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
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '分布统计',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: props.data
      }
    ],
    color: ['#2f7d4a', '#6fae7c', '#d7a12e', '#d95d56', '#5ea98a', '#4f9a5a', '#d28736', '#8b77b5', '#c56f88']
  }
  
  chart.value.setOption(option)
}
</script>
