import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface UIState {
  // Theme
  isDarkMode: boolean

  // Layout
  sidebarCollapsed: boolean

  // Modals
  isNewProjectModalOpen: boolean
  isVideoPlayerModalOpen: boolean

  // Loading states
  pageLoading: boolean
  globalLoading: boolean

  // Current video being played
  currentVideoUrl: string | null
  currentVideoTitle: string | null

  // Notifications
  notifications: Notification[]

  // Actions
  toggleTheme: () => void
  setDarkMode: (darkMode: boolean) => void
  toggleSidebar: () => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setNewProjectModalOpen: (open: boolean) => void
  setVideoPlayerModalOpen: (open: boolean) => void
  setPageLoading: (loading: boolean) => void
  setGlobalLoading: (loading: boolean) => void
  setCurrentVideo: (url: string | null, title?: string | null) => void
  addNotification: (notification: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set, get) => ({
        // Theme
        isDarkMode: true,

        // Layout
        sidebarCollapsed: false,

        // Modals
        isNewProjectModalOpen: false,
        isVideoPlayerModalOpen: false,

        // Loading states
        pageLoading: false,
        globalLoading: false,

        // Video player
        currentVideoUrl: null,
        currentVideoTitle: null,

        // Notifications
        notifications: [],

        // Actions
        toggleTheme: () => {
          const { isDarkMode } = get()
          set({ isDarkMode: !isDarkMode })
        },

        setDarkMode: (isDarkMode) => set({ isDarkMode }),

        toggleSidebar: () => {
          const { sidebarCollapsed } = get()
          set({ sidebarCollapsed: !sidebarCollapsed })
        },

        setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),

        setNewProjectModalOpen: (isNewProjectModalOpen) => set({ isNewProjectModalOpen }),

        setVideoPlayerModalOpen: (isVideoPlayerModalOpen) => set({ isVideoPlayerModalOpen }),

        setPageLoading: (pageLoading) => set({ pageLoading }),

        setGlobalLoading: (globalLoading) => set({ globalLoading }),

        setCurrentVideo: (currentVideoUrl, currentVideoTitle = null) => set({
          currentVideoUrl,
          currentVideoTitle
        }),

        addNotification: (notification) => {
          const id = Math.random().toString(36).substr(2, 9)
          const newNotification = { ...notification, id }
          const { notifications } = get()
          set({ notifications: [newNotification, ...notifications] })

          // Auto-remove after duration (default 5s)
          const duration = notification.duration || 5000
          setTimeout(() => {
            get().removeNotification(id)
          }, duration)
        },

        removeNotification: (id) => {
          const { notifications } = get()
          set({ notifications: notifications.filter(n => n.id !== id) })
        },

        clearNotifications: () => set({ notifications: [] })
      }),
      {
        name: 'ui-store',
        partialize: (state) => ({
          isDarkMode: state.isDarkMode,
          sidebarCollapsed: state.sidebarCollapsed
        })
      }
    ),
    {
      name: 'ui-store',
    }
  )
)

// Export notification type for use in components
export type { Notification }