import config from '@/config'
import { getAccessToken } from './auth'
import type { Quote, WSMessageType, WSSubscribe, WSUnsubscribe, WSPong, WSQuotesUpdate, WSError } from '@/types'

type WebSocketStatus = 'disconnected' | 'connecting' | 'connected'

type WSHandler = (data: WSMessageType) => void
type StatusHandler = (status: WebSocketStatus) => void

class QuoteWebSocket {
  private ws: WebSocket | null = null
  private status: WebSocketStatus = 'disconnected'
  private subscriptions: Set<string> = new Set()
  private handlers: WSHandler[] = []
  private statusHandlers: StatusHandler[] = []
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private pingTimer: ReturnType<typeof setInterval> | null = null

  constructor() {}

  // Subscribe to quote updates
  subscribe(codes: string[]) {
    codes.forEach(code => this.subscriptions.add(code))
    if (this.status === 'connected' && this.ws) {
      this.send({
        type: 'subscribe',
        codes,
      } as WSSubscribe)
    }
  }

  // Unsubscribe from quote updates
  unsubscribe(codes: string[]) {
    codes.forEach(code => this.subscriptions.delete(code))
    if (this.status === 'connected' && this.ws) {
      this.send({
        type: 'unsubscribe',
        codes,
      } as WSUnsubscribe)
    }
  }

  // Add a message handler
  onMessage(handler: WSHandler) {
    this.handlers.push(handler)
  }

  // Remove a message handler
  offMessage(handler: WSHandler) {
    const index = this.handlers.indexOf(handler)
    if (index > -1) {
      this.handlers.splice(index, 1)
    }
  }

  // Add a status change handler
  onStatusChange(handler: StatusHandler) {
    this.statusHandlers.push(handler)
  }

  // Remove a status change handler
  offStatusChange(handler: StatusHandler) {
    const index = this.statusHandlers.indexOf(handler)
    if (index > -1) {
      this.statusHandlers.splice(index, 1)
    }
  }

  // Connect to WebSocket server
  connect() {
    if (this.status !== 'disconnected') return

    const token = getAccessToken()
    if (!token) {
      console.warn('No access token, cannot connect to WebSocket')
      return
    }

    this.setStatus('connecting')

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/quotes?token=${token}`

    try {
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.setStatus('connected')
        this.reconnectAttempts = 0

        // Subscribe to current codes
        if (this.subscriptions.size > 0) {
          this.send({
            type: 'subscribe',
            codes: Array.from(this.subscriptions),
          } as WSSubscribe)
        }

        // Start ping timer
        this.pingTimer = setInterval(() => {
          // Server sends ping, we just need to listen
        }, 30000)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WSMessageType
          this.handleMessage(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        this.setStatus('disconnected')
        this.cleanup()
        this.scheduleReconnect()
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.setStatus('disconnected')
      this.scheduleReconnect()
    }
  }

  // Disconnect from WebSocket server
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.cleanup()
  }

  private cleanup() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private setStatus(status: WebSocketStatus) {
    this.status = status
    this.statusHandlers.forEach(handler => handler(status))
  }

  private send(message: WSMessageType) {
    if (this.ws && this.status === 'connected') {
      this.ws.send(JSON.stringify(message))
    }
  }

  private handleMessage(message: WSMessageType) {
    switch (message.type) {
      case 'ping':
        this.send({ type: 'pong' } as WSPong)
        break
      case 'quotes':
      case 'quote':
      case 'error':
        this.handlers.forEach(handler => handler(message))
        break
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000)
    console.log(`Reconnecting in ${delay}ms...`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }
}

// Singleton instance
const ws = new QuoteWebSocket()

export default ws
