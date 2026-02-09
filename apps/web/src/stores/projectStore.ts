import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { Project, Clip } from '../../../shared/types'

interface ProjectState {
  projects: Project[]
  currentProject: Project | null
  clips: Record<string, Clip[]> // projectId -> clips
  isLoading: boolean
  error: string | null

  // Actions
  setProjects: (projects: Project[]) => void
  addProject: (project: Project) => void
  updateProject: (projectId: string, updates: Partial<Project>) => void
  removeProject: (projectId: string) => void
  setCurrentProject: (project: Project | null) => void
  setClips: (projectId: string, clips: Clip[]) => void
  addClip: (projectId: string, clip: Clip) => void
  updateClip: (projectId: string, clipId: string, updates: Partial<Clip>) => void
  removeClip: (projectId: string, clipId: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  resetStore: () => void
}

export const useProjectStore = create<ProjectState>()(
  devtools(
    (set, get) => ({
      projects: [],
      currentProject: null,
      clips: {},
      isLoading: false,
      error: null,

      setProjects: (projects) => set({ projects, error: null }),

      addProject: (project) => {
        const { projects } = get()
        set({ projects: [project, ...projects] })
      },

      updateProject: (projectId, updates) => {
        const { projects, currentProject } = get()
        const updatedProjects = projects.map(p =>
          p.id === projectId ? { ...p, ...updates } : p
        )
        const updatedCurrentProject = currentProject?.id === projectId
          ? { ...currentProject, ...updates }
          : currentProject

        set({
          projects: updatedProjects,
          currentProject: updatedCurrentProject
        })
      },

      removeProject: (projectId) => {
        const { projects, currentProject } = get()
        const updatedProjects = projects.filter(p => p.id !== projectId)
        const updatedCurrentProject = currentProject?.id === projectId
          ? null
          : currentProject

        set({
          projects: updatedProjects,
          currentProject: updatedCurrentProject
        })
      },

      setCurrentProject: (project) => set({ currentProject: project }),

      setClips: (projectId, clips) => {
        const { clips: currentClips } = get()
        set({
          clips: {
            ...currentClips,
            [projectId]: clips
          }
        })
      },

      addClip: (projectId, clip) => {
        const { clips } = get()
        const projectClips = clips[projectId] || []
        set({
          clips: {
            ...clips,
            [projectId]: [clip, ...projectClips]
          }
        })
      },

      updateClip: (projectId, clipId, updates) => {
        const { clips } = get()
        const projectClips = clips[projectId] || []
        const updatedClips = projectClips.map(c =>
          c.id === clipId ? { ...c, ...updates } : c
        )

        set({
          clips: {
            ...clips,
            [projectId]: updatedClips
          }
        })
      },

      removeClip: (projectId, clipId) => {
        const { clips } = get()
        const projectClips = clips[projectId] || []
        const updatedClips = projectClips.filter(c => c.id !== clipId)

        set({
          clips: {
            ...clips,
            [projectId]: updatedClips
          }
        })
      },

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error }),

      resetStore: () => set({
        projects: [],
        currentProject: null,
        clips: {},
        isLoading: false,
        error: null
      })
    }),
    {
      name: 'project-store',
    }
  )
)