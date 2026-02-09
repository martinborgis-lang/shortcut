"use client";

import { useState, useEffect } from "react";
import { toast } from "sonner";

interface BillingData {
  billing_info: {
    plan: string;
    status: string;
    next_payment_date?: string;
    grace_period_end?: string;
    limits: {
      monthly_upload_minutes?: number;
      monthly_clips?: number;
      scheduling_enabled: boolean;
      max_scheduled_per_week?: number;
      watermark: boolean;
    };
    usage: {
      monthly_minutes_used: number;
      monthly_clips_generated: number;
      scheduled_posts_this_week: number;
      reset_date?: string;
    };
  };
  invoices: Array<{
    id: string;
    date: string;
    amount: number;
    status: string;
    pdf_url?: string;
  }>;
}

interface UseBillingReturn {
  data: BillingData | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  createCheckout: (planId: string, successUrl?: string, cancelUrl?: string) => Promise<string>;
  createPortal: () => Promise<string>;
  isCreatingCheckout: boolean;
  isCreatingPortal: boolean;
}

export function useBilling(): UseBillingReturn {
  const [data, setData] = useState<BillingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreatingCheckout, setIsCreatingCheckout] = useState(false);
  const [isCreatingPortal, setIsCreatingPortal] = useState(false);

  const getAuthToken = () => {
    // Adjust this based on your auth setup
    return localStorage.getItem("authToken") || sessionStorage.getItem("authToken");
  };

  const fetchBillingData = async () => {
    try {
      setError(null);
      const token = getAuthToken();

      const response = await fetch("/api/stripe/billing-info", {
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
        throw new Error(errorData.detail || "Failed to fetch billing data");
      }

      const billingData = await response.json();
      setData(billingData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load billing information";
      setError(errorMessage);
      console.error("Billing fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const createCheckout = async (
    planId: string,
    successUrl?: string,
    cancelUrl?: string
  ): Promise<string> => {
    setIsCreatingCheckout(true);
    try {
      const token = getAuthToken();

      const response = await fetch("/api/stripe/create-checkout", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          plan: planId,
          success_url: successUrl || `${window.location.origin}/settings/billing?success=true`,
          cancel_url: cancelUrl || `${window.location.origin}/pricing`
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || errorData.detail || "Failed to create checkout session");
      }

      const { checkout_url } = await response.json();
      return checkout_url;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create checkout session";
      toast.error(errorMessage);
      throw err;
    } finally {
      setIsCreatingCheckout(false);
    }
  };

  const createPortal = async (): Promise<string> => {
    setIsCreatingPortal(true);
    try {
      const token = getAuthToken();

      const response = await fetch("/api/stripe/create-portal", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create portal session");
      }

      const { portal_url } = await response.json();
      return portal_url;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to create portal session";
      toast.error(errorMessage);
      throw err;
    } finally {
      setIsCreatingPortal(false);
    }
  };

  const refetch = async () => {
    setIsLoading(true);
    await fetchBillingData();
  };

  useEffect(() => {
    fetchBillingData();
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch,
    createCheckout,
    createPortal,
    isCreatingCheckout,
    isCreatingPortal
  };
}

// Hook for upgrading to a specific plan
export function useUpgrade() {
  const { createCheckout } = useBilling();

  const upgrade = async (planId: string) => {
    try {
      const checkoutUrl = await createCheckout(planId);
      window.location.href = checkoutUrl;
    } catch (error) {
      // Error is already handled in createCheckout
      throw error;
    }
  };

  return { upgrade };
}

// Hook for managing subscription
export function useManageSubscription() {
  const { createPortal } = useBilling();

  const manage = async () => {
    try {
      const portalUrl = await createPortal();
      window.location.href = portalUrl;
    } catch (error) {
      // Error is already handled in createPortal
      throw error;
    }
  };

  return { manage };
}