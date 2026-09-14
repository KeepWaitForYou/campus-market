/**
 * API 统一响应结构与业务数据类型定义。
 *
 * 后端约定所有 API 返回体：{ code: 0, message, data }；
 * 分页数据固定为 { count, next, previous, results }。
 * 登录/刷新接口（SimpleJWT 原生）不套统一包装。
 */

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页响应 */
export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// ---------------- 用户 ----------------
export interface UserProfile {
  id: number
  username: string
  nickname: string
  phone: string
  email: string
  avatar: string | null
  avatar_url: string | null
  student_no: string
  is_verified: boolean
  /** 管理员标记（后端 UserSerializer 已输出） */
  is_staff: boolean
  is_superuser: boolean
  date_joined: string
}

export interface LoginResult {
  access: string
  refresh: string
  user: UserProfile
}

export interface RegisterPayload {
  username: string
  password: string
  confirm_password: string
  email?: string
  phone?: string
  nickname?: string
  student_no?: string
}

// ---------------- 分类 ----------------
export interface CategoryItem {
  id: number
  name: string
  sort: number
  is_active: boolean
  product_count: number
}

// ---------------- 商品 ----------------
export type ProductCondition = 'brand_new' | 'like_new' | 'lightly_used' | 'used' | 'damaged'

export type ProductStatus = 'pending' | 'on_sale' | 'off_shelf' | 'sold' | 'rejected'

export interface ProductImage {
  id: number
  url: string
  is_cover: boolean
  sort: number
}

export interface SellerBrief {
  id: number
  username: string
  nickname: string
  avatar_url: string | null
}

export interface ProductListItem {
  id: number
  title: string
  price: string
  original_price: string | null
  condition: ProductCondition
  condition_label: string
  campus: string
  location: string
  cover: string | null
  category_name: string
  seller_nickname: string
  view_count: number
  favorite_count: number
  status: ProductStatus
  created_at: string
}

export interface ProductDetail extends ProductListItem {
  description: string
  status_label: string
  reject_reason: string
  category: number
  category_name: string
  images: ProductImage[]
  seller: SellerBrief
  is_favorite: boolean
  updated_at: string
}

/** 发布/编辑商品载荷（多图 multipart） */
export interface ProductPayload {
  title: string
  description: string
  price: string | number
  original_price?: string | number | null
  condition: ProductCondition
  campus: string
  location: string
  category: number
  images?: File[]
}

export interface ProductListParams {
  page?: number
  page_size?: number
  category?: number
  min_price?: number
  max_price?: number
  condition?: ProductCondition
  campus?: string
  search?: string
  ordering?: string
  /** mine=1：卖家查看自己的全部商品（含待审核/下架等所有状态） */
  mine?: '1' | '0'
  /** 按商品状态筛选（配合 mine=1 在“我的发布”使用） */
  status?: ProductStatus
}

export interface FavoriteItem {
  id: number
  product: ProductListItem
  created_at: string
}

export interface HotSearchItem {
  keyword: string
  hot: number
}

// ---------------- 订单 ----------------
export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'completed' | 'cancelled'

export interface ProductBrief {
  id: number
  title: string
  price: string
  cover: string | null
  status: ProductStatus
  status_label: string
  campus: string
  location: string
}

export interface OrderItem {
  id: number
  order_no: string
  product: ProductBrief
  buyer: SellerBrief
  seller: SellerBrief
  amount: string
  status: OrderStatus
  status_label: string
  /** bought=我是买家 / sold=我是卖家 / admin=管理员视角 */
  role: 'bought' | 'sold' | 'admin'
  remark: string
  pay_time: string | null
  ship_time: string | null
  finish_time: string | null
  cancel_time: string | null
  created_at: string
  product_description?: string
}

export interface OrderListParams {
  role?: 'bought' | 'sold'
  status?: OrderStatus
  page?: number
  page_size?: number
}

// ---------------- 通知 ----------------
export type NotificationType = 'review' | 'order' | 'favorite' | 'system'

export interface NotificationItem {
  id: number
  title: string
  content: string
  type: NotificationType
  type_label: string
  is_read: boolean
  created_at: string
}

// ---------------- 后台管理 ----------------
export interface AdminUser {
  id: number
  username: string
  nickname: string
  phone: string
  email: string
  student_no: string
  avatar_url: string | null
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  is_verified: boolean
  date_joined: string
  last_login: string | null
}

export interface AdminUserListParams {
  page?: number
  search?: string
  is_active?: '0' | '1'
  is_staff?: '0' | '1'
}

export interface AdminOrderListParams {
  page?: number
  status?: OrderStatus
  role?: 'bought' | 'sold'
  search?: string
  sort?: string
}

export interface CategoryDistItem {
  name: string
  cnt: number
}

export interface AdminStats {
  total_users: number
  total_products: number
  total_orders: number
  total_amount: string
  pending_products: number
  today_new_users: number
  today_new_products: number
  today_new_orders: number
  category_dist: CategoryDistItem[]
}