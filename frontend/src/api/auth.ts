import type { LoginResult, RegisterPayload, UserProfile } from '@/types/api'
import http from '@/utils/request'

/** POST /api/v1/auth/register/ 注册（成功后直接返回 token 与用户信息） */
export function register(data: RegisterPayload): Promise<LoginResult> {
  return http.post<LoginResult>('/auth/register/', data)
}

/** POST /api/v1/auth/login/ 用户名 + 密码登录 */
export function login(data: { username: string; password: string }): Promise<LoginResult> {
  return http.post<LoginResult>('/auth/login/', data)
}