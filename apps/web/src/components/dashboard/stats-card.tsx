import { ReactNode } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: ReactNode
  trend?: {
    value: number
    isPositive: boolean
  }
  badge?: {
    text: string
    variant: 'default' | 'secondary' | 'success' | 'warning' | 'viral'
  }
}

export function StatsCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  badge
}: StatsCardProps) {
  return (
    <Card className="p-6 bg-[#1A1A2E] border-[#2A2A3E] hover:border-[#E94560]/20 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-400">{title}</p>
            {badge && (
              <Badge variant={badge.variant} className="text-xs">
                {badge.text}
              </Badge>
            )}
          </div>

          <div className="flex items-baseline space-x-2">
            <h3 className="text-2xl font-bold text-white">{value}</h3>
            {trend && (
              <span
                className={`text-xs font-medium ${
                  trend.isPositive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
            )}
          </div>

          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div className="text-[#E94560] ml-4">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}