<script setup lang="ts">
/**
 * 发布商品页：标题 / 描述 / 价格 / 原价 / 分类 / 成色 / 校区 / 地点 / 多图上传。
 * 支持编辑模式：/publish?edit={id}（从“我的发布”进入），回填并 PATCH 保存。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadUserFile } from 'element-plus'
import { storeToRefs } from 'pinia'

import { createProduct, getCategories, getProduct, updateProduct } from '@/api'
import { CAMPUS_OPTIONS, PRODUCT_CONDITIONS } from '@/constants/options'
import { useUserStore } from '@/stores/user'
import type { CategoryItem, ProductCondition, ProductDetail } from '@/types/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

/** 编辑模式下的商品 id（无则为新发布） */
const editId = computed<number | null>(() => {
  const v = Number(route.query.edit)
  return Number.isFinite(v) && v > 0 ? v : null
})

const categories = ref<CategoryItem[]>([])
const submitting = ref(false)
const loading = ref(false)

const form = reactive({
  title: '',
  description: '',
  price: undefined as number | undefined,
  original_price: undefined as number | undefined,
  category: undefined as number | undefined,
  condition: 'like_new' as ProductCondition,
  campus: '',
  location: '',
})

/** 上传文件列表（仅新添加的图片文件） */
const fileList = ref<UploadUserFile[]>([])

/** 编辑模式：当前商品已有图片（只读预览） */
const existingImages = ref<{ id: number; url: string }[]>([])

const rules = {
  title: [{ required: true, message: '请输入商品标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  condition: [{ required: true, message: '请选择成色', trigger: 'change' }],
  price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
  campus: [{ required: false }],
}

const formRef = ref()

/** 编辑器模式：加载商品详情回填 */
async function loadForEdit(): Promise<void> {
  if (!editId.value) return
  loading.value = true
  try {
    const detail: ProductDetail = await getProduct(editId.value)
    form.title = detail.title
    form.description = detail.description
    form.price = Number(detail.price)
    form.original_price = detail.original_price ? Number(detail.original_price) : undefined
    form.category = detail.category
    form.condition = detail.condition
    form.campus = detail.campus
    form.location = detail.location
    existingImages.value = detail.images.map((img) => ({ id: img.id, url: img.url }))
  } catch {
    ElMessage.error('商品加载失败，请返回重试')
    router.push({ name: 'user-products' })
  } finally {
    loading.value = false
  }
}

/** 获取表单内待上传的真实文件 */
function collectFiles(): File[] {
  const files: File[] = []
  fileList.value.forEach((f) => {
    if (f.raw) files.push(f.raw as unknown as File)
  })
  return files
}

function beforeUpload(file: File): boolean {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (file.size > 8 * 1024 * 1024) {
    ElMessage.error('单张图片不能超过 8MB')
    return false
  }
  return true
}

function beforeRemove(uploadFile: UploadFile): Promise<boolean> | boolean {
  return ElMessageBoxConfirm(`确定移除图片「${uploadFile.name}」吗？`)
}

async function ElMessageBoxConfirm(content: string): Promise<boolean> {
  const { ElMessageBox } = await import('element-plus')
  try {
    await ElMessageBox.confirm(content, '提示', { type: 'warning' })
    return true
  } catch {
    return false
  }
}

async function handleSubmit(): Promise<void> {
  const formEl = formRef.value as { validate: () => Promise<boolean> } | null
  if (!formEl) return

  const valid = await formEl.validate().catch(() => false)
  if (!valid) return

  const files = collectFiles()
  // 新发布必须至少一张图片
  if (!editId.value && files.length === 0) {
    ElMessage.warning('请至少上传一张商品图片')
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: form.title,
      description: form.description,
      price: form.price as number,
      original_price: form.original_price ?? null,
      condition: form.condition,
      campus: form.campus,
      location: form.location,
      category: form.category as number,
      images: files,
    }
    if (editId.value) {
      await updateProduct(editId.value, payload)
      ElMessage.success('商品已更新')
    } else {
      await createProduct(payload)
      ElMessage.success('发布成功，等待管理员审核')
    }
    // 清理首页缓存后跳回“我的发布”
    router.push({ name: 'user-products' })
  } catch {
    /* 请求层已统一提示 */
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    categories.value = await getCategories()
  } catch {
    categories.value = []
  }
  await loadForEdit()
})
</script>

