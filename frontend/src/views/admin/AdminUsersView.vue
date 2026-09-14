<script setup lang="ts">
/**
 * 用户管理：用户列表、关键词搜索、状态/身份筛选、禁用 / 启用。
 * 安全约束：不能操作当前登录的管理员自己。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { getAdminUsers, toggleUserActive } from '@/api'
import { useUserStore } from '@/stores/user'
import type { AdminUser } from '@/types/api'

const userStore = useUserStore()

const loading = ref(false)
const list = ref<AdminUser[]>([])
const total = ref(0)
const page = ref(1)
const PAGE_SIZE = 10

const search = ref('')
const filterActive = ref<'' | '1' | '0'>('')
const filterStaff = ref<'' | '1' | '0'>('')

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    const data = await getAdminUsers({
      page: page.value,
      search: search.value.trim() || undefined,
      is_active: filterActive.value || undefined,
      is_staff: filterStaff.value || undefined,
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

function handleSearch(): void {
  page.value = 1
  fetchList()
}

function formatTime(iso: string): string {
  return iso ? new Date(iso).toLocaleString('zh-CN') : '—'
}

function isSelf(u: AdminUser): boolean {
  return userStore.profile?.id === u.id
}

async function handleToggle(u: AdminUser): Promise<void> {
  if (isSelf(u)) return
  const action = u.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(
      u.is_active
        ? `禁用「${u.nickname || u.username}」后，该用户将无法登录，确认继续？`
        : `启用「${u.nickname || u.username}」，恢复其登录权限？`,
      `${action}用户`,
      { type: u.is_active ? 'warning' : 'info', confirmButtonText: action },
    )
  } catch {
    return
  }
  try {
    await toggleUserActive(u.id)
    ElMessage.success(`已${action} ${u.nickname || u.username}`)
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  }
}
</script>

<template>
  <div class="admin-users">
    <el-card shadow="never">
      <template #header>
        <span class="card-header-title">用户管理</span>
      </template>

      <div class="filter-row">
        <el-input
          v-model="search"
          placeholder="搜索用户名 / 昵称 / 手机号 / 学号"
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="filterActive" placeholder="账号状态" clearable class="filter-item" @change="handleSearch">
          <el-option label="正常" value="1" />
          <el-option label="已禁用" value="0" />
        </el-select>
        <el-select v-model="filterStaff" placeholder="用户类型" clearable class="filter-item" @change="handleSearch">
          <el-option label="普通用户" value="0" />
          <el-option label="管理员" value="1" />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>

      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="用户" min-width="140">
          <template #default="{ row }">
            <div class="user-cell">
              <el-avatar :size="28" :src="row.avatar_url || undefined">
                {{ (row.nickname || row.username).slice(0, 1) }}
              </el-avatar>
              <div class="user-name">
                <div class="name-line">
                  {{ row.nickname || row.username }}
                  <el-tag v-if="row.is_superuser" size="small" type="danger" effect="plain">超管</el-tag>
                  <el-tag v-else-if="row.is_staff" size="small" type="warning" effect="plain">管理员</el-tag>
                </div>
                <div class="sub-line">@{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="120">
          <template #default="{ row }">{{ row.phone || '—' }}</template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column prop="student_no" label="学号" width="120">
          <template #default="{ row }">{{ row.student_no || '—' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="160">
          <template #default="{ row }">{{ formatTime(row.date_joined) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-tooltip :content="isSelf(row) ? '不能操作当前登录账号' : ''" :disabled="!isSelf(row)">
              <span>
                <el-button
                  size="small"
                  :type="row.is_active ? 'danger' : 'success'"
                  plain
                  :disabled="isSelf(row)"
                  @click="handleToggle(row)"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
              </span>
            </el-tooltip>
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
  width: 280px;
}

.filter-item {
  width: 140px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-line {
  font-weight: 500;
}

.sub-line {
  font-size: 12px;
  color: #909399;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>