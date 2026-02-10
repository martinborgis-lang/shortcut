'use client'

import { VideoIcon, Play, Clock, TrendingUp } from 'lucide-react'
import { StatsCard } from '@/components/dashboard/stats-card'
import { RecentProjects } from '@/components/dashboard/recent-projects'
import { RecentClips } from '@/components/dashboard/recent-clips'
import { DashboardSkeleton } from '@/components/shared/loading-skeleton'
import { Button } from '@/components/ui/button'
import { useUserStore, useUIStore } from '@/stores'
import { useUser, useDashboardStats, useProjects } from '@/hooks'
import { Progress } from '@/components/ui/progress'

export default function DashboardPage() {
  const { user, usage } = useUserStore()
  const { setNewProjectModalOpen } = useUIStore()

  // Fetch data
  const { data: userFromAPI, isLoading: isUserLoading } = useUser()
  const { data: stats, isLoading: isStatsLoading } = useDashboardStats()
  const { data: projects = [], isLoading: isProjectsLoading } = useProjects()

  const isLoading = isUserLoading || isStatsLoading

  if (isLoading) {
    return <DashboardSkeleton />
  }

  // Calculate usage percentage
  const usagePercentage = usage
    ? Math.round((usage.monthly_minutes_used / usage.monthly_minutes_limit) * 100)
    : 0

  // Mock recent clips data (would come from API)
  const recentClips: any[] = []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Welcome back! Here's what's happening with your projects.</p>
        </div>
        <Button
          onClick={() => setNewProjectModalOpen(true)}
          className="bg-[#E94560] hover:bg-[#E94560]/90 text-white"
        >
          <Play className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Projects"
          value={stats?.totalProjects || projects.length}
          subtitle="All time"
          icon={<VideoIcon className="w-6 h-6" />}
        />

        <StatsCard
          title="Clips Generated"
          value={stats?.totalClips || 0}
          subtitle="This month"
          icon={<Play className="w-6 h-6" />}
        />

        <StatsCard
          title="Minutes Used"
          value={`${usage?.monthly_minutes_used || 0}/${usage?.monthly_minutes_limit || 100}`}
          subtitle={`${usagePercentage}% of plan limit`}
          icon={<Clock className="w-6 h-6" />}
          badge={{
            text: usage?.plan || 'Free',
            variant: usage?.plan === 'free' ? 'secondary' : 'success'
          }}
        />

        <StatsCard
          title="Avg. Viral Score"
          value="78%"
          subtitle="+12% from last month"
          icon={<TrendingUp className="w-6 h-6" />}
          trend={{
            value: 12,
            isPositive: true
          }}
        />
      </div>

      {/* Usage Progress */}
      {usage && (
        <div className="bg-[#1A1A2E] border border-[#2A2A3E] rounded-xl p-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-white">Monthly Usage</h3>
            <span className="text-sm text-gray-400">
              {usage.monthly_minutes_used} / {usage.monthly_minutes_limit} minutes
            </span>
          </div>
          <Progress
            value={usagePercentage}
            className="h-2"
          />
          <div className="flex justify-between mt-2 text-sm text-gray-400">
            <span>Plan: {usage.plan}</span>
            <span className={usagePercentage > 80 ? 'text-yellow-400' : usagePercentage > 95 ? 'text-red-400' : 'text-green-400'}>
              {usage.monthly_minutes_limit - usage.monthly_minutes_used} minutes remaining
            </span>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <RecentProjects projects={projects} isLoading={isProjectsLoading} />
        <RecentClips clips={recentClips} isLoading={false} />
      </div>
    </div>
  )
}