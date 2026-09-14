import type { CategoryItem } from '@/types/api'
import http from '@/utils/request'

/** GET /api/v1/categories/ 启用分类列表（带在售商品数，不分页） */
export function getCategories(): Promise<CategoryItem[]> {
  return http.get<CategoryItem[]>('/categories/')
}