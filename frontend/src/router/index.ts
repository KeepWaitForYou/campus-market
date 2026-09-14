/**
 * 前端路由表与守卫。
 *
 * 布局分层：
 * - MainLayout   商城前台（首页 / 详情 / 发布 / 通知）
 * - UserLayout   用户中心（资料 / 我的发布 / 我的订单 / 我的收藏）
 * - AdminLayout  管理后台（统计 / 商品审核 / 用户管理 / 订单管理）
 *
 * 守卫规则：
 * - requiresAuth：未登录跳转登录页（携带 redirect 回跳参数）
 * - requiresAdmin：非管理员回首页（未登录先登录）
 * - guestOnly：已登录用户访问登录/注册页时回首页
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/HomeView.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'products/:id(\\d+)',
        name: 'product-detail',
        component: () => import('@/views/ProductDetailView.vue'),
        meta: { title: '商品详情' },
        props: true,
      },
      {
        path: 'publish',
        name: 'publish',
        component: () => import('@/views/PublishView.vue'),
        meta: { title: '发布闲置', requiresAuth: true },
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('@/views/NotificationsView.vue'),
        meta: { title: '消息通知', requiresAuth: true },
      },
    ],
  },
  {
    path: '/user',
    component: () => import('@/layouts/UserLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: { name: 'user-profile' } },
      {
        path: 'profile',
        name: 'user-profile',
        component: () => import('@/views/user/ProfileView.vue'),
        meta: { title: '个人资料' },
      },
      {
        path: 'products',
        name: 'user-products',
        component: () => import('@/views/user/ProductsView.vue'),
        meta: { title: '我的发布' },
      },
      {
        path: 'orders',
        name: 'user-orders',
        component: () => import('@/views/user/OrdersView.vue'),
        meta: { title: '我的订单' },
      },
      {
        path: 'favorites',
        name: 'user-favorites',
        component: () => import('@/views/user/FavoritesView.vue'),
        meta: { title: '我的收藏' },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'admin-home',
        component: () => import('@/views/admin/AdminHomeView.vue'),
        meta: { title: '管理后台' },
      },
      {
        path: 'stats',
        name: 'admin-stats',
        component: () => import('@/views/admin/AdminStatsView.vue'),
        meta: { title: '数据统计' },
      },
      {
        path: 'products',
        name: 'admin-products',
        component: () => import('@/views/admin/AdminProductsView.vue'),
        meta: { title: '商品审核' },
      },
      {
        path: 'categories',
        name: 'admin-categories',
        component: () => import('@/views/admin/AdminCategoriesView.vue'),
        meta: { title: '分类管理' },
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/admin/AdminUsersView.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'orders',
        name: 'admin-orders',
        component: () => import('@/views/admin/AdminOrdersView.vue'),
        meta: { title: '订单管理' },
      },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { title: '注册', guestOnly: true },
  },
  { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ---------------- 全局前置守卫 ----------------
router.beforeEach(async (to) => {
  const userStore = useUserStore()

  // 登录拦截：受限页面未登录 -> 登录页
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // 已登录但 profile 缺失（页面刷新）：懒加载 profile，保证 isAdmin 判断准确
  if (to.meta.requiresAuth && userStore.isLoggedIn && !userStore.profile) {
    try {
      await userStore.fetchProfile()
    } catch {
      // 请求层已统一提示；若刷新失败导致登录态失效，由 401 拦截跳转
    }
  }

  // 管理后台：非管理员拦截
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    if (!userStore.isLoggedIn) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    ElMessage.warning('您没有权限访问管理后台')
    return { name: 'home' }
  }

  // 游客专属页（登录/注册）：已登录回首页
  if (to.meta.guestOnly && userStore.isLoggedIn) {
    return { name: 'home' }
  }

  // 浏览器标题
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - 校园二手交易平台` : '校园二手交易平台'
  return true
})

export default router