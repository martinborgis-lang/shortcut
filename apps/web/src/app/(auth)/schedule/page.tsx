"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, Clock, TrendingUp, AlertCircle, Plus } from "lucide-react";
import { toast } from 'sonner';

export default function SchedulePage() {
  const [isNotificationRequested, setIsNotificationRequested] = useState(false);

  const handleSchedulePost = () => {
    toast.info('Schedule Post feature is coming soon! Your request has been noted.');
  };

  const handleGetNotified = () => {
    if (!isNotificationRequested) {
      setIsNotificationRequested(true);
      toast.success('You\'ll be notified when the scheduling feature is available!');
    } else {
      toast.info('You\'re already subscribed to notifications for this feature.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Schedule</h1>
          <p className="text-gray-400">Manage your content schedule</p>
        </div>
        <Button onClick={handleSchedulePost} className="bg-[#E94560] hover:bg-[#E94560]/90 text-white">
          <Plus className="w-4 h-4 mr-2" />
          Schedule Post
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-[#1A1A2E] border-[#2A2A3E]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Total Posts</p>
                <p className="text-2xl font-bold text-white">12</p>
              </div>
              <Calendar className="w-8 h-8 text-[#E94560]" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#1A1A2E] border-[#2A2A3E]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Scheduled</p>
                <p className="text-2xl font-bold text-blue-400">8</p>
              </div>
              <Clock className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#1A1A2E] border-[#2A2A3E]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Published</p>
                <p className="text-2xl font-bold text-green-400">24</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#1A1A2E] border-[#2A2A3E]">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">Failed</p>
                <p className="text-2xl font-bold text-red-400">1</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Card className="bg-[#1A1A2E] border-[#2A2A3E]">
        <CardHeader>
          <CardTitle className="text-white">Content Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Schedule Feature Coming Soon</h3>
            <p className="text-gray-400 mb-6">
              The scheduling calendar and advanced features are being finalized.
            </p>
            <Button onClick={handleGetNotified} className="bg-[#E94560] hover:bg-[#E94560]/90 text-white">
              <Plus className="w-4 h-4 mr-2" />
              {isNotificationRequested ? 'Notification Set!' : 'Get Notified When Available'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}