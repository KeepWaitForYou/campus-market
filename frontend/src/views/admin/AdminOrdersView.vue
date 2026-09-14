<script setup lang="ts">
/**
 * 订单管理：查看全部订单，支持状态 / 角色 / 关键词筛选与排序。
 */
import { onMounted, ref } from 'vue'

import { getAdminOrders } from '@/api'
import type { OrderItem, OrderStatus } from '@/types/api'

const loading = ref(false)
const list = ref<OrderItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

/** 状态筛选（''=全部） */
const activeStatus = ref<'' | OrderStatus>('')
const keyword = ref('')
/** role：bought=普通买家视角订单 / sold=普通卖家视角订单 */
const role = ref<'' | 'bought' | 'sold'>('')
const sort = ref('-created_at')

const STATUS_TABS: { label: string; value: '' | OrderStatus }[] = [
  { label: '全部', value: '' },
  { label: '待支付', value: 'pending' },
  { label: '已支付', value: 'paid' },
  { label: '已发货', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

const STATUS_TAG: Record<OrderStatus, 'warning' | 'primary' | 'info' | 'success' | 'danger'> = {
  pending: 'warning',
  paid: 'primary',
  shipped: 'info',
  completed: 'success',
  cancelled: 'danger',
}

/** el-table 的 row 为 any，封装类型安全的取色函数 */
function statusTag(s: OrderStatus): 'warning' | 'primary' | 'info' | 'success' | 'danger' {
  return STATUS_TAG[s] ?? 'info'
}

/** 详情对话框 */
const detailVisible = ref(false)
const detail = ref<OrderItem | null>(null)

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getAdminOrders({
      page: page.value,
      status: activeStatus.value || undefined,
      role: role.value || undefined,
      search: keyword.value.trim() || undefined,
      sort: sort.value,
    })
    list.value = data.results
    total.value = data.count
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function handleParamsChange(): void {
  page.value = 1
  fetchList()
}

function formatTime(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString('zh-CN') : '—'
}

function openDetail(o: OrderItem): void {
  detail.value = o
  detailVisible.value = true
}
</script>

<template>
  <div class="admin-orders">
    <el-card shadow="never">
      <template #header>
        <span class="card-header-title">订单管理</span>
      </template>

      <el-tabs v-model="activeStatus" @tab-change="handleParamsChange">
        <el-tab-pane
          v-for="t in STATUS_TABS"
          :key="t.value"
          :label="t.label"
          :name="t.value"
        />
      </el-tabs>

      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="搜索订单号 / 买家用户名 / 卖家用户名"
          clearable
          class="search-input"
          @keyup.enter="handleParamsChange"
          @clear="handleParamsChange"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="role" placeholder="交易方向" clearable class="filter-item" @change="handleParamsChange">
          <el-option label="买家视角订单" value="bought" />
          <el-option label="卖家视角订单" value="sold" />
        </el-select>
        <el-select v-model="sort" class="filter-item" @change="handleParamsChange">
          <el-option label="最新下单" value="-created_at" />
          <el-option label="成交额从高到低" value="-amount" />
          <el-option label="成交额从低到高" value="amount" />
        </el-select>
      </div>

      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column label="订单号" width="200">
          <template #default="{ row }">
            <span class="order-no">{{ row.order_no }}</span>
          </template>
        </el-table-column>
        <el-table-column label="商品" min-width="180">
          <template #default="{ row }">
            <div class="product-cell">
              <el-image
                v-if="row.product.cover"
                :src="row.product.cover"
                fit="cover"
                class="product-cover"
                :preview-src-list="[row.product.cover]"
                preview-teleported
              />
              <div v-else class="product-cover no-cover">
                <el-icon :size="18"><Picture /></el-icon>
              </div>
              <span class="product-title ellipsis">{{ row.product.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="买家" width="120">
          <template #default="{ row }">
            <div class="person">
              <span class="person-name">{{ row.buyer.nickname || row.buyer.username }}</span>
              <span class="person-sub">@{{ row.buyer.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="卖家" width="120">
          <template #default="{ row }">
            <div class="person">
              <span class="person-name">{{ row.seller.nickname || row.seller.username }}</span>
              <span class="person-sub">@{{ row.seller.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">
            <span class="amount">¥{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > 0" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="PAGE_SIZE"
          :total="total"
          layout="prev, pager, next, total"
          background
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 订单详情 -->
    <el-dialog v-model="detailVisible" title="订单详情" width="560px">
      <div v-if="detail" class="detail-body">
        <div class="detail-head">
          <el-image
            v-if="detail.product.cover"
            :src="detail.product.cover"
            fit="cover"
            class="detail-cover"
          />
          <div v-else class="detail-cover no-cover">
            <el-icon :size="30"><Picture /></el-icon>
          </div>
          <div class="detail-head-main">
            <div class="detail-title">{{ detail.product.title }}</div>
            <div class="detail-order-no">订单号：{{ detail.order_no }}</div>
            <div class="detail-price">¥{{ detail.amount }}</div>
          </div>
        </div>

        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="状态">
            <el-tag :type="statusTag(detail.status)" size="small">{{ detail.status_label }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="下单时间">{{ formatTime(detail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="买家">{{ detail.buyer.nickname || detail.buyer.username }}</el-descriptions-item>
          <el-descriptions-item label="卖家">{{ detail.seller.nickname || detail.seller.username }}</el-descriptions-item>
          <el-descriptions-item label="支付时间">{{ formatTime(detail.pay_time) }}</el-descriptions-item>
          <el-descriptions-item label="发货时间">{{ formatTime(detail.ship_time) }}</el-descriptions-item>
          <el-descriptions-item label="完成时间">{{ formatTime(detail.finish_time) }}</el-descriptions-item>
          <el-descriptions-item label="取消时间">{{ formatTime(detail.cancel_time) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detail.remark || '无' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.card-header-title {
  font-weight: 600;
}

.filter-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
}

.filter-item {
  width: 150px;
}

.order-no {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
  color: #606266;
}

.product-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.product-cover {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: #f5f7fa;
  flex-shrink: 0;
  overflow: hidden;
}

.no-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.product-title {
  max-width: 160px;
}

.person-name {
  display: block;
  font-weight: 500;
}

.person-sub {
  font-size: 12px;
  color: #909399;
}

.amount {
  font-weight: 600;
  color: #f56c6c;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.detail-head {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-cover {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  background: #f5f7fa;
  flex-shrink: 0;
  overflow: hidden;
}

.detail-head-main {
  flex: 1;
  min-width: 0;
}

.detail-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 6px;
}

.detail-order-no {
  font-size: 12px;
  color: #909399;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  margin-bottom: 8px;
}

.detail-price {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}
</style>