<template>
  <div class="page-container publish-page">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="header-row">
          <span class="card-header-title">{{ editId ? '编辑商品' : '发布闲置' }}</span>
          <el-tag v-if="editId" type="warning" effect="plain">编辑后仍需重新提交审核的商品会保持原状态</el-tag>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        class="publish-form"
      >
        <el-form-item label="商品标题" prop="title">
          <el-input
            v-model="form.title"
            maxlength="60"
            show-word-limit
            placeholder="一句话说清楚卖什么，如：九成新高数教材，附笔记"
          />
        </el-form-item>

        <el-form-item label="商品描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="5"
            maxlength="2000"
            show-word-limit
            placeholder="成色细节、入手渠道、转手原因、可接受的价格区间等"
          />
        </el-form-item>

        <el-form-item label="售价（元）" prop="price">
          <el-input-number
            v-model="form.price"
            :min="0.01"
            :precision="2"
            :step="1"
            :controls="false"
            class="num-input"
            placeholder="0.00"
          />
        </el-form-item>

        <el-form-item label="原价（元）">
          <el-input-number
            v-model="form.original_price"
            :min="0"
            :precision="2"
            :step="1"
            :controls="false"
            class="num-input"
            placeholder="选填，用于展示折扣"
          />
        </el-form-item>

        <el-form-item label="商品分类" prop="category">
          <el-select v-model="form.category" placeholder="请选择分类" class="select-input">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="成色" prop="condition">
          <el-radio-group v-model="form.condition">
            <el-radio v-for="c in PRODUCT_CONDITIONS" :key="c.value" :value="c.value">
              {{ c.label }}
            </el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="校区" prop="campus">
          <el-select
            v-model="form.campus"
            placeholder="选择或输入校区"
            filterable
            allow-create
            default-first-option
            class="select-input"
          >
            <el-option v-for="c in CAMPUS_OPTIONS" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>

        <el-form-item label="交易地点" prop="location">
          <el-input
            v-model="form.location"
            maxlength="50"
            placeholder="如：东校区食堂门口、图书馆一楼大厅"
          />
        </el-form-item>

        <el-form-item label="商品图片" prop="images">
          <div class="upload-wrap">
            <!-- 编辑模式：展示已有图片 -->
            <div v-if="existingImages.length" class="existing-imgs">
              <div v-for="img in existingImages" :key="img.id" class="existing-img">
                <el-image :src="img.url" fit="cover" class="existing-img-el" />
                <span class="existing-cover" v-if="existingImages[0].id === img.id">封面</span>
              </div>
            </div>

            <el-upload
              v-model:file-list="fileList"
              list-type="picture-card"
              :auto-upload="false"
              :limit="9"
              accept="image/*"
              :before-upload="beforeUpload"
              :before-remove="beforeRemove"
            >
              <el-icon><Plus /></el-icon>
            </el-upload>
            <div class="upload-tip">
              支持 jpg / png / webp，单张不超过 8MB，最多 9 张，第一张为封面。
              <template v-if="editId">不选择新图片则保留原有图片。</template>
            </div>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            {{ editId ? '保存修改' : '确认发布' }}
          </el-button>
          <el-button size="large" @click="router.push('/')">取消</el-button>
          <span v-if="!editId" class="submit-tip">发布后需管理员审核通过才会展示在首页</span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.publish-page {
  max-width: 860px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header-title {
  font-weight: 600;
}

.publish-form {
  padding: 8px 24px 0 0;
}

.num-input {
  width: 220px;
}

.select-input {
  width: 260px;
}

.upload-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.existing-imgs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.existing-img {
  position: relative;
}

.existing-img-el {
  width: 100px;
  height: 100px;
  border-radius: 6px;
  display: block;
}

.existing-cover {
  position: absolute;
  left: 4px;
  bottom: 4px;
  padding: 1px 6px;
  font-size: 12px;
  color: #fff;
  background: rgba(64, 158, 255, 0.85);
  border-radius: 4px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
}

.submit-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #e6a23c;
}
</style>