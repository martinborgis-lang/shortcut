import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ExternalLink, Play, Clock } from 'lucide-react'

type Project = any

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

interface RecentProjectsProps {
  projects: Project[]
  isLoading?: boolean
}

const statusColors: Record<string, string> = {
  pending: 'warning',
  processing: 'secondary',
  completed: 'success',
  failed: 'destructive'
}

const statusLabels: Record<string, string> = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed'
}

export function RecentProjects({ projects, isLoading }: RecentProjectsProps) {
  if (isLoading) {
    return (
      <Card className="p-6 bg-zinc-900/50 backdrop-blur-sm border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Projects</h3>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center space-x-3">
                <div className="h-12 w-12 bg-[#2A2A3E] rounded-lg"></div>
                <div className="flex-1">
                  <div className="h-4 bg-[#2A2A3E] rounded mb-2"></div>
                  <div className="h-3 bg-[#2A2A3E] rounded w-2/3"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    )
  }

  if (projects.length === 0) {
    return (
      <Card className="p-6 bg-zinc-900/50 backdrop-blur-sm border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Projects</h3>
        <div className="text-center py-8 text-gray-400">
          <Play className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No projects yet</p>
          <p className="text-sm">Create your first project to get started</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Recent Projects</h3>
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="text-[#E94560] hover:text-[#E94560]/80">
            View all
            <ExternalLink className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </div>

      <div className="space-y-3">
        {projects.slice(0, 5).map((project: any) => (
          <Link
            key={project.id}
            href={`/projects/${project.id}`}
            className="block group"
          >
            <div className="flex items-center space-x-3 p-3 rounded-lg hover:bg-[#2A2A3E] transition-colors">
              <div className="h-12 w-12 rounded-lg bg-[#E94560]/10 flex items-center justify-center flex-shrink-0">
                <Play className="w-6 h-6 text-[#E94560]" />
              </div>

              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-white truncate group-hover:text-[#E94560] transition-colors">
                  {project.name || project.title || 'Untitled'}
                </h4>
                <div className="flex items-center space-x-2 mt-1">
                  <Badge variant={(statusColors[project.status] || 'secondary') as any}>
                    {statusLabels[project.status] || project.status || 'Unknown'}
                  </Badge>
                  <span className="text-xs text-gray-400 flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {safeTimeAgo(project.createdAt || project.created_at)}
                  </span>
                </div>
              </div>

              {project.status === 'processing' && (
                <div className="text-right">
                  <div className="text-sm text-gray-400">{project.processingProgress || 0}%</div>
                  <div className="w-16 h-1 bg-[#2A2A3E] rounded-full mt-1">
                    <div
                      className="h-full bg-[#E94560] rounded-full transition-all duration-300"
                      style={{ width: `${project.processingProgress || 0}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </Link>
        ))}
      </div>
    </Card>
  )
}