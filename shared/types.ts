// Shared types for the ShortCut application
// These types should eventually match the backend API schemas

export interface User {
  id: string
  email: string
  name: string
  firstName?: string
  lastName?: string
  profileImageUrl?: string
  plan: 'FREE' | 'STARTER' | 'PRO' | 'ENTERPRISE'
  monthlyMinutesUsed: number
  monthlyMinutesLimit: number
  clipsGenerated: number
  clipsLimit: number
  isPremium: boolean
  createdAt: string
}

export interface Project {
  id: string
  userId: string
  name: string
  description?: string
  sourceUrl: string
  sourceFilename?: string
  sourceSize?: number
  sourceDuration?: number
  videoMetadata?: any
  status: 'pending' | 'processing' | 'completed' | 'failed'
  currentStep?: string
  processingProgress: number
  errorMessage?: string
  transcriptJson?: any
  viralSegments?: any
  maxClipsRequested: number
  createdAt: string
  updatedAt?: string
  completedAt?: string
}

export interface Clip {
  id: string
  projectId: string
  title: string
  description?: string
  startTime: number
  endTime: number
  duration: number
  s3Key?: string
  videoUrl?: string
  thumbnailUrl?: string
  previewGifUrl?: string
  viralScore?: number
  reason?: string
  hook?: string
  subtitleStyle: string
  subtitleConfig?: any
  cropSettings?: any
  status: 'pending' | 'processing' | 'completed' | 'failed'
  processingProgress: number
  errorMessage?: string
  isFavorite: boolean
  userRating?: number
  userNotes?: string
  createdAt: string
  updatedAt?: string
  generatedAt?: string
}

export interface SocialAccount {
  id: string
  userId: string
  platform: string
  platformUserId: string
  username: string
  displayName?: string
  isActive: boolean
  isVerified: boolean
  lastSync?: string
  accountMetadata?: any
  publishingPermissions?: any
  createdAt: string
  updatedAt?: string
}

export interface ScheduledPost {
  id: string
  clipId: string
  socialAccountId: string
  scheduledTime: string
  timeZone: string
  caption?: string
  hashtags?: string[]
  mentions?: string[]
  platformSettings?: any
  status: 'pending' | 'published' | 'failed' | 'cancelled'
  postedAt?: string
  failedAt?: string
  errorMessage?: string
  platformPostId?: string
  platformResponse?: any
  views?: number
  likes?: number
  shares?: number
  comments?: number
  engagementRate?: number
  createdAt: string
  updatedAt?: string
}

// API Response types
export interface ApiResponse<T> {
  success: boolean
  data: T
  message?: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  totalPages: number
}

// Usage & billing types
export interface UsageStats {
  monthlyMinutesUsed: number
  monthlyMinutesLimit: number
  monthlyMinutesRemaining: number
  clipsGenerated: number
  clipsLimit: number
  plan: 'FREE' | 'STARTER' | 'PRO' | 'ENTERPRISE'
}

export interface BillingInfo {
  plan: 'FREE' | 'STARTER' | 'PRO' | 'ENTERPRISE'
  status: string
  currentPeriodEnd?: string
  cancelAtPeriodEnd?: boolean
  stripeCustomerId?: string
}