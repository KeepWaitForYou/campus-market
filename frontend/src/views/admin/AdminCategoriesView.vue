<script setup lang="ts">
/**
 * 分类管理：全部分类（含已禁用）列表，支持新增 / 编辑 / 启停。
 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { adminCreateCategory, adminUpdateCategory, getAdminCategories } from '@/api'
import type { CategoryItem } from '@/types/api'

const loading = ref(false)
const list = ref<CategoryItem[]>([])

/** 编辑 / 新增对话框 */
const dialogVisible = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({ id: 0, name: '', sort: 0, is_active: true })

async function fetchList(): Promise<void> {
  loading.value = true
  try {
    list.value = await getAdminCategories()
  } catch {
    list.value = []
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  isEdit.value = false
  form.value = { id: 0, name: '', sort: list.value.length + 1, is_active: true }
  dialogVisible.value = true
}

function openEdit(c: CategoryItem): void {
  isEdit.value = true
  form.value = { id: c.id, name: c.name, sort: c.sort, is_active: c.is_active }
  dialogVisible.value = true
}

async function handleSave(): Promise<void> {
  const name = form.value.name.trim()
  if (!name) {
    ElMessage.warning('请填写分类名称')
    return
  }
  saving.value = true
  try {
    if (isEdit.value) {
      await adminUpdateCategory(form.value.id, {
        name,
        sort: form.value.sort,
        is_active: form.value.is_active,
      })
      ElMessage.success('分类已更新')
    } else {
      await adminCreateCategory({
        name,
        sort: form.value.sort,
        is_active: form.value.is_active,
      })
      ElMessage.success('分类已创建')
    }
    dialogVisible.value = false
    fetchList()
  } catch {
    /* 请求层已统一提示 */
  } finally {
    saving.value = false
  }
}

async function handleToggle(c: CategoryItem): Promise<void> {
  const nextActive = !c.is_active
  // el-switch 已即时变化，这里在失败或取消时回滚
  const prevActive = c.is_active
  try {
    await ElMessageBox.confirm(
      nextActive ? `启用分类「${c.name}」？` : `禁用分类「${c.name}」？禁用后新商品将无法选择该分类。`,
      nextActive ? '启用分类' : '禁用分类',
      { type: nextActive ? 'info' : 'warning', confirmButtonText: nextActive ? '启用' : '禁用' },
    )
  } catch {
    c.is_active = prevActive
    return
  }
  try {
    await adminUpdateCategory(c.id, { is_active: nextActive })
    ElMessage.success(nextActive ? '已启用' : '已禁用')
  } catch {
    c.is_active = prevActive
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="admin-categories">
    <el-card shadow="never">
      <template #header>
        <div class="head-row">
          <span class="card-header-title">分类管理</span>
          <el-button type="primary" @click="openCreate">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            新增分类
          </el-button>
        </div>
      </template>

      <el-table v-loading="loading" :data="list" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="分类名称" min-width="180" />
        <el-table-column prop="sort" label="排序" width="90" />
        <el-table-column prop="product_count" label="商品数量" width="110" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_active"
              :loading="loading"
              inline-prompt
              active-text="启用"
              inactive-text="禁用"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑分类' : '新增分类'"
      width="440px"
      :close-on-click-modal="false"
    >
      <el-form label-width="90px">
        <el-form-item label="分类名称" required>
          <el-input v-model="form.name" placeholder="如：数码电子、教材书籍" maxlength="30" />
        </el-form-item>
        <el-form-item label="排序值">
          <el-input-number v-model="form.sort" :min="0" :max="9999" />
          <span class="form-tip">数值越小越靠前</span>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" inline-prompt active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
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

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>