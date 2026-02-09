"use client";

import { CreditCard, Calendar, AlertTriangle, CheckCircle, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface BillingOverviewProps {
  currentPlan: string;
  planStatus: string;
  nextPaymentDate?: string;
  gracePeriodEnd?: string;
  onManageSubscription: () => void;
  onUpgrade: () => void;
  isLoadingPortal?: boolean;
}

export function BillingOverview({
  currentPlan,
  planStatus,
  nextPaymentDate,
  gracePeriodEnd,
  onManageSubscription,
  onUpgrade,
  isLoadingPortal = false
}: BillingOverviewProps) {
  const getPlanDisplayName = (plan: string) => {
    return plan.charAt(0).toUpperCase() + plan.slice(1);
  };

  const getPlanPrice = (plan: string) => {
    const prices = {
      free: "€0",
      starter: "€9.99",
      pro: "€29.99",
      enterprise: "€79.99"
    };
    return prices[plan as keyof typeof prices] || "€0";
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      active: { color: "bg-green-500", text: "Active", icon: CheckCircle },
      past_due: { color: "bg-yellow-500", text: "Past Due", icon: AlertTriangle },
      canceled: { color: "bg-red-500", text: "Canceled", icon: AlertTriangle },
      trialing: { color: "bg-blue-500", text: "Trial", icon: CheckCircle }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || {
      color: "bg-gray-500",
      text: status,
      icon: CheckCircle
    };

    const IconComponent = config.icon;

    return (
      <Badge className={`${config.color} text-white`}>
        <IconComponent className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-6">
      {/* Grace Period Alert */}
      {gracePeriodEnd && (
        <Alert className="border-yellow-500 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            <strong>Payment Issue:</strong> Your account is in a grace period until{" "}
            {formatDate(gracePeriodEnd)}. Please update your payment method to avoid service interruption.
          </AlertDescription>
        </Alert>
      )}

      {/* Current Plan Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CreditCard className="w-5 h-5 mr-2" />
            Current Subscription
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-gray-900">
                {getPlanDisplayName(currentPlan)} Plan
              </h3>
              {currentPlan !== "free" && (
                <p className="text-gray-600">
                  {getPlanPrice(currentPlan)}/month
                </p>
              )}
            </div>
            <div className="text-right">
              {getStatusBadge(planStatus)}
            </div>
          </div>

          {nextPaymentDate && (
            <div className="flex items-center text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
              <Calendar className="w-4 h-4 mr-2" />
              <span>
                {planStatus === "canceled" ? "Subscription ends" : "Next billing date"}:{" "}
                {formatDate(nextPaymentDate)}
              </span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            {currentPlan !== "free" ? (
              <Button
                onClick={onManageSubscription}
                disabled={isLoadingPortal}
                className="flex-1"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                {isLoadingPortal ? "Loading..." : "Manage Subscription"}
              </Button>
            ) : (
              <Button onClick={onUpgrade} className="flex-1">
                <CreditCard className="w-4 h-4 mr-2" />
                Upgrade Plan
              </Button>
            )}

            {currentPlan === "free" && (
              <Button
                variant="outline"
                onClick={() => window.location.href = "/pricing"}
                className="flex-1"
              >
                View All Plans
              </Button>
            )}
          </div>

          {/* Plan Benefits Summary */}
          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-3">Plan Benefits</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
              {currentPlan === "free" && (
                <>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    30 min upload/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    5 clips/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    TikTok platform
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Basic styles
                  </div>
                </>
              )}
              {currentPlan === "starter" && (
                <>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    2 hours upload/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    30 clips/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    TikTok + YouTube
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Scheduling enabled
                  </div>
                </>
              )}
              {currentPlan === "pro" && (
                <>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    10 hours upload/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    150 clips/month
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    All platforms
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Unlimited scheduling
                  </div>
                </>
              )}
              {currentPlan === "enterprise" && (
                <>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Unlimited uploads
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Unlimited clips
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    All features
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-500" />
                    Priority support
                  </div>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}