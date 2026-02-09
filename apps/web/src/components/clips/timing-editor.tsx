'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { Clock, Play, RotateCcw, Scissors } from 'lucide-react'
import { toast } from 'sonner'
import type { Clip } from '../../../../shared/types'

interface TimingEditorProps {
  clip: Clip
  onChange: (startTime: number, endTime: number) => void
}

/**
 * Timing Editor Component
 *
 * Critères PRD F5-07: Éditeur de timing - Slider double pour ajuster start/end time avec preview en temps réel
 */
export function TimingEditor({ clip, onChange }: TimingEditorProps) {
  const [startTime, setStartTime] = useState(clip.startTime || 0)
  const [endTime, setEndTime] = useState(clip.endTime || 30)
  const [duration, setDuration] = useState(0)
  const [previewTime, setPreviewTime] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  // Get source duration (assuming it's available from the project)
  const sourceDuration = clip.project?.sourceDuration || 300 // 5 minutes default

  useEffect(() => {
    const newDuration = endTime - startTime
    setDuration(newDuration)
    onChange(startTime, endTime)
  }, [startTime, endTime, onChange])

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const handleSliderChange = (values: number[]) => {
    const [newStart, newEnd] = values

    // Validation
    const newDuration = newEnd - newStart
    if (newDuration < 10) {
      toast.error('Clip duration must be at least 10 seconds')
      return
    }
    if (newDuration > 120) {
      toast.error('Clip duration cannot exceed 120 seconds')
      return
    }

    setStartTime(newStart)
    setEndTime(newEnd)
  }

  const handleStartTimeInput = (value: string) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue) && numValue >= 0 && numValue < endTime) {
      setStartTime(numValue)
    }
  }

  const handleEndTimeInput = (value: string) => {
    const numValue = parseFloat(value)
    if (!isNaN(numValue) && numValue > startTime && numValue <= sourceDuration) {
      setEndTime(numValue)
    }
  }

  const handlePresetDuration = (durationSeconds: number) => {
    const newEndTime = startTime + durationSeconds
    if (newEndTime <= sourceDuration) {
      setEndTime(newEndTime)
    } else {
      const maxStartTime = sourceDuration - durationSeconds
      setStartTime(maxStartTime)
      setEndTime(sourceDuration)
    }
  }

  const handleReset = () => {
    setStartTime(clip.startTime || 0)
    setEndTime(clip.endTime || 30)
  }

  const handleOptimizeForViral = () => {
    // Optimize timing based on viral patterns (usually shorter is better)
    const idealDuration = Math.min(duration, 45) // Max 45 seconds for viral content
    const currentCenter = (startTime + endTime) / 2

    const newStartTime = Math.max(0, currentCenter - idealDuration / 2)
    const newEndTime = Math.min(sourceDuration, newStartTime + idealDuration)

    setStartTime(newStartTime)
    setEndTime(newEndTime)
    toast.success('Timing optimized for viral potential')
  }

  const getDurationColor = (dur: number): string => {
    if (dur < 15) return 'text-yellow-400' // Too short
    if (dur <= 45) return 'text-green-400' // Perfect for viral
    if (dur <= 90) return 'text-blue-400' // Good length
    return 'text-orange-400' // Getting long
  }

  const getDurationLabel = (dur: number): string => {
    if (dur < 15) return 'Very Short'
    if (dur <= 30) return 'Ideal for TikTok'
    if (dur <= 45) return 'Great for Viral'
    if (dur <= 60) return 'Standard Length'
    if (dur <= 90) return 'Long Form'
    return 'Extended'
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Clock className="w-5 h-5 text-[#E94560]" />
        <h3 className="text-lg font-medium text-white">Clip Timing</h3>
        <Badge variant="outline" className={getDurationColor(duration)}>
          {getDurationLabel(duration)}
        </Badge>
      </div>

      {/* Visual Timeline */}
      <div className="space-y-4">
        <div className="relative">
          <Label className="text-sm font-medium text-gray-300">
            Timeline ({formatTime(0)} - {formatTime(sourceDuration)})
          </Label>

          {/* Dual Range Slider */}
          <div className="mt-3 px-3">
            <Slider
              value={[startTime, endTime]}
              onValueChange={handleSliderChange}
              max={sourceDuration}
              step={1}
              className="w-full"
            />
          </div>

          {/* Timeline Labels */}
          <div className="flex justify-between text-xs text-gray-400 mt-2 px-3">
            <span>{formatTime(startTime)}</span>
            <span className={`font-medium ${getDurationColor(duration)}`}>
              {formatTime(duration)} duration
            </span>
            <span>{formatTime(endTime)}</span>
          </div>
        </div>

        {/* Visual representation of the clip within source */}
        <div className="relative h-8 bg-[#2A2A3E] rounded-lg overflow-hidden">
          <div className="absolute inset-y-0 bg-gray-600 opacity-50" style={{
            left: 0,
            width: '100%'
          }}>
          </div>
          <div
            className="absolute inset-y-0 bg-[#E94560] rounded"
            style={{
              left: `${(startTime / sourceDuration) * 100}%`,
              width: `${(duration / sourceDuration) * 100}%`,
            }}
          >
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <Scissors className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>

      {/* Precise Time Inputs */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="start-time" className="text-sm font-medium text-gray-300">
            Start Time
          </Label>
          <div className="flex space-x-2">
            <Input
              id="start-time"
              type="number"
              value={startTime.toFixed(1)}
              onChange={(e) => handleStartTimeInput(e.target.value)}
              className="bg-[#2A2A3E] border-[#3A3A4E] text-white"
              step={0.1}
              min={0}
              max={endTime - 10}
            />
            <span className="text-sm text-gray-400 self-center">sec</span>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="end-time" className="text-sm font-medium text-gray-300">
            End Time
          </Label>
          <div className="flex space-x-2">
            <Input
              id="end-time"
              type="number"
              value={endTime.toFixed(1)}
              onChange={(e) => handleEndTimeInput(e.target.value)}
              className="bg-[#2A2A3E] border-[#3A3A4E] text-white"
              step={0.1}
              min={startTime + 10}
              max={sourceDuration}
            />
            <span className="text-sm text-gray-400 self-center">sec</span>
          </div>
        </div>
      </div>

      {/* Duration Stats */}
      <div className="grid grid-cols-3 gap-4 p-4 bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg">
        <div className="text-center">
          <div className="text-sm text-gray-400 mb-1">Current Duration</div>
          <div className={`text-lg font-bold ${getDurationColor(duration)}`}>
            {formatTime(duration)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400 mb-1">Original Duration</div>
          <div className="text-sm text-gray-300">
            {formatTime((clip.endTime || 30) - (clip.startTime || 0))}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-400 mb-1">Source Duration</div>
          <div className="text-sm text-gray-300">
            {formatTime(sourceDuration)}
          </div>
        </div>
      </div>

      {/* Quick Duration Presets */}
      <div className="space-y-2">
        <Label className="text-sm font-medium text-gray-300">Quick Duration</Label>
        <div className="flex flex-wrap gap-2">
          {[15, 30, 45, 60, 90].map(seconds => (
            <Button
              key={seconds}
              onClick={() => handlePresetDuration(seconds)}
              variant="outline"
              size="sm"
              disabled={startTime + seconds > sourceDuration}
              className="border-[#3A3A4E] text-gray-300 hover:bg-[#2A2A3E] text-xs"
            >
              {seconds}s
            </Button>
          ))}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between items-center pt-4 border-t border-[#2A2A3E]">
        <div className="flex space-x-2">
          <Button
            onClick={handleReset}
            variant="ghost"
            size="sm"
            className="text-gray-400 hover:text-white"
          >
            <RotateCcw className="w-4 h-4 mr-1" />
            Reset
          </Button>

          <Button
            onClick={handleOptimizeForViral}
            variant="outline"
            size="sm"
            className="border-[#3A3A4E] text-gray-300 hover:bg-[#2A2A3E]"
          >
            ✨ Optimize for Viral
          </Button>
        </div>

        {/* Preview Button (would integrate with video player) */}
        <Button
          variant="ghost"
          size="sm"
          className="text-[#E94560] hover:text-[#E94560]/80"
          disabled // Placeholder for future video preview integration
        >
          <Play className="w-4 h-4 mr-1" />
          Preview
        </Button>
      </div>

      {/* Timing Guidelines */}
      <div className="p-4 bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg">
        <h4 className="text-sm font-medium text-gray-300 mb-2">⏱️ Timing Best Practices</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• <strong>15-30s:</strong> Perfect for TikTok and Instagram Reels</li>
          <li>• <strong>30-45s:</strong> Optimal for viral content across all platforms</li>
          <li>• <strong>45-60s:</strong> Good for detailed explanations</li>
          <li>• <strong>60s+:</strong> Better for longer-form platforms like YouTube</li>
        </ul>
      </div>

      {/* Validation Messages */}
      {duration < 10 && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">
            ⚠️ Clip is too short. Minimum duration is 10 seconds.
          </p>
        </div>
      )}

      {duration > 120 && (
        <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <p className="text-sm text-orange-400">
            ⚠️ Clip is very long. Consider shortening for better engagement.
          </p>
        </div>
      )}
    </div>
  )
}