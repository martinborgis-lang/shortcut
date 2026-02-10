import { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-center justify-center p-12 text-center border-dashed border-[#2A2A3E] bg-zinc-900/50 backdrop-blur-sm">
      <div className="mb-4 text-gray-400">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400 mb-6 max-w-md">{description}</p>
      {action && (
        <Button
          onClick={action.onClick}
          className="bg-[#E94560] hover:bg-[#E94560]/90 text-white"
        >
          {action.label}
        </Button>
      )}
    </Card>
  )
}

export function EmptyProjects({ onCreateProject }: { onCreateProject: () => void }) {
  return (
    <EmptyState
      icon={
        <div className="w-16 h-16 rounded-full bg-[#2A2A3E] flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2h4a1 1 0 011 1v1a1 1 0 01-1 1h-1v12a2 2 0 01-2 2H6a2 2 0 01-2-2V7H3a1 1 0 01-1-1V5a1 1 0 011-1h4z" />
          </svg>
        </div>
      }
      title="No projects yet"
      description="Create your first project by uploading a video or pasting a YouTube/Twitch URL to generate viral clips automatically."
      action={{
        label: "Create Project",
        onClick: onCreateProject
      }}
    />
  )
}

export function EmptyClips() {
  return (
    <EmptyState
      icon={
        <div className="w-16 h-16 rounded-full bg-[#2A2A3E] flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1a4 4 0 014 4v1a1 1 0 001 1h3a1 1 0 001-1v-1a4 4 0 014-4h1m-1 4a4 4 0 01-4 4H9a4 4 0 01-4-4v-1a1 1 0 011-1h3a1 1 0 001-1v-1a4 4 0 014-4z" />
          </svg>
        </div>
      }
      title="No clips generated yet"
      description="Clips will appear here once your video has been processed. This usually takes a few minutes depending on the video length."
    />
  )
}