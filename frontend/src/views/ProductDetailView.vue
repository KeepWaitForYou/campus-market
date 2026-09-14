<script setup lang="ts">
/**
 * 商品详情页：图片轮播、卖家信息、收藏、立即购买（创建订单）。
 * 游客可浏览；购买/收藏需登录；卖家本人不可购买自己的商品。
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createOrder, favoriteProduct, getProduct, unfavoriteProduct } from '@/api'
import { useUserStore } from '@/stores/user'
import type { ProductDetail } from '@/types/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const productId = computed(() => Number(route.params.id))

const loading = ref(true)
const product = ref<ProductDetail | null>(null)

/** 下单对话框 */
const orderDialogVisible = ref(false)
const orderRemark = ref('')
const orderSubmitting = ref(false)

/** 当前用户是否为卖家本人 */
const isOwner = computed(
  () => userStore.profile?.id != null && product.value?.seller.id === userStore.profile.id,
)

async function loadProduct(): Promise<void> {
  loading.value = true
  try {
    product.value = await getProduct(productId.value)
  } finally {
    loading.value = false
  }
}

// ---------------- 收藏 ----------------
async function toggleFavorite(): Promise<void> {
  if (!product.value) return
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录再收藏商品')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  try {
    const data = product.value.is_favorite
      ? await unfavoriteProduct(product.value.id)
      : await favoriteProduct(product.value.id)
    product.value.is_favorite = data.favorite
    product.value.favorite_count = data.favorite_count
  } catch {
    /* 请求层已统一提示 */
  }
}

// ---------------- 立即购买 ----------------
function openOrderDialog(): void {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后再购买')
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  if (isOwner.value) {
    ElMessage.info('不能购买自己发布的商品')
    return
  }
  orderRemark.value = ''
  orderDialogVisible.value = true
}

async function submitOrder(): Promise<void> {
  if (!product.value) return
  orderSubmitting.value = true
  try {
    const order = await createOrder({
      product: product.value.id,
      remark: orderRemark.value || undefined,
    })
    orderDialogVisible.value = false
    ElMessage.success('下单成功，请尽快完成支付（30 分钟内未支付将自动取消）')
    router.push({ name: 'user-orders', query: { tab: 'bought' } })
    // 下单成功后商品会被锁定（待支付），重新拉取详情展示最新状态
    loadProduct()
    // order 变量仅用于避免未使用告警
    void order
  } catch {
    /* 请求层已统一提示 */
  } finally {
    orderSubmitting.value = false
  }
}

// ---------------- 卖家其他商品 ----------------
onMounted(loadProduct)
</script>

