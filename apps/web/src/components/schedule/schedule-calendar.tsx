/**
 * F6-12: Schedule Calendar Component
 * Calendar view showing scheduled posts
 */

"use client";

import { useState } from "react";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Clock, TrendingUp, AlertCircle } from "lucide-react";

interface ScheduledPost {
  id: string;
  scheduled_time: string;
  status: string;
  caption?: string;
  platform?: string;
}

interface ScheduleCalendarProps {
  posts: ScheduledPost[];
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
  onPostClick: (post: ScheduledPost) => void;
}

export function ScheduleCalendar({ posts, selectedDate, onDateSelect, onPostClick }: ScheduleCalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  // Group posts by date
  const postsByDate = posts.reduce((acc, post) => {
    const date = new Date(post.scheduled_time).toDateString();
    if (!acc[date]) {
      acc[date] = [];
    }
    acc[date].push(post);
    return acc;
  }, {} as Record<string, ScheduledPost[]>);

  // Get posts for selected date
  const selectedDatePosts = postsByDate[selectedDate.toDateString()] || [];

  // Check if date has posts
  const hasPostsOnDate = (date: Date) => {
    return Boolean(postsByDate[date.toDateString()]?.length);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "scheduled": return "bg-blue-500";
      case "publishing": return "bg-yellow-500";
      case "published": return "bg-green-500";
      case "failed": return "bg-red-500";
      default: return "bg-gray-500";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "scheduled": return <Clock className="w-3 h-3" />;
      case "publishing": return <div className="w-3 h-3 animate-spin border border-white border-t-transparent rounded-full" />;
      case "published": return <TrendingUp className="w-3 h-3" />;
      case "failed": return <AlertCircle className="w-3 h-3" />;
      default: return <Clock className="w-3 h-3" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Calendar */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <CardTitle>Calendar</CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-sm font-medium min-w-[120px] text-center">
              {currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={(date) => date && onDateSelect(date)}
            month={currentMonth}
            onMonthChange={setCurrentMonth}
            modifiers={{
              hasPosts: hasPostsOnDate,
            }}
            modifiersStyles={{
              hasPosts: {
                backgroundColor: 'rgb(59 130 246 / 0.1)',
                border: '2px solid rgb(59 130 246)',
                borderRadius: '6px',
              },
            }}
            className="rounded-md border-0"
          />

          {/* Legend */}
          <div className="mt-4 pt-4 border-t">
            <p className="text-sm font-medium mb-2">Legend</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <span>Scheduled</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span>Publishing</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span>Published</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Failed</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Selected Date Posts */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedDate.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </CardTitle>
          {selectedDatePosts.length > 0 && (
            <p className="text-sm text-gray-600">
              {selectedDatePosts.length} post{selectedDatePosts.length > 1 ? 's' : ''} scheduled
            </p>
          )}
        </CardHeader>
        <CardContent>
          {selectedDatePosts.length === 0 ? (
            <div className="text-center py-8">
              <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-sm">No posts scheduled for this date</p>
            </div>
          ) : (
            <div className="space-y-3">
              {selectedDatePosts
                .sort((a, b) => new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime())
                .map((post) => (
                  <div
                    key={post.id}
                    className="p-3 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => onPostClick(post)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${getStatusColor(post.status)}`}></div>
                        <span className="text-sm font-medium">
                          {new Date(post.scheduled_time).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit',
                            hour12: true,
                          })}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={post.status === 'published' ? 'default' :
                                  post.status === 'failed' ? 'destructive' : 'secondary'}
                          className="text-xs flex items-center gap-1"
                        >
                          {getStatusIcon(post.status)}
                          {post.status}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {post.caption || "No caption"}
                    </p>

                    <div className="flex items-center gap-2">
                      <div className="w-5 h-5 bg-black rounded-full flex items-center justify-center text-white text-xs font-bold">
                        T
                      </div>
                      <span className="text-xs text-gray-500">TikTok</span>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}