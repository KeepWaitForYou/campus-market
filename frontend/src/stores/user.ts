/**
 * 用户登录态 Pinia Store。
 *
 * token 持久化在 localStorage（utils/auth 统一管理）；
 * profile 仅存于内存，刷新页面后由路由守卫懒加载（fetchProfile）。
 */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { getUnreadCount, login as apiLogin, register as apiRegister, updateMe, getMe } from '@/api'
import type { LoginResult, RegisterPayload, UserProfile } from '@/types/api'
import { clearAuthTokens, getAccessToken, setTokens } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)
  /** 未读通知数（导航栏角标；通知页操作后本地联动刷新） */
  const unreadCount = ref(0)

  /** 是否已登录：以本地是否存在 access token 为准 */
  const isLoggedIn = computed(() => Boolean(getAccessToken()))

  /** 是否管理员：is_staff 或 is_superuser（需先取得 profile） */
  const isAdmin = computed(
    () => profile.value?.is_staff === true || profile.value?.is_superuser === true,
  )

  /** 展示名：优先昵称，其次用户名 */
  const displayName = computed(() => profile.value?.nickname || profile.value?.username || '')

  function applyLogin(data: LoginResult): void {
    setTokens(data.access, data.refresh)
    profile.value = data.user
  }

  /** 登录：成功后写入 token 与 profile */
  async function login(payload: { username: string; password: string }): Promise<UserProfile> {
    const data = await apiLogin(payload)
    applyLogin(data)
    return data.user
  }

  /** 注册：成功后直接写入登录态 */
  async function register(payload: RegisterPayload): Promise<UserProfile> {
    const data = await apiRegister(payload)
    applyLogin(data)
    return data.user
  }

  /** 拉取当前用户资料（页面刷新后路由守卫调用） */
  async function fetchProfile(): Promise<UserProfile | null> {
    if (!isLoggedIn.value) return null
    profile.value = await getMe()
    return profile.value
  }

  /** 更新昵称 / 手机号 / 邮箱 */
  async function updateProfile(payload: {
    nickname?: string
    phone?: string
    email?: string
  }): Promise<UserProfile> {
    profile.value = await updateMe(payload)
    return profile.value
  }

  /** 登出：清空 token 与 profile */
  function logout(): void {
    clearAuthTokens()
    profile.value = null
    unreadCount.value = 0
  }

  /** 拉取未读通知数（登录后 / 路由切换时由布局调用） */
  async function fetchUnreadCount(): Promise<void> {
    if (!isLoggedIn.value) {
      unreadCount.value = 0
      return
    }
    try {
      unreadCount.value = (await getUnreadCount()).unread_count
    } catch {
      unreadCount.value = 0
    }
  }

  return {
    profile,
    unreadCount,
    isLoggedIn,
    isAdmin,
    displayName,
    login,
    register,
    fetchProfile,
    updateProfile,
    logout,
    fetchUnreadCount,
  }
})