import type { NotificationItem, Paginated } from '@/types/api'
import http from '@/utils/request'

/** GET /api/v1/notifications/ 我的通知（?is_read=0 只看未读，分页） */
export function getNotifications(params?: {
  page?: number
  page_size?: number
  is_read?: '0' | '1'
}): Promise<Paginated<NotificationItem>> {
  return http.get<Paginated<NotificationItem>>('/notifications/', { params })
}

/** GET /api/v1/notifications/unread_count/ 未读通知数 */
export function getUnreadCount(): Promise<{ unread_count: number }> {
  return http.get<{ unread_count: number }>('/notifications/unread_count/')
}

/** POST /api/v1/notifications/{id}/read/ 标记单条已读 */
export function markNotificationRead(id: number): Promise<{ id: number; is_read: boolean }> {
  return http.post<{ id: number; is_read: boolean }>(`/notifications/${id}/read/`)
}

/** POST /api/v1/notifications/read_all/ 一键全部已读 */
export function markAllNotificationsRead(): Promise<{ marked: number }> {
  return http.post<{ marked: number }>('/notifications/read_all/')
}