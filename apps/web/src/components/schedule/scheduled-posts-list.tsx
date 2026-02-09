/**
 * Scheduled Posts List Component
 * List view of scheduled posts with actions
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Calendar,
  Clock,
  TrendingUp,
  AlertCircle,
  MoreVertical,
  Edit,
  Trash2,
  Eye,
  Hash,
  Search,
  Filter,
} from "lucide-react";

interface ScheduledPost {
  id: string;
  scheduled_time: string;
  status: string;
  caption?: string;
  hashtags?: string[];
  platform?: string;
  views?: number;
  likes?: number;
  engagement_rate?: number;
}

interface ScheduledPostsListProps {
  posts: ScheduledPost[];
  onPostEdit: (post: ScheduledPost) => void;
  onPostCancel: (postId: string) => void;
}

export function ScheduledPostsList({ posts, onPostEdit, onPostCancel }: ScheduledPostsListProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("scheduled_time");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [cancelPostId, setCancelPostId] = useState<string | null>(null);

  // Filter and sort posts
  const filteredPosts = posts
    .filter(post => {
      const matchesSearch = !searchTerm ||
        (post.caption?.toLowerCase().includes(searchTerm.toLowerCase()) ||
         post.hashtags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase())));
      const matchesStatus = statusFilter === "all" || post.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      let comparison = 0;

      switch (sortBy) {
        case "scheduled_time":
          comparison = new Date(a.scheduled_time).getTime() - new Date(b.scheduled_time).getTime();
          break;
        case "status":
          comparison = a.status.localeCompare(b.status);
          break;
        case "engagement_rate":
          comparison = (a.engagement_rate || 0) - (b.engagement_rate || 0);
          break;
        default:
          comparison = 0;
      }

      return sortOrder === "desc" ? -comparison : comparison;
    });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "scheduled": return "bg-blue-100 text-blue-800";
      case "publishing": return "bg-yellow-100 text-yellow-800";
      case "published": return "bg-green-100 text-green-800";
      case "failed": return "bg-red-100 text-red-800";
      case "cancelled": return "bg-gray-100 text-gray-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "scheduled": return <Clock className="w-3 h-3" />;
      case "publishing": return <div className="w-3 h-3 animate-spin border border-current border-t-transparent rounded-full" />;
      case "published": return <TrendingUp className="w-3 h-3" />;
      case "failed": return <AlertCircle className="w-3 h-3" />;
      case "cancelled": return <Trash2 className="w-3 h-3" />;
      default: return <Clock className="w-3 h-3" />;
    }
  };

  const canEdit = (post: ScheduledPost) => {
    return post.status === "scheduled" || post.status === "failed";
  };

  const canCancel = (post: ScheduledPost) => {
    return post.status === "scheduled";
  };

  return (
    <div className="space-y-6">
      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search posts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Status Filter */}
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="publishing">Publishing</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>

            {/* Sort By */}
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger>
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="scheduled_time">Scheduled Time</SelectItem>
                <SelectItem value="status">Status</SelectItem>
                <SelectItem value="engagement_rate">Engagement Rate</SelectItem>
              </SelectContent>
            </Select>

            {/* Sort Order */}
            <Select value={sortOrder} onValueChange={(value: "asc" | "desc") => setSortOrder(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="asc">Ascending</SelectItem>
                <SelectItem value="desc">Descending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Posts List */}
      <div className="space-y-4">
        {filteredPosts.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600 mb-2">No posts found</h3>
              <p className="text-gray-500">
                {searchTerm || statusFilter !== "all"
                  ? "Try adjusting your filters or search terms"
                  : "You haven't scheduled any posts yet"
                }
              </p>
            </CardContent>
          </Card>
        ) : (
          filteredPosts.map((post) => (
            <Card key={post.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  {/* Left Content */}
                  <div className="flex-1 min-w-0 space-y-3">
                    {/* Status and Time */}
                    <div className="flex items-center gap-3">
                      <Badge className={`${getStatusColor(post.status)} flex items-center gap-1`}>
                        {getStatusIcon(post.status)}
                        {post.status}
                      </Badge>

                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Calendar className="w-4 h-4" />
                        {new Date(post.scheduled_time).toLocaleDateString()}
                      </div>

                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        {new Date(post.scheduled_time).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                          hour12: true,
                        })}
                      </div>

                      {/* Platform */}
                      <div className="flex items-center gap-2">
                        <div className="w-5 h-5 bg-black rounded-full flex items-center justify-center text-white text-xs font-bold">
                          T
                        </div>
                        <span className="text-sm text-gray-500">TikTok</span>
                      </div>
                    </div>

                    {/* Caption */}
                    <div>
                      <p className="text-gray-800 line-clamp-2">
                        {post.caption || <span className="text-gray-500 italic">No caption</span>}
                      </p>
                    </div>

                    {/* Hashtags */}
                    {post.hashtags && post.hashtags.length > 0 && (
                      <div className="flex items-center gap-2 flex-wrap">
                        <Hash className="w-4 h-4 text-gray-400" />
                        {post.hashtags.slice(0, 5).map((tag, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            #{tag}
                          </Badge>
                        ))}
                        {post.hashtags.length > 5 && (
                          <span className="text-xs text-gray-500">
                            +{post.hashtags.length - 5} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Performance Metrics (for published posts) */}
                    {post.status === "published" && (
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        {post.views !== undefined && (
                          <div className="flex items-center gap-1">
                            <Eye className="w-4 h-4" />
                            <span>{post.views.toLocaleString()} views</span>
                          </div>
                        )}
                        {post.likes !== undefined && (
                          <div className="flex items-center gap-1">
                            <TrendingUp className="w-4 h-4" />
                            <span>{post.likes.toLocaleString()} likes</span>
                          </div>
                        )}
                        {post.engagement_rate !== undefined && (
                          <div className="flex items-center gap-1">
                            <span>{post.engagement_rate.toFixed(1)}% engagement</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 ml-4">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {post.status === "published" && (
                          <>
                            <DropdownMenuItem>
                              <Eye className="w-4 h-4 mr-2" />
                              View Analytics
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                          </>
                        )}

                        {canEdit(post) && (
                          <DropdownMenuItem onClick={() => onPostEdit(post)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit Post
                          </DropdownMenuItem>
                        )}

                        {canCancel(post) && (
                          <DropdownMenuItem
                            onClick={() => setCancelPostId(post.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Cancel Post
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={!!cancelPostId} onOpenChange={() => setCancelPostId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Scheduled Post</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this scheduled post? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Keep Post</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (cancelPostId) {
                  onPostCancel(cancelPostId);
                  setCancelPostId(null);
                }
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              Cancel Post
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}