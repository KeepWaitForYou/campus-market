<script setup lang="ts">
/**
 * 个人资料页：头像上传、昵称 / 手机号 / 邮箱修改。
 * 用户名、学号、注册时间只读展示。
 */
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

const formRef = ref()
const saving = ref(false)
const avatarUploading = ref(false)

const form = reactive({
  nickname: profile.value?.nickname ?? '',
  phone: profile.value?.phone ?? '',
  email: profile.value?.email ?? '',
})

const rules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^1\d{10}$/, message: '手机号格式不正确', trigger: 'blur' }],
}

const joinedDate = computed(() =>
  profile.value ? new Date(profile.value.date_joined).toLocaleString('zh-CN') : '',
)

/** 自定义头像上传（替代 el-upload 自带请求，走统一请求层） */
async function handleAvatarUpload(options: { file: File }): Promise<void> {
  avatarUploading.value = true
  try {
    const { uploadAvatar } = await import('@/api')
    await uploadAvatar(options.file)
    // 刷新 profile 获取最新头像地址
    await userStore.fetchProfile()
    ElMessage.success('头像已更新')
  } catch {
    /* 请求层已统一提示 */
  } finally {
    avatarUploading.value = false
  }
}

async function handleSave(): Promise<void> {
  const formEl = formRef.value as { validate: () => Promise<boolean> } | null
  if (!formEl) return
  const valid = await formEl.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    await userStore.updateProfile({
      nickname: form.nickname,
      phone: form.phone,
      email: form.email,
    })
    ElMessage.success('资料已保存')
  } catch {
    /* 请求层已统一提示 */
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="profile-wrap">
    <el-card shadow="never">
      <template #header>
        <span class="card-header-title">个人资料</span>
      </template>

      <div v-if="profile" class="profile-body">
        <!-- 头像区 -->
        <div class="avatar-panel">
          <el-avatar :size="96" :src="profile.avatar_url || undefined" class="big-avatar">
            {{ (profile.nickname || profile.username).slice(0, 1) }}
          </el-avatar>
          <el-upload
            :show-file-list="false"
            :http-request="handleAvatarUpload"
            accept="image/*"
            :disabled="avatarUploading"
          >
            <el-button size="small" :loading="avatarUploading">
              {{ avatarUploading ? '上传中' : '更换头像' }}
            </el-button>
          </el-upload>
          <p class="avatar-tip">支持 jpg / png / webp，不超过 8MB</p>
        </div>

        <!-- 资料表单 -->
        <el-form ref="formRef" :model="form" :rules="rules" label-width="90px" class="profile-form">
          <el-form-item label="用户名">
            <el-input :model-value="profile.username" disabled />
          </el-form-item>
          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="form.nickname" maxlength="30" />
          </el-form-item>
          <el-form-item label="学号">
            <el-input :model-value="profile.student_no || '未填写'" disabled />
          </el-form-item>
          <el-form-item label="手机号" prop="phone">
            <el-input v-model="form.phone" placeholder="选填" maxlength="11" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="选填" maxlength="60" />
          </el-form-item>
          <el-form-item label="注册时间">
            <span class="readonly-text">{{ joinedDate }}</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.profile-body {
  display: flex;
  gap: 32px;
  padding: 8px 0;
}

.avatar-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  width: 160px;
  flex-shrink: 0;
}

.big-avatar {
  font-size: 32px;
  background: #409eff;
}

.avatar-tip {
  margin: 0;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.profile-form {
  flex: 1;
  max-width: 480px;
}

.readonly-text {
  color: #606266;
}

@media (max-width: 720px) {
  .profile-body {
    flex-direction: column;
  }
}
</style>