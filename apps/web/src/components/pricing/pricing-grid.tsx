"use client";

import { Check, Star, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PlanFeature {
  text: string;
  included: boolean;
}

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

interface PricingGridProps {
  plans: Plan[];
  currentPlan?: string;
  onUpgrade: (planId: string) => Promise<void>;
  isLoading?: string | null;
}

export function PricingGrid({
  plans,
  currentPlan,
  onUpgrade,
  isLoading
}: PricingGridProps) {
  const getPlanCtaText = (plan: Plan) => {
    if (plan.id === "free") {
      return currentPlan === "free" ? "Current Plan" : "Downgrade";
    }
    if (currentPlan === plan.id) {
      return "Current Plan";
    }
    return plan.ctaText;
  };

  const isPlanDisabled = (plan: Plan) => {
    if (plan.disabled) return true;
    if (currentPlan === plan.id) return true;
    // Disable downgrade options (except free)
    if (plan.id !== "free" && currentPlan) {
      const planHierarchy = { free: 0, starter: 1, pro: 2, enterprise: 3 };
      const currentLevel = planHierarchy[currentPlan as keyof typeof planHierarchy];
      const targetLevel = planHierarchy[plan.id as keyof typeof planHierarchy];
      return targetLevel < currentLevel;
    }
    return false;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
      {plans.map((plan) => (
        <PlanCard
          key={plan.id}
          plan={plan}
          currentPlan={currentPlan}
          onUpgrade={onUpgrade}
          isLoading={isLoading}
          ctaText={getPlanCtaText(plan)}
          disabled={isPlanDisabled(plan)}
        />
      ))}
    </div>
  );
}

interface PlanCardProps {
  plan: Plan;
  currentPlan?: string;
  onUpgrade: (planId: string) => Promise<void>;
  isLoading?: string | null;
  ctaText: string;
  disabled: boolean;
}

function PlanCard({
  plan,
  currentPlan,
  onUpgrade,
  isLoading,
  ctaText,
  disabled
}: PlanCardProps) {
  return (
    <Card
      className={`relative transition-all duration-200 ${
        plan.popular
          ? "ring-2 ring-blue-500 shadow-lg scale-105"
          : "hover:shadow-lg hover:scale-102"
      } ${currentPlan === plan.id ? "ring-2 ring-green-500" : ""}`}
    >
      {plan.popular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <Badge className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-1">
            <Star className="w-3 h-3 mr-1" />
            Most Popular
          </Badge>
        </div>
      )}

      {currentPlan === plan.id && (
        <div className="absolute -top-4 right-4">
          <Badge className="bg-green-500 hover:bg-green-600 text-white px-3 py-1">
            Current
          </Badge>
        </div>
      )}

      <CardHeader className="pb-4">
        <CardTitle className="text-xl font-bold text-slate-900">
          {plan.name}
        </CardTitle>
        <CardDescription className="text-slate-600">
          {plan.description}
        </CardDescription>
        <div className="mt-4">
          <span className="text-3xl font-bold text-slate-900">
            {plan.price}
          </span>
          <span className="text-slate-600">/{plan.interval}</span>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Features */}
        <ul className="space-y-3 mb-6">
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <Check className="w-4 h-4 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
              <span className="text-sm text-slate-600">{feature}</span>
            </li>
          ))}
        </ul>

        {/* CTA Button */}
        <Button
          onClick={() => onUpgrade(plan.id)}
          disabled={disabled || isLoading !== null}
          className={`w-full ${
            plan.popular
              ? "bg-blue-600 hover:bg-blue-700"
              : currentPlan === plan.id
              ? "bg-green-600 hover:bg-green-700"
              : "bg-slate-900 hover:bg-slate-800"
          }`}
          variant={disabled ? "outline" : "default"}
        >
          {isLoading === plan.id ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            ctaText
          )}
        </Button>
      </CardContent>
    </Card>
  );
}