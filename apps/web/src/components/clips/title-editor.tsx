'use client'

import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Type, Hash, BookOpen } from 'lucide-react'
import type { Clip } from '../../../../shared/types'

interface TitleEditorProps {
  clip: Clip
  onChange: (title: string, description?: string, notes?: string) => void
}

/**
 * Title Editor Component
 *
 * Critères PRD F5-09: Éditeur de titre - Input editable pour le titre du clip
 * + Extension pour description et notes utilisateur
 */
export function TitleEditor({ clip, onChange }: TitleEditorProps) {
  const [title, setTitle] = useState(clip.title || '')
  const [description, setDescription] = useState(clip.description || '')
  const [notes, setNotes] = useState(clip.userNotes || '')
  const [titleLength, setTitleLength] = useState(0)

  useEffect(() => {
    setTitleLength(title.length)
  }, [title])

  const handleTitleChange = (newTitle: string) => {
    setTitle(newTitle)
    onChange(newTitle, description, notes)
  }

  const handleDescriptionChange = (newDescription: string) => {
    setDescription(newDescription)
    onChange(title, newDescription, notes)
  }

  const handleNotesChange = (newNotes: string) => {
    setNotes(newNotes)
    onChange(title, description, newNotes)
  }

  const generateSuggestedTitles = () => {
    // Generate title suggestions based on clip content
    const suggestions = [
      `Viral Moment: ${clip.hook || 'Engaging Content'}`,
      `${Math.round((clip.viralScore || 0) * 100)}% Viral: ${clip.reason || 'Must Watch'}`,
      `${Math.floor(clip.duration)}s of Pure Gold`,
      clip.hook || 'Captivating Clip',
      `Best ${Math.floor(clip.duration)}s You'll Watch Today`
    ].filter(Boolean).slice(0, 3)

    return suggestions
  }

  const suggestedTitles = generateSuggestedTitles()

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2">
        <Type className="w-5 h-5 text-[#E94560]" />
        <h3 className="text-lg font-medium text-white">Title & Description</h3>
      </div>

      {/* Main Title */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="clip-title" className="text-sm font-medium text-gray-300">
            Clip Title *
          </Label>
          <div className="flex items-center space-x-2">
            <span className={`text-xs ${titleLength > 100 ? 'text-red-400' : 'text-gray-400'}`}>
              {titleLength}/100
            </span>
            {titleLength > 100 && (
              <Badge variant="destructive" className="text-xs">
                Too long
              </Badge>
            )}
          </div>
        </div>

        <Input
          id="clip-title"
          value={title}
          onChange={(e) => handleTitleChange(e.target.value)}
          placeholder="Enter a compelling title for your clip"
          className="bg-[#2A2A3E] border-[#3A3A4E] text-white placeholder:text-gray-400"
          maxLength={100}
        />

        {title.length === 0 && (
          <p className="text-xs text-red-400">Title is required</p>
        )}
      </div>

      {/* Title Suggestions */}
      {suggestedTitles.length > 0 && (
        <div className="space-y-2">
          <Label className="text-sm font-medium text-gray-300">
            Suggested Titles
          </Label>
          <div className="space-y-2">
            {suggestedTitles.map((suggestion, index) => (
              <Button
                key={index}
                onClick={() => handleTitleChange(suggestion)}
                variant="ghost"
                size="sm"
                className="w-full justify-start text-left h-auto p-3 text-gray-300 hover:text-white hover:bg-[#2A2A3E] border border-[#3A3A4E]"
              >
                <Hash className="w-3 h-3 mr-2 flex-shrink-0 mt-0.5" />
                <span className="truncate">{suggestion}</span>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Description */}
      <div className="space-y-3">
        <Label htmlFor="clip-description" className="text-sm font-medium text-gray-300">
          Description (Optional)
        </Label>
        <Textarea
          id="clip-description"
          value={description}
          onChange={(e) => handleDescriptionChange(e.target.value)}
          placeholder="Add a description to help viewers understand what this clip is about"
          className="bg-[#2A2A3E] border-[#3A3A4E] text-white placeholder:text-gray-400 min-h-[100px]"
          maxLength={500}
        />
        <div className="flex justify-between items-center">
          <p className="text-xs text-gray-400">
            A good description can improve engagement and searchability
          </p>
          <span className="text-xs text-gray-400">
            {description.length}/500
          </span>
        </div>
      </div>

      {/* Personal Notes */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-gray-400" />
          <Label htmlFor="clip-notes" className="text-sm font-medium text-gray-300">
            Personal Notes (Private)
          </Label>
        </div>
        <Textarea
          id="clip-notes"
          value={notes}
          onChange={(e) => handleNotesChange(e.target.value)}
          placeholder="Add private notes about this clip (only visible to you)"
          className="bg-[#2A2A3E] border-[#3A3A4E] text-white placeholder:text-gray-400 min-h-[80px]"
          maxLength={1000}
        />
        <div className="flex justify-between items-center">
          <p className="text-xs text-gray-400">
            Use notes to remember why this clip is special or ideas for improvement
          </p>
          <span className="text-xs text-gray-400">
            {notes.length}/1000
          </span>
        </div>
      </div>

      {/* Title Best Practices */}
      <div className="p-4 bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg">
        <h4 className="text-sm font-medium text-gray-300 mb-2">💡 Title Best Practices</h4>
        <ul className="text-xs text-gray-400 space-y-1">
          <li>• Keep it under 60 characters for best social media compatibility</li>
          <li>• Start with action words or questions to grab attention</li>
          <li>• Include emotional triggers (amazing, shocking, must-see)</li>
          <li>• Mention the duration if it's short (under 30s)</li>
          <li>• Use numbers when relevant (3 tips, 5 seconds, etc.)</li>
        </ul>
      </div>

      {/* Current Clip Stats */}
      {(clip.viralScore || clip.hook || clip.reason) && (
        <div className="p-4 bg-[#0F0F1A] border border-[#2A2A3E] rounded-lg">
          <h4 className="text-sm font-medium text-gray-300 mb-3">Clip Insights</h4>
          <div className="space-y-2">
            {clip.viralScore && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Viral Score:</span>
                <Badge variant="success" className="text-xs">
                  {Math.round(clip.viralScore * 100)}%
                </Badge>
              </div>
            )}
            {clip.hook && (
              <div>
                <span className="text-xs text-gray-400">Hook:</span>
                <p className="text-xs text-gray-300 mt-1">{clip.hook}</p>
              </div>
            )}
            {clip.reason && (
              <div>
                <span className="text-xs text-gray-400">Why it's viral:</span>
                <p className="text-xs text-gray-300 mt-1">{clip.reason}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}