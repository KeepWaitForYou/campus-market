/**
 * 注册页：用户名 / 密码 / 邮箱 / 手机号 / 昵称 / 学号。
 * 注册成功即自动登录并跳转首页。
 */
<template>
  <div class="auth-page">
    <el-card class="auth-card" shadow="always">
      <div class="auth-brand">
        <el-icon :size="34" color="#409eff"><ShoppingBag /></el-icon>
        <h1>注册账号</h1>
        <p>加入校园二手交易平台，开始你的闲置买卖</p>
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
          <el-input v-model="form.username" placeholder="3-20 位字母/数字/下划线" :prefix-icon="User" clearable />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="至少 6 位" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="请再次输入密码" :prefix-icon="Lock" show-password />
        </el-form-item>

        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="form.nickname" placeholder="展示用昵称" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学号" prop="student_no">
              <el-input v-model="form.student_no" placeholder="（选填）" clearable />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="（选填）" :prefix-icon="Message" clearable />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="（选填）" :prefix-icon="Iphone" clearable />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="handleSubmit"
        >
          注 册
        </el-button>
      </el-form>

      <div class="auth-footer">
        已有账号？<router-link to="/login">直接登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { Iphone, Lock, Message, ShoppingBag, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
  confirm_password: '',
  nickname: '',
  student_no: '',
  email: '',
  phone: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{3,20}$/, message: '3-20 位字母、数字或下划线', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [
    {
      pattern: /^1[3-9]\d{9}$/,
      message: '手机号格式不正确',
      trigger: 'blur',
    },
  ],
}

async function handleSubmit(): Promise<void> {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      password: form.password,
      confirm_password: form.confirm_password,
      nickname: form.nickname,
      student_no: form.student_no,
      email: form.email,
      phone: form.phone,
    })
    ElMessage.success('注册成功，已自动登录')
    router.push('/')
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
  width: 480px;
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
</style>