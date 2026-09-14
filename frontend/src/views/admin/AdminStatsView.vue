<script setup lang="ts">
/**
 * 数据统计：核心指标卡 + ECharts 分类分布图。
 */
import { onMounted, onBeforeUnmount, ref } from 'vue'
import * as echarts from 'echarts'

import { getAdminStats } from '@/api'
import type { AdminStats } from '@/types/api'

const loading = ref(false)
const stats = ref<AdminStats | null>(null)

const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

type MetricKey =
  | 'total_users'
  | 'total_products'
  | 'total_orders'
  | 'total_amount'
  | 'pending_products'
  | 'today_new_users'
  | 'today_new_products'
  | 'today_new_orders'

interface MetricCard {
  key: MetricKey
  label: string
  icon: string
  color: string
  isMoney?: boolean
}

const METRIC_CARDS: MetricCard[] = [
  { key: 'total_users', label: '总用户数', icon: 'User', color: '#409eff' },
  { key: 'total_products', label: '总商品数', icon: 'Goods', color: '#67c23a' },
  { key: 'total_orders', label: '总订单数', icon: 'Tickets', color: '#e6a23c' },
  { key: 'total_amount', label: '累计成交额', icon: 'Money', color: '#f56c6c', isMoney: true },
  { key: 'pending_products', label: '待审核商品', icon: 'Clock', color: '#e6a23c' },
  { key: 'today_new_users', label: '今日新增用户', icon: 'UserFilled', color: '#409eff' },
  { key: 'today_new_products', label: '今日新增商品', icon: 'GoodsFilled', color: '#67c23a' },
  { key: 'today_new_orders', label: '今日新增订单', icon: 'Tickets', color: '#e6a23c' },
]

function metricValue(key: MetricKey): string | number {
  const s = stats.value
  if (!s) return 0
  if (key === 'total_amount') return s.total_amount as string
  return s[key] as number
}

function renderChart(): void {
  if (!chartEl.value) return
  const dist = stats.value?.category_dist ?? []
  chart = echarts.init(chartEl.value)
  chart.setOption({
    color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#9a7bd8', '#26c6da', '#ffaaa5'],
    tooltip: { trigger: 'item', formatter: '{b}<br/>{c} 件（{d}%）' },
    legend: { orient: 'vertical', left: 'left', top: 'middle' },
    series: [
      {
        name: '分类分布',
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['58%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b}: {c}' },
        emphasis: {
          label: { show: true, fontWeight: 'bold' },
        },
        data: dist.map((d) => ({ name: d.name, value: d.cnt })),
      },
    ],
  })
}

function resizeChart(): void {
  chart?.resize()
}

async function loadStats(): Promise<void> {
  loading.value = true
  try {
    stats.value = await getAdminStats()
  } catch {
    stats.value = null
  } finally {
    loading.value = false
  }
  renderChart()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="admin-stats" v-loading="loading">
    <div class="metric-grid">
      <el-card v-for="m in METRIC_CARDS" :key="m.key" shadow="hover" class="metric-card">
        <div class="metric-inner">
          <el-icon :size="30" :style="{ color: m.color }" class="metric-icon">
            <!-- 动态图标 -->
            <component :is="m.icon" />
          </el-icon>
          <div class="metric-text">
            <div class="metric-value">{{ m.isMoney ? `¥${metricValue(m.key)}` : metricValue(m.key) }}</div>
            <div class="metric-label">{{ m.label }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <el-card shadow="never" class="chart-card">
      <template #header>
        <span class="card-header-title">商品分类分布</span>
      </template>
      <div v-if="stats && stats.category_dist.length > 0" ref="chartEl" class="chart-box" />
      <el-empty v-else description="暂无商品数据，图表将在有商品后展示" :image-size="80" />
    </el-card>
  </div>
</template>

<style scoped>
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.metric-inner {
  display: flex;
  align-items: center;
  gap: 14px;
}

.metric-icon {
  flex-shrink: 0;
}

.metric-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.card-header-title {
  font-weight: 600;
}

.chart-box {
  height: 380px;
  width: 100%;
}

@media (max-width: 1100px) {
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 620px) {
  .metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>