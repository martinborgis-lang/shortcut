'use client'

import { useState, useRef, useEffect } from 'react'
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface VideoPlayerProps {
  src: string
  poster?: string
  title?: string
  className?: string
  autoPlay?: boolean
  muted?: boolean
  controls?: boolean
  onTimeUpdate?: (currentTime: number, duration: number) => void
  onEnded?: () => void
}

export function VideoPlayer({
  src,
  poster,
  title,
  className,
  autoPlay = false,
  muted = true,
  controls = true,
  onTimeUpdate,
  onEnded,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(muted)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [showControls, setShowControls] = useState(true)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleLoadedMetadata = () => {
      setDuration(video.duration)
    }

    const handleTimeUpdate = () => {
      const current = video.currentTime
      setCurrentTime(current)
      onTimeUpdate?.(current, video.duration)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      onEnded?.()
    }

    const handleFullscreenChange = () => {
      setIsFullscreen(document.fullscreenElement === video)
    }

    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('ended', handleEnded)
    document.addEventListener('fullscreenchange', handleFullscreenChange)

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('ended', handleEnded)
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [onTimeUpdate, onEnded])

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return

    if (isPlaying) {
      video.pause()
    } else {
      video.play()
    }
    setIsPlaying(!isPlaying)
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return

    video.muted = !isMuted
    setIsMuted(!isMuted)
  }

  const handleSeek = (percentage: number) => {
    const video = videoRef.current
    if (!video || !duration) return

    const newTime = (percentage / 100) * duration
    video.currentTime = newTime
    setCurrentTime(newTime)
  }

  const toggleFullscreen = () => {
    const video = videoRef.current
    if (!video) return

    if (isFullscreen) {
      document.exitFullscreen()
    } else {
      video.requestFullscreen()
    }
  }

  const restart = () => {
    const video = videoRef.current
    if (!video) return

    video.currentTime = 0
    setCurrentTime(0)
    if (!isPlaying) {
      video.play()
      setIsPlaying(true)
    }
  }

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      className={cn(
        "relative bg-black rounded-lg overflow-hidden group",
        className
      )}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => setShowControls(false)}
    >
      <video
        ref={videoRef}
        src={src}
        poster={poster}
        autoPlay={autoPlay}
        muted={isMuted}
        playsInline
        className="w-full h-full object-contain"
        onClick={togglePlay}
      />

      {/* Play Button Overlay */}
      {!isPlaying && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20">
          <Button
            size="lg"
            onClick={togglePlay}
            className="bg-[#E94560] hover:bg-[#E94560]/90 text-white rounded-full w-16 h-16 p-0"
          >
            <Play className="w-8 h-8 ml-1" />
          </Button>
        </div>
      )}

      {/* Controls */}
      {controls && (
        <div
          className={cn(
            "absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-200",
            showControls ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          )}
        >
          {/* Progress Bar */}
          <div className="mb-3">
            <Progress
              value={progressPercentage}
              className="h-1 cursor-pointer"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const percentage = ((e.clientX - rect.left) / rect.width) * 100
                handleSeek(percentage)
              }}
            />
          </div>

          <div className="flex items-center justify-between">
            {/* Left Controls */}
            <div className="flex items-center space-x-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={togglePlay}
                className="text-white hover:text-[#E94560] p-1"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={restart}
                className="text-white hover:text-[#E94560] p-1"
              >
                <RotateCcw className="w-4 h-4" />
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={toggleMute}
                className="text-white hover:text-[#E94560] p-1"
              >
                {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
              </Button>

              {/* Time Display */}
              <span className="text-xs text-white font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
            </div>

            {/* Right Controls */}
            <div className="flex items-center space-x-2">
              {title && (
                <span className="text-sm text-white truncate max-w-48">
                  {title}
                </span>
              )}

              <Button
                size="sm"
                variant="ghost"
                onClick={toggleFullscreen}
                className="text-white hover:text-[#E94560] p-1"
              >
                <Maximize className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}