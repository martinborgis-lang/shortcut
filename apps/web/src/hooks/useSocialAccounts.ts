/**
 * Hooks for social media accounts management
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

// Types
interface SocialAccount {
  id: string;
  user_id: string;
  platform: string;
  platform_user_id: string;
  username: string;
  display_name?: string;
  is_active: boolean;
  is_verified: boolean;
  last_sync?: string;
  account_metadata?: Record<string, any>;
  publishing_permissions?: Record<string, any>;
  error_count: number;
  last_error?: string;
  disabled_until?: string;
  default_hashtags?: string[];
  created_at: string;
  updated_at?: string;
  connected_at?: string;
}

interface ConnectedAccountsResponse {
  accounts: SocialAccount[];
  total: number;
}

interface SocialAccountUpdate {
  is_active?: boolean;
  default_hashtags?: string[];
  default_caption_template?: string;
}

interface TikTokAuthResponse {
  auth_url: string;
}

interface OAuthCallbackRequest {
  code: string;
  state: string;
}

interface SocialAccountStatus {
  platform: string;
  is_connected: boolean;
  is_active: boolean;
  has_publishing_permission: boolean;
  last_error?: string;
  token_expires_at?: string;
  needs_reconnection: boolean;
}

interface BulkAccountStatusResponse {
  accounts: SocialAccountStatus[];
  summary: Record<string, number>;
}

// API functions
const api = {
  getTikTokAuthUrl: async (): Promise<TikTokAuthResponse> => {
    const response = await fetch('/api/social/tiktok/auth');
    if (!response.ok) {
      throw new Error('Failed to get TikTok auth URL');
    }
    return response.json();
  },

  connectTikTokAccount: async (data: OAuthCallbackRequest): Promise<SocialAccount> => {
    const response = await fetch('/api/social/tiktok/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to connect TikTok account');
    }
    return response.json();
  },

  getConnectedAccounts: async (platform?: string, activeOnly?: boolean): Promise<ConnectedAccountsResponse> => {
    const params = new URLSearchParams();
    if (platform) params.set('platform', platform);
    if (activeOnly !== undefined) params.set('active_only', activeOnly.toString());

    const response = await fetch(`/api/social/accounts?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch connected accounts');
    }
    return response.json();
  },

  getSocialAccount: async (id: string): Promise<SocialAccount> => {
    const response = await fetch(`/api/social/accounts/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch social account');
    }
    return response.json();
  },

  updateSocialAccount: async (id: string, data: SocialAccountUpdate): Promise<SocialAccount> => {
    const response = await fetch(`/api/social/accounts/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update social account');
    }
    return response.json();
  },

  disconnectSocialAccount: async (id: string): Promise<{ message: string; disconnected_account: SocialAccount }> => {
    const response = await fetch(`/api/social/accounts/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to disconnect social account');
    }
    return response.json();
  },

  getAccountsStatus: async (): Promise<BulkAccountStatusResponse> => {
    const response = await fetch('/api/social/accounts/status/bulk');
    if (!response.ok) {
      throw new Error('Failed to fetch accounts status');
    }
    return response.json();
  },
};

// Hooks
export function useSocialAccounts(platform?: string, activeOnly: boolean = true) {
  return useQuery({
    queryKey: ['social-accounts', platform, activeOnly],
    queryFn: () => api.getConnectedAccounts(platform, activeOnly),
    staleTime: 30000, // 30 seconds
  });
}

export function useSocialAccount(id: string) {
  return useQuery({
    queryKey: ['social-account', id],
    queryFn: () => api.getSocialAccount(id),
    enabled: !!id,
  });
}

export function useTikTokAuth() {
  return useMutation({
    mutationFn: api.getTikTokAuthUrl,
    onSuccess: (data) => {
      // Open TikTok OAuth in a new window
      const popup = window.open(
        data.auth_url,
        'tiktok-oauth',
        'width=500,height=700,scrollbars=yes,resizable=yes'
      );

      // Listen for OAuth completion
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          // Refresh accounts data after potential connection
          setTimeout(() => {
            window.location.reload();
          }, 1000);
        }
      }, 1000);
    },
    onError: (error: Error) => {
      toast.error('Failed to start TikTok connection', {
        description: error.message,
      });
    },
  });
}

export function useConnectTikTok() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.connectTikTokAccount,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['social-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-status'] });
      toast.success('TikTok account connected successfully!', {
        description: `Connected @${data.username}`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to connect TikTok account', {
        description: error.message,
      });
    },
  });
}

export function useUpdateSocialAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SocialAccountUpdate }) =>
      api.updateSocialAccount(id, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['social-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['social-account', variables.id] });
      toast.success('Account settings updated successfully!');
    },
    onError: (error: Error) => {
      toast.error('Failed to update account settings', {
        description: error.message,
      });
    },
  });
}

export function useDisconnectSocialAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.disconnectSocialAccount,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['social-accounts'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-status'] });
      toast.success('Account disconnected successfully', {
        description: `Disconnected ${data.disconnected_account.platform} account`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to disconnect account', {
        description: error.message,
      });
    },
  });
}

export function useAccountsStatus() {
  return useQuery({
    queryKey: ['accounts-status'],
    queryFn: api.getAccountsStatus,
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // 5 minutes
  });
}

// Helper hooks
export function useTikTokAccounts() {
  return useSocialAccounts('tiktok', true);
}

export function useHasConnectedAccounts() {
  const { data: accounts } = useSocialAccounts();
  return {
    hasAccounts: (accounts?.total || 0) > 0,
    hasTikTok: accounts?.accounts.some(acc => acc.platform === 'tiktok' && acc.is_active) || false,
    totalAccounts: accounts?.total || 0,
  };
}