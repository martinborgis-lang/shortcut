import type { Project, Clip, User as SharedUser, ApiResponse, PaginatedResponse } from '../../../shared/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// API-specific types that extend shared types
export interface User {
  id: string
  clerk_id: string
  email: string
  name: string
  first_name: string | null
  last_name: string | null
  profile_image_url: string | null
  plan: 'free' | 'starter' | 'pro' | 'enterprise'
  monthly_minutes_used: number
  monthly_minutes_limit: number
  created_at: string
}

export interface UsageStats {
  monthly_minutes_used: number
  monthly_minutes_limit: number
  monthly_minutes_remaining: number
  clips_generated: number
  clips_limit: number
  plan: 'free' | 'starter' | 'pro' | 'enterprise'
}

export interface CreateProjectRequest {
  name: string
  description?: string
  originalVideoUrl?: string
}

export interface DashboardStats {
  totalProjects: number
  totalClips: number
  monthlyMinutesUsed: number
  monthlyMinutesLimit: number
  recentProjects: Project[]
  recentClips: Clip[]
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    token?: string | null
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    }

    // Add authorization header if token is provided
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    const config: RequestInit = {
      headers,
      ...options,
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`)
    }

    return response.json()
  }

  // Health check
  async health(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health')
  }

  // User endpoints
  async getCurrentUser(token: string): Promise<User> {
    return this.request<User>('/api/users/me', {}, token)
  }

  async getUserUsage(token: string): Promise<UsageStats> {
    return this.request<UsageStats>('/api/users/me/usage', {}, token)
  }

  async resetMonthlyUsage(token: string): Promise<{ status: string; message: string; monthly_minutes_used: number }> {
    return this.request('/api/users/me/reset-usage', {
      method: 'POST',
    }, token)
  }

  // Dashboard
  async getDashboardStats(token: string): Promise<DashboardStats> {
    return this.request<DashboardStats>('/api/dashboard/stats', {}, token)
  }

  // Projects
  async getProjects(token?: string): Promise<Project[]> {
    return this.request<Project[]>('/api/projects', {}, token)
  }

  async getProject(projectId: string, token?: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}`, {}, token)
  }

  async createProject(data: CreateProjectRequest, token?: string): Promise<Project> {
    return this.request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    }, token)
  }

  async updateProject(projectId: string, data: Partial<Project>, token?: string): Promise<Project> {
    return this.request<Project>(`/api/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, token)
  }

  async deleteProject(projectId: string, token?: string): Promise<void> {
    return this.request<void>(`/api/projects/${projectId}`, {
      method: 'DELETE',
    }, token)
  }

  // Clips
  async getClips(projectId: string, token?: string): Promise<Clip[]> {
    return this.request<Clip[]>(`/api/projects/${projectId}/clips`, {}, token)
  }

  async getClip(clipId: string, token?: string): Promise<Clip> {
    return this.request<Clip>(`/api/clips/${clipId}`, {}, token)
  }

  async updateClip(clipId: string, data: Partial<Clip>, token?: string): Promise<Clip> {
    return this.request<Clip>(`/api/clips/${clipId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }, token)
  }

  async deleteClip(clipId: string, token?: string): Promise<void> {
    return this.request<void>(`/api/clips/${clipId}`, {
      method: 'DELETE',
    }, token)
  }

  async downloadClip(clipId: string, token?: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/clips/${clipId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`)
    }

    return response.blob()
  }

  // Video upload and processing
  async uploadVideo(file: File, token?: string): Promise<{ upload_url: string; project_id: string }> {
    const formData = new FormData()
    formData.append('file', file)

    return this.request<{ upload_url: string; project_id: string }>('/api/upload/video', {
      method: 'POST',
      headers: {}, // Remove Content-Type to let browser set it for FormData
      body: formData,
    }, token)
  }

  async processVideoFromUrl(url: string, maxClips?: number, token?: string): Promise<Project> {
    const payload = {
      url,
      max_clips: maxClips || 5
    }
    console.log('processVideoFromUrl called with payload:', payload)
    console.log('API Base URL:', this.baseUrl)
    console.log('Full URL:', `${this.baseUrl}/api/projects`)

    const result = await this.request<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, token)

    console.log('processVideoFromUrl result:', result)
    return result
  }
}

export const apiClient = new ApiClient(API_BASE_URL)