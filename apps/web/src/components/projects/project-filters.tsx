'use client'

import { useState } from 'react'
import { Search, Filter, SortAsc } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface ProjectFiltersProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  statusFilter: string | null
  onStatusFilterChange: (status: string | null) => void
  sortBy: 'created' | 'updated' | 'name'
  sortOrder: 'asc' | 'desc'
  onSortChange: (sortBy: 'created' | 'updated' | 'name', sortOrder: 'asc' | 'desc') => void
}

const statusOptions = [
  { value: null, label: 'All Status', count: 0 },
  { value: 'pending', label: 'Pending', count: 0 },
  { value: 'processing', label: 'Processing', count: 0 },
  { value: 'completed', label: 'Completed', count: 0 },
  { value: 'failed', label: 'Failed', count: 0 },
]

const sortOptions = [
  { value: 'created-desc', label: 'Newest first', sortBy: 'created', sortOrder: 'desc' },
  { value: 'created-asc', label: 'Oldest first', sortBy: 'created', sortOrder: 'asc' },
  { value: 'updated-desc', label: 'Recently updated', sortBy: 'updated', sortOrder: 'desc' },
  { value: 'name-asc', label: 'Name A-Z', sortBy: 'name', sortOrder: 'asc' },
  { value: 'name-desc', label: 'Name Z-A', sortBy: 'name', sortOrder: 'desc' },
] as const

export function ProjectFilters({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  sortBy,
  sortOrder,
  onSortChange,
}: ProjectFiltersProps) {
  const getCurrentSortLabel = () => {
    const option = sortOptions.find(
      opt => opt.sortBy === sortBy && opt.sortOrder === sortOrder
    )
    return option?.label || 'Newest first'
  }

  const getCurrentStatusLabel = () => {
    const option = statusOptions.find(opt => opt.value === statusFilter)
    return option?.label || 'All Status'
  }

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
        <Input
          placeholder="Search projects..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Filters and Sort */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {/* Status Filter */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="border-[#2A2A3E] text-gray-300">
                <Filter className="w-4 h-4 mr-2" />
                {getCurrentStatusLabel()}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuLabel>Filter by status</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {statusOptions.map((option) => (
                <DropdownMenuItem
                  key={option.value || 'all'}
                  onClick={() => onStatusFilterChange(option.value)}
                  className={statusFilter === option.value ? 'bg-[#2A2A3E]' : ''}
                >
                  {option.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Active Filters */}
          {(statusFilter || searchQuery) && (
            <div className="flex items-center gap-2">
              {statusFilter && (
                <Badge
                  variant="secondary"
                  className="cursor-pointer hover:bg-[#E94560]/20"
                  onClick={() => onStatusFilterChange(null)}
                >
                  {getCurrentStatusLabel()} ×
                </Badge>
              )}
              {searchQuery && (
                <Badge
                  variant="secondary"
                  className="cursor-pointer hover:bg-[#E94560]/20"
                  onClick={() => onSearchChange('')}
                >
                  Search: {searchQuery} ×
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Sort */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="border-[#2A2A3E] text-gray-300">
              <SortAsc className="w-4 h-4 mr-2" />
              {getCurrentSortLabel()}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Sort by</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {sortOptions.map((option) => (
              <DropdownMenuItem
                key={option.value}
                onClick={() => onSortChange(option.sortBy, option.sortOrder)}
                className={
                  sortBy === option.sortBy && sortOrder === option.sortOrder
                    ? 'bg-[#2A2A3E]'
                    : ''
                }
              >
                {option.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}