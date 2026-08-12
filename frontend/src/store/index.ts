import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { User, Board, Quote, AuthState } from '@/types'
import { getAccessToken, getRefreshToken, clearTokens, setTokens as saveTokens } from '@/services/auth'

// === Auth Store ===
interface AuthStore extends AuthState {
  setUser: (user: User | null) => void
  setTokens: (accessToken: string, refreshToken: string, expiresIn: number) => void
  clearAuth: () => void
  initAuth: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      setUser: (user) => set({ user }),

      setTokens: (accessToken, refreshToken, expiresIn) => {
        saveTokens(accessToken, refreshToken, expiresIn)
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
        })
      },

      clearAuth: () => {
        clearTokens()
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      initAuth: () => {
        const accessToken = getAccessToken()
        const refreshToken = getRefreshToken()
        if (accessToken) {
          set({
            accessToken,
            refreshToken,
            isAuthenticated: true,
          })
        }
      },
    }),
    {
      name: 'astock-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Don't persist tokens here, we handle separately
        user: state.user,
      }),
    }
  )
)

// === Quotes Store ===
interface QuoteStore {
  quotes: Map<string, Quote>
  updateQuote: (quote: Quote) => void
  updateQuotes: (quotes: Quote[]) => void
  getQuote: (code: string) => Quote | undefined
  clearQuotes: () => void
}

export const useQuoteStore = create<QuoteStore>((set, get) => ({
  quotes: new Map(),

  updateQuote: (quote) =>
    set((state) => {
      const newQuotes = new Map(state.quotes)
      newQuotes.set(quote.code, quote)
      return { quotes: newQuotes }
    }),

  updateQuotes: (newQuotes) =>
    set((state) => {
      const updatedQuotes = new Map(state.quotes)
      newQuotes.forEach((quote) => updatedQuotes.set(quote.code, quote))
      return { quotes: updatedQuotes }
    }),

  getQuote: (code) => get().quotes.get(code),

  clearQuotes: () => set({ quotes: new Map() }),
}))

// === Boards Store ===
interface BoardsStore {
  boards: Board[]
  isLoading: boolean
  setBoards: (boards: Board[]) => void
  addBoard: (board: Board) => void
  updateBoard: (id: number, data: Partial<Board>) => void
  deleteBoard: (id: number) => void
  addStockToBoard: (boardId: number, stock: any) => void
  removeStockFromBoard: (boardId: number, stockId: number) => void
  setLoading: (loading: boolean) => void
}

export const useBoardStore = create<BoardsStore>((set, get) => ({
  boards: [],
  isLoading: false,

  setBoards: (boards) => set({ boards, isLoading: false }),

  addBoard: (board) =>
    set((state) => ({
      boards: [...state.boards, board],
    })),

  updateBoard: (id, data) =>
    set((state) => ({
      boards: state.boards.map((b) => (b.id === id ? { ...b, ...data } : b)),
    })),

  deleteBoard: (id) =>
    set((state) => ({
      boards: state.boards.filter((b) => b.id !== id),
    })),

  addStockToBoard: (boardId, stock) =>
    set((state) => ({
      boards: state.boards.map((b) =>
        b.id === boardId ? { ...b, stocks: [...b.stocks, stock] } : b
      ),
    })),

  removeStockFromBoard: (boardId, stockId) =>
    set((state) => ({
      boards: state.boards.map((b) =>
        b.id === boardId
          ? { ...b, stocks: b.stocks.filter((s) => s.id !== stockId) }
          : b
      ),
    })),

  setLoading: (loading) => set({ isLoading: loading }),
}))

// === UI Store ===
interface UIStore {
  theme: 'light' | 'dark'
  sidebarOpen: boolean
  refreshInterval: number
  setTheme: (theme: 'light' | 'dark') => void
  toggleSidebar: () => void
  setRefreshInterval: (interval: number) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      refreshInterval: 5,

      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setRefreshInterval: (interval) => set({ refreshInterval: interval }),
    }),
    {
      name: 'astock-ui',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

// Helper selectors
export const useAllStockCodes = () => {
  return useBoardStore((state) =>
    state.boards.flatMap((b) => b.stocks.map((s) => s.code))
  )
}

export const useBoardQuotes = (boardId: number) => {
  const board = useBoardStore((state) => state.boards.find((b) => b.id === boardId))
  const getQuote = useQuoteStore((state) => state.getQuote)
  return board?.stocks.map((stock) => getQuote(stock.code)).filter(Boolean) as Quote[]
}
