// User types
export interface User {
  id: number
  username: string
  created_at: string
}

export interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
}

// Board types
export interface Board {
  id: number
  user_id: number
  name: string
  sort_order: number
  created_at: string
  updated_at: string
  stocks: Stock[]
}

export interface BoardCreate {
  name: string
}

export interface BoardUpdate {
  name?: string
  sort_order?: number
}

// Stock types
export interface Stock {
  id: number
  board_id: number
  code: string
  name: string
  sort_order: number
  created_at: string
}

export interface StockCreate {
  code: string
  name: string
}

// Quote types
export interface Quote {
  code: string
  name: string
  price: number
  pre_close: number
  open: number
  high: number
  low: number
  volume: number
  amount: number
  change: number
  change_percent: number
  bid1?: number
  bid1_volume?: number
  ask1?: number
  ask1_volume?: number
  timestamp: number
  stale?: boolean
}

// K-line types
export interface KLineItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  change: number
  change_percent: number
}

export type KLinePeriod = '1d' | '1w' | '1M' | '5m' | '15m' | '30m' | '60m'

// User settings types
export interface UserSetting {
  id: number
  user_id: number
  refresh_interval: number
  data_sources: string
  theme: 'light' | 'dark'
  created_at: string
  updated_at: string
}

export interface UserSettingUpdate {
  refresh_interval?: number
  data_sources?: string
  theme?: 'light' | 'dark'
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
  details?: Array<{ field: string; message: string }>
  request_id?: string
}

// Login/Register types
export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  password: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

// WebSocket message types
export interface WSMessage {
  type: string
}

export interface WSSubscribe extends WSMessage {
  type: 'subscribe'
  codes: string[]
}

export interface WSUnsubscribe extends WSMessage {
  type: 'unsubscribe'
  codes: string[]
}

export interface WSPong extends WSMessage {
  type: 'pong'
}

export interface WSPing extends WSMessage {
  type: 'ping'
}

export interface WSQuotesData {
  quotes: Quote[]
}

export interface WSQuotesUpdate extends WSMessage {
  type: 'quotes'
  data: WSQuotesData
}

export interface WSError extends WSMessage {
  type: 'error'
  code: string
  message: string
}

export type WSMessageType = WSSubscribe | WSUnsubscribe | WSPong | WSPing | WSQuotesUpdate | WSError
