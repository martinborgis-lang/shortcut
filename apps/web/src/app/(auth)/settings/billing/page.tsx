"use client";

import { useState, useEffect } from "react";
import {
  CreditCard,
  Calendar,
  Download,
  ExternalLink,
  TrendingUp,
  Clock,
  Film,
  Zap,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
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

export default function BillingPage() {
  const [billingData, setBillingData] = useState<BillingData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingPortal, setIsLoadingPortal] = useState(false);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      const response = await fetch("/api/stripe/billing-info", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("authToken")}` // Adjust based on your auth setup
        }
      });

      if (!response.ok) {
        throw new Error("Failed to fetch billing data");
      }

      const data = await response.json();
      setBillingData(data);
    } catch (error) {
      console.error("Error fetching billing data:", error);
      toast.error("Failed to load billing information");
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setIsLoadingPortal(true);

    try {
      const response = await fetch("/api/stripe/create-portal", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("authToken")}`
        }
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to create portal session");
      }

      const { portal_url } = await response.json();
      window.location.href = portal_url;

    } catch (error) {
      console.error("Portal error:", error);
      toast.error(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setIsLoadingPortal(false);
    }
  };

  const formatPrice = (amountCents: number) => {
    return (amountCents / 100).toLocaleString('en-US', {
      style: 'currency',
      currency: 'EUR'
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getUsagePercentage = (used: number, limit?: number) => {
    if (!limit || limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getPlanDisplayName = (plan: string) => {
    return plan.charAt(0).toUpperCase() + plan.slice(1);
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { color: "bg-green-500", text: "Active" },
      past_due: { color: "bg-yellow-500", text: "Past Due" },
      canceled: { color: "bg-red-500", text: "Canceled" },
      trialing: { color: "bg-blue-500", text: "Trial" }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || {
      color: "bg-gray-500",
      text: status
    };

    return (
      <Badge className={`${config.color} text-white`}>
        {config.text}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-32 bg-gray-300 rounded"></div>
            <div className="h-32 bg-gray-300 rounded"></div>
            <div className="h-32 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!billingData) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load billing information. Please try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const { billing_info, invoices } = billingData;

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Billing & Subscription</h1>
        <p className="text-gray-600">
          Manage your subscription, view usage, and download invoices
        </p>
      </div>

      {/* Grace Period Alert */}
      {billing_info.grace_period_end && (
        <Alert className="mb-6 border-yellow-500 bg-yellow-50">
          <AlertCircle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            Your account is in a grace period until {formatDate(billing_info.grace_period_end)}.
            Please update your payment method to avoid service interruption.
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Current Plan */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="w-5 h-5 mr-2" />
              Current Plan
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold">{getPlanDisplayName(billing_info.plan)}</h3>
                {billing_info.plan !== "free" && (
                  <p className="text-gray-600">
                    {billing_info.plan === "starter" && "€9.99/month"}
                    {billing_info.plan === "pro" && "€29.99/month"}
                    {billing_info.plan === "enterprise" && "€79.99/month"}
                  </p>
                )}
              </div>
              {getStatusBadge(billing_info.status)}
            </div>

            {billing_info.next_payment_date && (
              <div className="flex items-center text-sm text-gray-600">
                <Calendar className="w-4 h-4 mr-2" />
                Next billing: {formatDate(billing_info.next_payment_date)}
              </div>
            )}

            <div className="flex gap-3">
              {billing_info.plan !== "free" ? (
                <Button
                  onClick={handleManageSubscription}
                  disabled={isLoadingPortal}
                  className="flex-1"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  {isLoadingPortal ? "Loading..." : "Manage Subscription"}
                </Button>
              ) : (
                <Button
                  onClick={() => window.location.href = "/pricing"}
                  className="flex-1"
                >
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Upgrade Plan
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Usage Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Usage This Month
            </CardTitle>
            <CardDescription>
              {billing_info.usage.reset_date &&
                `Resets on ${formatDate(billing_info.usage.reset_date)}`
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Upload Minutes */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-2 text-blue-500" />
                  <span className="text-sm font-medium">Upload Minutes</span>
                </div>
                <span className="text-sm text-gray-600">
                  {billing_info.usage.monthly_minutes_used}
                  {billing_info.limits.monthly_upload_minutes
                    ? ` / ${billing_info.limits.monthly_upload_minutes}`
                    : " / Unlimited"
                  }
                </span>
              </div>
              <Progress
                value={getUsagePercentage(
                  billing_info.usage.monthly_minutes_used,
                  billing_info.limits.monthly_upload_minutes
                )}
                className="h-2"
              />
            </div>

            {/* Clips Generated */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Film className="w-4 h-4 mr-2 text-purple-500" />
                  <span className="text-sm font-medium">Clips Generated</span>
                </div>
                <span className="text-sm text-gray-600">
                  {billing_info.usage.monthly_clips_generated}
                  {billing_info.limits.monthly_clips
                    ? ` / ${billing_info.limits.monthly_clips}`
                    : " / Unlimited"
                  }
                </span>
              </div>
              <Progress
                value={getUsagePercentage(
                  billing_info.usage.monthly_clips_generated,
                  billing_info.limits.monthly_clips
                )}
                className="h-2"
              />
            </div>

            {/* Scheduled Posts */}
            {billing_info.limits.scheduling_enabled && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    <Zap className="w-4 h-4 mr-2 text-green-500" />
                    <span className="text-sm font-medium">Posts This Week</span>
                  </div>
                  <span className="text-sm text-gray-600">
                    {billing_info.usage.scheduled_posts_this_week}
                    {billing_info.limits.max_scheduled_per_week
                      ? ` / ${billing_info.limits.max_scheduled_per_week}`
                      : " / Unlimited"
                    }
                  </span>
                </div>
                <Progress
                  value={getUsagePercentage(
                    billing_info.usage.scheduled_posts_this_week,
                    billing_info.limits.max_scheduled_per_week
                  )}
                  className="h-2"
                />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Plan Features */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Plan Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-3 text-green-500" />
              <span className="text-sm">
                {billing_info.limits.monthly_upload_minutes
                  ? `${billing_info.limits.monthly_upload_minutes} min/month upload`
                  : "Unlimited uploads"
                }
              </span>
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-3 text-green-500" />
              <span className="text-sm">
                {billing_info.limits.monthly_clips
                  ? `${billing_info.limits.monthly_clips} clips/month`
                  : "Unlimited clips"
                }
              </span>
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-3 text-green-500" />
              <span className="text-sm">
                {billing_info.limits.scheduling_enabled ? "Scheduling enabled" : "No scheduling"}
              </span>
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-4 h-4 mr-3 text-green-500" />
              <span className="text-sm">
                {billing_info.limits.watermark ? "Watermark included" : "No watermark"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Invoice History */}
      {invoices && invoices.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Invoice History</CardTitle>
            <CardDescription>
              Download your billing invoices and receipts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {invoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                      <CreditCard className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Invoice #{invoice.id.slice(-8)}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatDate(invoice.date)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium">{formatPrice(invoice.amount)}</p>
                      <Badge
                        variant={invoice.status === "paid" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {invoice.status}
                      </Badge>
                    </div>
                    {invoice.pdf_url && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(invoice.pdf_url, "_blank")}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}