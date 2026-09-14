/**
 * 用户中心布局：左侧菜单 + 内容区。
 */
<template>
  <div class="user-layout page-container">
    <el-card class="side-card" shadow="never">
      <div class="user-summary">
        <el-avatar :size="56" :src="userStore.profile?.avatar_url || undefined">
          {{ userStore.displayName.slice(0, 1) }}
        </el-avatar>
        <div class="user-name">{{ userStore.displayName }}</div>
        <div class="user-sub">@{{ userStore.profile?.username }}</div>
      </div>
      <el-menu :default-active="route.path" router class="user-menu">
        <el-menu-item index="/user/profile">
          <el-icon><User /></el-icon>
          <span>个人资料</span>
        </el-menu-item>
        <el-menu-item index="/user/products">
          <el-icon><Goods /></el-icon>
          <span>我的发布</span>
        </el-menu-item>
        <el-menu-item index="/user/orders">
          <el-icon><Tickets /></el-icon>
          <span>我的订单</span>
        </el-menu-item>
        <el-menu-item index="/user/favorites">
          <el-icon><Star /></el-icon>
          <span>我的收藏</span>
        </el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <span>消息通知</span>
        </el-menu-item>
      </el-menu>
    </el-card>

    <div class="user-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
</script>

<style scoped>
.user-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.side-card {
  width: 240px;
  flex-shrink: 0;
}

.user-summary {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 8px 0 16px;
  border-bottom: 1px solid #ebeef5;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
}

.user-sub {
  font-size: 13px;
  color: #909399;
}

.user-menu {
  border-right: none;
  margin-top: 8px;
}

.user-content {
  flex: 1;
  min-width: 0;
}
</style>