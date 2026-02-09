import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
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
  Download,
  Calendar,
  Edit,
  Heart,
  MoreVertical,
  TrendingUp,
  Clock,
  Star,
} from 'lucide-react'
import { VideoPlayer } from '@/components/shared/video-player'
import { useUIStore } from '@/stores'
import { useDownloadClip, useUpdateClip } from '@/hooks'
import { toast } from 'sonner'
import type { Clip } from '../../../../shared/types'

interface ClipCardProps {
  clip: Clip
  onEdit?: (clip: Clip) => void
  onSchedule?: (clip: Clip) => void
  showProject?: boolean
}

const statusColors = {
  pending: 'warning',
  processing: 'secondary',
  ready: 'success',
  failed: 'destructive'
} as const

export function ClipCard({ clip, onEdit, onSchedule, showProject = false }: ClipCardProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const { setCurrentVideo, setVideoPlayerModalOpen } = useUIStore()

  const downloadClip = useDownloadClip()
  const updateClip = useUpdateClip()

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getViralScoreColor = (score?: number) => {
    if (!score) return 'text-gray-400'
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getViralScoreLabel = (score?: number) => {
    if (!score) return 'Unknown'
    if (score >= 0.8) return 'High'
    if (score >= 0.6) return 'Medium'
    return 'Low'
  }

  const handlePreview = () => {
    if (clip.videoUrl) {
      setCurrentVideo(clip.videoUrl, clip.title)
      setVideoPlayerModalOpen(true)
    } else {
      toast.error('Video preview not available')
    }
  }

  const handleDownload = () => {
    downloadClip.mutate(clip.id, {
      onSuccess: () => {
        toast.success('Clip downloaded successfully')
      },
      onError: () => {
        toast.error('Failed to download clip')
      }
    })
  }

  const handleFavorite = () => {
    updateClip.mutate({
      clipId: clip.id,
      data: { isFavorite: !clip.isFavorite }
    }, {
      onSuccess: () => {
        toast.success(clip.isFavorite ? 'Removed from favorites' : 'Added to favorites')
      },
      onError: () => {
        toast.error('Failed to update favorite status')
      }
    })
  }

  return (
    <Card className="group hover:border-[#E94560]/20 transition-all duration-200 bg-[#1A1A2E] border-[#2A2A3E] overflow-hidden">
      {/* Thumbnail/Preview */}
      <div className="relative aspect-video bg-[#0F0F1A] overflow-hidden">
        {clip.thumbnailUrl ? (
          <img
            src={clip.thumbnailUrl}
            alt={clip.title}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[#2A2A3E]">
            <Play className="w-12 h-12 text-gray-400" />
          </div>
        )}

        {/* Overlay with Play Button */}
        <div className="absolute inset-0 bg-black/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <Button
            size="lg"
            onClick={handlePreview}
            className="bg-[#E94560] hover:bg-[#E94560]/90 text-white rounded-full w-12 h-12 p-0"
            disabled={!clip.videoUrl}
          >
            <Play className="w-5 h-5 ml-0.5" />
          </Button>
        </div>

        {/* Status Badge */}
        <div className="absolute top-3 left-3">
          <Badge variant={statusColors[clip.status]} className="text-xs">
            {clip.status}
          </Badge>
        </div>

        {/* Duration */}
        <div className="absolute bottom-3 right-3">
          <Badge variant="secondary" className="bg-black/60 text-white text-xs">
            {formatDuration(clip.duration)}
          </Badge>
        </div>

        {/* Favorite Button */}
        <div className="absolute top-3 right-3">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleFavorite}
            className={`p-1 ${clip.isFavorite ? 'text-[#E94560]' : 'text-gray-400 hover:text-[#E94560]'}`}
          >
            {clip.isFavorite ? <Heart className="w-4 h-4 fill-current" /> : <Heart className="w-4 h-4" />}
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Title and Actions */}
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-white truncate flex-1 mr-2">
            {clip.title}
          </h3>

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
              <DropdownMenuItem onClick={handlePreview} disabled={!clip.videoUrl}>
                <Play className="w-4 h-4 mr-2" />
                Preview
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleDownload} disabled={clip.status !== 'ready'}>
                <Download className="w-4 h-4 mr-2" />
                Download
              </DropdownMenuItem>
              {onSchedule && (
                <DropdownMenuItem onClick={() => onSchedule(clip)} disabled={clip.status !== 'ready'}>
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule
                </DropdownMenuItem>
              )}
              {onEdit && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => onEdit(clip)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Description */}
        {clip.description && (
          <p className="text-sm text-gray-400 mb-3 line-clamp-2">
            {clip.description}
          </p>
        )}

        {/* Viral Score */}
        {clip.viralScore && clip.viralScore > 0 && (
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-[#E94560]" />
              <span className="text-sm text-gray-400">Viral Score</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`text-sm font-medium ${getViralScoreColor(clip.viralScore)}`}>
                {Math.round(clip.viralScore * 100)}%
              </div>
              <Badge
                variant="viral"
                className="text-xs"
              >
                {getViralScoreLabel(clip.viralScore)}
              </Badge>
            </div>
          </div>
        )}

        {/* User Rating */}
        {clip.userRating && (
          <div className="flex items-center space-x-1 mb-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={`w-3 h-3 ${
                  i < clip.userRating! ? 'text-yellow-400 fill-current' : 'text-gray-600'
                }`}
              />
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {formatDistanceToNow(new Date(clip.createdAt), { addSuffix: true })}
          </span>

          {/* Action Buttons */}
          <div className="flex items-center space-x-1">
            <Button
              size="sm"
              onClick={handlePreview}
              disabled={!clip.videoUrl}
              className="bg-[#E94560] hover:bg-[#E94560]/90 text-white h-7 px-3 text-xs"
            >
              <Play className="w-3 h-3 mr-1" />
              Preview
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleDownload}
              disabled={clip.status !== 'ready' || downloadClip.isPending}
              className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E] h-7 px-3 text-xs"
            >
              <Download className="w-3 h-3 mr-1" />
              Download
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}