<template>
  <div class="page-container detail-page">
    <div v-loading="loading" class="detail-wrap">
      <template v-if="product">
        <el-card shadow="never" class="detail-card">
          <div class="detail-main">
            <!-- 图片轮播 -->
            <div class="gallery">
              <el-carousel v-if="product.images.length" height="420px" :interval="4000" arrow="hover">
                <el-carousel-item v-for="img in product.images" :key="img.id">
                  <img :src="img.url" :alt="product.title" class="gallery-img" />
                </el-carousel-item>
              </el-carousel>
              <div v-else class="gallery-empty">
                <el-icon :size="56"><Picture /></el-icon>
                <p>暂无图片</p>
              </div>
            </div>

            <!-- 信息区 -->
            <div class="info">
              <div class="info-tags">
                <el-tag v-if="product.status !== 'on_sale'" :type="product.status === 'sold' ? 'info' : 'warning'">
                  {{ product.status_label }}
                </el-tag>
                <el-tag type="success" effect="plain">{{ product.condition_label }}</el-tag>
              </div>
              <h1 class="info-title">{{ product.title }}</h1>

              <div class="info-price">
                <span class="price">¥{{ product.price }}</span>
                <span v-if="product.original_price" class="origin">¥{{ product.original_price }}</span>
              </div>

              <el-descriptions :column="2" border class="info-desc">
                <el-descriptions-item label="分类">{{ product.category_name }}</el-descriptions-item>
                <el-descriptions-item label="成色">{{ product.condition_label }}</el-descriptions-item>
                <el-descriptions-item label="校区">{{ product.campus || '未填写' }}</el-descriptions-item>
                <el-descriptions-item label="交易地点">{{ product.location || '未填写' }}</el-descriptions-item>
                <el-descriptions-item label="发布时间">
                  {{ new Date(product.created_at).toLocaleString('zh-CN') }}
                </el-descriptions-item>
                <el-descriptions-item label="浏览次数">
                  <el-icon><View /></el-icon> {{ product.view_count }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 卖家信息 -->
              <div class="seller-row">
                <el-avatar :size="44" :src="product.seller.avatar_url || undefined">
                  {{ (product.seller.nickname || product.seller.username).slice(0, 1) }}
                </el-avatar>
                <div class="seller-info">
                  <div class="seller-name">
                    {{ product.seller.nickname || product.seller.username }}
                  </div>
                  <div class="seller-sub">@{{ product.seller.username }}</div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="action-row">
                <el-button
                  size="large"
                  :type="product.is_favorite ? 'warning' : 'default'"
                  :plain="!product.is_favorite"
                  @click="toggleFavorite"
                >
                  <el-icon><StarFilled v-if="product.is_favorite" /><Star v-else /></el-icon>
                  {{ product.is_favorite ? '已收藏' : '收藏' }}
                  <span class="fav-count">{{ product.favorite_count }}</span>
                </el-button>
                <el-button
                  v-if="product.status === 'on_sale' && !isOwner"
                  size="large"
                  type="primary"
                  @click="openOrderDialog"
                >
                  <el-icon><ShoppingCart /></el-icon>
                  立即购买
                </el-button>
                <el-tag v-if="isOwner" type="info" size="large" effect="plain">这是我的商品</el-tag>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 商品描述 -->
        <el-card shadow="never" class="desc-card">
          <template #header>
            <span class="card-header-title">商品描述</span>
          </template>
          <p class="desc-text">{{ product.description || '卖家很懒，没有写描述~' }}</p>
        </el-card>
      </template>
    </div>

    <!-- 下单确认对话框 -->
    <el-dialog v-model="orderDialogVisible" title="确认下单" width="440px" :close-on-click-modal="false">
      <div v-if="product" class="order-dialog-body">
        <div class="order-product">
          <img v-if="product.cover" :src="product.cover" class="order-cover" :alt="product.title" />
          <div class="order-product-info">
            <div class="order-product-title ellipsis">{{ product.title }}</div>
            <div class="order-product-price">¥{{ product.price }}</div>
          </div>
        </div>
        <p class="order-tip">下单后请尽快支付，超过 30 分钟未支付系统将自动取消订单。</p>
        <el-input
          v-model="orderRemark"
          type="textarea"
          :rows="2"
          maxlength="200"
          show-word-limit
          placeholder="给卖家留言（选填）"
        />
      </div>
      <template #footer>
        <el-button @click="orderDialogVisible = false">再想想</el-button>
        <el-button type="primary" :loading="orderSubmitting" @click="submitOrder">
          确认下单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.detail-main {
  display: flex;
  gap: 24px;
}

.gallery {
  width: 440px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}

.gallery-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery-empty {
  height: 420px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c0c4cc;
  background: #f5f7fa;
}

.info {
  flex: 1;
  min-width: 0;
}

.info-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.info-title {
  margin: 0 0 12px;
  font-size: 22px;
  color: #303133;
  line-height: 1.4;
}

.info-price {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 16px;
}

.price {
  font-size: 28px;
  font-weight: 700;
  color: #f56c6c;
}

.origin {
  font-size: 14px;
  color: #c0c4cc;
  text-decoration: line-through;
}

.info-desc {
  margin-bottom: 16px;
}

.seller-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid #f0f2f5;
  border-bottom: 1px solid #f0f2f5;
}

.seller-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.seller-sub {
  font-size: 12px;
  color: #909399;
}

.action-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 18px;
}

.fav-count {
  margin-left: 4px;
  font-weight: 400;
  color: #909399;
}

.desc-card {
  margin-top: 16px;
}

.card-header-title {
  font-weight: 600;
}

.desc-text {
  margin: 0;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
}

.order-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-product {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.order-cover {
  width: 64px;
  height: 64px;
  border-radius: 6px;
  object-fit: cover;
  background: #e4e7ed;
}

.order-product-info {
  flex: 1;
  min-width: 0;
}

.order-product-title {
  font-size: 14px;
  color: #303133;
}

.order-product-price {
  margin-top: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.order-tip {
  margin: 0;
  font-size: 12px;
  color: #e6a23c;
}

@media (max-width: 900px) {
  .detail-main {
    flex-direction: column;
  }

  .gallery {
    width: 100%;
  }
}
</style>