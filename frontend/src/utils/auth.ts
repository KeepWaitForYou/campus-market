/**
 * Token 存取工具：统一管理 access / refresh token 的本地持久化。
 */

const ACCESS_KEY = 'campus_market_access'
const REFRESH_KEY = 'campus_market_refresh'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function setTokens(access: string, refresh?: string | null): void {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh) {
    localStorage.setItem(REFRESH_KEY, refresh)
  }
}

export function clearAuthTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function isLoggedIn(): boolean {
  return Boolean(getAccessToken())
}