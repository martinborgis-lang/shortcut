'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { UserButton } from '@clerk/nextjs'
import {
  Home,
  VideoIcon,
  Calendar,
  Settings,
  Plus,
  ChevronLeft,
  ChevronRight,
  Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { useUIStore } from '@/stores'

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home,
  },
  {
    name: 'Projects',
    href: '/projects',
    icon: VideoIcon,
  },
  {
    name: 'Schedule',
    href: '/schedule',
    icon: Calendar,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
  {
    name: 'Pricing',
    href: '/pricing',
    icon: Zap,
  },
]

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarCollapsed, toggleSidebar, setNewProjectModalOpen } = useUIStore()

  return (
    <div className={cn(
      "flex h-screen flex-col bg-[#0F0F1A] border-r border-[#2A2A3E] transition-all duration-300",
      "lg:relative lg:translate-x-0",
      sidebarCollapsed ? "w-16 lg:w-16" : "w-64 lg:w-64"
    )}>
      {/* Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-[#2A2A3E]">
        {!sidebarCollapsed && (
          <div className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-[#E94560] to-[#F27121]">
              <Zap className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white">Shortcut</span>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className="text-gray-400 hover:text-white hover:bg-[#2A2A3E]"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* New Project Button */}
      <div className="p-4">
        <Button
          onClick={() => setNewProjectModalOpen(true)}
          className={cn(
            "bg-[#E94560] hover:bg-[#E94560]/90 text-white font-medium",
            sidebarCollapsed ? "w-8 h-8 p-0" : "w-full"
          )}
        >
          <Plus className="h-4 w-4" />
          {!sidebarCollapsed && <span className="ml-2">New Project</span>}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center px-2 py-2 text-sm font-medium rounded-lg transition-colors",
                isActive
                  ? "bg-[#E94560]/10 text-[#E94560] border border-[#E94560]/20"
                  : "text-gray-300 hover:bg-[#2A2A3E] hover:text-white",
                sidebarCollapsed && "justify-center"
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  isActive ? "text-[#E94560]" : "text-gray-400 group-hover:text-white"
                )}
              />
              {!sidebarCollapsed && (
                <span className="ml-3">{item.name}</span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User Menu */}
      <div className="border-t border-[#2A2A3E] p-4">
        {sidebarCollapsed ? (
          <div className="flex justify-center">
            <UserButton afterSignOutUrl="/" />
          </div>
        ) : (
          <div className="flex items-center space-x-3">
            <UserButton afterSignOutUrl="/" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                User Account
              </p>
              <p className="text-xs text-gray-400 truncate">
                Manage your account
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}