<script setup lang="ts">
/**
 * 首页：商品列表（搜索 / 分类 / 成色 / 价格区间 / 校区 / 排序 / 分页）。
 * 筛选条件与 URL query 同步，便于分享和刷新后保留状态。
 */
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getCategories, getHotSearches, getProducts } from '@/api'
import { PRODUCT_CONDITIONS } from '@/constants/options'
import type { CategoryItem, HotSearchItem, ProductCondition, ProductListItem } from '@/types/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const products = ref<ProductListItem[]>([])
const total = ref(0)
const categories = ref<CategoryItem[]>([])
const hotSearches = ref<HotSearchItem[]>([])

/** 筛选条件（与 URL query 同步） */
const query = reactive({
  page: 1,
  search: '',
  category: '' as number | '',
  condition: '',
  min_price: '' as number | '',
  max_price: '' as number | '',
  ordering: '-created_at',
})

/** 首页轮播/横幅文案（无独立 banner 需求，展示简洁运营栏） */
const banners = [
  { title: '让闲置流动起来', sub: '同校当面交易 · 安全便捷', color: '#409eff' },
]

// ---------------- 数据加载 ----------------
async function loadProducts(): Promise<void> {
  loading.value = true
  try {
    const data = await getProducts({
      page: query.page,
      category: query.category || undefined,
      condition: (query.condition || undefined) as ProductCondition | undefined,
      min_price: query.min_price || undefined,
      max_price: query.max_price || undefined,
      search: query.search || undefined,
      ordering: query.ordering,
    })
    products.value = data.results
    total.value = data.count
  } finally {
    loading.value = false
  }
}

/** 条件变更：重置到第一页并刷新 URL */
function applyFilters(resetPage = true): void {
  if (resetPage) query.page = 1
  syncUrl()
}

/** 将当前条件写入 URL query（触发下方 watch 重新加载） */
function syncUrl(): void {
  const q: Record<string, string> = {}
  if (query.page > 1) q.page = String(query.page)
  if (query.search) q.search = query.search
  if (query.category !== '') q.category = String(query.category)
  if (query.condition) q.condition = query.condition
  if (query.min_price !== '') q.min_price = String(query.min_price)
  if (query.max_price !== '') q.max_price = String(query.max_price)
  if (query.ordering !== '-created_at') q.ordering = query.ordering
  router.replace({ path: '/', query: q })
}

/** URL query -> 本地条件（页面刷新 / 外部跳入） */
function applyUrlQuery(): void {
  const q = route.query
  query.page = q.page ? Number(q.page) || 1 : 1
  query.search = typeof q.search === 'string' ? q.search : ''
  query.category = q.category ? Number(q.category) : ''
  query.condition = typeof q.condition === 'string' ? q.condition : ''
  query.min_price = q.min_price ? Number(q.min_price) : ''
  query.max_price = q.max_price ? Number(q.max_price) : ''
  query.ordering =
    typeof q.ordering === 'string' &&
    ['-price', 'price', '-created_at', '-view_count', '-favorite_count'].includes(q.ordering)
      ? q.ordering
      : '-created_at'
}

/** 点击热门搜索关键词 */
function pickHotSearch(kw: string): void {
  query.search = kw
  applyFilters()
}

/** 清空全部筛选 */
function resetFilters(): void {
  query.search = ''
  query.category = ''
  query.condition = ''
  query.min_price = ''
  query.max_price = ''
  query.ordering = '-created_at'
  applyFilters()
}

/** URL 变化时重新加载（包含本地 applyFilters -> syncUrl 的回流） */
watch(
  () => route.query,
  () => {
    applyUrlQuery()
    loadProducts()
  },
)

onMounted(async () => {
  applyUrlQuery()
  // 分类与热门搜索只加载一次
  try {
    categories.value = await getCategories()
  } catch {
    categories.value = []
  }
  try {
    hotSearches.value = await getHotSearches()
  } catch {
    hotSearches.value = []
  }
  await loadProducts()
})
</script>

