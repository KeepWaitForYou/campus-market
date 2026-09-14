/**
 * Axios 统一请求封装。
 *
 * 能力：
 * 1. 自动携带 access token（请求拦截器）
 * 2. 401 时用 refresh token 静默刷新并重放原请求（并发请求排队等待）
 * 3. 统一解包后端 { code, message, data }，业务失败统一弹出提示
 * 4. 刷新失败（refresh 过期/失效）时清空登录态并跳转登录页
 *
 * baseURL 固定 /api/v1：本地开发走 Vite 代理，生产走 Nginx 反向代理。
 */
import axios, {
  AxiosError,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'

import type { ApiResponse } from '@/types/api'
import { clearAuthTokens, getAccessToken, getRefreshToken, setTokens } from './auth'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// ---------------- 401 并发刷新 ----------------
let isRefreshing = false
let waitQueue: Array<(token: string | null) => void> = []

function flushQueue(token: string | null): void {
  waitQueue.forEach((cb) => cb(token))
  waitQueue = []
}

/** 跳转登录页并携带当前地址，便于登录后回跳 */
function redirectToLogin(): void {
  clearAuthTokens()
  const redirect = encodeURIComponent(window.location.pathname + window.location.search)
  window.location.href = `/login?redirect=${redirect}`
}

// ---------------- 请求拦截器：携带 access token ----------------
service.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------------- 响应拦截器：统一解包 / 401 刷新 / 错误提示 ----------------
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    // SimpleJWT 原生响应（如 refresh）不含 code 字段，直接透传
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code !== 0) {
        ElMessage.error(res.message || '请求失败')
        throw new Error(res.message || '请求失败')
      }
      return res.data as never
    }
    return response.data as never
  },
  async (error: AxiosError<{ message?: string }>) => {
    const { response, config } = error
    const original = config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined

    // ---- 401：排除认证端点本身，其余走一次刷新重放 ----
    if (response?.status === 401 && original) {
      const url = original.url ?? ''
      const isAuthEndpoint =
        url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/refresh')

      if (isAuthEndpoint) {
        ElMessage.error(response.data?.message || '用户名或密码错误')
        redirectToLogin()
        return Promise.reject(error)
      }

      if (!original._retry) {
        original._retry = true
        const refreshToken = getRefreshToken()
        if (!refreshToken) {
          ElMessage.error('登录状态已失效，请重新登录')
          redirectToLogin()
          return Promise.reject(error)
        }

        // 已有刷新在进行：排队等待同一刷新结果
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            waitQueue.push((token) => {
              if (!token) {
                reject(error)
                return
              }
              original.headers.Authorization = `Bearer ${token}`
              resolve(service(original))
            })
          })
        }

        isRefreshing = true
        try {
          const data = await service.post<unknown, { access: string; refresh?: string }>(
            '/auth/refresh/',
            { refresh: refreshToken },
          )
          const nextAccess = data.access
          setTokens(nextAccess, data.refresh ?? refreshToken)
          flushQueue(nextAccess)
          original.headers.Authorization = `Bearer ${nextAccess}`
          return service(original)
        } catch (refreshError) {
          flushQueue(null)
          ElMessage.error('登录已过期，请重新登录')
          redirectToLogin()
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }
    }

    // ---- 其他错误：优先展示后端 message ----
    const msg = (response?.data as { message?: string } | undefined)?.message || '网络异常，请稍后重试'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

/** 类型化请求方法：拦截器已将返回值解包为业务 data */
const http = {
  get: <T>(url: string, config?: AxiosRequestConfig) => service.get<unknown, T>(url, config),
  post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    service.post<unknown, T>(url, data, config),
  patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    service.patch<unknown, T>(url, data, config),
  put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    service.put<unknown, T>(url, data, config),
  delete: <T>(url: string, config?: AxiosRequestConfig) => service.delete<unknown, T>(url, config),
}

export default http