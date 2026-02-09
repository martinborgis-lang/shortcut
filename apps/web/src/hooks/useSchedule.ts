/**
 * Hooks for scheduled posts management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

// Types
interface ScheduledPost {
  id: string;
  clip_id: string;
  social_account_id: string;
  scheduled_time: string;
  time_zone: string;
  caption?: string;
  hashtags?: string[];
  mentions?: string[];
  platform_settings?: Record<string, any>;
  status: 'scheduled' | 'publishing' | 'published' | 'failed' | 'cancelled';
  posted_at?: string;
  failed_at?: string;
  error_message?: string;
  platform_post_id?: string;
  platform_response?: Record<string, any>;
  views?: number;
  likes?: number;
  shares?: number;
  comments?: number;
  engagement_rate?: number;
  retry_count: number;
  max_retries: number;
  next_retry_at?: string;
  created_at: string;
  updated_at?: string;
}

interface ScheduledPostsResponse {
  posts: ScheduledPost[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

interface CreateScheduledPostRequest {
  clip_id: string;
  social_account_id: string;
  scheduled_time: string;
  time_zone?: string;
  caption?: string;
  hashtags?: string[];
  mentions?: string[];
  platform_settings?: Record<string, any>;
}

interface UpdateScheduledPostRequest {
  scheduled_time?: string;
  caption?: string;
  hashtags?: string[];
  mentions?: string[];
  platform_settings?: Record<string, any>;
}

interface ScheduledPostStats {
  total_scheduled: number;
  total_published: number;
  total_failed: number;
  total_cancelled: number;
  success_rate: number;
  avg_engagement_rate?: number;
}

// API functions
const api = {
  getScheduledPosts: async (params?: {
    page?: number;
    per_page?: number;
    status?: string;
    platform?: string;
    clip_id?: string;
    social_account_id?: string;
    scheduled_after?: string;
    scheduled_before?: string;
  }): Promise<ScheduledPostsResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.set(key, value.toString());
        }
      });
    }

    const response = await fetch(`/api/schedule?${searchParams}`);
    if (!response.ok) {
      throw new Error('Failed to fetch scheduled posts');
    }
    return response.json();
  },

  getScheduledPost: async (id: string): Promise<ScheduledPost> => {
    const response = await fetch(`/api/schedule/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch scheduled post');
    }
    return response.json();
  },

  createScheduledPost: async (data: CreateScheduledPostRequest): Promise<ScheduledPost> => {
    const response = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create scheduled post');
    }
    return response.json();
  },

  updateScheduledPost: async (id: string, data: UpdateScheduledPostRequest): Promise<ScheduledPost> => {
    const response = await fetch(`/api/schedule/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update scheduled post');
    }
    return response.json();
  },

  cancelScheduledPost: async (id: string, reason?: string): Promise<{ message: string; cancelled_post: ScheduledPost }> => {
    const response = await fetch(`/api/schedule/${id}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to cancel scheduled post');
    }
    return response.json();
  },

  getScheduleStats: async (days?: number): Promise<ScheduledPostStats> => {
    const params = days ? `?days=${days}` : '';
    const response = await fetch(`/api/schedule/stats/summary${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch schedule stats');
    }
    return response.json();
  },
};

// Hooks
export function useScheduledPosts(params?: {
  page?: number;
  per_page?: number;
  status?: string;
  platform?: string;
  clip_id?: string;
  social_account_id?: string;
  scheduled_after?: string;
  scheduled_before?: string;
}) {
  return useQuery({
    queryKey: ['scheduled-posts', params],
    queryFn: () => api.getScheduledPosts(params),
    staleTime: 30000, // 30 seconds
  });
}

export function useScheduledPost(id: string) {
  return useQuery({
    queryKey: ['scheduled-post', id],
    queryFn: () => api.getScheduledPost(id),
    enabled: !!id,
  });
}

export function useCreateScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.createScheduledPost,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-posts'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
      toast.success('Post scheduled successfully!', {
        description: `Your post will be published on ${new Date(data.scheduled_time).toLocaleDateString()}`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to schedule post', {
        description: error.message,
      });
    },
  });
}

export function useUpdateScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateScheduledPostRequest }) =>
      api.updateScheduledPost(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-posts'] });
      queryClient.invalidateQueries({ queryKey: ['scheduled-post', variables.id] });
      toast.success('Post updated successfully!');
    },
    onError: (error: Error) => {
      toast.error('Failed to update post', {
        description: error.message,
      });
    },
  });
}

export function useCancelScheduledPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      api.cancelScheduledPost(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scheduled-posts'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
      toast.success('Post cancelled successfully');
    },
    onError: (error: Error) => {
      toast.error('Failed to cancel post', {
        description: error.message,
      });
    },
  });
}

export function useScheduleStats(days?: number) {
  return useQuery({
    queryKey: ['schedule-stats', days],
    queryFn: () => api.getScheduleStats(days),
    staleTime: 60000, // 1 minute
  });
}

// Real-time updates hook
export function useScheduleRealtime() {
  const queryClient = useQueryClient();

  // In a real implementation, you would connect to WebSocket here
  // For now, we'll just poll every 30 seconds for scheduled posts
  return useQuery({
    queryKey: ['schedule-realtime'],
    queryFn: () => {
      // Refresh scheduled posts data
      queryClient.invalidateQueries({ queryKey: ['scheduled-posts'] });
      queryClient.invalidateQueries({ queryKey: ['schedule-stats'] });
      return null;
    },
    refetchInterval: 30000, // 30 seconds
    enabled: false, // Only enable when there are active scheduled posts
  });
}