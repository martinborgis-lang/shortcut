'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'

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
import Link from 'next/link'
import {
  ArrowLeft,
  Play,
  Download,
  Share2,
  MoreVertical,
  TrendingUp,
  Clock,
  FileVideo,
  Grid3X3,
  List,
  Filter
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ClipCard } from '@/components/clips/clip-card'
import { VideoPlayer } from '@/components/shared/video-player'
import { EmptyClips } from '@/components/shared/empty-state'
import { ClipCardSkeleton } from '@/components/shared/loading-skeleton'
import { useProject, useClips } from '@/hooks'
import { useProjectStore } from '@/stores'
import { toast } from 'sonner'
// Type will be defined later - using any for now
type Clip = any

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string

  const { data: project, isLoading: projectLoading, error: projectError } = useProject(projectId)
  const { data: clips = [], isLoading: clipsLoading } = useClips({ projectId })
  const { setCurrentProject } = useProjectStore()

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState<'created' | 'viral' | 'duration'>('created')

  useEffect(() => {
    if (project) {
      setCurrentProject(project)
    }
  }, [project, setCurrentProject])

  if (projectLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-[#2A2A3E] rounded w-64 mb-4"></div>
          <div className="h-4 bg-[#2A2A3E] rounded w-96"></div>
        </div>
      </div>
    )
  }

  if (projectError || !project) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-red-400 mb-2">Project not found</p>
          <Link href="/projects">
            <Button variant="outline" className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]">
              Back to Projects
            </Button>
          </Link>
        </div>
      </div>
    )
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

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'Unknown'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const sortedClips = [...clips].sort((a, b) => {
    switch (sortBy) {
      case 'viral':
        return (b.viralScore || 0) - (a.viralScore || 0)
      case 'duration':
        return b.duration - a.duration
      case 'created':
      default:
        const aTime = new Date(a.createdAt || (a as any).created_at || 0).getTime();
        const bTime = new Date(b.createdAt || (b as any).created_at || 0).getTime();
        return isNaN(bTime) ? -1 : isNaN(aTime) ? 1 : bTime - aTime
    }
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-4">
          <Link href="/projects">
            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>

          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-2xl font-bold text-white">{project.name}</h1>
              <Badge variant={statusColors[project.status as keyof typeof statusColors] || 'secondary'}>
                {statusLabels[project.status as keyof typeof statusLabels] || project.status}
              </Badge>
            </div>

            {project.description && (
              <p className="text-gray-400 mb-2">{project.description}</p>
            )}

            <div className="flex items-center space-x-4 text-sm text-gray-400">
              <span className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                {safeTimeAgo(project.createdAt || (project as any).created_at)}
              </span>
              {project.originalVideoDuration && (
                <span className="flex items-center">
                  <FileVideo className="w-4 h-4 mr-1" />
                  {formatDuration(project.originalVideoDuration)}
                </span>
              )}
              <span>{clips.length} clips generated</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
            <MoreVertical className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Processing Progress */}
      {project.status === 'processing' && (
        <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Processing Video</h3>
            <span className="text-sm text-gray-400">{project.processingProgress}%</span>
          </div>
          <Progress value={project.processingProgress} className="h-2 mb-2" />
          <p className="text-sm text-gray-400">
            Your video is being processed. This usually takes a few minutes depending on the video length.
          </p>
        </Card>
      )}

      {/* Error Message */}
      {project.status === 'failed' && project.errorMessage && (
        <Card className="p-6 bg-red-500/10 border-red-500/20">
          <h3 className="text-lg font-semibold text-red-400 mb-2">Processing Failed</h3>
          <p className="text-sm text-red-300 mb-4">{project.errorMessage}</p>
          <Button className="bg-[#E94560] hover:bg-[#E94560]/90 text-white">
            Retry Processing
          </Button>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Original Video */}
        <div className="lg:col-span-1">
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <h3 className="text-lg font-semibold text-white mb-4">Original Video</h3>

            {project.originalVideoUrl ? (
              <div className="space-y-4">
                <VideoPlayer
                  src={project.originalVideoUrl}
                  title={project.name}
                  className="w-full aspect-video rounded-lg"
                />

                <div className="space-y-2 text-sm">
                  {project.originalVideoDuration && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Duration:</span>
                      <span className="text-white">{formatDuration(project.originalVideoDuration)}</span>
                    </div>
                  )}
                  {project.originalVideoSize && (
                    <div className="flex justify-between">
                      <span className="text-gray-400">Size:</span>
                      <span className="text-white">
                        {(project.originalVideoSize / 1024 / 1024).toFixed(1)} MB
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-400">Format:</span>
                    <span className="text-white">MP4</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="aspect-video bg-[#2A2A3E] rounded-lg flex items-center justify-center">
                <div className="text-center text-gray-400">
                  <FileVideo className="w-12 h-12 mx-auto mb-2" />
                  <p>Video not available</p>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Generated Clips */}
        <div className="lg:col-span-2">
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-semibold text-white">Generated Clips</h3>
                <Badge variant="secondary" className="bg-[#E94560]/10 text-[#E94560]">
                  {clips.length}
                </Badge>
              </div>

              <div className="flex items-center space-x-2">
                {/* Sort */}
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-[#0F0F1A] border border-[#2A2A3E] text-white text-sm rounded px-3 py-1"
                >
                  <option value="created">Newest</option>
                  <option value="viral">Viral Score</option>
                  <option value="duration">Duration</option>
                </select>

                {/* View Mode */}
                <div className="flex items-center border border-[#2A2A3E] rounded">
                  <Button
                    variant={viewMode === 'grid' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('grid')}
                    className={viewMode === 'grid' ? 'bg-[#E94560] text-white' : 'text-gray-400'}
                  >
                    <Grid3X3 className="w-4 h-4" />
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
              </div>
            </div>

            {/* Clips Grid */}
            {clipsLoading ? (
              <div className={viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
                : 'space-y-4'
              }>
                {Array.from({ length: 4 }).map((_, i) => (
                  <ClipCardSkeleton key={i} />
                ))}
              </div>
            ) : clips.length === 0 ? (
              <EmptyClips />
            ) : (
              <div className={viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
                : 'space-y-4'
              }>
                {sortedClips.map((clip) => (
                  <ClipCard
                    key={clip.id}
                    clip={clip}
                    onEdit={(clip) => console.log('Edit clip:', clip)}
                    onSchedule={(clip) => console.log('Schedule clip:', clip)}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}