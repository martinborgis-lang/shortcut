"use client"

import { useAuth } from '@clerk/nextjs'
import { useQuery } from '@tanstack/react-query'
import { apiClient, User, UsageStats } from '@/lib/api'

export function useCurrentUser() {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: ['user', 'current'],
    queryFn: async (): Promise<User> => {
      const token = await getToken()
      if (!token) {
        throw new Error('No authentication token')
      }
      return apiClient.getCurrentUser(token)
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useUserUsage() {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: ['user', 'usage'],
    queryFn: async (): Promise<UsageStats> => {
      const token = await getToken()
      if (!token) {
        throw new Error('No authentication token')
      }
      return apiClient.getUserUsage(token)
    },
    retry: false,
    staleTime: 1 * 60 * 1000, // 1 minute (usage changes more frequently)
  })
}

// Alias for compatibility with existing imports
export const useUser = useCurrentUser