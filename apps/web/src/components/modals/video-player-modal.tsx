'use client'

import {
  Dialog,
  DialogContent,
} from '@/components/ui/dialog'
import { VideoPlayer } from '@/components/shared/video-player'
import { useUIStore } from '@/stores'

export function VideoPlayerModal() {
  const {
    isVideoPlayerModalOpen,
    setVideoPlayerModalOpen,
    currentVideoUrl,
    currentVideoTitle,
    setCurrentVideo
  } = useUIStore()

  const handleClose = () => {
    setVideoPlayerModalOpen(false)
    setCurrentVideo(null)
  }

  if (!currentVideoUrl) return null

  return (
    <Dialog open={isVideoPlayerModalOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl w-full p-0 bg-black border-none">
        <VideoPlayer
          src={currentVideoUrl}
          title={currentVideoTitle || undefined}
          className="w-full aspect-video"
          autoPlay
          controls
        />
      </DialogContent>
    </Dialog>
  )
}