<template>
  <div class="page-container home-page">
    <!-- 顶部搜索区 -->
    <el-card shadow="never" class="search-card">
      <div class="banner" v-for="b in banners" :key="b.title">
        <div class="banner-title">{{ b.title }}</div>
        <div class="banner-sub">{{ b.sub }}</div>
      </div>
      <div class="search-row">
        <el-input
          v-model="query.search"
          placeholder="搜索标题 / 描述 / 校区 / 交易地点"
          clearable
          size="large"
          class="search-input"
          @keyup.enter="applyFilters()"
          @clear="applyFilters()"
        >
          <template #append>
            <el-button @click="applyFilters()">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
      <div v-if="hotSearches.length" class="hot-row">
        <span class="hot-label">热门搜索：</span>
        <el-tag
          v-for="item in hotSearches"
          :key="item.keyword"
          class="hot-tag"
          type="info"
          effect="plain"
          @click="pickHotSearch(item.keyword)"
        >
          {{ item.keyword }}
        </el-tag>
      </div>
    </el-card>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-select v-model="query.category" placeholder="全部分类" clearable class="filter-item" @change="applyFilters()">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="query.condition" placeholder="全部成色" clearable class="filter-item" @change="applyFilters()">
          <el-option v-for="c in PRODUCT_CONDITIONS" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
        <div class="price-range">
          <el-input-number
            v-model="query.min_price"
            :min="0"
            :controls="false"
            placeholder="最低价"
            class="price-input"
          />
          <span class="price-sep">-</span>
          <el-input-number
            v-model="query.max_price"
            :min="0"
            :controls="false"
            placeholder="最高价"
            class="price-input"
          />
          <el-button size="small" @click="applyFilters()">确定</el-button>
        </div>
        <el-select v-model="query.ordering" class="filter-item order-select" @change="applyFilters()">
          <el-option label="最新发布" value="-created_at" />
          <el-option label="价格从低到高" value="price" />
          <el-option label="价格从高到低" value="-price" />
          <el-option label="浏览最多" value="-view_count" />
          <el-option label="收藏最多" value="-favorite_count" />
        </el-select>
        <el-button text type="primary" class="reset-btn" @click="resetFilters()">重置</el-button>
      </div>
    </el-card>

    <!-- 商品网格 -->
    <div v-loading="loading" class="grid-wrap">
      <el-empty v-if="!loading && products.length === 0" description="没有找到符合条件的商品" />
      <div v-else class="product-grid">
        <el-card
          v-for="p in products"
          :key="p.id"
          shadow="hover"
          class="product-card"
          @click="router.push(`/products/${p.id}`)"
        >
          <img
            v-if="p.cover"
            :src="p.cover"
            :alt="p.title"
            class="product-cover"
            loading="lazy"
          />
          <div v-else class="product-cover no-cover">
            <el-icon :size="40"><Picture /></el-icon>
          </div>
          <div class="card-body">
            <div class="card-title ellipsis">{{ p.title }}</div>
            <div class="card-price">
              <span class="price">¥{{ p.price }}</span>
              <span v-if="p.original_price" class="origin">¥{{ p.original_price }}</span>
            </div>
            <div class="card-tags">
              <el-tag size="small" type="info" effect="plain">{{ p.condition_label }}</el-tag>
              <el-tag v-if="p.category_name" size="small" type="success" effect="plain">
                {{ p.category_name }}
              </el-tag>
            </div>
            <div class="card-meta">
              <span class="meta-item"><el-icon><Location /></el-icon>{{ p.campus || '未填写校区' }}</span>
              <span class="meta-item"><el-icon><View /></el-icon>{{ p.view_count }}</span>
              <span class="meta-item"><el-icon><Star /></el-icon>{{ p.favorite_count }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination">
      <el-pagination
        v-model:current-page="query.page"
        :page-size="10"
        :total="total"
        layout="prev, pager, next, jumper, total"
        background
        @current-change="syncUrl"
      />
    </div>
  </div>
</template>

<style scoped>
.search-card {
  margin-bottom: 16px;
  background: linear-gradient(135deg, #ecf5ff 0%, #ffffff 100%);
}

.banner {
  margin-bottom: 16px;
}

.banner-title {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
}

.banner-sub {
  margin-top: 6px;
  font-size: 14px;
  color: #909399;
}

.search-row {
  display: flex;
  justify-content: center;
}

.search-input {
  max-width: 640px;
}

.hot-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.hot-label {
  font-size: 13px;
  color: #909399;
}

.hot-tag {
  cursor: pointer;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-item {
  width: 150px;
}

.order-select {
  width: 140px;
}

.price-range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.price-input {
  width: 100px;
}

.price-input :deep(.el-input__wrapper) {
  padding: 0 8px;
}

.price-sep {
  color: #909399;
}

.reset-btn {
  margin-left: auto;
}

.grid-wrap {
  min-height: 300px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(215px, 1fr));
  gap: 16px;
}

.product-card {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.product-card:hover {
  transform: translateY(-3px);
}

.no-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
}

.card-body {
  padding: 10px 4px 2px;
}

.card-title {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
  min-height: 40px;
}

.card-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 6px 0;
}

.price {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

.origin {
  font-size: 12px;
  color: #c0c4cc;
  text-decoration: line-through;
}

.card-tags {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  min-height: 24px;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #909399;
  font-size: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}
</style>