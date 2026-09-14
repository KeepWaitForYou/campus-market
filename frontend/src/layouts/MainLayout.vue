/**
 * 商城前台公共布局：顶部导航 + 内容区 + 页脚。
 */
<template>
  <div class="main-layout">
    <header class="main-header">
      <div class="header-inner">
        <router-link to="/" class="logo">
          <el-icon :size="26" color="#409eff"><ShoppingBag /></el-icon>
          <span class="logo-text">校园二手交易</span>
        </router-link>

        <nav class="nav">
          <router-link to="/" class="nav-link" :class="{ active: route.path === '/' }">首页</router-link>
          <router-link to="/publish" class="nav-link">发布闲置</router-link>
          <router-link
            v-if="userStore.isLoggedIn"
            to="/notifications"
            class="nav-link"
            :class="{ active: route.path === '/notifications' }"
          >
            消息通知
            <el-badge v-if="userStore.unreadCount > 0" :value="userStore.unreadCount" class="badge" />
          </router-link>
        </nav>

        <div class="actions">
          <template v-if="!userStore.isLoggedIn">
            <el-button type="primary" round @click="router.push('/login')">登录</el-button>
            <el-button round @click="router.push('/register')">注册</el-button>
          </template>
          <template v-else>
            <router-link v-if="userStore.isAdmin" to="/admin" class="admin-entry">
              <el-button size="small" round>管理后台</el-button>
            </router-link>
            <el-dropdown trigger="click" @command="handleCommand">
              <span class="user-entry">
                <el-avatar :size="30" :src="userStore.profile?.avatar_url || undefined">
                  {{ userStore.displayName.slice(0, 1) }}
                </el-avatar>
                <span class="username">{{ userStore.displayName }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="/user/profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="/user/products">我的发布</el-dropdown-item>
                  <el-dropdown-item command="/user/orders">我的订单</el-dropdown-item>
                  <el-dropdown-item command="/user/favorites">我的收藏</el-dropdown-item>
                  <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </div>
      </div>
    </header>

    <main class="main-content">
      <router-view />
    </main>

    <footer class="main-footer">
      <p>校园二手交易平台 · 仅供在校学生之间进行二手交易 · 请当面验货，谨防诈骗</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

function handleCommand(command: string): void {
  if (command === 'logout') {
    userStore.logout()
    router.push('/')
    return
  }
  router.push(command)
}

onMounted(() => userStore.fetchUnreadCount())
// 路由切换后刷新未读角标（如阅读完通知返回）
watch(() => route.path, () => userStore.fetchUnreadCount())
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  max-width: 1200px;
  height: 60px;
  margin: 0 auto;
  padding: 0 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.nav {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-link {
  position: relative;
  padding: 6px 14px;
  color: #606266;
  text-decoration: none;
  border-radius: 6px;
  font-size: 14px;
}

.nav-link:hover,
.nav-link.active {
  color: #409eff;
  background: #ecf5ff;
}

.badge {
  margin-left: 4px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #303133;
}

.username {
  max-width: 100px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.main-content {
  flex: 1;
}

.main-footer {
  padding: 18px 16px;
  text-align: center;
  color: #909399;
  font-size: 13px;
  background: #fff;
  border-top: 1px solid #ebeef5;
}

.main-footer p {
  margin: 0;
}
</style>