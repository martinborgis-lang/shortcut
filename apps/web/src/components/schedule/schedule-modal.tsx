/**
 * F6-13: Schedule Modal
 * Modal de scheduling : Sélection du clip, plateforme, date/heure, caption, hashtags
 */

"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Calendar, Clock, Hash, Video, Send, X } from "lucide-react";
import { useClips } from "@/hooks/useClips";
import { useSocialAccounts } from "@/hooks/useSocialAccounts";
import { useCreateScheduledPost } from "@/hooks/useSchedule";

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultDate?: Date;
  clipId?: string;
}

export function ScheduleModal({ isOpen, onClose, defaultDate, clipId }: ScheduleModalProps) {
  const [selectedClip, setSelectedClip] = useState<string>(clipId || "");
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [scheduledDate, setScheduledDate] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [hashtagInput, setHashtagInput] = useState("");
  const [privacy, setPrivacy] = useState("PUBLIC_TO_EVERYONE");

  const { data: clips } = useClips();
  const { data: socialAccounts } = useSocialAccounts();
  const createPost = useCreateScheduledPost();

  // Set default date and time
  useEffect(() => {
    if (defaultDate) {
      setScheduledDate(defaultDate.toISOString().split('T')[0]);
      const now = new Date();
      now.setHours(now.getHours() + 1, 0, 0, 0);
      setScheduledTime(now.toTimeString().slice(0, 5));
    }
  }, [defaultDate]);

  const handleAddHashtag = () => {
    if (hashtagInput.trim() && !hashtags.includes(hashtagInput.trim())) {
      setHashtags([...hashtags, hashtagInput.trim().replace('#', '')]);
      setHashtagInput("");
    }
  };

  const handleRemoveHashtag = (tag: string) => {
    setHashtags(hashtags.filter(h => h !== tag));
  };

  const handleSubmit = async () => {
    if (!selectedClip || !selectedAccount || !scheduledDate || !scheduledTime) {
      return;
    }

    const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);

    try {
      await createPost.mutateAsync({
        clip_id: selectedClip,
        social_account_id: selectedAccount,
        scheduled_time: scheduledDateTime.toISOString(),
        caption,
        hashtags,
        platform_settings: {
          privacy_level: privacy,
          disable_duet: false,
          disable_comment: false,
          disable_stitch: false,
        },
      });

      // Reset form
      setSelectedClip("");
      setSelectedAccount("");
      setScheduledDate("");
      setScheduledTime("");
      setCaption("");
      setHashtags([]);
      setHashtagInput("");
      setPrivacy("PUBLIC_TO_EVERYONE");

      onClose();
    } catch (error) {
      console.error("Failed to schedule post:", error);
    }
  };

  const selectedClipData = clips?.clips.find(c => c.id === selectedClip);
  const tiktokAccounts = socialAccounts?.accounts.filter(a => a.platform === "tiktok" && a.is_active) || [];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Schedule Post
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Clip Selection */}
          <div className="space-y-3">
            <Label htmlFor="clip">Select Clip</Label>
            <Select value={selectedClip} onValueChange={setSelectedClip}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a clip to schedule" />
              </SelectTrigger>
              <SelectContent>
                {clips?.clips.map((clip) => (
                  <SelectItem key={clip.id} value={clip.id}>
                    <div className="flex items-center gap-3">
                      <Video className="w-4 h-4" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{clip.title || "Untitled Clip"}</p>
                        <p className="text-xs text-gray-500">{clip.duration}s</p>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Clip Preview */}
            {selectedClipData && (
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                      <Video className="w-8 h-8 text-gray-500" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{selectedClipData.title || "Untitled"}</h4>
                      <p className="text-sm text-gray-600">{selectedClipData.description || "No description"}</p>
                      <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                        <span>{selectedClipData.duration}s</span>
                        <span>{selectedClipData.status}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Platform Selection */}
          <div className="space-y-3">
            <Label htmlFor="platform">Platform</Label>
            <Select value={selectedAccount} onValueChange={setSelectedAccount}>
              <SelectTrigger>
                <SelectValue placeholder="Choose platform account" />
              </SelectTrigger>
              <SelectContent>
                {tiktokAccounts.map((account) => (
                  <SelectItem key={account.id} value={account.id}>
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 bg-black rounded-full flex items-center justify-center text-white text-xs font-bold">
                        T
                      </div>
                      <div>
                        <p className="font-medium">{account.username}</p>
                        <p className="text-xs text-gray-500">{account.platform.toUpperCase()}</p>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {tiktokAccounts.length === 0 && (
              <p className="text-sm text-gray-500">
                No connected accounts. <a href="/settings" className="text-blue-600 hover:underline">Connect a TikTok account</a>
              </p>
            )}
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-3">
              <Label htmlFor="date">Scheduled Date</Label>
              <Input
                type="date"
                value={scheduledDate}
                onChange={(e) => setScheduledDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div className="space-y-3">
              <Label htmlFor="time">Scheduled Time</Label>
              <Input
                type="time"
                value={scheduledTime}
                onChange={(e) => setScheduledTime(e.target.value)}
              />
            </div>
          </div>

          {/* Caption */}
          <div className="space-y-3">
            <Label htmlFor="caption">Caption</Label>
            <Textarea
              placeholder="Write your caption here..."
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              maxLength={2200}
              rows={4}
            />
            <p className="text-xs text-gray-500 text-right">
              {caption.length}/2200 characters
            </p>
          </div>

          {/* Hashtags */}
          <div className="space-y-3">
            <Label htmlFor="hashtags">Hashtags</Label>
            <div className="flex gap-2">
              <Input
                placeholder="Add hashtag (without #)"
                value={hashtagInput}
                onChange={(e) => setHashtagInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddHashtag()}
              />
              <Button type="button" onClick={handleAddHashtag} size="sm">
                <Hash className="w-4 h-4" />
              </Button>
            </div>
            {hashtags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {hashtags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="flex items-center gap-1">
                    #{tag}
                    <X
                      className="w-3 h-3 cursor-pointer hover:text-red-500"
                      onClick={() => handleRemoveHashtag(tag)}
                    />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Privacy Settings */}
          <div className="space-y-3">
            <Label htmlFor="privacy">Privacy Level</Label>
            <Select value={privacy} onValueChange={setPrivacy}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="PUBLIC_TO_EVERYONE">Public</SelectItem>
                <SelectItem value="MUTUAL_FOLLOW_FRIENDS">Friends Only</SelectItem>
                <SelectItem value="SELF_ONLY">Private</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!selectedClip || !selectedAccount || !scheduledDate || !scheduledTime || createPost.isPending}
              className="flex items-center gap-2"
            >
              {createPost.isPending ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Send className="w-4 h-4" />
              )}
              Schedule Post
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}