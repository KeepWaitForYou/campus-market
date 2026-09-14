/**
 * 登录页：用户名 + 密码，JWT 登录。
 * 登录成功后按 redirect 参数回跳，默认回首页。
 */
<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="always">
      <div class="auth-brand">
        <el-icon :size="34" color="#409eff"><ShoppingBag /></el-icon>
        <h1>校园二手交易平台</h1>
        <p>登录后即可发布、收藏与购买校园二手好物</p>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            clearable
            autocomplete="username"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            autocomplete="current-password"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="handleSubmit"
        >
          登 录
        </el-button>
      </el-form>

      <div class="auth-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>

      <el-alert
        class="auth-hint"
        type="info"
        :closable="false"
        title="默认管理员账号：admin / Admin123456；普通用户请先注册"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Lock, ShoppingBag, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleSubmit(): Promise<void> {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    ElMessage.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(135deg, #e8f3ff 0%, #f5f7fa 60%, #ecf5ff 100%);
}

.auth-card {
  width: 420px;
  max-width: 100%;
  border-radius: 12px;
}

.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.auth-brand h1 {
  margin: 12px 0 4px;
  font-size: 20px;
  color: #303133;
}

.auth-brand p {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}

.auth-footer {
  margin-top: 16px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.auth-footer a {
  color: #409eff;
  text-decoration: none;
}

.auth-hint {
  margin-top: 16px;
}
</style>