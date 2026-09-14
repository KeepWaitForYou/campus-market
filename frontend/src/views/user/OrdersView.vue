<script setup lang="ts">
/**
 * 我的订单：我买到的 / 我卖出的，支持状态筛选与全流程操作。
 * 操作权限矩阵（role + status）：
 * - bought + pending  -> 支付 / 取消
 * - bought + shipped  -> 确认收货
 * - sold   + paid     -> 发货
 */
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import { cancelOrder, confirmOrder, getOrders, payOrder, shipOrder } from '@/api'
import { ORDER_STATUS_LABELS, ORDER_STATUS_TAGS } from '@/constants/options'
import type { OrderItem, OrderStatus } from '@/types/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const list = ref<OrderItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

/** 视角：我买到的 / 我卖出的（支持 URL query tab 进入） */
const role = ref<'bought' | 'sold'>('bought')
/** 状态筛选：全部状态用空串 */
const status = ref('')

const STATUS_TABS = [
  { label: '全部', value: '' },
  { label: '待支付', value: 'pending' },
  { label: '已支付', value: 'paid' },
  { label: '已发货', value: 'shipped' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getOrders({
      role: role.value,
      status: (status.value || undefined) as OrderStatus | undefined,
      page: page.value,
      page_size: PAGE_SIZE,
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

function handleRoleChange(): void {
  page.value = 1
  status.value = ''
  syncUrl()
  fetchList()
}

function handleStatusChange(): void {
  page.value = 1
  syncUrl()
  fetchList()
}

/** tab / status 写入 URL（便于从详情页"去支付"直达） */
function syncUrl(): void {
  router.replace({
    path: route.path,
    query: {
      tab: role.value,
      ...(status.value ? { status: status.value } : {}),
    },
  })
}

function applyUrlQuery(): void {
  const q = route.query
  if (q.tab === 'sold' || q.tab === 'bought') {
    role.value = q.tab
  }
  if (typeof q.status === 'string' && STATUS_TABS.some((t) => t.value === q.status)) {
    status.value = q.status
  }
}

/** 从订单状态时间字段提取时间展示 */
function orderTime(o: OrderItem): string {
  return new Date(o.created_at).toLocaleString('zh-CN')
}

/** 交易对方（买到的下单商品 -> 卖家；卖出的 -> 买家） */
function counterpart(o: OrderItem): { name: string; sub: string } {
  if (role.value === 'bought') {
    return { name: o.seller.nickname || o.seller.username, sub: `卖家 @${o.seller.username}` }
  }
  return { name: o.buyer.nickname || o.buyer.username, sub: `买家 @${o.buyer.username}` }
}

// ---------------- 订单操作 ----------------
async function opPay(o: OrderItem): Promise<void> {
  try {
    await payOrder(o.id)
    ElMessage.success('支付成功，等待卖家发货')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

async function opCancel(o: OrderItem): Promise<void> {
  try {
    await ElMessageBox.confirm('确定取消该订单吗？商品将恢复在售状态。', '取消订单', { type: 'warning' })
  } catch {
    return
  }
  try {
    await cancelOrder(o.id)
    ElMessage.success('订单已取消')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

async function opShip(o: OrderItem): Promise<void> {
  try {
    await ElMessageBox.confirm('确认已交付商品并发货？', '确认发货', { type: 'info' })
  } catch {
    return
  }
  try {
    await shipOrder(o.id)
    ElMessage.success('已发货，等待买家确认收货')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

async function opConfirm(o: OrderItem): Promise<void> {
  try {
    await ElMessageBox.confirm('请确认已收到商品，确认后订单完成。', '确认收货', { type: 'success' })
  } catch {
    return
  }
  try {
    await confirmOrder(o.id)
    ElMessage.success('交易完成，感谢使用校园二手交易平台')
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

/** 展示该订单在当前视角下可执行的首个主操作 */
function primaryAction(o: OrderItem): { key: string; text: string; type: 'primary' | 'success' | 'danger' | 'warning' } | null {
  if (role.value === 'bought') {
    if (o.status === 'pending') return { key: 'pay', text: '立即支付', type: 'primary' }
    if (o.status === 'shipped') return { key: 'confirm', text: '确认收货', type: 'success' }
  } else if (role.value === 'sold') {
    if (o.status === 'paid') return { key: 'ship', text: '发货', type: 'primary' }
  }
  return null
}

function onPrimary(o: OrderItem): void {
  const action = primaryAction(o)
  if (!action) return
  if (action.key === 'pay') opPay(o)
  if (action.key === 'confirm') opConfirm(o)
  if (action.key === 'ship') opShip(o)
}

function isCancellable(o: OrderItem): boolean {
  return role.value === 'bought' && o.status === 'pending'
}

onMounted(() => {
  applyUrlQuery()
  fetchList()
})

// 若外部以 query 进入（如详情页下单后），监听 query 变化重新加载
watch(
  () => route.query,
  () => {
    applyUrlQuery()
    fetchList()
  },
)
</script>

<template>
  <div class="orders-wrap">
    <el-card shadow="never" class="head-card">
      <div class="role-row">
        <el-radio-group v-model="role" @change="handleRoleChange">
          <el-radio-button value="bought">我买到的</el-radio-button>
          <el-radio-button value="sold">我卖出的</el-radio-button>
        </el-radio-group>
        <el-radio-group v-model="status" class="status-group" @change="handleStatusChange">
          <el-radio-button v-for="t in STATUS_TABS" :key="t.value" :value="t.value">
            {{ t.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!loading && list.length === 0" description="暂无订单" />

        <div v-else class="order-list">
          <div v-for="o in list" :key="o.id" class="order-item">
            <div class="order-head">
              <span class="order-no">订单号：{{ o.order_no }}</span>
              <span class="order-time">{{ orderTime(o) }}</span>
              <el-tag size="small" :type="ORDER_STATUS_TAGS[o.status]">
                {{ o.status_label || ORDER_STATUS_LABELS[o.status] }}
              </el-tag>
            </div>

            <div class="order-body">
              <el-image
                v-if="o.product.cover"
                :src="o.product.cover"
                fit="cover"
                class="order-cover"
                :preview-src-list="[o.product.cover]"
                preview-teleported
              />
              <div v-else class="order-cover no-cover">
                <el-icon :size="24"><Picture /></el-icon>
              </div>

              <div class="order-info" @click="router.push(`/products/${o.product.id}`)">
                <div class="order-title ellipsis">{{ o.product.title }}</div>
                <div class="order-sub">
                  {{ counterpart(o).name }}
                  <span class="muted">（{{ counterpart(o).sub }}）</span>
                </div>
                <div v-if="o.remark" class="order-remark">备注：{{ o.remark }}</div>
              </div>

              <div class="order-amount">
                <span class="amount">¥{{ o.amount }}</span>
              </div>

              <div class="order-actions">
                <el-button
                  v-if="primaryAction(o)"
                  :type="primaryAction(o)?.type"
                  size="small"
                  @click="onPrimary(o)"
                >
                  {{ primaryAction(o)?.text }}
                </el-button>
                <el-button
                  v-if="isCancellable(o)"
                  type="danger"
                  plain
                  size="small"
                  @click="opCancel(o)"
                >
                  取消订单
                </el-button>
              </div>
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

.role-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.status-group {
  flex-wrap: wrap;
}

.list-wrap {
  min-height: 200px;
}

.order-list {
  display: flex;
  flex-direction: column;
}

.order-item {
  padding: 14px 0;
  border-bottom: 1px solid #f0f2f5;
}

.order-item:last-child {
  border-bottom: none;
}

.order-head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}

.order-no {
  font-size: 13px;
  color: #909399;
  font-family: Consolas, monospace;
}

.order-time {
  font-size: 12px;
  color: #c0c4cc;
}

.order-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.order-cover {
  width: 72px;
  height: 72px;
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

.order-info {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.order-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.order-sub {
  margin-top: 6px;
  font-size: 13px;
  color: #606266;
}

.muted {
  color: #c0c4cc;
  font-size: 12px;
}

.order-remark {
  margin-top: 4px;
  font-size: 12px;
  color: #e6a23c;
}

.order-amount {
  width: 100px;
  text-align: right;
  flex-shrink: 0;
}

.amount {
  font-size: 16px;
  font-weight: 700;
  color: #f56c6c;
}

.order-actions {
  display: flex;
  gap: 8px;
  width: 170px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

@media (max-width: 720px) {
  .order-body {
    flex-wrap: wrap;
  }

  .order-actions {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>