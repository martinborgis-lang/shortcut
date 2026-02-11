'use client'

import { useState, useMemo } from 'react'
import { Plus, Grid, List } from 'lucide-react'

function safeTimeAgo(dateValue: any): string {
  try {
    if (!dateValue) return 'Just now'
    const date = new Date(dateValue)
    if (!date || isNaN(date.getTime())) return 'Just now'
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
    if (seconds < 0) return 'Just now'
    if (seconds < 60) return 'Just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  } catch (e) {
    return 'Just now'
  }
}
import { Button } from '@/components/ui/button'
import { ProjectCard } from '@/components/projects/project-card'
import { ProjectFilters } from '@/components/projects/project-filters'
import { EmptyProjects } from '@/components/shared/empty-state'
import { ProjectCardSkeleton } from '@/components/shared/loading-skeleton'
import { useUIStore } from '@/stores'
import { useProjects } from '@/hooks'
// Type will be defined later - using any for now
type Project = any

type ViewMode = 'grid' | 'list'
type SortBy = 'created' | 'updated' | 'name'
type SortOrder = 'asc' | 'desc'

export default function ProjectsPage() {
  const { setNewProjectModalOpen } = useUIStore()
  const { data: projects = [], isLoading, error } = useProjects()

  // Local state for filters and view
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<SortBy>('created')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')

  // Filter and sort projects
  const filteredAndSortedProjects = useMemo(() => {
    let filtered = projects

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(project =>
        project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    // Apply status filter
    if (statusFilter) {
      filtered = filtered.filter(project => project.status === statusFilter)
    }

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'created':
          const aCreated = new Date(a.createdAt || (a as any).created_at || 0).getTime();
          const bCreated = new Date(b.createdAt || (b as any).created_at || 0).getTime();
          comparison = isNaN(aCreated) ? 1 : isNaN(bCreated) ? -1 : aCreated - bCreated;
          break
        case 'updated':
          const aUpdated = new Date(a.updatedAt || (a as any).updated_at || 0).getTime();
          const bUpdated = new Date(b.updatedAt || (b as any).updated_at || 0).getTime();
          comparison = isNaN(aUpdated) ? 1 : isNaN(bUpdated) ? -1 : aUpdated - bUpdated;
          break
      }

      return sortOrder === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [projects, searchQuery, statusFilter, sortBy, sortOrder])

  const handleSortChange = (newSortBy: SortBy, newSortOrder: SortOrder) => {
    setSortBy(newSortBy)
    setSortOrder(newSortOrder)
  }

  const handleEditProject = (project: Project) => {
    // TODO: Implement edit project modal
    console.log('Edit project:', project)
  }

  const handleDeleteProject = (project: Project) => {
    // TODO: Implement delete confirmation dialog
    console.log('Delete project:', project)
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-400 mb-2">Failed to load projects</p>
          <p className="text-gray-400 text-sm">Please try refreshing the page</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Projects</h1>
          <p className="text-gray-400">
            Manage your video projects and generated clips
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* View Mode Toggle */}
          <div className="flex items-center border border-[#2A2A3E] rounded-lg">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className={viewMode === 'grid' ? 'bg-[#E94560] text-white' : 'text-gray-400'}
            >
              <Grid className="w-4 h-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className={viewMode === 'list' ? 'bg-[#E94560] text-white' : 'text-gray-400'}
            >
              <List className="w-4 h-4" />
            </Button>
          </div>

          {/* New Project Button */}
          <Button
            onClick={() => setNewProjectModalOpen(true)}
            className="bg-[#E94560] hover:bg-[#E94560]/90 text-white"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </div>
      </div>

      {/* Filters */}
      <ProjectFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />

      {/* Projects Count */}
      <div className="flex items-center justify-between text-sm text-gray-400">
        <span>
          {isLoading ? 'Loading...' : `${filteredAndSortedProjects.length} project${filteredAndSortedProjects.length !== 1 ? 's' : ''}`}
        </span>
        {searchQuery && (
          <span>Showing results for "{searchQuery}"</span>
        )}
      </div>

      {/* Projects Grid/List */}
      {isLoading ? (
        <div className={viewMode === 'grid'
          ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
          : 'space-y-4'
        }>
          {Array.from({ length: 6 }).map((_, i) => (
            <ProjectCardSkeleton key={i} />
          ))}
        </div>
      ) : filteredAndSortedProjects.length === 0 ? (
        projects.length === 0 ? (
          <EmptyProjects onCreateProject={() => setNewProjectModalOpen(true)} />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-2">No projects match your filters</p>
            <Button
              variant="outline"
              onClick={() => {
                setSearchQuery('')
                setStatusFilter(null)
              }}
              className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]"
            >
              Clear filters
            </Button>
          </div>
        )
      ) : (
        <div className={viewMode === 'grid'
          ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
          : 'space-y-4'
        }>
          {filteredAndSortedProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onEdit={handleEditProject}
              onDelete={handleDeleteProject}
            />
          ))}
        </div>
      )}
    </div>
  )
}