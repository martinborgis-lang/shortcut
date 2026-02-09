"use client";

import { Check, Star, Loader2, Crown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface PlanCardProps {
  plan: {
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
  };
  currentPlan?: string;
  onSelect: (planId: string) => void;
  isLoading?: boolean;
  compact?: boolean;
}

export function PlanCard({
  plan,
  currentPlan,
  onSelect,
  isLoading = false,
  compact = false
}: PlanCardProps) {
  const isCurrentPlan = currentPlan === plan.id;
  const isEnterprise = plan.id === "enterprise";

  return (
    <Card
      className={`relative transition-all duration-200 ${
        plan.popular && !isCurrentPlan
          ? "ring-2 ring-blue-500 shadow-lg scale-105"
          : isCurrentPlan
          ? "ring-2 ring-green-500 shadow-lg"
          : "hover:shadow-lg hover:scale-102"
      } ${compact ? "h-fit" : ""}`}
    >
      {/* Badges */}
      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 flex gap-2">
        {plan.popular && !isCurrentPlan && (
          <Badge className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1">
            <Star className="w-3 h-3 mr-1" />
            Popular
          </Badge>
        )}
        {isCurrentPlan && (
          <Badge className="bg-green-500 hover:bg-green-600 text-white px-3 py-1">
            Current Plan
          </Badge>
        )}
        {isEnterprise && (
          <Badge className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1">
            <Crown className="w-3 h-3 mr-1" />
            Enterprise
          </Badge>
        )}
      </div>

      <CardHeader className={`${compact ? "pb-3" : "pb-4"} pt-6`}>
        <CardTitle className={`${compact ? "text-lg" : "text-xl"} font-bold text-slate-900`}>
          {plan.name}
        </CardTitle>
        <CardDescription className="text-slate-600">
          {plan.description}
        </CardDescription>

        <div className="mt-4">
          <div className="flex items-baseline">
            <span className={`${compact ? "text-2xl" : "text-3xl"} font-bold text-slate-900`}>
              {plan.price}
            </span>
            <span className="text-slate-600 ml-1">/{plan.interval}</span>
          </div>
          {plan.priceAmount > 0 && (
            <p className="text-xs text-slate-500 mt-1">
              Billed monthly • Cancel anytime
            </p>
          )}
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Features */}
        <ul className={`space-y-${compact ? "2" : "3"} mb-6`}>
          {plan.features.map((feature, index) => (
            <li key={index} className="flex items-start">
              <Check className={`w-4 h-4 text-green-500 mt-0.5 mr-3 flex-shrink-0`} />
              <span className={`${compact ? "text-xs" : "text-sm"} text-slate-600`}>
                {feature}
              </span>
            </li>
          ))}
        </ul>

        {/* CTA Button */}
        <Button
          onClick={() => onSelect(plan.id)}
          disabled={plan.disabled || isLoading || isCurrentPlan}
          className={`w-full ${
            plan.popular && !isCurrentPlan
              ? "bg-blue-600 hover:bg-blue-700"
              : isCurrentPlan
              ? "bg-green-600 hover:bg-green-700"
              : isEnterprise
              ? "bg-purple-600 hover:bg-purple-700"
              : "bg-slate-900 hover:bg-slate-800"
          } ${compact ? "text-sm py-2" : ""}`}
          variant={plan.disabled || isCurrentPlan ? "outline" : "default"}
          size={compact ? "sm" : "default"}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : isCurrentPlan ? (
            "Current Plan"
          ) : plan.disabled ? (
            "Not Available"
          ) : (
            plan.ctaText
          )}
        </Button>

        {/* Additional Info */}
        {plan.id === "enterprise" && (
          <p className="text-xs text-slate-500 mt-3 text-center">
            Need custom features?{" "}
            <a
              href="mailto:sales@shortcut.ai"
              className="text-blue-600 hover:text-blue-700 underline"
            >
              Contact sales
            </a>
          </p>
        )}
      </CardContent>
    </Card>
  );
}