/**
 * 管理后台布局：深色侧边菜单 + 内容区。
 */
<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="admin-aside">
      <div class="admin-logo">
        <el-icon :size="22" color="#409eff"><Shop /></el-icon>
        <span>管理后台</span>
      </div>
      <el-menu :default-active="route.path" router background-color="#1d232f" text-color="#a6adbb" active-text-color="#ffffff" class="admin-menu">
        <el-menu-item index="/admin">
          <el-icon><HomeFilled /></el-icon>
          <span>后台首页</span>
        </el-menu-item>
        <el-menu-item index="/admin/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据统计</span>
        </el-menu-item>
        <el-menu-item index="/admin/products">
          <el-icon><Stamp /></el-icon>
          <span>商品审核</span>
        </el-menu-item>
        <el-menu-item index="/admin/categories">
          <el-icon><Collection /></el-icon>
          <span>分类管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><UserFilled /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/orders">
          <el-icon><Tickets /></el-icon>
          <span>订单管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <el-button text @click="router.push('/')">
          <el-icon><Back /></el-icon>
          <span>返回商城</span>
        </el-button>
        <span class="admin-user">{{ userStore.displayName }}</span>
        <el-button text @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </el-button>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

function handleLogout(): void {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
}

.admin-aside {
  background: #1d232f;
}

.admin-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 60px;
  padding: 0 20px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.admin-menu {
  border-right: none;
}

.admin-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.admin-user {
  flex: 1;
  text-align: right;
  color: #606266;
}

.admin-main {
  background: #f5f7fa;
}
</style>