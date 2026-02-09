'use client'

import { useState } from 'react'
import { Button } from './button'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CalendarProps {
  selected?: Date
  onSelect?: (date: Date) => void
  className?: string
}

export function Calendar({ selected, onSelect, className }: CalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(selected || new Date())

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
  }

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay()
  }

  const previousMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1))
  }

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1))
  }

  const handleDateClick = (day: number) => {
    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day)
    onSelect?.(newDate)
  }

  const daysInMonth = getDaysInMonth(currentMonth)
  const firstDay = getFirstDayOfMonth(currentMonth)
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1)
  const emptyDays = Array.from({ length: firstDay }, (_, i) => null)

  const monthYear = currentMonth.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric'
  })

  return (
    <div className={cn('p-3', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <Button
          variant="outline"
          size="icon"
          onClick={previousMonth}
          className="h-7 w-7"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <h2 className="font-semibold text-sm">{monthYear}</h2>
        <Button
          variant="outline"
          size="icon"
          onClick={nextMonth}
          className="h-7 w-7"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Days of week */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map((day) => (
          <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar days */}
      <div className="grid grid-cols-7 gap-1">
        {emptyDays.map((_, index) => (
          <div key={`empty-${index}`} className="h-9" />
        ))}
        {days.map((day) => {
          const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day)
          const isSelected = selected &&
            date.getDate() === selected.getDate() &&
            date.getMonth() === selected.getMonth() &&
            date.getFullYear() === selected.getFullYear()
          const isToday =
            date.getDate() === new Date().getDate() &&
            date.getMonth() === new Date().getMonth() &&
            date.getFullYear() === new Date().getFullYear()

          return (
            <Button
              key={day}
              variant="ghost"
              className={cn(
                'h-9 w-9 p-0 font-normal text-sm',
                isSelected && 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground focus:bg-primary focus:text-primary-foreground',
                isToday && !isSelected && 'bg-accent text-accent-foreground'
              )}
              onClick={() => handleDateClick(day)}
            >
              {day}
            </Button>
          )
        })}
      </div>
    </div>
  )
}