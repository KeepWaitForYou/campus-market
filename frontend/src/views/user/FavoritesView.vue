<script setup lang="ts">
/**
 * 我的收藏：收藏商品列表（分页），支持取消收藏、跳转详情。
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getFavorites, unfavoriteProduct } from '@/api'
import { PRODUCT_STATUS_LABELS } from '@/constants/options'
import type { FavoriteItem } from '@/types/api'

const router = useRouter()

const loading = ref(false)
const list = ref<FavoriteItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getFavorites(page.value)
    list.value = data.results
    total.value = data.count
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** 商品已售出/下架时提示 */
function productSoldOut(p: FavoriteItem['product']): boolean {
  return p.status !== 'on_sale'
}

function statusText(p: FavoriteItem['product']): string {
  return PRODUCT_STATUS_LABELS[p.status] || p.status
}

async function handleUnfavorite(item: FavoriteItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定取消收藏「${item.product.title}」吗？`, '取消收藏', { type: 'warning' })
  } catch {
    return
  }
  try {
    await unfavoriteProduct(item.product.id)
    ElMessage.success('已取消收藏')
    // 当前页删空后回退一页
    if (list.value.length === 1 && page.value > 1) {
      page.value -= 1
    }
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="favorites-wrap">
    <el-card shadow="never">
      <template #header>
        <div class="head-row">
          <span class="card-header-title">我的收藏</span>
          <span class="head-count">共 {{ total }} 件</span>
        </div>
      </template>

      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!loading && list.length === 0" description="还没有收藏任何商品" />

        <div v-else class="fav-list">
          <div v-for="item in list" :key="item.id" class="fav-item">
            <el-image
              v-if="item.product.cover"
              :src="item.product.cover"
              fit="cover"
              class="item-cover"
              :preview-src-list="[item.product.cover]"
              preview-teleported
            />
            <div v-else class="item-cover no-cover">
              <el-icon :size="28"><Picture /></el-icon>
            </div>

            <div class="item-main" @click="router.push(`/products/${item.product.id}`)">
              <div class="item-title ellipsis">{{ item.product.title }}</div>
              <div class="item-sub">
                <el-tag
                  size="small"
                  :type="productSoldOut(item.product) ? 'info' : 'success'"
                  effect="plain"
                >
                  {{ statusText(item.product) }}
                </el-tag>
                <span class="item-meta">
                  {{ item.product.condition_label }} · {{ item.product.campus || '校区未填' }}
                </span>
              </div>
              <div class="item-meta2">
                收藏于 {{ new Date(item.created_at).toLocaleDateString('zh-CN') }}
              </div>
            </div>

            <div class="item-price">
              <span class="price">¥{{ item.product.price }}</span>
            </div>

            <div class="item-actions">
              <el-button
                v-if="!productSoldOut(item.product)"
                size="small"
                type="primary"
                plain
                @click="router.push(`/products/${item.product.id}`)"
              >
                去看看
              </el-button>
              <el-button size="small" type="danger" plain @click="handleUnfavorite(item)">
                取消收藏
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
.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-title {
  font-weight: 600;
}

.head-count {
  font-size: 13px;
  color: #909399;
}

.list-wrap {
  min-height: 200px;
}

.fav-list {
  display: flex;
  flex-direction: column;
}

.fav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
}

.fav-item:last-child {
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

.item-meta {
  font-size: 12px;
  color: #909399;
}

.item-meta2 {
  margin-top: 4px;
  font-size: 12px;
  color: #c0c4cc;
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

@media (max-width: 720px) {
  .fav-item {
    flex-wrap: wrap;
  }
}
</style>