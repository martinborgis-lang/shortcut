'use client'

import { Toaster } from 'sonner'

export function NotificationProvider() {
  return (
    <Toaster
      theme="dark"
      position="bottom-right"
      expand
      visibleToasts={4}
      toastOptions={{
        style: {
          background: '#1A1A2E',
          border: '1px solid #2A2A3E',
          color: '#FFFFFF',
        },
        className: 'rounded-lg',
        duration: 5000,
        closeButton: true,
      }}
      icons={{
        success: '✅',
        info: '💡',
        warning: '⚠️',
        error: '❌',
      }}
    />
  )
}