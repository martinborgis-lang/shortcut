"use client";

import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";

interface QuotaData {
  plan: string;
  limits: {
    monthly_upload_minutes?: number;
    monthly_clips?: number;
    scheduling_enabled: boolean;
    max_scheduled_per_week?: number;
    watermark: boolean;
  };
  usage: {
    upload_minutes: {
      used: number;
      remaining: number | null;
      limit: number | null;
      reset_date?: string;
    };
    clips: {
      generated: number;
      remaining: number | null;
      limit: number | null;
      reset_date?: string;
    };
    scheduling: {
      enabled: boolean;
      remaining: number | null;
      limit: number | null;
      reset_date?: string;
    };
  };
}

interface UseQuotaReturn {
  data: QuotaData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  checkUploadQuota: (minutes: number) => boolean;
  checkClipQuota: (count?: number) => boolean;
  checkSchedulingQuota: () => boolean;
  checkPlatformAccess: (platform: string) => boolean;
  checkSubtitleStyleAccess: (style: string) => boolean;
  shouldApplyWatermark: () => boolean;
  getUsagePercentage: (type: "upload" | "clips" | "scheduling") => number;
}

export function useQuota(): UseQuotaReturn {
  const [data, setData] = useState<QuotaData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getAuthToken = () => {
    return localStorage.getItem("authToken") || sessionStorage.getItem("authToken");
  };

  const fetchQuotaData = async () => {
    try {
      setError(null);
      const token = getAuthToken();

      const response = await fetch("/api/stripe/quota-status", {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication required. Please log in again.");
        }
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to fetch quota data");
      }

      const quotaData = await response.json();
      setData(quotaData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load quota information";
      setError(errorMessage);
      console.error("Quota fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const refetch = async () => {
    setIsLoading(true);
    await fetchQuotaData();
  };

  const checkUploadQuota = useCallback((minutes: number): boolean => {
    if (!data) return false;

    const { upload_minutes } = data.usage;

    // Unlimited plan
    if (upload_minutes.limit === null) return true;

    // Check if there's enough quota remaining
    if (upload_minutes.remaining === null) return false;

    return upload_minutes.remaining >= minutes;
  }, [data]);

  const checkClipQuota = useCallback((count: number = 1): boolean => {
    if (!data) return false;

    const { clips } = data.usage;

    // Unlimited plan
    if (clips.limit === null) return true;

    // Check if there's enough quota remaining
    if (clips.remaining === null) return false;

    return clips.remaining >= count;
  }, [data]);

  const checkSchedulingQuota = useCallback((): boolean => {
    if (!data) return false;

    const { scheduling } = data.usage;

    // Scheduling not enabled for plan
    if (!scheduling.enabled) return false;

    // Unlimited scheduling
    if (scheduling.limit === null) return true;

    // Check if there's quota remaining
    if (scheduling.remaining === null) return false;

    return scheduling.remaining > 0;
  }, [data]);

  const checkPlatformAccess = useCallback((platform: string): boolean => {
    if (!data) return false;

    const platformMap = {
      free: ["tiktok"],
      starter: ["tiktok", "youtube"],
      pro: ["tiktok", "youtube", "instagram"],
      enterprise: ["tiktok", "youtube", "instagram"]
    };

    const availablePlatforms = platformMap[data.plan as keyof typeof platformMap] || [];
    return availablePlatforms.includes(platform.toLowerCase());
  }, [data]);

  const checkSubtitleStyleAccess = useCallback((style: string): boolean => {
    if (!data) return false;

    const styleMap = {
      free: ["clean", "minimal"],
      starter: ["clean", "minimal", "hormozi", "neon", "karaoke"],
      pro: "all",
      enterprise: "all"
    };

    const availableStyles = styleMap[data.plan as keyof typeof styleMap];

    if (availableStyles === "all") return true;
    if (Array.isArray(availableStyles)) {
      return availableStyles.includes(style.toLowerCase());
    }

    return false;
  }, [data]);

  const shouldApplyWatermark = useCallback((): boolean => {
    if (!data) return true; // Default to watermark if no data

    return data.limits.watermark;
  }, [data]);

  const getUsagePercentage = useCallback((type: "upload" | "clips" | "scheduling"): number => {
    if (!data) return 0;

    const usage = data.usage[type === "upload" ? "upload_minutes" : type];

    if (!usage.limit || usage.limit === 0) return 0;

    const used = type === "upload"
      ? usage.used
      : type === "clips"
        ? usage.generated
        : (usage.limit - (usage.remaining || 0));

    return Math.min((used / usage.limit) * 100, 100);
  }, [data]);

  useEffect(() => {
    fetchQuotaData();
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch,
    checkUploadQuota,
    checkClipQuota,
    checkSchedulingQuota,
    checkPlatformAccess,
    checkSubtitleStyleAccess,
    shouldApplyWatermark,
    getUsagePercentage
  };
}

// Hook for quota checks with user feedback
export function useQuotaCheck() {
  const { checkUploadQuota, checkClipQuota, checkSchedulingQuota } = useQuota();

  const checkWithFeedback = useCallback((
    type: "upload" | "clips" | "scheduling",
    amount?: number
  ): boolean => {
    let canProceed = false;
    let message = "";

    switch (type) {
      case "upload":
        canProceed = checkUploadQuota(amount || 1);
        message = canProceed ? "" : "Upload quota exceeded. Please upgrade your plan or wait for next month's reset.";
        break;

      case "clips":
        canProceed = checkClipQuota(amount || 1);
        message = canProceed ? "" : "Clip generation quota exceeded. Please upgrade your plan or wait for next month's reset.";
        break;

      case "scheduling":
        canProceed = checkSchedulingQuota();
        message = canProceed ? "" : "Scheduling quota exceeded. Please upgrade your plan or wait for next week's reset.";
        break;
    }

    if (!canProceed && message) {
      toast.error(message, {
        action: {
          label: "Upgrade",
          onClick: () => window.location.href = "/pricing"
        }
      });
    }

    return canProceed;
  }, [checkUploadQuota, checkClipQuota, checkSchedulingQuota]);

  return { checkWithFeedback };
}

// Hook for plan-based feature access
export function usePlanAccess() {
  const quota = useQuota();

  const hasFeature = useCallback((feature: string): boolean => {
    if (!quota.data) return false;

    const plan = quota.data.plan;

    // Feature access map
    const featureAccess = {
      scheduling: quota.data.limits.scheduling_enabled,
      unlimited_uploads: quota.data.limits.monthly_upload_minutes === undefined,
      unlimited_clips: quota.data.limits.monthly_clips === undefined,
      no_watermark: !quota.data.limits.watermark,
      youtube: quota.checkPlatformAccess("youtube"),
      instagram: quota.checkPlatformAccess("instagram"),
      all_styles: plan === "pro" || plan === "enterprise",
      priority_support: plan === "pro" || plan === "enterprise"
    };

    return featureAccess[feature as keyof typeof featureAccess] || false;
  }, [quota]);

  const requiresUpgrade = useCallback((feature: string): boolean => {
    return !hasFeature(feature);
  }, [hasFeature]);

  return {
    ...quota,
    hasFeature,
    requiresUpgrade
  };
}