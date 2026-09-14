/**
 * 业务常量：商品成色 / 商品状态 / 订单状态的中文选项。
 */

export const PRODUCT_CONDITIONS = [
  { value: 'brand_new', label: '全新' },
  { value: 'like_new', label: '几乎全新' },
  { value: 'lightly_used', label: '轻微使用' },
  { value: 'used', label: '明显使用' },
  { value: 'damaged', label: '有瑕疵/破损' },
] as const

export const PRODUCT_STATUS_LABELS: Record<string, string> = {
  pending: '待审核',
  on_sale: '在售',
  off_shelf: '已下架',
  sold: '已售出',
  rejected: '审核不通过',
}

export const ORDER_STATUS_LABELS: Record<string, string> = {
  pending: '待支付',
  paid: '已支付',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消',
}

export const ORDER_STATUS_TAGS: Record<string, 'warning' | 'primary' | 'info' | 'success' | 'danger'> = {
  pending: 'warning',
  paid: 'primary',
  shipped: 'info',
  completed: 'success',
  cancelled: 'danger',
}

/** 常用交易校区（可在发布页自定义） */
export const CAMPUS_OPTIONS = ['校本部', '东校区', '西校区', '南校区', '北校区']

/** 价格排序选项 */
export const PRICE_SORTS = [
  { value: '-price', label: '价格从高到低' },
  { value: 'price', label: '价格从低到高' },
  { value: '-created_at', label: '最新发布' },
  { value: '-view_count', label: '浏览最多' },
  { value: '-favorite_count', label: '收藏最多' },
]