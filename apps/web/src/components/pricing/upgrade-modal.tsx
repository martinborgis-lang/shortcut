"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Check, X, TrendingUp, Loader2 } from "lucide-react";
import { PlanCard } from "./plan-card";

interface Plan {
  id: string;
  name: string;
  price: string;
  priceAmount: number;
  interval: string;
  description: string;
  popular: boolean;
  features: string[];
  ctaText: string;
  disabled?: boolean;
}

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan: string;
  onUpgrade: (planId: string) => Promise<void>;
  reason?: string;
  title?: string;
  description?: string;
}

const plans: Plan[] = [
  {
    id: "starter",
    name: "Starter",
    price: "€9.99",
    priceAmount: 999,
    interval: "month",
    description: "Great for content creators",
    popular: true,
    features: [
      "2 hours upload/month",
      "30 clips/month",
      "TikTok + YouTube",
      "5 subtitle styles",
      "Scheduling (5 posts/week)",
      "No watermark"
    ],
    ctaText: "Upgrade to Starter"
  },
  {
    id: "pro",
    name: "Pro",
    price: "€29.99",
    priceAmount: 2999,
    interval: "month",
    description: "For professional creators",
    popular: false,
    features: [
      "10 hours upload/month",
      "150 clips/month",
      "All platforms",
      "All subtitle styles",
      "Unlimited scheduling",
      "Priority support"
    ],
    ctaText: "Upgrade to Pro"
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "€79.99",
    priceAmount: 7999,
    interval: "month",
    description: "For teams and agencies",
    popular: false,
    features: [
      "Unlimited uploads",
      "Unlimited clips",
      "All platforms",
      "All features",
      "Dedicated support",
      "Custom integrations"
    ],
    ctaText: "Upgrade to Enterprise"
  }
];

export function UpgradeModal({
  isOpen,
  onClose,
  currentPlan,
  onUpgrade,
  reason = "Upgrade your plan to access this feature",
  title = "Upgrade Required",
  description = "Choose a plan that fits your needs"
}: UpgradeModalProps) {
  const [isLoading, setIsLoading] = useState<string | null>(null);

  const handleUpgrade = async (planId: string) => {
    setIsLoading(planId);
    try {
      await onUpgrade(planId);
      onClose();
    } catch (error) {
      // Error handling is done in the parent component
    } finally {
      setIsLoading(null);
    }
  };

  // Filter out plans that are downgrades
  const availablePlans = plans.filter(plan => {
    const planHierarchy = { free: 0, starter: 1, pro: 2, enterprise: 3 };
    const currentLevel = planHierarchy[currentPlan as keyof typeof planHierarchy] || 0;
    const planLevel = planHierarchy[plan.id as keyof typeof planHierarchy];
    return planLevel > currentLevel;
  });

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <TrendingUp className="w-6 h-6 mr-3 text-blue-600" />
              <div>
                <DialogTitle className="text-2xl font-bold">{title}</DialogTitle>
                <DialogDescription className="mt-1">
                  {description}
                </DialogDescription>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>

        {/* Reason for upgrade */}
        {reason && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-blue-800 text-sm">
              <strong>Why upgrade?</strong> {reason}
            </p>
          </div>
        )}

        {/* Current Plan Info */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h3 className="font-medium text-gray-900 mb-2">Your Current Plan</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">
                You're currently on the{" "}
                <span className="font-medium capitalize">{currentPlan}</span> plan
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.href = "/settings/billing"}
            >
              View Details
            </Button>
          </div>
        </div>

        {/* Available Plans */}
        {availablePlans.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {availablePlans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={{
                  ...plan,
                  ctaText: isLoading === plan.id ? "Processing..." : plan.ctaText
                }}
                currentPlan={currentPlan}
                onSelect={handleUpgrade}
                isLoading={isLoading === plan.id}
                compact
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Check className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              You're on the highest plan!
            </h3>
            <p className="text-gray-600 mb-4">
              You already have access to all features. If you need custom features,
              contact our sales team.
            </p>
            <Button
              onClick={() => window.open("mailto:sales@shortcut.ai", "_blank")}
              variant="outline"
            >
              Contact Sales
            </Button>
          </div>
        )}

        {/* Footer */}
        <div className="border-t pt-6 mt-6">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center">
              <Check className="w-4 h-4 mr-2 text-green-500" />
              <span>Cancel anytime • No long-term commitment</span>
            </div>
            <div className="flex items-center">
              <Check className="w-4 h-4 mr-2 text-green-500" />
              <span>Secure payments with Stripe</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}