<script setup lang="ts">
/**
 * 我的发布：展示当前用户发布的全部商品（含所有状态）。
 * 支持状态筛选、编辑 / 下架 / 删除操作。
 */
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteProduct, getProducts, offShelfProduct } from '@/api'
import { PRODUCT_STATUS_LABELS } from '@/constants/options'
import type { ProductListItem, ProductStatus } from '@/types/api'

const router = useRouter()

const loading = ref(false)
const list = ref<ProductListItem[]>([])
const total = ref(0)

/** 状态筛选：全部状态用空串 */
const statusFilter = ref('')
const page = ref(1)
const PAGE_SIZE = 10

const STATUS_TABS = [
  { label: '全部', value: '' },
  { label: '待审核', value: 'pending' },
  { label: '在售', value: 'on_sale' },
  { label: '已下架', value: 'off_shelf' },
  { label: '已售出', value: 'sold' },
  { label: '审核不通过', value: 'rejected' },
]

/** 状态展示标签类型 */
function statusTagType(status: ProductListItem['status']): 'warning' | 'success' | 'info' | 'danger' {
  switch (status) {
    case 'pending':
      return 'warning'
    case 'on_sale':
      return 'success'
    case 'sold':
      return 'info'
    case 'rejected':
      return 'danger'
    default:
      return 'info'
  }
}

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getProducts({
      page: page.value,
      page_size: PAGE_SIZE,
      mine: '1',
      status: (statusFilter.value || undefined) as ProductStatus | undefined,
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

function handleTabChange(): void {
  page.value = 1
  fetchList()
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleDateString('zh-CN')
}

/** 编辑：跳转发布页编辑模式 */
function goEdit(p: ProductListItem): void {
  router.push({ path: '/publish', query: { edit: String(p.id) } })
}

/** 下架（仅在售 / 待审核可操作） */
async function handleOffShelf(p: ProductListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定下架「${p.title}」吗？下架后首页将不再展示。`, '下架确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await offShelfProduct(p.id)
    ElMessage.success('商品已下架')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

/** 删除（待审核 / 已下架 / 审核不通过可删；涉及订单的商品后端会拒绝） */
async function handleDelete(p: ProductListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除「${p.title}」吗？删除后不可恢复。`,
      '删除确认',
      { type: 'warning', confirmButtonText: '删除', confirmButtonClass: 'el-button--danger' },
    )
  } catch {
    return
  }
  try {
    await deleteProduct(p.id)
    ElMessage.success('商品已删除')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

onMounted(fetchList)
watch(statusFilter, handleTabChange)
</script>

<template>
  <div class="products-wrap">
    <el-card shadow="never" class="head-card">
      <el-tabs v-model="statusFilter" @tab-change="handleTabChange">
        <el-tab-pane v-for="tab in STATUS_TABS" :key="tab.value" :label="tab.label" :name="tab.value" />
      </el-tabs>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!loading && list.length === 0" description="暂无符合条件的商品" />

        <div v-else class="product-list">
          <div v-for="p in list" :key="p.id" class="product-item">
            <el-image
              v-if="p.cover"
              :src="p.cover"
              fit="cover"
              class="item-cover"
              :preview-src-list="[p.cover]"
              preview-teleported
            />
            <div v-else class="item-cover no-cover">
              <el-icon :size="28"><Picture /></el-icon>
            </div>

            <div class="item-main" @click="router.push(`/products/${p.id}`)">
              <div class="item-title ellipsis">{{ p.title }}</div>
              <div class="item-sub">
                <el-tag size="small" :type="statusTagType(p.status)">
                  {{ PRODUCT_STATUS_LABELS[p.status] || p.status }}
                </el-tag>
                <span class="item-date">发布于 {{ formatTime(p.created_at) }}</span>
              </div>
            </div>

            <div class="item-stats">
              <span class="stat"><el-icon><View /></el-icon>{{ p.view_count }}</span>
              <span class="stat"><el-icon><Star /></el-icon>{{ p.favorite_count }}</span>
            </div>

            <div class="item-price">
              <span class="price">¥{{ p.price }}</span>
            </div>

            <div class="item-actions">
              <el-button
                v-if="['pending', 'on_sale', 'off_shelf', 'rejected'].includes(p.status)"
                size="small"
                @click="goEdit(p)"
              >
                编辑
              </el-button>
              <el-button
                v-if="['pending', 'on_sale'].includes(p.status)"
                size="small"
                type="warning"
                plain
                @click="handleOffShelf(p)"
              >
                下架
              </el-button>
              <el-button
                v-if="['pending', 'off_shelf', 'rejected'].includes(p.status)"
                size="small"
                type="danger"
                plain
                @click="handleDelete(p)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

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
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.head-card {
  margin-bottom: 16px;
}

.list-wrap {
  min-height: 200px;
}

.product-list {
  display: flex;
  flex-direction: column;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
}

.product-item:last-child {
  border-bottom: none;
}

.item-cover {
  width: 88px;
  height: 88px;
  border-radius: 8px;
  flex-shrink: 0;
  background: #f5f7fa;
  overflow: hidden;
}

.no-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.item-main {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.item-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.item-sub {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
}

.item-date {
  font-size: 12px;
  color: #909399;
}

.item-stats {
  display: flex;
  gap: 14px;
  color: #909399;
  font-size: 13px;
  flex-shrink: 0;
}

.stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.item-price {
  width: 90px;
  text-align: right;
  flex-shrink: 0;
}

.price {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.item-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>