import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Play,
  MoreVertical,
  ExternalLink,
  Edit,
  Trash2,
  Clock,
  FileVideo,
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import type { Project } from '../../../../shared/types'

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

interface ProjectCardProps {
  project: Project
  onEdit?: (project: Project) => void
  onDelete?: (project: Project) => void
}

const statusColors = {
  pending: 'warning',
  processing: 'secondary',
  completed: 'success',
  failed: 'destructive'
} as const

const statusLabels = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed'
} as const

export function ProjectCard({ project, onEdit, onDelete }: ProjectCardProps) {
  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  return (
    <Card className="group hover:border-[#E94560]/20 transition-all duration-200 bg-[#1A1A2E] border-[#2A2A3E]">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <Link href={`/projects/${project.id}`}>
              <h3 className="text-lg font-semibold text-white truncate group-hover:text-[#E94560] transition-colors cursor-pointer">
                {project.name}
              </h3>
            </Link>
            {project.description && (
              <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                {project.description}
              </p>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white h-8 w-8 p-0"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link href={`/projects/${project.id}`} className="flex items-center">
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Details
                </Link>
              </DropdownMenuItem>
              {onEdit && (
                <DropdownMenuItem onClick={() => onEdit(project)}>
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Project
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              {onDelete && (
                <DropdownMenuItem
                  onClick={() => onDelete(project)}
                  className="text-red-400 focus:text-red-400"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Project
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Status Badge */}
        <div className="flex items-center justify-between mb-4">
          <Badge variant={statusColors[project.status]}>
            {statusLabels[project.status]}
          </Badge>
          <span className="text-xs text-gray-400 flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {safeTimeAgo(project.createdAt || (project as any).created_at)}
          </span>
        </div>

        {/* Processing Progress */}
        {project.status === 'processing' && (
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-400">Processing</span>
              <span className="text-sm text-white">{project.processingProgress}%</span>
            </div>
            <Progress
              value={project.processingProgress}
              className="h-2"
            />
          </div>
        )}

        {/* Video Info */}
        {project.originalVideoDuration && (
          <div className="flex items-center space-x-4 text-sm text-gray-400 mb-4">
            <div className="flex items-center">
              <FileVideo className="w-4 h-4 mr-1" />
              {formatDuration(project.originalVideoDuration)}
            </div>
            {project.originalVideoSize && (
              <div>
                {(project.originalVideoSize / 1024 / 1024).toFixed(1)} MB
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {project.status === 'failed' && project.errorMessage && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg mb-4">
            <p className="text-sm text-red-400">{project.errorMessage}</p>
          </div>
        )}

        {/* Action Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {/* Clips count placeholder */}
            <span className="text-sm text-gray-400">0 clips</span>
          </div>

          <Link href={`/projects/${project.id}`}>
            <Button
              size="sm"
              className="bg-[#E94560] hover:bg-[#E94560]/90 text-white"
            >
              <Play className="w-4 h-4 mr-1" />
              View
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  )
}