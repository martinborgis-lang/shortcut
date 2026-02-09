'use client'

import { ReactNode } from 'react'
import { RedirectToSignIn, useAuth } from '@clerk/nextjs'
import { Sidebar } from '@/components/layout/sidebar'
import { NotificationProvider } from '@/components/layout/notification-provider'
import { NewProjectModal } from '@/components/modals/new-project-modal'
import { VideoPlayerModal } from '@/components/modals/video-player-modal'
import { useUIStore } from '@/stores'
import { cn } from '@/lib/utils'

interface AuthLayoutProps {
  children: ReactNode
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const { isLoaded, isSignedIn } = useAuth()
  const { sidebarCollapsed } = useUIStore()

  if (!isLoaded) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0F0F1A]">
        <div className="text-white">Loading...</div>
      </div>
    )
  }

  if (!isSignedIn) {
    return <RedirectToSignIn />
  }

  return (
    <div className="h-screen flex bg-[#0F0F1A]">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-auto bg-[#0F0F1A] p-4 lg:p-6">
          {children}
        </div>
      </main>
      <NewProjectModal />
      <VideoPlayerModal />
      <NotificationProvider />
    </div>
  )
}