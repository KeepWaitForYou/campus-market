import type {
  AdminOrderListParams,
  AdminStats,
  AdminUser,
  AdminUserListParams,
  CategoryItem,
  OrderItem,
  OrderStatus,
  Paginated,
  ProductListItem,
} from '@/types/api'
import http from '@/utils/request'

// ---------------- 商品审核 ----------------
/** GET /api/v1/admin/products/pending/ 待审核商品列表 */
export function getPendingProducts(page = 1): Promise<Paginated<ProductListItem>> {
  return http.get<Paginated<ProductListItem>>('/admin/products/pending/', { params: { page } })
}

/** POST /api/v1/admin/products/{id}/approve/ 审核通过 */
export function approveProduct(id: number): Promise<void> {
  return http.post<void>(`/admin/products/${id}/approve/`)
}

/** POST /api/v1/admin/products/{id}/reject/ 审核不通过（需原因） */
export function rejectProduct(id: number, reason: string): Promise<void> {
  return http.post<void>(`/admin/products/${id}/reject/`, { reason })
}

/** POST /api/v1/admin/products/{id}/forbid/ 违规强制下架 */
export function forbidProduct(id: number): Promise<void> {
  return http.post<void>(`/admin/products/${id}/forbid/`)
}

// ---------------- 用户管理 ----------------
/** GET /api/v1/admin/users/ 用户列表（搜索 / 状态筛选 / 分页） */
export function getAdminUsers(params?: AdminUserListParams): Promise<Paginated<AdminUser>> {
  return http.get<Paginated<AdminUser>>('/admin/users/', { params })
}

/** POST /api/v1/admin/users/{id}/toggle_active/ 禁用 / 启用用户 */
export function toggleUserActive(id: number): Promise<{ id: number; is_active: boolean }> {
  return http.post<{ id: number; is_active: boolean }>(`/admin/users/${id}/toggle_active/`)
}

// ---------------- 订单管理 ----------------
/** GET /api/v1/admin/orders/ 全部订单（状态 / 角色 / 关键词 / 排序） */
export function getAdminOrders(params?: AdminOrderListParams): Promise<Paginated<OrderItem>> {
  return http.get<Paginated<OrderItem>>('/admin/orders/', { params })
}

export type { OrderStatus }

// ---------------- 分类管理 ----------------
/** GET /api/v1/admin/categories/ 全部分类（含禁用，管理后台用） */
export function getAdminCategories(): Promise<CategoryItem[]> {
  return http.get<CategoryItem[]>('/admin/categories/')
}

/** POST /api/v1/admin/categories/ 新增分类 */
export function adminCreateCategory(data: {
  name: string
  sort?: number
  is_active?: boolean
}): Promise<CategoryItem> {
  return http.post<CategoryItem>('/admin/categories/', data)
}

/** PATCH /api/v1/admin/categories/{id}/ 编辑分类（名称 / 排序 / 启用状态） */
export function adminUpdateCategory(
  id: number,
  data: Partial<{ name: string; sort: number; is_active: boolean }>,
): Promise<CategoryItem> {
  return http.patch<CategoryItem>(`/admin/categories/${id}/`, data)
}

/** GET /api/v1/admin/stats/ 平台数据统计（后台首页 + ECharts） */
export function getAdminStats(): Promise<AdminStats> {
  return http.get<AdminStats>('/admin/stats/')
}