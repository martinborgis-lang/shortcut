"use client";

import { Clock, Film, Zap, Calendar, TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";

interface UsageData {
  monthly_minutes_used: number;
  monthly_clips_generated: number;
  scheduled_posts_this_week: number;
  reset_date?: string;
}

interface PlanLimits {
  monthly_upload_minutes?: number;
  monthly_clips?: number;
  scheduling_enabled: boolean;
  max_scheduled_per_week?: number;
  watermark: boolean;
}

interface UsageMeterProps {
  usage: UsageData;
  limits: PlanLimits;
  plan: string;
}

export function UsageMeter({ usage, limits, plan }: UsageMeterProps) {
  const getUsagePercentage = (used: number, limit?: number) => {
    if (!limit || limit === 0) return 0;
    return Math.min((used / limit) * 100, 100);
  };

  const getUsageStatus = (percentage: number) => {
    if (percentage >= 90) return { color: "text-red-600", bg: "bg-red-100", label: "Critical" };
    if (percentage >= 75) return { color: "text-yellow-600", bg: "bg-yellow-100", label: "High" };
    if (percentage >= 50) return { color: "text-blue-600", bg: "bg-blue-100", label: "Moderate" };
    return { color: "text-green-600", bg: "bg-green-100", label: "Low" };
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatMinutes = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <TrendingUp className="w-5 h-5 mr-2" />
          Usage This Month
        </CardTitle>
        <CardDescription>
          {usage.reset_date && (
            <span className="flex items-center">
              <Calendar className="w-4 h-4 mr-1" />
              Resets on {formatDate(usage.reset_date)}
            </span>
          )}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Upload Minutes */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-2 text-blue-500" />
              <span className="text-sm font-medium">Upload Minutes</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {formatMinutes(usage.monthly_minutes_used)}
                {limits.monthly_upload_minutes
                  ? ` / ${formatMinutes(limits.monthly_upload_minutes)}`
                  : " / Unlimited"
                }
              </span>
              {limits.monthly_upload_minutes && (
                <Badge
                  variant="secondary"
                  className={`text-xs ${
                    getUsageStatus(
                      getUsagePercentage(usage.monthly_minutes_used, limits.monthly_upload_minutes)
                    ).bg
                  } ${
                    getUsageStatus(
                      getUsagePercentage(usage.monthly_minutes_used, limits.monthly_upload_minutes)
                    ).color
                  }`}
                >
                  {getUsageStatus(
                    getUsagePercentage(usage.monthly_minutes_used, limits.monthly_upload_minutes)
                  ).label}
                </Badge>
              )}
            </div>
          </div>

          {limits.monthly_upload_minutes ? (
            <Progress
              value={getUsagePercentage(usage.monthly_minutes_used, limits.monthly_upload_minutes)}
              className="h-2"
            />
          ) : (
            <div className="text-xs text-green-600 font-medium">✓ Unlimited</div>
          )}

          {limits.monthly_upload_minutes && (
            <div className="text-xs text-gray-500">
              {limits.monthly_upload_minutes - usage.monthly_minutes_used > 0
                ? `${formatMinutes(limits.monthly_upload_minutes - usage.monthly_minutes_used)} remaining`
                : "Limit reached"
              }
            </div>
          )}
        </div>

        {/* Clips Generated */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Film className="w-4 h-4 mr-2 text-purple-500" />
              <span className="text-sm font-medium">Clips Generated</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">
                {usage.monthly_clips_generated}
                {limits.monthly_clips
                  ? ` / ${limits.monthly_clips}`
                  : " / Unlimited"
                }
              </span>
              {limits.monthly_clips && (
                <Badge
                  variant="secondary"
                  className={`text-xs ${
                    getUsageStatus(
                      getUsagePercentage(usage.monthly_clips_generated, limits.monthly_clips)
                    ).bg
                  } ${
                    getUsageStatus(
                      getUsagePercentage(usage.monthly_clips_generated, limits.monthly_clips)
                    ).color
                  }`}
                >
                  {getUsageStatus(
                    getUsagePercentage(usage.monthly_clips_generated, limits.monthly_clips)
                  ).label}
                </Badge>
              )}
            </div>
          </div>

          {limits.monthly_clips ? (
            <Progress
              value={getUsagePercentage(usage.monthly_clips_generated, limits.monthly_clips)}
              className="h-2"
            />
          ) : (
            <div className="text-xs text-green-600 font-medium">✓ Unlimited</div>
          )}

          {limits.monthly_clips && (
            <div className="text-xs text-gray-500">
              {limits.monthly_clips - usage.monthly_clips_generated > 0
                ? `${limits.monthly_clips - usage.monthly_clips_generated} clips remaining`
                : "Limit reached"
              }
            </div>
          )}
        </div>

        {/* Scheduled Posts (if scheduling is enabled) */}
        {limits.scheduling_enabled && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Zap className="w-4 h-4 mr-2 text-green-500" />
                <span className="text-sm font-medium">Scheduled This Week</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">
                  {usage.scheduled_posts_this_week}
                  {limits.max_scheduled_per_week
                    ? ` / ${limits.max_scheduled_per_week}`
                    : " / Unlimited"
                  }
                </span>
                {limits.max_scheduled_per_week && (
                  <Badge
                    variant="secondary"
                    className={`text-xs ${
                      getUsageStatus(
                        getUsagePercentage(usage.scheduled_posts_this_week, limits.max_scheduled_per_week)
                      ).bg
                    } ${
                      getUsageStatus(
                        getUsagePercentage(usage.scheduled_posts_this_week, limits.max_scheduled_per_week)
                      ).color
                    }`}
                  >
                    {getUsageStatus(
                      getUsagePercentage(usage.scheduled_posts_this_week, limits.max_scheduled_per_week)
                    ).label}
                  </Badge>
                )}
              </div>
            </div>

            {limits.max_scheduled_per_week ? (
              <Progress
                value={getUsagePercentage(usage.scheduled_posts_this_week, limits.max_scheduled_per_week)}
                className="h-2"
              />
            ) : (
              <div className="text-xs text-green-600 font-medium">✓ Unlimited</div>
            )}

            {limits.max_scheduled_per_week && (
              <div className="text-xs text-gray-500">
                Resets every Monday
              </div>
            )}
          </div>
        )}

        {/* Plan Upgrade CTA */}
        {plan === "free" && (
          <div className="border-t pt-4">
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-1">Need more capacity?</h4>
              <p className="text-sm text-gray-600 mb-3">
                Upgrade your plan for higher limits and more features
              </p>
              <button
                onClick={() => window.location.href = "/pricing"}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                View upgrade options →
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}