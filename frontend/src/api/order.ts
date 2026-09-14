import type { OrderItem, OrderListParams, Paginated } from '@/types/api'
import http from '@/utils/request'

/** POST /api/v1/orders/ 创建订单（选择商品 + 可选备注） */
export function createOrder(data: { product: number; remark?: string }): Promise<OrderItem> {
  return http.post<OrderItem>('/orders/', data)
}

/** GET /api/v1/orders/ 我的订单（?role=bought|sold，支持状态筛选，分页） */
export function getOrders(params?: OrderListParams): Promise<Paginated<OrderItem>> {
  return http.get<Paginated<OrderItem>>('/orders/', { params })
}

/** GET /api/v1/orders/{id}/ 订单详情 */
export function getOrder(id: number): Promise<OrderItem> {
  return http.get<OrderItem>(`/orders/${id}/`)
}

/** POST /api/v1/orders/{id}/pay/ 模拟支付（仅买家） */
export function payOrder(id: number): Promise<OrderItem> {
  return http.post<OrderItem>(`/orders/${id}/pay/`)
}

/** POST /api/v1/orders/{id}/cancel/ 取消订单（仅待支付，仅买家） */
export function cancelOrder(id: number): Promise<OrderItem> {
  return http.post<OrderItem>(`/orders/${id}/cancel/`)
}

/** POST /api/v1/orders/{id}/ship/ 卖家发货（仅已支付，仅卖家） */
export function shipOrder(id: number): Promise<OrderItem> {
  return http.post<OrderItem>(`/orders/${id}/ship/`)
}

/** POST /api/v1/orders/{id}/confirm/ 买家确认收货（仅已发货，仅买家） */
export function confirmOrder(id: number): Promise<OrderItem> {
  return http.post<OrderItem>(`/orders/${id}/confirm/`)
}