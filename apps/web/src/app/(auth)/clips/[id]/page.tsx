'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Download, Heart, MoreVertical, Play, Share, Star, TrendingUp } from 'lucide-react'

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
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { VideoPlayer } from '@/components/shared/video-player'
import { ClipEditor } from '@/components/clips/clip-editor'
import { LoadingSkeleton } from '@/components/shared/loading-skeleton'

import { useClip, useDownloadClip, useDeleteClip, useToggleFavorite, clipUtils } from '@/hooks'
import { toast } from 'sonner'

/**
 * Clip Detail Page Component
 *
 * Critères PRD F5-06: Page clip detail frontend
 * - Player vidéo plein écran (portrait)
 * - Infos du clip
 * - Boutons d'action
 * - Intégration avec les éditeurs (F5-07, F5-08, F5-09)
 */
export default function ClipDetailPage() {
  const params = useParams()
  const router = useRouter()
  const clipId = params.id as string

  const [isEditing, setIsEditing] = useState(false)
  const [videoPlayerOpen, setVideoPlayerOpen] = useState(false)

  // React Query hooks
  const { data: clip, isLoading, error } = useClip(clipId)
  const downloadClip = useDownloadClip()
  const deleteClip = useDeleteClip()
  const toggleFavorite = useToggleFavorite()

  const handleBack = () => {
    router.back()
  }

  const handleDownload = () => {
    if (clip && clipUtils.canDownload(clip)) {
      downloadClip.mutate(clipId)
    } else {
      toast.error('Clip is not ready for download')
    }
  }

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this clip? This action cannot be undone.')) {
      deleteClip.mutate(clipId, {
        onSuccess: () => {
          router.back()
        }
      })
    }
  }

  const handleToggleFavorite = () => {
    if (clip) {
      toggleFavorite.mutate({
        clipId: clip.id,
        currentValue: clip.isFavorite || false
      })
    }
  }

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: clip?.title,
        text: `Check out this viral clip: ${clip?.title}`,
        url: window.location.href,
      })
    } else {
      navigator.clipboard.writeText(window.location.href)
      toast.success('Link copied to clipboard!')
    }
  }

  const handlePlayVideo = () => {
    setVideoPlayerOpen(true)
  }

  // Loading state
  if (isLoading) {
    return <ClipDetailPageSkeleton />
  }

  // Error state
  if (error || !clip) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <Button onClick={handleBack} variant="ghost" className="mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <Card className="p-8 text-center">
            <h2 className="text-2xl font-bold text-white mb-4">Clip Not Found</h2>
            <p className="text-gray-400 mb-6">
              The clip you're looking for doesn't exist or you don't have permission to view it.
            </p>
            <Button onClick={handleBack} className="bg-[#E94560] hover:bg-[#E94560]/90">
              Go Back
            </Button>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button onClick={handleBack} variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Clips
          </Button>

          <div className="flex items-center space-x-2">
            <Button
              onClick={handleToggleFavorite}
              variant="ghost"
              size="sm"
              disabled={toggleFavorite.isPending}
              className={clip.isFavorite ? 'text-[#E94560]' : 'text-gray-400 hover:text-[#E94560]'}
            >
              <Heart className={`w-4 h-4 ${clip.isFavorite ? 'fill-current' : ''}`} />
            </Button>

            <Button onClick={handleShare} variant="ghost" size="sm">
              <Share className="w-4 h-4" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setIsEditing(!isEditing)}>
                  Edit Clip
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleDelete} className="text-red-400">
                  Delete Clip
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Video Player */}
          <div className="lg:col-span-1">
            <Card className="bg-[#1A1A2E] border-[#2A2A3E] overflow-hidden">
              {/* Video Container */}
              <div className="relative aspect-[9/16] bg-[#0F0F1A] flex items-center justify-center">
                {clip.signed_video_url ? (
                  <>
                    {/* Video Thumbnail */}
                    {clip.signed_thumbnail_url && (
                      <img
                        src={clip.signed_thumbnail_url}
                        alt={clip.title}
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                    )}

                    {/* Play Button Overlay */}
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                      <Button
                        onClick={handlePlayVideo}
                        size="lg"
                        className="bg-[#E94560] hover:bg-[#E94560]/90 text-white rounded-full w-16 h-16 p-0"
                      >
                        <Play className="w-6 h-6 ml-1" />
                      </Button>
                    </div>

                    {/* Status Badge */}
                    <div className="absolute top-4 left-4">
                      <Badge variant={clipUtils.getStatusColor(clip.status)}>
                        {clip.status}
                      </Badge>
                    </div>

                    {/* Duration */}
                    <div className="absolute bottom-4 right-4">
                      <Badge variant="secondary" className="bg-black/60 text-white">
                        {clipUtils.formatDuration(clip.duration)}
                      </Badge>
                    </div>
                  </>
                ) : (
                  <div className="text-center text-gray-400">
                    <Play className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Video not available</p>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="p-4 space-y-3">
                <Button
                  onClick={handlePlayVideo}
                  className="w-full bg-[#E94560] hover:bg-[#E94560]/90 text-white"
                  disabled={!clip.signed_video_url}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Watch Clip
                </Button>

                <Button
                  onClick={handleDownload}
                  variant="outline"
                  className="w-full border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]"
                  disabled={!clipUtils.canDownload(clip) || downloadClip.isPending}
                >
                  <Download className="w-4 h-4 mr-2" />
                  {downloadClip.isPending ? 'Preparing...' : 'Download MP4'}
                </Button>
              </div>
            </Card>
          </div>

          {/* Right Column - Clip Info and Editor */}
          <div className="lg:col-span-2 space-y-6">
            {/* Clip Information Card */}
            <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-6">
              <div className="space-y-4">
                {/* Title and Status */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h1 className="text-2xl font-bold text-white mb-2">{clip.title}</h1>
                    {clip.description && (
                      <p className="text-gray-400">{clip.description}</p>
                    )}
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Viral Score */}
                  {clip.viralScore && (
                    <div className="text-center">
                      <div className="flex items-center justify-center space-x-1 mb-1">
                        <TrendingUp className="w-4 h-4 text-[#E94560]" />
                        <span className="text-sm text-gray-400">Viral Score</span>
                      </div>
                      <div className={`text-lg font-bold ${clipUtils.getViralScoreColor(clip.viralScore)}`}>
                        {Math.round(clip.viralScore * 100)}%
                      </div>
                      <Badge variant="viral" className="text-xs mt-1">
                        {clipUtils.getViralScoreLabel(clip.viralScore)}
                      </Badge>
                    </div>
                  )}

                  {/* Duration */}
                  <div className="text-center">
                    <div className="text-sm text-gray-400 mb-1">Duration</div>
                    <div className="text-lg font-bold text-white">
                      {clipUtils.formatDuration(clip.duration)}
                    </div>
                  </div>

                  {/* User Rating */}
                  {clip.userRating && (
                    <div className="text-center">
                      <div className="text-sm text-gray-400 mb-1">Your Rating</div>
                      <div className="flex justify-center space-x-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star
                            key={i}
                            className={`w-4 h-4 ${
                              i < clip.userRating! ? 'text-yellow-400 fill-current' : 'text-gray-600'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Created Date */}
                  <div className="text-center">
                    <div className="text-sm text-gray-400 mb-1">Created</div>
                    <div className="text-sm text-white">
                      {safeTimeAgo(clip.createdAt || (clip as any).created_at)}
                    </div>
                  </div>
                </div>

                {/* Clip Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[#2A2A3E]">
                  <div>
                    <div className="text-sm text-gray-400 mb-1">Subtitle Style</div>
                    <Badge variant="outline" className="text-white">
                      {clip.subtitleStyle}
                    </Badge>
                  </div>

                  <div>
                    <div className="text-sm text-gray-400 mb-1">Timing</div>
                    <div className="text-sm text-white">
                      {clipUtils.formatDuration(clip.startTime)} - {clipUtils.formatDuration(clip.endTime)}
                    </div>
                  </div>
                </div>

                {/* User Notes */}
                {clip.userNotes && (
                  <div className="pt-4 border-t border-[#2A2A3E]">
                    <div className="text-sm text-gray-400 mb-2">Notes</div>
                    <p className="text-sm text-gray-300">{clip.userNotes}</p>
                  </div>
                )}

                {/* Hook and Reason */}
                {(clip.hook || clip.reason) && (
                  <div className="pt-4 border-t border-[#2A2A3E] space-y-3">
                    {clip.hook && (
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Hook</div>
                        <p className="text-sm text-gray-300">{clip.hook}</p>
                      </div>
                    )}
                    {clip.reason && (
                      <div>
                        <div className="text-sm text-gray-400 mb-1">Why it's viral</div>
                        <p className="text-sm text-gray-300">{clip.reason}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>

            {/* Clip Editor */}
            {isEditing && clipUtils.canEdit(clip) && (
              <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">Edit Clip</h2>
                  <Button
                    onClick={() => setIsEditing(false)}
                    variant="ghost"
                    size="sm"
                  >
                    Close Editor
                  </Button>
                </div>

                <ClipEditor
                  clip={clip}
                  onUpdate={() => {
                    // The hook handles cache updates
                    toast.success('Clip updated successfully')
                  }}
                  onClose={() => setIsEditing(false)}
                />
              </Card>
            )}
          </div>
        </div>

        {/* Video Player Modal */}
        {videoPlayerOpen && clip.signed_video_url && (
          <VideoPlayerModal
            isOpen={videoPlayerOpen}
            onClose={() => setVideoPlayerOpen(false)}
            videoUrl={clip.signed_video_url}
            title={clip.title}
          />
        )}
      </div>
    </div>
  )
}

/**
 * Loading skeleton for clip detail page
 */
function ClipDetailPageSkeleton() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-8">
          <Skeleton className="h-9 w-24" />
          <div className="flex space-x-2">
            <Skeleton className="h-8 w-8" />
            <Skeleton className="h-8 w-8" />
            <Skeleton className="h-8 w-8" />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video player skeleton */}
          <div className="lg:col-span-1">
            <Card className="bg-[#1A1A2E] border-[#2A2A3E] overflow-hidden">
              <Skeleton className="aspect-[9/16] w-full" />
              <div className="p-4 space-y-3">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            </Card>
          </div>

          {/* Info skeleton */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-6">
              <div className="space-y-4">
                <Skeleton className="h-8 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <div className="grid grid-cols-4 gap-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="text-center">
                      <Skeleton className="h-4 w-16 mx-auto mb-2" />
                      <Skeleton className="h-6 w-12 mx-auto" />
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Simple video player modal component
 */
function VideoPlayerModal({
  isOpen,
  onClose,
  videoUrl,
  title
}: {
  isOpen: boolean
  onClose: () => void
  videoUrl: string
  title: string
}) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
      <div className="relative max-w-sm mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden">
          <VideoPlayer
            src={videoUrl}
            title={title}
            className="w-full h-full"
          />
        </div>

        <Button
          onClick={onClose}
          variant="ghost"
          size="sm"
          className="absolute -top-12 right-0 text-white hover:text-gray-300"
        >
          ✕ Close
        </Button>
      </div>
    </div>
  )
}