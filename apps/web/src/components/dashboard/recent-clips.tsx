import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ExternalLink, Play, Clock, TrendingUp } from 'lucide-react'
import type { Clip } from '../../../../shared/types'

function safeTimeAgo(dateValue: any): string {
  try {
    if (!dateValue) return 'Just now';
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return 'Just now';
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Just now';
  }
}

interface RecentClipsProps {
  clips: Clip[]
  isLoading?: boolean
}

const statusColors = {
  pending: 'warning',
  processing: 'secondary',
  ready: 'success',
  failed: 'destructive'
} as const

export function RecentClips({ clips, isLoading }: RecentClipsProps) {
  if (isLoading) {
    return (
      <Card className="p-6 bg-zinc-900/50 backdrop-blur-sm border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Clips</h3>
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

  if (clips.length === 0) {
    return (
      <Card className="p-6 bg-zinc-900/50 backdrop-blur-sm border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Clips</h3>
        <div className="text-center py-8 text-gray-400">
          <Play className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>No clips yet</p>
          <p className="text-sm">Process a video to generate clips</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Recent Clips</h3>
        <Link href="/projects">
          <Button variant="ghost" size="sm" className="text-[#E94560] hover:text-[#E94560]/80">
            View all
            <ExternalLink className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </div>

      <div className="space-y-3">
        {clips.slice(0, 5).map((clip) => (
          <div
            key={clip.id}
            className="flex items-center space-x-3 p-3 rounded-lg hover:bg-[#2A2A3E] transition-colors group cursor-pointer"
          >
            {/* Clip thumbnail */}
            <div className="relative h-12 w-12 rounded-lg bg-[#2A2A3E] flex items-center justify-center flex-shrink-0 overflow-hidden">
              {clip.thumbnailUrl ? (
                <img
                  src={clip.thumbnailUrl}
                  alt={clip.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Play className="w-6 h-6 text-gray-400" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-white truncate group-hover:text-[#E94560] transition-colors">
                {clip.title}
              </h4>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant={statusColors[clip.status]} className="text-xs">
                  {clip.status}
                </Badge>
                <span className="text-xs text-gray-400">{Math.round(clip.duration)}s</span>
                <span className="text-xs text-gray-400 flex items-center">
                  <Clock className="w-3 h-3 mr-1" />
                  {safeTimeAgo(clip.createdAt || (clip as any).created_at)}
                </span>
              </div>
            </div>

            {/* Viral score */}
            {clip.viralScore && clip.viralScore > 0 && (
              <div className="text-right flex-shrink-0">
                <div className="flex items-center space-x-1 text-[#E94560]">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm font-medium">{Math.round(clip.viralScore * 100)}%</span>
                </div>
                <div className="text-xs text-gray-400">Viral Score</div>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}