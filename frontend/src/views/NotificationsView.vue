<script setup lang="ts">
/**
 * 消息通知：全部 / 未读筛选，逐条已读与一键全部已读。
 * 已读操作联动导航栏未读角标（user store.unreadCount）。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getNotifications, markAllNotificationsRead, markNotificationRead } from '@/api'
import { useUserStore } from '@/stores/user'
import type { NotificationItem, NotificationType } from '@/types/api'

const userStore = useUserStore()

const loading = ref(false)
const list = ref<NotificationItem[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

/** 筛选：全部 / 未读 */
const filter = ref<'all' | 'unread'>('all')

const TYPE_META: Record<NotificationType, { icon: string; tag: string }> = {
  review: { icon: 'Review', tag: '审核' },
  order: { icon: 'Tickets', tag: '订单' },
  favorite: { icon: 'Star', tag: '收藏' },
  system: { icon: 'Bell', tag: '系统' },
}

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getNotifications({
      page: page.value,
      page_size: PAGE_SIZE,
      is_read: filter.value === 'unread' ? '0' : undefined,
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

function handleFilterChange(): void {
  page.value = 1
  fetchList()
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('zh-CN')
}

/** 单条标记已读（点击卡片） */
async function handleRead(item: NotificationItem): Promise<void> {
  if (item.is_read) return
  try {
    await markNotificationRead(item.id)
    item.is_read = true
    if (userStore.unreadCount > 0) {
      userStore.unreadCount -= 1
    }
  } catch {
    /* 请求层已统一提示 */
  }
}

/** 一键全部已读 */
async function handleReadAll(): Promise<void> {
  try {
    await ElMessageBox.confirm('确定将全部通知标记为已读吗？', '全部已读', { type: 'info' })
  } catch {
    return
  }
  try {
    const data = await markAllNotificationsRead()
    ElMessage.success(`已将 ${data.marked} 条通知标记为已读`)
    userStore.unreadCount = 0
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="notify-page">
    <el-card shadow="never" class="notify-card">
      <template #header>
        <div class="head-row">
          <div class="head-tabs">
            <el-radio-group v-model="filter" @change="handleFilterChange">
              <el-radio-button value="all">全部</el-radio-button>
              <el-radio-button value="unread">
                未读
                <el-badge
                  v-if="filter === 'unread'"
                  :value="total"
                  :max="99"
                  class="tab-badge"
                />
              </el-radio-button>
            </el-radio-group>
          </div>
          <el-button text type="primary" :disabled="list.length === 0" @click="handleReadAll">
            一键全部已读
          </el-button>
        </div>
      </template>

      <div v-loading="loading" class="list-wrap">
        <el-empty v-if="!loading && list.length === 0" description="暂无通知" />

        <div v-else class="notify-list">
          <div
            v-for="item in list"
            :key="item.id"
            class="notify-item"
            :class="{ unread: !item.is_read }"
            @click="handleRead(item)"
          >
            <div class="notify-icon" :class="`type-${item.type}`">
              <el-icon :size="20"><component :is="TYPE_META[item.type]?.icon || 'Bell'" /></el-icon>
            </div>

            <div class="notify-main">
              <div class="notify-title">
                {{ item.title }}
                <el-tag v-if="TYPE_META[item.type]" size="small" type="info" effect="plain">
                  {{ TYPE_META[item.type].tag }}
                </el-tag>
                <span v-if="!item.is_read" class="unread-dot" />
              </div>
              <div class="notify-content">{{ item.content }}</div>
              <div class="notify-time">{{ formatTime(item.created_at) }}</div>
            </div>

            <div class="notify-flag">
              <span v-if="!item.is_read" class="flag-text">未读</span>
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
.notify-page {
  max-width: 860px;
  margin: 0 auto;
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tab-badge {
  margin-left: 6px;
  transform: translateY(-2px);
}

.list-wrap {
  min-height: 200px;
}

.notify-list {
  display: flex;
  flex-direction: column;
}

.notify-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 8px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background 0.2s ease;
}

.notify-item:hover {
  background: #f5f7fa;
}

.notify-item.unread {
  background: #ecf5ff;
}

.notify-item.unread:hover {
  background: #d9ecff;
}

.notify-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
}

.type-review {
  background: #e6a23c;
}

.type-order {
  background: #409eff;
}

.type-favorite {
  background: #f56c6c;
}

.type-system {
  background: #909399;
}

.notify-main {
  flex: 1;
  min-width: 0;
}

.notify-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
}

.notify-content {
  margin-top: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  word-break: break-word;
  white-space: pre-wrap;
}

.notify-time {
  margin-top: 6px;
  font-size: 12px;
  color: #c0c4cc;
}

.notify-flag {
  width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.flag-text {
  font-size: 12px;
  color: #f56c6c;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>