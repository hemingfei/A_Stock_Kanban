import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import config from '@/config'
import { getAccessToken, refreshTokenIfNeeded } from './auth'
import type { ApiResponse } from '@/types'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
api.interceptors.request.use(
  async (config) => {
    // Try to refresh token if needed
    await refreshTokenIfNeeded()

    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle responses
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    return response
  },
  async (error) => {
    return Promise.reject(error)
  }
)

export default api
