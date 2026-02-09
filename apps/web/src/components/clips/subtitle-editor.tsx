'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Subtitles, Palette, Type, MapPin, Sparkles } from 'lucide-react'
import type { Clip } from '../../../../shared/types'

interface SubtitleEditorProps {
  clip: Clip
  onChange: (style: string, config?: Record<string, any>) => void
}

// Predefined subtitle styles
const SUBTITLE_STYLES = [
  {
    id: 'hormozi',
    name: 'Hormozi',
    description: 'Bold white text with black outline, perfect for business content',
    preview: {
      fontFamily: 'Arial Black',
      fontSize: 48,
      fontColor: '#FFFFFF',
      outlineColor: '#000000',
      outlineWidth: 2,
      position: 'center',
      background: false,
      animation: 'word_highlight'
    },
    bestFor: ['Business', 'Motivation', 'Education'],
    platforms: ['Instagram', 'TikTok', 'YouTube Shorts']
  },
  {
    id: 'clean',
    name: 'Clean',
    description: 'Simple and readable with semi-transparent background',
    preview: {
      fontFamily: 'Helvetica',
      fontSize: 44,
      fontColor: '#FFFFFF',
      outlineColor: '#333333',
      outlineWidth: 1,
      position: 'bottom',
      background: true,
      backgroundColor: 'rgba(0,0,0,0.7)',
      animation: 'none'
    },
    bestFor: ['Professional', 'News', 'Corporate'],
    platforms: ['LinkedIn', 'YouTube', 'Instagram']
  },
  {
    id: 'neon',
    name: 'Neon',
    description: 'Eye-catching neon colors with glow effects',
    preview: {
      fontFamily: 'Impact',
      fontSize: 50,
      fontColor: '#00FFFF',
      outlineColor: '#FF00FF',
      outlineWidth: 3,
      position: 'center',
      background: false,
      animation: 'glow',
      shadow: true
    },
    bestFor: ['Gaming', 'Entertainment', 'Music'],
    platforms: ['TikTok', 'Instagram Reels', 'Twitch']
  },
  {
    id: 'karaoke',
    name: 'Karaoke',
    description: 'Fun animated text that highlights words as spoken',
    preview: {
      fontFamily: 'Comic Sans MS',
      fontSize: 46,
      fontColor: '#FFD700',
      outlineColor: '#000000',
      outlineWidth: 2,
      position: 'center',
      background: false,
      animation: 'word_by_word'
    },
    bestFor: ['Music', 'Comedy', 'Entertainment'],
    platforms: ['TikTok', 'Instagram Reels', 'YouTube Shorts']
  },
  {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean and simple without outlines or backgrounds',
    preview: {
      fontFamily: 'SF Pro',
      fontSize: 40,
      fontColor: '#FFFFFF',
      outlineColor: 'none',
      outlineWidth: 0,
      position: 'bottom',
      background: false,
      animation: 'fade'
    },
    bestFor: ['Aesthetic', 'Lifestyle', 'Art'],
    platforms: ['Instagram', 'Pinterest', 'YouTube']
  }
]

/**
 * Subtitle Editor Component
 *
 * Critères PRD F5-08: Éditeur de sous-titres
 * - Sélecteur de style
 * - Preview du rendu
 * - Options de couleur/taille/position
 */
