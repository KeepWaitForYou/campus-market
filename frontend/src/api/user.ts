import type { UserProfile } from '@/types/api'
import http from '@/utils/request'

/** GET /api/v1/users/me/ 当前用户资料 */
export function getMe(): Promise<UserProfile> {
  return http.get<UserProfile>('/users/me/')
}

/** PATCH /api/v1/users/me/ 修改昵称 / 手机号 / 邮箱 */
export function updateMe(data: {
  nickname?: string
  phone?: string
  email?: string
}): Promise<UserProfile> {
  return http.patch<UserProfile>('/users/me/', data)
}

/** POST /api/v1/users/me/avatar/ 上传 / 更换头像（multipart），返回头像 URL */
export function uploadAvatar(file: File): Promise<string | null> {
  const fd = new FormData()
  fd.append('avatar', file)
  return http.post<string | null>('/users/me/avatar/', fd)
}