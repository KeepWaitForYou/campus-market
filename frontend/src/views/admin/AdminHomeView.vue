<script setup lang="ts">
/**
 * 管理后台首页：核心指标一览 + 待办提醒 + 快捷导航。
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getAdminStats } from '@/api'
import type { AdminStats } from '@/types/api'

const router = useRouter()

const loading = ref(true)
const stats = ref<AdminStats | null>(null)

/** 指标卡配置：label / 字段 / 前缀 / 颜色 */
const metricCards = [
  { label: '平台用户', field: 'total_users' as const, color: '#409eff', suffix: '' },
  { label: '在库商品', field: 'total_products' as const, color: '#67c23a', suffix: '' },
  { label: '累计订单', field: 'total_orders' as const, color: '#e6a23c', suffix: '' },
  { label: '平台成交额', field: 'total_amount' as const, color: '#f56c6c', prefix: '¥' },
  { label: '待审核商品', field: 'pending_products' as const, color: '#f56c6c', suffix: '' },
  { label: '今日新增用户', field: 'today_new_users' as const, color: '#409eff', suffix: '' },
  { label: '今日新增商品', field: 'today_new_products' as const, color: '#67c23a', suffix: '' },
  { label: '今日新增订单', field: 'today_new_orders' as const, color: '#e6a23c', suffix: '' },
]

/** 快捷入口 */
const quickLinks = [
  { title: '商品审核', desc: '处理待审核商品', path: '/admin/products', icon: 'Stamp', color: '#409eff' },
  { title: '数据统计', desc: '平台运行数据总览', path: '/admin/stats', icon: 'DataAnalysis', color: '#67c23a' },
  { title: '分类管理', desc: '新增 / 编辑 / 启停分类', path: '/admin/categories', icon: 'Collection', color: '#e6a23c' },
  { title: '用户管理', desc: '查看与禁用用户', path: '/admin/users', icon: 'UserFilled', color: '#f56c6c' },
  { title: '订单管理', desc: '查看全部订单', path: '/admin/orders', icon: 'Tickets', color: '#909399' },
]

onMounted(async () => {
  try {
    stats.value = await getAdminStats()
  } catch {
    stats.value = null
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="admin-home">
    <!-- 待办提醒 -->
    <el-alert
      v-if="stats && stats.pending_products > 0"
      type="warning"
      :closable="false"
      class="todo-alert"
      show-icon
    >
      <template #title>
        有
        <el-link type="warning" @click="router.push('/admin/products')">
          {{ stats.pending_products }} 件商品
        </el-link>
        等待审核，请及时处理。
      </template>
    </el-alert>

    <!-- 指标卡 -->
    <div v-loading="loading" class="metric-grid">
      <el-card v-for="m in metricCards" :key="m.label" shadow="hover" class="metric-card">
        <div class="metric-label">{{ m.label }}</div>
        <div class="metric-value" :style="{ color: m.color }">
          <span v-if="m.prefix" class="metric-prefix">{{ m.prefix }}</span>
          {{ stats ? String(stats[m.field]) : '--' }}
          <span v-if="m.suffix" class="metric-suffix">{{ m.suffix }}</span>
        </div>
      </el-card>
    </div>

    <!-- 快捷导航 -->
    <el-card shadow="never" class="quick-card">
      <template #header>
        <span class="card-header-title">快捷入口</span>
      </template>
      <div class="quick-grid">
        <div
          v-for="q in quickLinks"
          :key="q.path"
          class="quick-item"
          @click="router.push(q.path)"
        >
          <div class="quick-icon" :style="{ background: q.color }">
            <el-icon :size="22"><component :is="q.icon" /></el-icon>
          </div>
          <div class="quick-text">
            <div class="quick-title">{{ q.title }}</div>
            <div class="quick-desc">{{ q.desc }}</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.todo-alert {
  margin-bottom: 16px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
  min-height: 100px;
}

.metric-card {
  text-align: center;
}

.metric-label {
  font-size: 13px;
  color: #909399;
}

.metric-value {
  margin-top: 10px;
  font-size: 28px;
  font-weight: 700;
}

.metric-prefix {
  font-size: 16px;
  font-weight: 400;
}

.metric-suffix {
  font-size: 13px;
  font-weight: 400;
}

.quick-card {
  margin-bottom: 16px;
}

.card-header-title {
  font-weight: 600;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.quick-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.quick-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.quick-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.quick-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>