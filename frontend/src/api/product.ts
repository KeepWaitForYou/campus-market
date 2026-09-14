import type {
  FavoriteItem,
  HotSearchItem,
  Paginated,
  ProductDetail,
  ProductListItem,
  ProductListParams,
  ProductPayload,
} from '@/types/api'
import http from '@/utils/request'

/** GET /api/v1/products/ 商品列表（搜索 / 筛选 / 排序 / 分页） */
export function getProducts(params?: ProductListParams): Promise<Paginated<ProductListItem>> {
  return http.get<Paginated<ProductListItem>>('/products/', { params })
}

/** GET /api/v1/products/hot_searches/ 热门搜索 Top10 */
export function getHotSearches(): Promise<HotSearchItem[]> {
  return http.get<HotSearchItem[]>('/products/hot_searches/')
}

/** GET /api/v1/products/{id}/ 商品详情 */
export function getProduct(id: number): Promise<ProductDetail> {
  return http.get<ProductDetail>(`/products/${id}/`)
}

/** POST /api/v1/products/ 发布商品（multipart 多图上传） */
export function createProduct(data: ProductPayload): Promise<ProductDetail> {
  const fd = buildFormData(data)
  return http.post<ProductDetail>('/products/', fd)
}

/** PATCH /api/v1/products/{id}/ 编辑商品（仅卖家） */
export function updateProduct(id: number, data: Partial<ProductPayload>): Promise<ProductDetail> {
  const fd = buildFormData(data as ProductPayload)
  return http.patch<ProductDetail>(`/products/${id}/`, fd)
}

/** DELETE /api/v1/products/{id}/ 删除商品（仅卖家） */
export function deleteProduct(id: number): Promise<void> {
  return http.delete<void>(`/products/${id}/`)
}

/** POST /api/v1/products/{id}/off_shelf/ 卖家下架商品 */
export function offShelfProduct(id: number): Promise<{ message?: string }> {
  return http.post<{ message?: string }>(`/products/${id}/off_shelf/`)
}

/** POST /api/v1/products/{id}/favorite/ 收藏（幂等） */
export function favoriteProduct(id: number): Promise<{ favorite: boolean; favorite_count: number }> {
  return http.post<{ favorite: boolean; favorite_count: number }>(`/products/${id}/favorite/`)
}

/** DELETE /api/v1/products/{id}/favorite/ 取消收藏 */
export function unfavoriteProduct(id: number): Promise<{ favorite: boolean; favorite_count: number }> {
  return http.delete<{ favorite: boolean; favorite_count: number }>(`/products/${id}/favorite/`)
}

/** GET /api/v1/favorites/ 我的收藏（分页） */
export function getFavorites(page = 1): Promise<Paginated<FavoriteItem>> {
  return http.get<Paginated<FavoriteItem>>('/favorites/', { params: { page } })
}

/** 构造发布/编辑商品的 multipart 表单 */
function buildFormData(data: ProductPayload): FormData {
  const fd = new FormData()
  fd.append('title', data.title)
  fd.append('description', data.description ?? '')
  fd.append('price', String(data.price))
  if (data.original_price !== undefined && data.original_price !== null) {
    fd.append('original_price', String(data.original_price))
  }
  fd.append('condition', data.condition)
  fd.append('campus', data.campus ?? '')
  fd.append('location', data.location ?? '')
  fd.append('category', String(data.category))
  data.images?.forEach((file) => fd.append('images', file))
  return fd
}