'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Switch } from '@/components/ui/switch'
import { Progress } from '@/components/ui/progress'
import {
  User,
  CreditCard,
  Bell,
  Shield,
  Zap,
  ExternalLink,
  Twitter,
  Instagram,
  Youtube,
  Plus
} from 'lucide-react'
import { useUserStore } from '@/stores'
import { useUser } from '@/hooks'

export default function SettingsPage() {
  const { user, usage } = useUserStore()
  const { data: userFromAPI } = useUser()

  // Local state for settings
  const [emailNotifications, setEmailNotifications] = useState(true)
  const [pushNotifications, setPushNotifications] = useState(true)
  const [autoSchedule, setAutoSchedule] = useState(false)
  const [userName, setUserName] = useState('')

  const currentUser = userFromAPI || user

  // Initialize userName when currentUser changes
  React.useEffect(() => {
    if (currentUser?.name) {
      setUserName(currentUser.name)
    }
  }, [currentUser?.name])

  const usagePercentage = usage
    ? Math.round((usage.monthly_minutes_used / usage.monthly_minutes_limit) * 100)
    : 0

  const planFeatures = {
    free: ['100 minutes/month', '5 clips/month', 'Basic viral analysis', 'Standard support'],
    starter: ['500 minutes/month', '25 clips/month', 'Advanced viral analysis', 'Auto-scheduling', 'Priority support'],
    pro: ['2000 minutes/month', '100 clips/month', 'AI-powered optimization', 'Custom branding', 'Team collaboration'],
    enterprise: ['Unlimited minutes', 'Unlimited clips', 'White-label solution', 'Dedicated support', 'Custom integrations']
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-gray-400">Manage your account preferences and billing</p>
      </div>

      <Tabs defaultValue="account" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 bg-[#2A2A3E]">
          <TabsTrigger value="account" className="text-white">Account</TabsTrigger>
          <TabsTrigger value="billing" className="text-white">Billing</TabsTrigger>
          <TabsTrigger value="notifications" className="text-white">Notifications</TabsTrigger>
          <TabsTrigger value="social" className="text-white">Social Media</TabsTrigger>
        </TabsList>

        {/* Account Settings */}
        <TabsContent value="account" className="space-y-6">
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <div className="flex items-center mb-6">
              <User className="w-5 h-5 text-[#E94560] mr-2" />
              <h3 className="text-lg font-semibold text-white">Account Information</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Email</label>
                <Input
                  value={currentUser?.email || ''}
                  readOnly
                  className="bg-[#2A2A3E] border-[#2A2A3E] cursor-not-allowed"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Name</label>
                <Input
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="Enter your name"
                  className="bg-[#0F0F1A] border-[#2A2A3E]"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Plan</label>
                <div className="flex items-center space-x-2">
                  <Badge variant={usage?.plan === 'free' ? 'secondary' : 'success'} className="capitalize">
                    {usage?.plan || 'Free'}
                  </Badge>
                  {usage?.plan === 'free' && (
                    <Button asChild size="sm" className="bg-[#E94560] hover:bg-[#E94560]/90">
                      <Link href="/pricing">
                        <Zap className="w-4 h-4 mr-1" />
                        Upgrade
                      </Link>
                    </Button>
                  )}
                </div>
              </div>
            </div>

            <div className="flex justify-end mt-6">
              <Button className="bg-[#E94560] hover:bg-[#E94560]/90 text-white">
                Save Changes
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Billing Settings */}
        <TabsContent value="billing" className="space-y-6">
          {/* Current Plan */}
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <CreditCard className="w-5 h-5 text-[#E94560] mr-2" />
                <h3 className="text-lg font-semibold text-white">Current Plan</h3>
              </div>
              <Badge variant={usage?.plan === 'free' ? 'secondary' : 'success'} className="capitalize">
                {usage?.plan || 'Free'}
              </Badge>
            </div>

            {usage && (
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Usage this month</span>
                    <span className="text-white">
                      {usage.monthly_minutes_used} / {usage.monthly_minutes_limit} minutes
                    </span>
                  </div>
                  <Progress value={usagePercentage} className="h-2" />
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-400">Clips Generated:</span>
                    <span className="text-white ml-2">{usage.clips_generated} / {usage.clips_limit}</span>
                  </div>
                  <div>
                    <span className="text-gray-400">Remaining:</span>
                    <span className="text-white ml-2">{usage.monthly_minutes_limit - usage.monthly_minutes_used} min</span>
                  </div>
                </div>
              </div>
            )}

            {usage?.plan === 'free' && (
              <div className="mt-6 p-4 bg-[#E94560]/10 border border-[#E94560]/20 rounded-lg">
                <h4 className="text-white font-medium mb-2">Upgrade to unlock more features</h4>
                <ul className="text-sm text-gray-300 space-y-1 mb-4">
                  {planFeatures.starter.map((feature, index) => (
                    <li key={index}>• {feature}</li>
                  ))}
                </ul>
                <Button asChild className="bg-[#E94560] hover:bg-[#E94560]/90 text-white">
                  <Link href="/pricing">
                    <Zap className="w-4 h-4 mr-2" />
                    Upgrade to Starter - 9€/month
                  </Link>
                </Button>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Notifications */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <div className="flex items-center mb-6">
              <Bell className="w-5 h-5 text-[#E94560] mr-2" />
              <h3 className="text-lg font-semibold text-white">Notification Preferences</h3>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">Email Notifications</h4>
                  <p className="text-sm text-gray-400">Receive updates about your projects via email</p>
                </div>
                <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">Push Notifications</h4>
                  <p className="text-sm text-gray-400">Get notified when clips are ready</p>
                </div>
                <Switch
                  checked={pushNotifications}
                  onCheckedChange={setPushNotifications}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium">Auto-Schedule</h4>
                  <p className="text-sm text-gray-400">Automatically schedule clips for optimal posting times</p>
                </div>
                <Switch
                  checked={autoSchedule}
                  onCheckedChange={setAutoSchedule}
                  disabled={usage?.plan === 'free'}
                />
              </div>

              {usage?.plan === 'free' && (
                <div className="p-3 bg-[#E94560]/10 border border-[#E94560]/20 rounded-lg">
                  <p className="text-sm text-gray-300">
                    Auto-scheduling is available on Starter plan and above.
                  </p>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Social Media Accounts */}
        <TabsContent value="social" className="space-y-6">
          <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E]">
            <div className="flex items-center mb-6">
              <Shield className="w-5 h-5 text-[#E94560] mr-2" />
              <h3 className="text-lg font-semibold text-white">Connected Accounts</h3>
            </div>

            <div className="space-y-4">
              {/* YouTube */}
              <div className="flex items-center justify-between p-4 border border-[#2A2A3E] rounded-lg">
                <div className="flex items-center space-x-3">
                  <Youtube className="w-5 h-5 text-red-500" />
                  <div>
                    <h4 className="text-white font-medium">YouTube</h4>
                    <p className="text-sm text-gray-400">Not connected</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-[#2A2A3E]">
                  <Plus className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              </div>

              {/* TikTok */}
              <div className="flex items-center justify-between p-4 border border-[#2A2A3E] rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 bg-black rounded-full flex items-center justify-center">
                    <div className="w-3 h-3 bg-white rounded-full"></div>
                  </div>
                  <div>
                    <h4 className="text-white font-medium">TikTok</h4>
                    <p className="text-sm text-gray-400">Not connected</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-[#2A2A3E]">
                  <Plus className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              </div>

              {/* Instagram */}
              <div className="flex items-center justify-between p-4 border border-[#2A2A3E] rounded-lg">
                <div className="flex items-center space-x-3">
                  <Instagram className="w-5 h-5 text-pink-500" />
                  <div>
                    <h4 className="text-white font-medium">Instagram</h4>
                    <p className="text-sm text-gray-400">Not connected</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-[#2A2A3E]">
                  <Plus className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              </div>

              {/* Twitter */}
              <div className="flex items-center justify-between p-4 border border-[#2A2A3E] rounded-lg">
                <div className="flex items-center space-x-3">
                  <Twitter className="w-5 h-5 text-blue-500" />
                  <div>
                    <h4 className="text-white font-medium">Twitter / X</h4>
                    <p className="text-sm text-gray-400">Not connected</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" className="border-[#2A2A3E]">
                  <Plus className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              </div>
            </div>

            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-sm text-blue-300">
                Connect your social media accounts to automatically publish and schedule your clips.
              </p>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}