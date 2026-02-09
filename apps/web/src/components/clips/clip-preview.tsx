'use client'

import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Clock, TrendingUp, Star, Eye } from 'lucide-react'
import { clipUtils } from '@/hooks'
import type { Clip } from '../../../../shared/types'

interface ClipPreviewProps {
  clip: Clip
  highlightChanges?: boolean
}

/**
 * Clip Preview Component
 *
 * Shows a preview of how the clip will appear with current settings
 */
export function ClipPreview({ clip, highlightChanges = false }: ClipPreviewProps) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center space-x-2">
        <Eye className="w-4 h-4 text-gray-400" />
        <h4 className="text-sm font-medium text-gray-300">Preview</h4>
        {highlightChanges && (
          <Badge variant="outline" className="text-xs text-[#E94560] border-[#E94560]">
            Modified
          </Badge>
        )}
      </div>

      {/* Mock Video Preview */}
      <div className="aspect-[9/16] max-w-sm mx-auto bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg relative overflow-hidden border-2 border-[#2A2A3E]">
        {/* Fake video background */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />

        {/* Status indicator */}
        <div className="absolute top-3 left-3">
          <Badge variant={clipUtils.getStatusColor(clip.status)} className="text-xs">
            {clip.status}
          </Badge>
        </div>

        {/* Duration badge */}
        <div className="absolute top-3 right-3">
          <Badge variant="secondary" className="bg-black/60 text-white text-xs">
            {clipUtils.formatDuration(clip.duration || 30)}
          </Badge>
        </div>

        {/* Subtitle preview positioned based on current settings */}
        <div
          className={`absolute inset-x-0 flex justify-center items-center px-4 ${
            clip.subtitleStyle === 'clean' || clip.subtitleStyle === 'minimal'
              ? 'bottom-8'
              : 'top-1/2 -translate-y-1/2'
          }`}
        >
          <div
            className="text-center font-bold leading-tight max-w-full"
            style={{
              fontSize: '12px', // Scaled for preview
              color: getStyleColor(clip.subtitleStyle),
              textShadow: getStyleOutline(clip.subtitleStyle),
              backgroundColor: getStyleBackground(clip.subtitleStyle),
              padding: needsBackground(clip.subtitleStyle) ? '2px 6px' : '0',
              borderRadius: needsBackground(clip.subtitleStyle) ? '2px' : '0',
            }}
          >
            {clip.title || 'Your clip title here'}
          </div>
        </div>

        {/* Play button overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-12 h-12 bg-[#E94560] rounded-full flex items-center justify-center opacity-80">
            <div className="w-0 h-0 border-l-[8px] border-l-white border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent ml-1"></div>
          </div>
        </div>

        {/* Timing indicators */}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-[#2A2A3E]">
          <div
            className="h-full bg-[#E94560] transition-all duration-200"
            style={{
              width: `${((clip.endTime || 30) - (clip.startTime || 0)) / 60 * 100}%`
            }}
          />
        </div>
      </div>

      {/* Clip Information */}
      <div className="space-y-3">
        {/* Title */}
        <div>
          <p className="text-sm font-medium text-white line-clamp-2">
            {clip.title || 'Untitled Clip'}
          </p>
          {clip.description && (
            <p className="text-xs text-gray-400 line-clamp-1 mt-1">
              {clip.description}
            </p>
          )}
        </div>

        <Separator className="bg-[#2A2A3E]" />

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Duration</span>
              <span className="text-white font-medium">
                {clipUtils.formatDuration(clip.duration || 30)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-400">Timing</span>
              <span className="text-white font-medium">
                {clipUtils.formatDuration(clip.startTime || 0)}-{clipUtils.formatDuration(clip.endTime || 30)}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            {clip.viralScore && (
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Viral Score</span>
                <div className={`font-medium ${clipUtils.getViralScoreColor(clip.viralScore)}`}>
                  {Math.round(clip.viralScore * 100)}%
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <span className="text-gray-400">Subtitle</span>
              <Badge variant="outline" className="text-xs capitalize">
                {clip.subtitleStyle || 'hormozi'}
              </Badge>
            </div>
          </div>
        </div>

        {/* User Rating */}
        {clip.userRating && (
          <>
            <Separator className="bg-[#2A2A3E]" />
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Your Rating</span>
              <div className="flex space-x-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Star
                    key={i}
                    className={`w-3 h-3 ${
                      i < clip.userRating! ? 'text-yellow-400 fill-current' : 'text-gray-600'
                    }`}
                  />
                ))}
              </div>
            </div>
          </>
        )}

        {/* Viral Insights */}
        {(clip.hook || clip.reason) && (
          <>
            <Separator className="bg-[#2A2A3E]" />
            <div className="space-y-2">
              {clip.hook && (
                <div>
                  <span className="text-xs text-gray-400">Hook:</span>
                  <p className="text-xs text-gray-300 line-clamp-2">{clip.hook}</p>
                </div>
              )}
              {clip.reason && (
                <div>
                  <span className="text-xs text-gray-400">Why it's viral:</span>
                  <p className="text-xs text-gray-300 line-clamp-2">{clip.reason}</p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Changes Indicator */}
      {highlightChanges && (
        <div className="p-2 bg-[#E94560]/10 border border-[#E94560]/20 rounded text-center">
          <p className="text-xs text-[#E94560]">
            Preview shows your changes. Save to apply them.
          </p>
        </div>
      )}
    </div>
  )
}

// Helper functions for subtitle styling
function getStyleColor(style: string): string {
  switch (style) {
    case 'hormozi': return '#FFFFFF'
    case 'clean': return '#FFFFFF'
    case 'neon': return '#00FFFF'
    case 'karaoke': return '#FFD700'
    case 'minimal': return '#FFFFFF'
    default: return '#FFFFFF'
  }
}

function getStyleOutline(style: string): string {
  switch (style) {
    case 'hormozi': return '1px 1px 0 #000000, -1px -1px 0 #000000, 1px -1px 0 #000000, -1px 1px 0 #000000'
    case 'clean': return '1px 1px 0 #333333, -1px -1px 0 #333333, 1px -1px 0 #333333, -1px 1px 0 #333333'
    case 'neon': return '1px 1px 0 #FF00FF, -1px -1px 0 #FF00FF, 1px -1px 0 #FF00FF, -1px 1px 0 #FF00FF, 0 0 10px #00FFFF'
    case 'karaoke': return '1px 1px 0 #000000, -1px -1px 0 #000000, 1px -1px 0 #000000, -1px 1px 0 #000000'
    case 'minimal': return 'none'
    default: return 'none'
  }
}

function getStyleBackground(style: string): string {
  switch (style) {
    case 'clean': return 'rgba(0,0,0,0.7)'
    default: return 'transparent'
  }
}

function needsBackground(style: string): boolean {
  return style === 'clean'
}