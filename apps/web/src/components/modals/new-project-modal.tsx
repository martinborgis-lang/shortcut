'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useUIStore } from '@/stores'
import { useProcessVideoFromUrl } from '@/hooks'
import { Loader2, Youtube, Twitch, AlertCircle } from 'lucide-react'

interface NewProjectFormData {
  url: string
  maxClips?: number
}

const validateUrl = (url: string): { isValid: boolean; platform?: 'youtube' | 'twitch'; error?: string } => {
  if (!url) return { isValid: false, error: 'URL is required' }

  // Enhanced YouTube URL patterns (according to PRD F4-14)
  const youtubePatterns = [
    // Standard watch URLs
    /^https?:\/\/(www\.|m\.)?youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]+)/,

    // Short URLs
    /^https?:\/\/(www\.)?youtu\.be\/([a-zA-Z0-9_-]+)/,

    // Shorts URLs
    /^https?:\/\/(www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]+)/,

    // Embed URLs
    /^https?:\/\/(www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]+)/
  ]

  // Enhanced Twitch URL patterns (according to PRD F4-14)
  const twitchPatterns = [
    // Video URLs (main requirement)
    /^https?:\/\/(www\.)?twitch\.tv\/videos\/\d+/,

    // Live stream URLs (also supported)
    /^https?:\/\/(www\.)?twitch\.tv\/[a-zA-Z0-9_-]+(?:\/.*)?$/
  ]

  const isYouTube = youtubePatterns.some(pattern => pattern.test(url))
  const isTwitch = twitchPatterns.some(pattern => pattern.test(url))

  if (isYouTube) {
    return { isValid: true, platform: 'youtube' }
  }

  if (isTwitch) {
    return { isValid: true, platform: 'twitch' }
  }

  return { isValid: false, error: 'URL must be from YouTube (youtu.be, youtube.com/watch, youtube.com/shorts) or Twitch (twitch.tv/videos/)' }
}

export function NewProjectModal() {
  console.log('NewProjectModal component mounted')
  const { isNewProjectModalOpen, setNewProjectModalOpen } = useUIStore()
  console.log('Modal open state:', isNewProjectModalOpen)
  const [urlValidation, setUrlValidation] = useState<{ isValid: boolean; platform?: 'youtube' | 'twitch'; error?: string }>({ isValid: false })

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors }
  } = useForm<NewProjectFormData>()

  const processVideoMutation = useProcessVideoFromUrl()

  const watchedUrl = watch('url')

  // Validate URL in real time using useEffect
  useEffect(() => {
    if (watchedUrl) {
      const validation = validateUrl(watchedUrl)
      console.log('URL validation for:', watchedUrl, 'Result:', validation)
      setUrlValidation(validation)
    } else {
      console.log('No URL provided, setting validation to false')
      setUrlValidation({ isValid: false })
    }
  }, [watchedUrl])

  const onSubmit = async (data: NewProjectFormData) => {
    console.log('onSubmit called with data:', data)

    const validation = validateUrl(data.url)
    console.log('URL validation result:', validation)

    if (!validation.isValid) {
      toast.error(validation.error || 'Invalid URL')
      return
    }

    try {
      console.log('Calling processVideoMutation.mutateAsync with:', {
        url: data.url,
        maxClips: data.maxClips || 5
      })

      await processVideoMutation.mutateAsync({
        url: data.url,
        maxClips: data.maxClips || 5
      })

      toast.success('Project created successfully! Processing will start shortly.')
      setNewProjectModalOpen(false)
      reset()
    } catch (error) {
      console.error('Error creating project:', error)
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project. Please try again.'
      toast.error(errorMessage)
    }
  }

  const handleClose = () => {
    setNewProjectModalOpen(false)
    reset()
    setUrlValidation({ isValid: false })
  }

  return (
    <Dialog open={isNewProjectModalOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <span>Create New Project</span>
          </DialogTitle>
          <DialogDescription>
            Paste a YouTube or Twitch URL to generate viral short clips automatically.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Video URL <span className="text-[#E94560]">*</span>
            </label>
            <Input
              {...register('url', { required: 'URL is required' })}
              placeholder="https://www.youtube.com/watch?v=... or https://twitch.tv/videos/..."
              className="w-full"
            />

            {/* URL Validation Feedback */}
            {watchedUrl && (
              <div className="flex items-center space-x-2">
                {urlValidation.isValid ? (
                  <>
                    {urlValidation.platform === 'youtube' && (
                      <Badge variant="secondary" className="bg-red-500/10 text-red-400 border-red-500/20">
                        <Youtube className="w-3 h-3 mr-1" />
                        YouTube
                      </Badge>
                    )}
                    {urlValidation.platform === 'twitch' && (
                      <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                        <Twitch className="w-3 h-3 mr-1" />
                        Twitch
                      </Badge>
                    )}
                    <span className="text-xs text-green-400">Valid URL detected</span>
                  </>
                ) : urlValidation.error && (
                  <div className="flex items-center space-x-1 text-red-400">
                    <AlertCircle className="w-3 h-3" />
                    <span className="text-xs">{urlValidation.error}</span>
                  </div>
                )}
              </div>
            )}

            {errors.url && (
              <p className="text-xs text-red-400">{errors.url.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">
              Maximum Clips <span className="text-gray-400">(Optional)</span>
            </label>
            <Input
              {...register('maxClips', {
                valueAsNumber: true,
                validate: value => !value || (value >= 1 && value <= 10) || 'Must be between 1 and 10 clips'
              })}
              type="number"
              min="1"
              max="10"
              placeholder="5"
              className="w-full"
            />
            <p className="text-xs text-gray-400">
              Number of clips to generate (1-10). Default: 5 clips
            </p>
            {errors.maxClips && (
              <p className="text-xs text-red-400">{errors.maxClips.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={false}
              className="bg-[#E94560] hover:bg-[#E94560]/90"
              onClick={() => console.log('Button clicked! Validation state:', urlValidation, 'Pending:', processVideoMutation.isPending)}
            >
              {processVideoMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                'Generate Clips'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}