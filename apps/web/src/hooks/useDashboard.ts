import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@clerk/nextjs'
import { apiClient } from '@/lib/api'

export function useDashboardStats() {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const token = await getToken()
      if (!token) throw new Error('No token available')
      return apiClient.getDashboardStats(token)
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}