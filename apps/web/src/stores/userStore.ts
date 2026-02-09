import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

interface User {
  id: string
  clerk_id: string
  email: string
  name: string
  first_name: string | null
  last_name: string | null
  profile_image_url: string | null
  plan: 'free' | 'starter' | 'pro' | 'enterprise'
  monthly_minutes_used: number
  monthly_minutes_limit: number
  created_at: string
}

interface UsageStats {
  monthly_minutes_used: number
  monthly_minutes_limit: number
  monthly_minutes_remaining: number
  clips_generated: number
  clips_limit: number
  plan: 'free' | 'starter' | 'pro' | 'enterprise'
}

interface UserState {
  user: User | null
  usage: UsageStats | null
  isLoading: boolean
  error: string | null

  // Actions
  setUser: (user: User | null) => void
  setUsage: (usage: UsageStats | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  resetUser: () => void
  updateUsage: (updates: Partial<UsageStats>) => void
}

export const useUserStore = create<UserState>()(
  devtools(
    (set, get) => ({
      user: null,
      usage: null,
      isLoading: false,
      error: null,

      setUser: (user) => set({ user, error: null }),

      setUsage: (usage) => set({ usage }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      resetUser: () => set({
        user: null,
        usage: null,
        error: null,
        isLoading: false
      }),

      updateUsage: (updates) => {
        const currentUsage = get().usage
        if (currentUsage) {
          set({
            usage: { ...currentUsage, ...updates }
          })
        }
      }
    }),
    {
      name: 'user-store',
    }
  )
)