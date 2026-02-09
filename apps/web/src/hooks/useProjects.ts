import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '@clerk/nextjs'
import { apiClient, type CreateProjectRequest } from '@/lib/api'
import { useProjectStore } from '@/stores'
import type { Project } from '../../../shared/types'

export function useProjects() {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const token = await getToken()
      return apiClient.getProjects(token)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useProject(projectId: string) {
  const { getToken } = useAuth()

  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: async () => {
      const token = await getToken()
      return apiClient.getProject(projectId, token)
    },
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  })
}

export function useCreateProject() {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const { addProject } = useProjectStore()

  return useMutation({
    mutationFn: async (data: CreateProjectRequest) => {
      const token = await getToken()
      return apiClient.createProject(data, token)
    },
    onSuccess: (newProject: Project) => {
      // Update cache
      queryClient.invalidateQueries({ queryKey: ['projects'] })

      // Update store
      addProject(newProject)
    },
  })
}

export function useUpdateProject() {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const { updateProject } = useProjectStore()

  return useMutation({
    mutationFn: async ({ projectId, data }: { projectId: string; data: Partial<Project> }) => {
      const token = await getToken()
      return apiClient.updateProject(projectId, data, token)
    },
    onSuccess: (updatedProject: Project) => {
      // Update cache
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['projects', updatedProject.id] })

      // Update store
      updateProject(updatedProject.id, updatedProject)
    },
  })
}

export function useDeleteProject() {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const { removeProject } = useProjectStore()

  return useMutation({
    mutationFn: async (projectId: string) => {
      const token = await getToken()
      return apiClient.deleteProject(projectId, token)
    },
    onSuccess: (_, projectId) => {
      // Update cache
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.removeQueries({ queryKey: ['projects', projectId] })

      // Update store
      removeProject(projectId)
    },
  })
}

export function useProcessVideoFromUrl() {
  const { getToken } = useAuth()
  const queryClient = useQueryClient()
  const { addProject } = useProjectStore()

  return useMutation({
    mutationFn: async ({ url, maxClips }: { url: string; maxClips?: number }) => {
      console.log('useProcessVideoFromUrl mutationFn called with:', { url, maxClips })

      const token = await getToken()
      console.log('Token obtained:', token ? 'Token exists' : 'No token')

      const result = await apiClient.processVideoFromUrl(url, maxClips, token)
      console.log('API call result:', result)

      return result
    },
    onSuccess: (newProject: Project) => {
      console.log('useProcessVideoFromUrl onSuccess called with:', newProject)

      // Update cache
      queryClient.invalidateQueries({ queryKey: ['projects'] })

      // Update store
      addProject(newProject)
    },
    onError: (error) => {
      console.error('useProcessVideoFromUrl onError called with:', error)
    }
  })
}