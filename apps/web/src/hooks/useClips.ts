import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import type {
  Clip,
  UpdateClipRequest,
  RegenerateClipRequest,
  ClipDetailResponse,
  ClipDownloadResponse,
  ClipsListResponse,
  BulkDownloadRequest,
  BulkDownloadResponse
} from '../../../shared/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// API functions
const clipsApi = {
  // Get clip detail with signed URLs
  getClip: async (clipId: string): Promise<ClipDetailResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/${clipId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch clip: ${response.statusText}`)
    }
    return response.json()
  },

  // Update clip properties
  updateClip: async (clipId: string, data: UpdateClipRequest): Promise<Clip> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/${clipId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to update clip: ${response.statusText}`)
    }
    return response.json()
  },

  // Regenerate clip
  regenerateClip: async (clipId: string, data: RegenerateClipRequest = {}): Promise<any> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/${clipId}/regenerate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to regenerate clip: ${response.statusText}`)
    }
    return response.json()
  },

  // Get download URL
  getDownloadUrl: async (clipId: string): Promise<ClipDownloadResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/${clipId}/download`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to get download URL: ${response.statusText}`)
    }
    return response.json()
  },

  // Delete clip
  deleteClip: async (clipId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/${clipId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to delete clip: ${response.statusText}`)
    }
  },

  // List clips with filters and sorting
  listClips: async (params: {
    projectId?: string
    status?: string
    subtitleStyle?: string
    isFavorite?: boolean
    minViralScore?: number
    maxViralScore?: number
    minDuration?: number
    maxDuration?: number
    sortBy?: string
    sortOrder?: string
    page?: number
    size?: number
  } = {}): Promise<ClipsListResponse> => {
    const searchParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })

    const response = await fetch(`${API_BASE_URL}/api/clips?${searchParams}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (!response.ok) {
      throw new Error(`Failed to fetch clips: ${response.statusText}`)
    }
    return response.json()
  },

  // Bulk download clips
  bulkDownload: async (data: BulkDownloadRequest): Promise<BulkDownloadResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/clips/bulk-download`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to create bulk download: ${response.statusText}`)
    }
    return response.json()
  },

  // Download all clips from a project
  downloadProjectClips: async (projectId: string): Promise<BulkDownloadResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/download-all`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `Failed to download project clips: ${response.statusText}`)
    }
    return response.json()
  }
}

// React Query hooks

/**
 * Hook to fetch a single clip with detailed information and signed URLs
 * Critères PRD F5-01, F5-06: Get clip details for the detail page
 */
export function useClip(clipId: string) {
  return useQuery({
    queryKey: ['clips', clipId],
    queryFn: () => clipsApi.getClip(clipId),
    enabled: !!clipId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

/**
 * Hook to fetch clips list with filtering and sorting
 * Critères PRD F5-11: Tri et filtrage par score de viralité, date, durée
 */
export function useClips(params: Parameters<typeof clipsApi.listClips>[0] = {}) {
  return useQuery({
    queryKey: ['clips', 'list', params],
    queryFn: () => clipsApi.listClips(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook to update clip properties (title, timing, subtitle style)
 * Critères PRD F5-02, F5-07, F5-08, F5-09: Édition des propriétés du clip
 */
export function useUpdateClip() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ clipId, data }: { clipId: string; data: UpdateClipRequest }) =>
      clipsApi.updateClip(clipId, data),
    onSuccess: (updatedClip, { clipId }) => {
      // Update the clip in cache
      queryClient.setQueryData(['clips', clipId], (old: ClipDetailResponse | undefined) => {
        if (old) {
          return { ...old, ...updatedClip }
        }
        return old
      })

      // Invalidate clips list to refresh
      queryClient.invalidateQueries({ queryKey: ['clips', 'list'] })

      toast.success('Clip updated successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to update clip: ${error.message}`)
    }
  })
}

/**
 * Hook to regenerate clip with new settings
 * Critères PRD F5-03: Re-traite le clip avec les nouveaux paramètres
 */
export function useRegenerateClip() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ clipId, data }: { clipId: string; data?: RegenerateClipRequest }) =>
      clipsApi.regenerateClip(clipId, data || {}),
    onSuccess: (result, { clipId }) => {
      // Invalidate clip data to refetch
      queryClient.invalidateQueries({ queryKey: ['clips', clipId] })
      queryClient.invalidateQueries({ queryKey: ['clips', 'list'] })

      toast.success(`Clip regeneration started. Estimated completion: ${result.estimated_duration_seconds}s`)
    },
    onError: (error: Error) => {
      toast.error(`Failed to regenerate clip: ${error.message}`)
    }
  })
}

