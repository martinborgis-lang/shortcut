'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Clock, Type, Subtitles, Settings, Save, RotateCcw } from 'lucide-react'

import { TimingEditor } from './timing-editor'
import { SubtitleEditor } from './subtitle-editor'
import { TitleEditor } from './title-editor'
import { ClipPreview } from './clip-preview'

import { useUpdateClip, useRegenerateClip } from '@/hooks'
import { toast } from 'sonner'
import type { Clip } from '../../../../shared/types'

interface ClipEditorProps {
  clip: Clip
  onUpdate?: () => void
  onClose?: () => void
}

/**
 * Clip Editor Component
 *
 * Critères PRD F5-07, F5-08, F5-09:
 * - F5-07: Éditeur de timing avec slider double pour ajuster start/end time
 * - F5-08: Éditeur de sous-titres avec sélecteur de style et preview
 * - F5-09: Éditeur de titre avec input editable
 */
export function ClipEditor({ clip, onUpdate, onClose }: ClipEditorProps) {
  const [activeTab, setActiveTab] = useState('title')
  const [hasChanges, setHasChanges] = useState(false)
  const [pendingChanges, setPendingChanges] = useState<Partial<Clip>>({})

  const updateClip = useUpdateClip()
  const regenerateClip = useRegenerateClip()

  const handleFieldChange = (field: string, value: any) => {
    setPendingChanges(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  const handleSaveChanges = async () => {
    if (!hasChanges || Object.keys(pendingChanges).length === 0) {
      return
    }

    try {
      await updateClip.mutateAsync({
        clipId: clip.id,
        data: pendingChanges as any // Type assertion for the UpdateClipRequest
      })

      setHasChanges(false)
      setPendingChanges({})
      onUpdate?.()
      toast.success('Changes saved successfully')
    } catch (error) {
      console.error('Failed to save changes:', error)
    }
  }

  const handleRegenerate = async () => {
    if (!hasChanges) {
      // If no changes, just regenerate with current settings
      regenerateClip.mutate({ clipId: clip.id })
      return
    }

    // Save changes first, then regenerate
    try {
      await handleSaveChanges()

      // Then regenerate
      regenerateClip.mutate({ clipId: clip.id })

      toast.success('Clip will be regenerated with new settings')
    } catch (error) {
      console.error('Failed to regenerate clip:', error)
    }
  }

  const handleDiscardChanges = () => {
    setPendingChanges({})
    setHasChanges(false)
    toast.info('Changes discarded')
  }

  // Merge clip data with pending changes for preview
  const previewClip = { ...clip, ...pendingChanges }

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-white">Edit Clip</h3>
          {clip.status !== 'ready' && (
            <Badge variant="warning" className="text-xs">
              {clip.status}
            </Badge>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {hasChanges && (
            <>
              <Button
                onClick={handleDiscardChanges}
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white"
              >
                <RotateCcw className="w-4 h-4 mr-1" />
                Discard
              </Button>
              <Button
                onClick={handleSaveChanges}
                size="sm"
                disabled={updateClip.isPending}
                className="bg-[#E94560] hover:bg-[#E94560]/90"
              >
                <Save className="w-4 h-4 mr-1" />
                {updateClip.isPending ? 'Saving...' : 'Save'}
              </Button>
            </>
          )}

          <Button
            onClick={handleRegenerate}
            size="sm"
            variant="outline"
            disabled={regenerateClip.isPending || clip.status === 'processing'}
            className="border-[#2A2A3E] text-gray-300 hover:bg-[#2A2A3E]"
          >
            <Settings className="w-4 h-4 mr-1" />
            {regenerateClip.isPending ? 'Regenerating...' : 'Regenerate'}
          </Button>

          {onClose && (
            <Button onClick={onClose} variant="ghost" size="sm">
              ✕
            </Button>
          )}
        </div>
      </div>

      {hasChanges && (
        <div className="bg-[#E94560]/10 border border-[#E94560]/20 rounded-lg p-3">
          <p className="text-sm text-[#E94560]">
            You have unsaved changes. Save them before regenerating or they will be lost.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Editors */}
        <div className="space-y-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 bg-[#2A2A3E]">
              <TabsTrigger value="title" className="text-xs">
                <Type className="w-4 h-4 mr-1" />
                Title
              </TabsTrigger>
              <TabsTrigger value="timing" className="text-xs">
                <Clock className="w-4 h-4 mr-1" />
                Timing
              </TabsTrigger>
              <TabsTrigger value="subtitles" className="text-xs">
                <Subtitles className="w-4 h-4 mr-1" />
                Subtitles
              </TabsTrigger>
            </TabsList>

            <div className="mt-4">
              <TabsContent value="title" className="space-y-4">
                <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-4">
                  <TitleEditor
                    clip={previewClip}
                    onChange={(title) => handleFieldChange('title', title)}
                  />
                </Card>
              </TabsContent>

              <TabsContent value="timing" className="space-y-4">
                <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-4">
                  <TimingEditor
                    clip={previewClip}
                    onChange={(startTime, endTime) => {
                      handleFieldChange('start_time', startTime)
                      handleFieldChange('end_time', endTime)
                    }}
                  />
                </Card>
              </TabsContent>

              <TabsContent value="subtitles" className="space-y-4">
                <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-4">
                  <SubtitleEditor
                    clip={previewClip}
                    onChange={(style, config) => {
                      handleFieldChange('subtitle_style', style)
                      if (config) {
                        handleFieldChange('subtitle_config', config)
                      }
                    }}
                  />
                </Card>
              </TabsContent>
            </div>
          </Tabs>
        </div>

        {/* Right: Preview */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-gray-400">Preview</h4>
          <Card className="bg-[#1A1A2E] border-[#2A2A3E] p-4">
            <ClipPreview
              clip={previewClip}
              highlightChanges={hasChanges}
            />
          </Card>
        </div>
      </div>

      <Separator className="bg-[#2A2A3E]" />

      {/* Summary of changes */}
      {hasChanges && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-400">Pending Changes</h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(pendingChanges).map(([key, value]) => (
              <Badge key={key} variant="outline" className="text-xs">
                {key}: {String(value).substring(0, 30)}
                {String(value).length > 30 ? '...' : ''}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}