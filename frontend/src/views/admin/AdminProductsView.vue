<script setup lang="ts">
/**
 * 商品审核：待审核商品列表，支持通过 / 驳回（填写原因）/ 违规下架。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { approveProduct, forbidProduct, getPendingProducts, rejectProduct } from '@/api'
import type { ProductListItem } from '@/types/api'

const loading = ref(false)
const list = ref<ProductListItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

/** 详情对话框 */
const detailVisible = ref(false)
const detail = ref<ProductListItem | null>(null)

/** 驳回对话框 */
const rejectVisible = ref(false)
const rejectTarget = ref<ProductListItem | null>(null)
const rejectReason = ref('')
const rejectSubmitting = ref(false)

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getPendingProducts(page.value)
    list.value = data.results
    total.value = data.count
  } catch {
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}

function showDetail(p: ProductListItem): void {
  detail.value = p
  detailVisible.value = true
}

// ---------------- 审核操作 ----------------
async function handleApprove(p: ProductListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `审核通过「${p.title}」？通过后将在首页公开展示。`,
      '审核通过',
      { type: 'success', confirmButtonText: '通过' },
    )
  } catch {
    return
  }
  try {
    await approveProduct(p.id)
    ElMessage.success('已通过审核，商品已上架')
    detailVisible.value = false
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

function openReject(p: ProductListItem): void {
  rejectTarget.value = p
  rejectReason.value = ''
  rejectVisible.value = true
}

async function submitReject(): Promise<void> {
  if (!rejectTarget.value) return
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请填写驳回原因，卖家将收到通知')
    return
  }
  rejectSubmitting.value = true
  try {
    await rejectProduct(rejectTarget.value.id, rejectReason.value.trim())
    ElMessage.success('已驳回该商品')
    rejectVisible.value = false
    detailVisible.value = false
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  } finally {
    rejectSubmitting.value = false
  }
}

async function handleForbid(p: ProductListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `强制下架「${p.title}」？将通知卖家商品因违规被下架。`,
      '违规下架',
      { type: 'warning', confirmButtonText: '下架' },
    )
  } catch {
    return
  }
  try {
    await forbidProduct(p.id)
    ElMessage.success('商品已强制下架')
    detailVisible.value = false
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="admin-products">
    <el-card shadow="never">
      <template #header>
        <div class="head-row">
          <span class="card-header-title">待审核商品</span>
          <el-tag type="warning" effect="plain">共 {{ total }} 件待处理</el-tag>
        </div>
      </template>

      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!loading && list.length === 0" description="暂无待审核商品，太棒了！" />

        <div v-else class="review-list">
          <div v-for="p in list" :key="p.id" class="review-item">
            <el-image
              v-if="p.cover"
              :src="p.cover"
              fit="cover"
              class="item-cover"
              :preview-src-list="[p.cover]"
              preview-teleported
            />
            <div v-else class="item-cover no-cover">
              <el-icon :size="26"><Picture /></el-icon>
            </div>

            <div class="item-main" @click="showDetail(p)">
              <div class="item-title ellipsis">{{ p.title }}</div>
              <div class="item-tags">
                <el-tag size="small" type="success" effect="plain">{{ p.category_name }}</el-tag>
                <el-tag size="small" type="info" effect="plain">{{ p.condition_label }}</el-tag>
                <el-tag size="small" effect="plain">{{ p.campus || '校区未填' }}</el-tag>
              </div>
              <div class="item-meta">
                卖家：{{ p.seller_nickname }} · 发布于 {{ formatTime(p.created_at) }}
              </div>
            </div>

            <div class="item-price">
              <span class="price">¥{{ p.price }}</span>
              <span v-if="p.original_price" class="origin">¥{{ p.original_price }}</span>
            </div>

            <div class="item-actions">
              <el-button size="small" type="primary" @click="handleApprove(p)">通过</el-button>
              <el-button size="small" type="danger" plain @click="openReject(p)">驳回</el-button>
              <el-button size="small" @click="showDetail(p)">详情</el-button>
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

    <!-- 商品详情对话框 -->
    <el-dialog v-model="detailVisible" title="商品详情" width="560px">
      <div v-if="detail" class="detail-body">
        <div class="detail-gallery">
          <img v-if="detail.cover" :src="detail.cover" :alt="detail.title" class="detail-img" />
          <div v-else class="detail-img no-cover">
            <el-icon :size="40"><Picture /></el-icon>
          </div>
        </div>
        <div class="detail-info">
          <div class="detail-title">{{ detail.title }}</div>
          <div class="detail-price">¥{{ detail.price }}</div>
          <el-descriptions :column="2" border size="small" class="detail-desc">
            <el-descriptions-item label="分类">{{ detail.category_name }}</el-descriptions-item>
            <el-descriptions-item label="成色">{{ detail.condition_label }}</el-descriptions-item>
            <el-descriptions-item label="校区">{{ detail.campus || '未填' }}</el-descriptions-item>
            <el-descriptions-item label="地点">{{ detail.location || '未填' }}</el-descriptions-item>
          </el-descriptions>
          <div class="detail-meta">卖家：{{ detail.seller_nickname }} · {{ formatTime(detail.created_at) }}</div>
          <div class="detail-actions">
            <el-button type="primary" size="small" @click="handleApprove(detail)">审核通过</el-button>
            <el-button type="danger" size="small" plain @click="openReject(detail)">驳回</el-button>
            <el-button type="warning" size="small" plain @click="handleForbid(detail)">违规下架</el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 驳回原因对话框 -->
    <el-dialog v-model="rejectVisible" title="驳回商品" width="440px" :close-on-click-modal="false">
      <p v-if="rejectTarget" class="reject-tip">
        正在驳回「{{ rejectTarget.title }}」，请填写驳回原因（卖家会收到通知）。
      </p>
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="4"
        maxlength="255"
        show-word-limit
        placeholder="如：图片模糊、信息不全、涉嫌违规等"
      />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" :loading="rejectSubmitting" @click="submitReject">
          确认驳回
        </el-button>
      </template>
    </el-dialog>
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

.list-wrap {
  min-height: 200px;
}

.review-list {
  display: flex;
  flex-direction: column;
}

.review-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
}

.review-item:last-child {
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

.item-tags {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.item-meta {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

.item-price {
  width: 110px;
  text-align: right;
  flex-shrink: 0;
}

.price {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.origin {
  display: block;
  font-size: 12px;
  color: #c0c4cc;
  text-decoration: line-through;
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

.detail-gallery {
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 14px;
  background: #f5f7fa;
}

.detail-img {
  width: 100%;
  height: 260px;
  object-fit: cover;
  display: block;
}

.detail-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.detail-price {
  font-size: 20px;
  font-weight: 700;
  color: #f56c6c;
  margin-bottom: 12px;
}

.detail-desc {
  margin-bottom: 10px;
}

.detail-meta {
  margin-bottom: 14px;
  font-size: 13px;
  color: #909399;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.reject-tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}
</style>