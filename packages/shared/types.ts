// Shared TypeScript types between frontend and backend

export interface User {
  id: string;
  clerkId: string;
  email: string;
  firstName?: string;
  lastName?: string;
  profileImageUrl?: string;
  isPremium: boolean;
  clipsGenerated: number;
  clipsLimit: number;
  createdAt: string;
  updatedAt: string;
}

export interface Project {
  id: string;
  userId: string;
  name: string;
  description?: string;
  originalVideoUrl: string;
  originalVideoFilename: string;
  originalVideoSize: number;
  originalVideoDuration?: number;
  videoMetadata?: Record<string, any>;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  processingProgress: number;
  errorMessage?: string;
  transcription?: string;
  viralMoments?: ViralMoment[];
  topics?: string[];
  sentimentAnalysis?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export interface Clip {
  id: string;
  projectId: string;
  title: string;
  description?: string;
  startTime: number;
  endTime: number;
  duration: number;
  videoUrl?: string;
  thumbnailUrl?: string;
  previewGifUrl?: string;
  viralScore?: number;
  engagementPrediction?: Record<string, any>;
  hookStrength?: number;
  contentQuality?: number;
  subtitleStyle?: Record<string, any>;
  backgroundMusic?: string;
  visualEffects?: Record<string, any>;
  branding?: Record<string, any>;
  status: 'pending' | 'processing' | 'ready' | 'failed';
  processingProgress: number;
  errorMessage?: string;
  isFavorite: boolean;
  userRating?: number;
  userNotes?: string;
  createdAt: string;
  updatedAt: string;
  generatedAt?: string;
}

export interface ViralMoment {
  start: number;
  end: number;
  score: number;
  reason: string;
  duration?: number;
  transcript?: string;
  emotions?: string[];
  visualElements?: string[];
}

export interface SocialAccount {
  id: string;
  userId: string;
  platform: 'tiktok' | 'instagram' | 'youtube' | 'twitter';
  platformUserId: string;
  username: string;
  displayName?: string;
  isActive: boolean;
  isVerified: boolean;
  lastSync?: string;
  accountMetadata?: Record<string, any>;
  publishingPermissions?: Record<string, any>;
  lastError?: string;
  errorCount: number;
  disabledUntil?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ScheduledPost {
  id: string;
  clipId: string;
  socialAccountId: string;
  scheduledTime: string;
  timeZone: string;
  caption?: string;
  hashtags?: string[];
  mentions?: string[];
  platformSettings?: Record<string, any>;
  postMetadata?: Record<string, any>;
  status: 'scheduled' | 'posted' | 'failed' | 'cancelled';
  postedAt?: string;
  failedAt?: string;
  errorMessage?: string;
  platformPostId?: string;
  platformResponse?: Record<string, any>;
  views?: number;
  likes?: number;
  shares?: number;
  comments?: number;
  engagementRate?: number;
  retryCount: number;
  maxRetries: number;
  nextRetryAt?: string;
  createdAt: string;
  updatedAt: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Request types
export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface UploadVideoRequest {
  file: File;
  projectId?: string;
}

export interface CreateClipRequest {
  projectId: string;
  startTime: number;
  endTime: number;
  title?: string;
  description?: string;
}

export interface SchedulePostRequest {
  clipId: string;
  socialAccountId: string;
  scheduledTime: string;
  caption?: string;
  hashtags?: string[];
  platformSettings?: Record<string, any>;
}

// Webhook types
export interface WebhookEvent {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

// Error types
export interface ApiError {
  message: string;
  code: string;
  details?: Record<string, any>;
}