export function SubtitleEditor({ clip, onChange }: SubtitleEditorProps) {
  const [selectedStyle, setSelectedStyle] = useState(clip.subtitleStyle || 'hormozi')
  const [customConfig, setCustomConfig] = useState(clip.subtitleConfig || {})

  const currentStyle = SUBTITLE_STYLES.find(style => style.id === selectedStyle) || SUBTITLE_STYLES[0]

  useEffect(() => {
    onChange(selectedStyle, customConfig)
  }, [selectedStyle, customConfig, onChange])

  const handleStyleChange = (styleId: string) => {
    setSelectedStyle(styleId)
    // Reset custom config when changing style
    setCustomConfig({})
  }

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...customConfig, [key]: value }
    setCustomConfig(newConfig)
  }

  const getPreviewStyle = () => {
    const baseStyle = currentStyle.preview
    return { ...baseStyle, ...customConfig }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Subtitles className="w-5 h-5 text-[#E94560]" />
        <h3 className="text-lg font-medium text-white">Subtitle Style</h3>
      </div>

      {/* Style Selector */}
      <div className="space-y-3">
        <Label className="text-sm font-medium text-gray-300">
          Choose Style
        </Label>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SUBTITLE_STYLES.map((style) => (
            <div
              key={style.id}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedStyle === style.id
                  ? 'border-[#E94560] bg-[#E94560]/10'
                  : 'border-[#3A3A4E] hover:border-[#4A4A5E] bg-[#2A2A3E]'
              }`}
              onClick={() => handleStyleChange(style.id)}
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-white">{style.name}</h4>
                {selectedStyle === style.id && (
                  <Badge className="bg-[#E94560] text-white text-xs">
                    Selected
                  </Badge>
                )}
              </div>

              <p className="text-xs text-gray-400 mb-3">
                {style.description}
              </p>

              {/* Preview */}
              <div className="bg-[#0F0F1A] rounded-md p-3 mb-3 text-center">
                <div
                  className="text-sm font-bold"
                  style={{
                    fontFamily: style.preview.fontFamily,
                    color: style.preview.fontColor,
                    textShadow: style.preview.outlineWidth > 0
                      ? `1px 1px 0 ${style.preview.outlineColor}, -1px -1px 0 ${style.preview.outlineColor}, 1px -1px 0 ${style.preview.outlineColor}, -1px 1px 0 ${style.preview.outlineColor}`
                      : 'none',
                    backgroundColor: style.preview.background ? style.preview.backgroundColor : 'transparent',
                    padding: style.preview.background ? '4px 8px' : '0',
                    borderRadius: style.preview.background ? '4px' : '0',
                  }}
                >
                  Sample Text
                </div>
              </div>

              {/* Best For Tags */}
              <div className="flex flex-wrap gap-1 mb-2">
                {style.bestFor.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              {/* Platform Icons */}
              <div className="flex space-x-1">
                {style.platforms.map((platform) => (
                  <span key={platform} className="text-xs text-gray-400">
                    {platform}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <Separator className="bg-[#2A2A3E]" />

      {/* Custom Configuration */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Palette className="w-4 h-4 text-gray-400" />
          <Label className="text-sm font-medium text-gray-300">
            Customize "{currentStyle.name}" Style
          </Label>
        </div>

        {/* Font Size */}
        <div className="space-y-2">
          <Label className="text-sm text-gray-400">
            Font Size: {customConfig.fontSize || currentStyle.preview.fontSize}px
          </Label>
          <Slider
            value={[customConfig.fontSize || currentStyle.preview.fontSize]}
            onValueChange={(value) => handleConfigChange('fontSize', value[0])}
            min={24}
            max={72}
            step={2}
            className="w-full"
          />
        </div>

        {/* Position */}
        <div className="space-y-2">
          <Label className="text-sm text-gray-400">Position</Label>
          <Select
            value={customConfig.position || currentStyle.preview.position}
            onValueChange={(value) => handleConfigChange('position', value)}
          >
            <SelectTrigger className="bg-[#2A2A3E] border-[#3A3A4E] text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="top">Top</SelectItem>
              <SelectItem value="center">Center</SelectItem>
              <SelectItem value="bottom">Bottom</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Animation */}
        <div className="space-y-2">
          <Label className="text-sm text-gray-400">Animation</Label>
          <Select
            value={customConfig.animation || currentStyle.preview.animation}
            onValueChange={(value) => handleConfigChange('animation', value)}
          >
            <SelectTrigger className="bg-[#2A2A3E] border-[#3A3A4E] text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem value="fade">Fade In</SelectItem>
              <SelectItem value="word_highlight">Word Highlight</SelectItem>
              <SelectItem value="word_by_word">Word by Word</SelectItem>
              <SelectItem value="glow">Glow Effect</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Outline Width (if applicable) */}
        {currentStyle.preview.outlineWidth > 0 && (
          <div className="space-y-2">
            <Label className="text-sm text-gray-400">
              Outline Width: {customConfig.outlineWidth || currentStyle.preview.outlineWidth}px
            </Label>
            <Slider
              value={[customConfig.outlineWidth || currentStyle.preview.outlineWidth]}
              onValueChange={(value) => handleConfigChange('outlineWidth', value[0])}
              min={0}
              max={6}
              step={1}
              className="w-full"
            />
          </div>
        )}
      </div>

      <Separator className="bg-[#2A2A3E]" />

      {/* Live Preview */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-yellow-400" />
          <Label className="text-sm font-medium text-gray-300">
            Live Preview
          </Label>
        </div>

        <div className="bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg p-6">
          {/* Mock video background */}
          <div className="aspect-[9/16] max-w-xs mx-auto bg-gradient-to-br from-gray-800 to-gray-900 rounded-lg relative overflow-hidden">
            {/* Fake video content */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />

            {/* Subtitle preview positioned based on settings */}
            <div
              className={`absolute inset-x-0 flex justify-center items-center px-4 ${
                (customConfig.position || currentStyle.preview.position) === 'top'
                  ? 'top-8'
                  : (customConfig.position || currentStyle.preview.position) === 'center'
                  ? 'top-1/2 -translate-y-1/2'
                  : 'bottom-8'
              }`}
            >
              <div
                className="text-center font-bold leading-tight"
                style={{
                  fontFamily: customConfig.fontFamily || currentStyle.preview.fontFamily,
                  fontSize: `${(customConfig.fontSize || currentStyle.preview.fontSize) * 0.3}px`, // Scaled down for preview
                  color: customConfig.fontColor || currentStyle.preview.fontColor,
                  textShadow: (customConfig.outlineWidth || currentStyle.preview.outlineWidth) > 0
                    ? `1px 1px 0 ${customConfig.outlineColor || currentStyle.preview.outlineColor}, -1px -1px 0 ${customConfig.outlineColor || currentStyle.preview.outlineColor}, 1px -1px 0 ${customConfig.outlineColor || currentStyle.preview.outlineColor}, -1px 1px 0 ${customConfig.outlineColor || currentStyle.preview.outlineColor}`
                    : 'none',
                  backgroundColor: currentStyle.preview.background
                    ? (customConfig.backgroundColor || currentStyle.preview.backgroundColor)
                    : 'transparent',
                  padding: currentStyle.preview.background ? '2px 6px' : '0',
                  borderRadius: currentStyle.preview.background ? '2px' : '0',
                }}
              >
                This is how your subtitles will look
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-400 text-center mt-4">
            Preview is scaled down. Actual size will be larger on the video.
          </p>
        </div>
      </div>

      {/* Style Recommendations */}
      <div className="p-4 bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg">
        <h4 className="text-sm font-medium text-gray-300 mb-2">💡 Style Recommendations</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Current clip viral score:</span>
            <Badge variant="success" className="text-xs">
              {Math.round((clip.viralScore || 0) * 100)}%
            </Badge>
          </div>
          {clip.viralScore && clip.viralScore > 0.8 && (
            <p className="text-xs text-green-400">
              ✓ This clip has high viral potential. The current style works well!
            </p>
          )}
          {clip.viralScore && clip.viralScore < 0.5 && (
            <p className="text-xs text-yellow-400">
              ⚡ Try the "Hormozi" or "Neon" styles to boost engagement.
            </p>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex justify-between pt-4 border-t border-[#2A2A3E]">
        <Button
          onClick={() => {
            setSelectedStyle('hormozi')
            setCustomConfig({})
          }}
          variant="ghost"
          size="sm"
          className="text-gray-400 hover:text-white"
        >
          Reset to Default
        </Button>

        <Button
          onClick={() => {
            // Auto-optimize based on clip content
            if (clip.viralScore && clip.viralScore > 0.7) {
              setSelectedStyle('hormozi')
            } else if (clip.reason?.toLowerCase().includes('music')) {
              setSelectedStyle('karaoke')
            } else {
              setSelectedStyle('neon')
            }
            setCustomConfig({})
          }}
          variant="outline"
          size="sm"
          className="border-[#3A3A4E] text-gray-300 hover:bg-[#2A2A3E]"
        >
          <Sparkles className="w-4 h-4 mr-1" />
          Auto-Optimize
        </Button>
      </div>
    </div>
  )
}