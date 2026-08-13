// Configuration
const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const config = {
  apiUrl: apiBase,
  wsUrl: apiBase, // Will be converted to ws/wss in ws.ts
}

export default config
