import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@clerk/nextjs'

// Simple logger for frontend
const logger = {
  debug: (message: string, data?: any) => console.log(`[WS Debug] ${message}`, data),
  info: (message: string, data?: any) => console.log(`[WS Info] ${message}`, data),
  error: (message: string, data?: any) => console.error(`[WS Error] ${message}`, data),
}

export interface WebSocketMessage {
  type: 'project_update' | 'error' | 'pong'
  timestamp: string
  project_id?: string
  status?: string
  progress?: number
  current_step?: string
  step_details?: Record<string, any>
  error_message?: string
  error?: string
}

export interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  lastMessage: WebSocketMessage | null
}

interface UseWebSocketOptions {
  reconnectInterval?: number
  maxReconnectAttempts?: number
  pingInterval?: number
}

const DEFAULT_OPTIONS: Required<UseWebSocketOptions> = {
  reconnectInterval: 3000, // 3 seconds
  maxReconnectAttempts: 5,
  pingInterval: 30000, // 30 seconds
}

export function useWebSocket(
  projectId: string | null,
  options: UseWebSocketOptions = {}
) {
  const { getToken } = useAuth()
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options }

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const isManualCloseRef = useRef(false)

  const connect = useCallback(async () => {
    if (!projectId) {
      logger.debug('No project ID provided, skipping WebSocket connection')
      return
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING || wsRef.current?.readyState === WebSocket.OPEN) {
      logger.debug('WebSocket already connecting or connected', { projectId })
      return
    }

    try {
      setState(prev => ({ ...prev, isConnecting: true, error: null }))

      const token = await getToken()
      if (!token) {
        throw new Error('No authentication token available')
      }

      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}/ws/projects/${projectId}?token=${encodeURIComponent(token)}`

      logger.info('Connecting to WebSocket', { projectId, url: wsUrl.replace(/token=[^&]*/, 'token=***') })

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        logger.info('WebSocket connected', { projectId })
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
        }))
        reconnectAttemptsRef.current = 0

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, mergedOptions.pingInterval)
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          logger.debug('WebSocket message received', {
            projectId,
            messageType: message.type,
            status: message.status
          })

          setState(prev => ({
            ...prev,
            lastMessage: message,
            error: message.type === 'error' ? message.error || 'Unknown error' : prev.error,
          }))
        } catch (error) {
          logger.error('Failed to parse WebSocket message', {
            projectId,
            error: error instanceof Error ? error.message : 'Unknown error',
            data: event.data
          })
        }
      }

      ws.onclose = (event) => {
        logger.info('WebSocket disconnected', {
          projectId,
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })

        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }))

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = null
        }

        // Attempt reconnection if not manually closed
        if (!isManualCloseRef.current && reconnectAttemptsRef.current < mergedOptions.maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          logger.info('Attempting WebSocket reconnection', {
            projectId,
            attempt: reconnectAttemptsRef.current,
            maxAttempts: mergedOptions.maxReconnectAttempts
          })

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, mergedOptions.reconnectInterval)
        } else if (reconnectAttemptsRef.current >= mergedOptions.maxReconnectAttempts) {
          setState(prev => ({
            ...prev,
            error: 'Failed to reconnect after maximum attempts',
          }))
        }
      }

      ws.onerror = (error) => {
        logger.error('WebSocket error', {
          projectId,
          error: error instanceof Error ? error.message : 'Unknown error'
        })
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false,
        }))
      }

    } catch (error) {
      logger.error('Failed to connect WebSocket', {
        projectId,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }))
    }
  }, [projectId, getToken, mergedOptions])

  const disconnect = useCallback(() => {
    logger.info('Manually disconnecting WebSocket', { projectId })
    isManualCloseRef.current = true

    // Clear timeouts and intervals
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
    }))
  }, [projectId])

  const reconnect = useCallback(() => {
    logger.info('Manual WebSocket reconnection', { projectId })
    disconnect()
    isManualCloseRef.current = false
    reconnectAttemptsRef.current = 0
    setTimeout(connect, 100) // Small delay to ensure cleanup
  }, [disconnect, connect, projectId])

  // Effect to handle connection lifecycle
  useEffect(() => {
    if (projectId) {
      isManualCloseRef.current = false
      connect()
    }

    return () => {
      disconnect()
    }
  }, [projectId, connect, disconnect])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isManualCloseRef.current = true
      disconnect()
    }
  }, [disconnect])

  return {
    ...state,
    connect,
    disconnect,
    reconnect,
  }
}

export function useProjectWebSocket(projectId: string | null) {
  /**
   * Specialized hook for project updates with additional utilities
   */
  const webSocket = useWebSocket(projectId)

  // Extract project-specific data from messages
  const projectStatus = webSocket.lastMessage?.type === 'project_update'
    ? {
        status: webSocket.lastMessage.status,
        progress: webSocket.lastMessage.progress,
        currentStep: webSocket.lastMessage.current_step,
        stepDetails: webSocket.lastMessage.step_details,
        errorMessage: webSocket.lastMessage.error_message,
      }
    : null

  const isProcessing = projectStatus?.status && !['done', 'failed'].includes(projectStatus.status)
  const isCompleted = projectStatus?.status === 'done'
  const isFailed = projectStatus?.status === 'failed'

  return {
    ...webSocket,
    projectStatus,
    isProcessing,
    isCompleted,
    isFailed,
  }
}