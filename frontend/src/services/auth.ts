import api from './api'
import { AuthResponse, LoginData, RegisterData, ApiResponse } from '@/types'

// Token storage keys
const ACCESS_TOKEN_KEY = 'astock_access_token'
const REFRESH_TOKEN_KEY = 'astock_refresh_token'
const TOKEN_EXPIRES_AT_KEY = 'astock_token_expires_at'

// Get tokens from storage
export const getAccessToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export const getTokenExpiresAt = (): number | null => {
  const value = localStorage.getItem(TOKEN_EXPIRES_AT_KEY)
  return value ? parseInt(value, 10) : null
}

// Set tokens in storage
export const setTokens = (accessToken: string, refreshToken: string, expiresIn: number) => {
  const expiresAt = Date.now() + expiresIn * 1000
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  localStorage.setItem(TOKEN_EXPIRES_AT_KEY, expiresAt.toString())
}

// Clear tokens from storage
export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(TOKEN_EXPIRES_AT_KEY)
}

// Check if token needs refresh (within 5 minutes of expiration)
export const needsRefresh = (): boolean => {
  const expiresAt = getTokenExpiresAt()
  if (!expiresAt) return false
  return Date.now() > expiresAt - 5 * 60 * 1000
}

// Refresh token
let refreshPromise: Promise<void> | null = null

export const refreshTokenIfNeeded = async (): Promise<void> => {
  if (!needsRefresh()) return

  const refreshToken = getRefreshToken()
  if (!refreshToken) return

  // Avoid multiple concurrent refresh requests
  if (refreshPromise) {
    return refreshPromise
  }

  refreshPromise = (async () => {
    try {
      const response = await api.post<ApiResponse<{ access_token: string, token_type: string, expires_in: number }>>(
        '/api/v1/auth/refresh',
        { refresh_token: refreshToken }
      )

      if (response.data.success && response.data.data) {
        const { access_token, expires_in } = response.data.data
        // Update access token, keep refresh token
        const currentRefreshToken = getRefreshToken()
        if (currentRefreshToken) {
          setTokens(access_token, currentRefreshToken, expires_in)
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearTokens()
      window.location.href = '/login'
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}

// Auth API functions
export const login = async (data: LoginData): Promise<AuthResponse> => {
  const formData = new FormData()
  formData.append('username', data.username)
  formData.append('password', data.password)

  const response = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Login failed')
  }

  const authData = response.data.data!
  setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
  return authData
}

export const register = async (data: RegisterData): Promise<AuthResponse> => {
  const response = await api.post<ApiResponse<AuthResponse>>('/api/v1/auth/register', data)

  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Registration failed')
  }

  const authData = response.data.data!
  setTokens(authData.access_token, authData.refresh_token, authData.expires_in)
  return authData
}

export const logout = async (): Promise<void> => {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    try {
      await api.post('/api/v1/auth/logout', { refresh_token: refreshToken })
    } catch (error) {
      console.error('Logout API failed:', error)
    }
  }
  clearTokens()
}

export const getCurrentUser = async () => {
  const response = await api.get<ApiResponse<any>>('/api/v1/auth/me')
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Failed to get user')
  }
  return response.data.data
}