/**
 * Hook to get download URL for a clip
 * Critères PRD F5-04, F5-10: Download direct du clip final
 */
export function useDownloadClip() {
  return useMutation({
    mutationFn: (clipId: string) => clipsApi.getDownloadUrl(clipId),
    onSuccess: (downloadData) => {
      // Open download URL in new tab
      window.open(downloadData.download_url, '_blank')
      toast.success(`Download started. File: ${downloadData.filename}`)
    },
    onError: (error: Error) => {
      toast.error(`Failed to download clip: ${error.message}`)
    }
  })
}

/**
 * Hook to delete a clip
 * Critères PRD F5-05: Supprime le clip de S3 et de la DB
 */
export function useDeleteClip() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (clipId: string) => clipsApi.deleteClip(clipId),
    onSuccess: (_, clipId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ['clips', clipId] })

      // Update lists
      queryClient.invalidateQueries({ queryKey: ['clips', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })

      toast.success('Clip deleted successfully')
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete clip: ${error.message}`)
    }
  })
}

/**
 * Hook for bulk downloading multiple clips
 * Critères PRD F5-12: Batch download
 */
export function useBulkDownload() {
  return useMutation({
    mutationFn: (data: BulkDownloadRequest) => clipsApi.bulkDownload(data),
    onSuccess: (downloadData) => {
      // Open download URL in new tab
      window.open(downloadData.download_url, '_blank')
      toast.success(`Bulk download started. ${downloadData.clips_count} clips in ${downloadData.filename}`)
    },
    onError: (error: Error) => {
      toast.error(`Failed to create bulk download: ${error.message}`)
    }
  })
}

/**
 * Hook to download all clips from a project
 * Critères PRD F5-12: Télécharger tous les clips d'un projet en ZIP
 */
export function useDownloadProjectClips() {
  return useMutation({
    mutationFn: (projectId: string) => clipsApi.downloadProjectClips(projectId),
    onSuccess: (downloadData) => {
      // Open download URL in new tab
      window.open(downloadData.download_url, '_blank')
      toast.success(`Project download started. ${downloadData.clips_count} clips in ${downloadData.filename}`)
    },
    onError: (error: Error) => {
      toast.error(`Failed to download project clips: ${error.message}`)
    }
  })
}

/**
 * Hook to toggle clip favorite status
 */
export function useToggleFavorite() {
  const updateClip = useUpdateClip()

  return useMutation({
    mutationFn: ({ clipId, currentValue }: { clipId: string; currentValue: boolean }) =>
      updateClip.mutateAsync({
        clipId,
        data: { is_favorite: !currentValue }
      }),
    onError: (error: Error) => {
      toast.error(`Failed to toggle favorite: ${error.message}`)
    }
  })
}

/**
 * Hook to rate a clip (1-5 stars)
 */
export function useRateClip() {
  const updateClip = useUpdateClip()

  return useMutation({
    mutationFn: ({ clipId, rating }: { clipId: string; rating: number }) =>
      updateClip.mutateAsync({
        clipId,
        data: { user_rating: rating }
      }),
    onError: (error: Error) => {
      toast.error(`Failed to rate clip: ${error.message}`)
    }
  })
}

// Utility functions for clip operations
export const clipUtils = {
  /**
   * Format clip duration for display
   */
  formatDuration: (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  },

  /**
   * Get viral score color class
   */
  getViralScoreColor: (score?: number): string => {
    if (!score) return 'text-gray-400'
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  },

  /**
   * Get viral score label
   */
  getViralScoreLabel: (score?: number): string => {
    if (!score) return 'Unknown'
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  },

  /**
   * Get status color for badge
   */
  getStatusColor: (status: string): 'warning' | 'secondary' | 'success' | 'destructive' => {
    switch (status) {
      case 'pending': return 'warning'
      case 'processing': return 'secondary'
      case 'ready': return 'success'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  },

  /**
   * Check if clip can be edited (not processing)
   */
  canEdit: (clip: Clip): boolean => {
    return !['processing', 'pending_regeneration'].includes(clip.status)
  },

  /**
   * Check if clip can be downloaded
   */
  canDownload: (clip: Clip): boolean => {
    return clip.status === 'ready' && !!clip.s3_key
  }
}