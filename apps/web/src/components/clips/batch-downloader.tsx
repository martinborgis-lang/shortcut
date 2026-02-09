'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Download,
  Package,
  Clock,
  CheckCircle,
  XCircle,
  FileArchive,
  Loader2,
  Filter,
  TrendingUp
} from 'lucide-react'

import { useBulkDownload, useDownloadProjectClips, clipUtils } from '@/hooks'
import { toast } from 'sonner'
import type { Clip } from '../../../../shared/types'

interface BatchDownloaderProps {
  clips: Clip[]
  projectId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Batch Downloader Component
 *
 * Critères PRD F5-12: Batch download - télécharger tous les clips d'un projet en ZIP
 * - Sélection multiple de clips
 * - Filtrage par critères (viral score, durée, statut)
 * - Estimation de taille du ZIP
 * - Progress tracking
 */
export function BatchDownloader({ clips, projectId, open, onOpenChange }: BatchDownloaderProps) {
  const [selectedClips, setSelectedClips] = useState<string[]>([])
  const [filteredClips, setFilteredClips] = useState<Clip[]>(clips)
  const [filters, setFilters] = useState({
    status: 'all',
    minViralScore: 0,
    minDuration: 0,
    maxDuration: 120,
    onlyFavorites: false
  })

  const bulkDownload = useBulkDownload()
  const downloadProjectClips = useDownloadProjectClips()

  // Filter clips based on current filters
  useEffect(() => {
    let filtered = clips.filter(clip => {
      // Status filter
      if (filters.status !== 'all' && clip.status !== filters.status) {
        return false
      }

      // Viral score filter
      if (clip.viralScore && clip.viralScore * 100 < filters.minViralScore) {
        return false
      }

      // Duration filters
      if (clip.duration < filters.minDuration || clip.duration > filters.maxDuration) {
        return false
      }

      // Favorites filter
      if (filters.onlyFavorites && !clip.isFavorite) {
        return false
      }

      return true
    })

    setFilteredClips(filtered)

    // Update selected clips to only include those that pass the filter
    setSelectedClips(prev => prev.filter(clipId =>
      filtered.some(clip => clip.id === clipId)
    ))
  }, [clips, filters])

  const toggleClip = (clipId: string) => {
    setSelectedClips(prev =>
      prev.includes(clipId)
        ? prev.filter(id => id !== clipId)
        : [...prev, clipId]
    )
  }

  const selectAll = () => {
    const readyClips = filteredClips.filter(clip => clip.status === 'ready')
    setSelectedClips(readyClips.map(clip => clip.id))
  }

  const selectNone = () => {
    setSelectedClips([])
  }

  const selectTopViral = () => {
    const sortedByViral = [...filteredClips]
      .filter(clip => clip.status === 'ready' && clip.viralScore)
      .sort((a, b) => (b.viralScore || 0) - (a.viralScore || 0))
      .slice(0, 10)

    setSelectedClips(sortedByViral.map(clip => clip.id))
  }

  const handleBulkDownload = () => {
    if (selectedClips.length === 0) {
      toast.error('Please select at least one clip')
      return
    }

    bulkDownload.mutate(
      {
        clip_ids: selectedClips,
        project_id: projectId
      },
      {
        onSuccess: () => {
          onOpenChange(false)
          setSelectedClips([])
        }
      }
    )
  }

  const handleDownloadAll = () => {
    if (!projectId) {
      toast.error('Project ID is required')
      return
    }

    downloadProjectClips.mutate(projectId, {
      onSuccess: () => {
        onOpenChange(false)
      }
    })
  }

  // Calculate stats
  const readyClips = filteredClips.filter(clip => clip.status === 'ready')
  const selectedReadyClips = filteredClips.filter(clip =>
    selectedClips.includes(clip.id) && clip.status === 'ready'
  )
  const estimatedTotalDuration = selectedReadyClips.reduce((total, clip) => total + clip.duration, 0)
  const estimatedSizeMB = Math.round(estimatedTotalDuration * 2.5) // Rough estimate: 2.5MB per second

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden bg-[#1A1A2E] border-[#2A2A3E]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2 text-white">
            <Package className="w-5 h-5 text-[#E94560]" />
            <span>Batch Download Clips</span>
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Select clips to download as a ZIP archive. Ready clips only.
          </DialogDescription>
        </DialogHeader>

        {/* Filters */}
        <Card className="bg-[#2A2A3E] border-[#3A3A4E] p-4">
          <div className="flex items-center space-x-2 mb-4">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-300">Filters</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Status</label>
              <Select value={filters.status} onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}>
                <SelectTrigger className="bg-[#1A1A2E] border-[#3A3A4E] text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="ready">Ready Only</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs text-gray-400 mb-1 block">Min Viral Score</label>
              <Select
                value={filters.minViralScore.toString()}
                onValueChange={(value) => setFilters(prev => ({ ...prev, minViralScore: parseInt(value) }))}
              >
                <SelectTrigger className="bg-[#1A1A2E] border-[#3A3A4E] text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">Any Score</SelectItem>
                  <SelectItem value="50">50%+</SelectItem>
                  <SelectItem value="70">70%+</SelectItem>
                  <SelectItem value="80">80%+</SelectItem>
                  <SelectItem value="90">90%+</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs text-gray-400 mb-1 block">Duration Range</label>
              <Select
                value={`${filters.minDuration}-${filters.maxDuration}`}
                onValueChange={(value) => {
                  const [min, max] = value.split('-').map(Number)
                  setFilters(prev => ({ ...prev, minDuration: min, maxDuration: max }))
                }}
              >
                <SelectTrigger className="bg-[#1A1A2E] border-[#3A3A4E] text-white text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0-120">Any Duration</SelectItem>
                  <SelectItem value="15-30">15-30s (TikTok)</SelectItem>
                  <SelectItem value="30-60">30-60s (Instagram)</SelectItem>
                  <SelectItem value="60-120">60-120s (YouTube)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center space-x-2 text-sm text-gray-300">
                <Checkbox
                  checked={filters.onlyFavorites}
                  onCheckedChange={(checked) =>
                    setFilters(prev => ({ ...prev, onlyFavorites: checked as boolean }))
                  }
                />
                <span>Favorites Only</span>
              </label>
            </div>
          </div>
        </Card>

        {/* Stats and Quick Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 text-sm">
            <span className="text-gray-400">
              {filteredClips.length} clips ({readyClips.length} ready)
            </span>
            <span className="text-gray-400">
              {selectedClips.length} selected
            </span>
            {selectedReadyClips.length > 0 && (
              <Badge variant="outline" className="text-[#E94560] border-[#E94560]">
                ~{estimatedSizeMB}MB ZIP
              </Badge>
            )}
          </div>

          <div className="flex space-x-2">
            <Button onClick={selectNone} variant="ghost" size="sm" className="text-xs">
              Clear
            </Button>
            <Button onClick={selectTopViral} variant="ghost" size="sm" className="text-xs">
              <TrendingUp className="w-3 h-3 mr-1" />
              Top Viral
            </Button>
            <Button onClick={selectAll} variant="ghost" size="sm" className="text-xs">
              Select All Ready
            </Button>
          </div>
        </div>

        {/* Clips List */}
        <div className="flex-1 overflow-y-auto space-y-2 max-h-80">
          {filteredClips.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No clips match your filters</p>
            </div>
          ) : (
            filteredClips.map((clip) => {
              const isSelected = selectedClips.includes(clip.id)
              const canDownload = clip.status === 'ready'

              return (
                <Card
                  key={clip.id}
                  className={`p-3 transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#E94560]/10 border-[#E94560]/30'
                      : 'bg-[#2A2A3E] border-[#3A3A4E] hover:border-[#4A4A5E]'
                  } ${!canDownload ? 'opacity-50' : ''}`}
                  onClick={() => canDownload && toggleClip(clip.id)}
                >
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      checked={isSelected}
                      disabled={!canDownload}
                      onCheckedChange={() => canDownload && toggleClip(clip.id)}
                    />

                    {/* Thumbnail */}
                    <div className="w-12 h-12 bg-[#0F0F1A] rounded border border-[#3A3A4E] flex-shrink-0 overflow-hidden">
                      {clip.thumbnailUrl ? (
                        <img
                          src={clip.thumbnailUrl}
                          alt={clip.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Package className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className="text-sm font-medium text-white truncate">
                          {clip.title}
                        </h4>
                        <Badge variant={clipUtils.getStatusColor(clip.status)} className="text-xs">
                          {clip.status}
                        </Badge>
                      </div>

                      <div className="flex items-center space-x-4 text-xs text-gray-400">
                        <span className="flex items-center">
                          <Clock className="w-3 h-3 mr-1" />
                          {clipUtils.formatDuration(clip.duration)}
                        </span>

                        {clip.viralScore && (
                          <span className={`flex items-center ${clipUtils.getViralScoreColor(clip.viralScore)}`}>
                            <TrendingUp className="w-3 h-3 mr-1" />
                            {Math.round(clip.viralScore * 100)}%
                          </span>
                        )}

                        {clip.isFavorite && (
                          <span className="text-[#E94560]">★</span>
                        )}
                      </div>
                    </div>

                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      {clip.status === 'ready' && <CheckCircle className="w-4 h-4 text-green-400" />}
                      {clip.status === 'processing' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                      {clip.status === 'failed' && <XCircle className="w-4 h-4 text-red-400" />}
                    </div>
                  </div>
                </Card>
              )
            })
          )}
        </div>

        <Separator className="bg-[#2A2A3E]" />

        {/* Summary */}
        {selectedReadyClips.length > 0 && (
          <Card className="bg-[#0F0F1A] border-[#2A2A3E] p-4">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-white">{selectedReadyClips.length}</div>
                <div className="text-xs text-gray-400">Clips</div>
              </div>
              <div>
                <div className="text-lg font-bold text-white">
                  {clipUtils.formatDuration(estimatedTotalDuration)}
                </div>
                <div className="text-xs text-gray-400">Total Duration</div>
              </div>
              <div>
                <div className="text-lg font-bold text-white">~{estimatedSizeMB}MB</div>
                <div className="text-xs text-gray-400">Estimated Size</div>
              </div>
              <div>
                <div className="text-lg font-bold text-[#E94560]">
                  {selectedReadyClips.length > 0
                    ? Math.round(
                        selectedReadyClips.reduce((sum, clip) => sum + (clip.viralScore || 0), 0) /
                        selectedReadyClips.length * 100
                      )
                    : 0}%
                </div>
                <div className="text-xs text-gray-400">Avg Viral Score</div>
              </div>
            </div>
          </Card>
        )}

        <DialogFooter className="flex justify-between">
          <div className="flex space-x-2">
            {projectId && (
              <Button
                onClick={handleDownloadAll}
                variant="outline"
                disabled={downloadProjectClips.isPending}
                className="border-[#3A3A4E] text-gray-300 hover:bg-[#2A2A3E]"
              >
                {downloadProjectClips.isPending ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <FileArchive className="w-4 h-4 mr-2" />
                )}
                Download All Project Clips
              </Button>
            )}
          </div>

          <div className="flex space-x-2">
            <Button
              onClick={() => onOpenChange(false)}
              variant="ghost"
            >
              Cancel
            </Button>
            <Button
              onClick={handleBulkDownload}
              disabled={selectedClips.length === 0 || bulkDownload.isPending}
              className="bg-[#E94560] hover:bg-[#E94560]/90"
            >
              {bulkDownload.isPending ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Download Selected ({selectedClips.length})
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}