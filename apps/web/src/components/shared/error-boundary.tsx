"use client"

import { Component, ErrorInfo, ReactNode } from "react"
import { Button } from "@/components/ui/button"
import { AlertTriangle, RefreshCw, Home } from "lucide-react"

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  }

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)

    // You can log the error to an error reporting service here
    // Example: logErrorToService(error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center">
          <div className="text-center space-y-8 p-8">
            <div className="space-y-4">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <h2 className="text-2xl font-bold text-white">
                Something went wrong
              </h2>
              <p className="text-muted-foreground max-w-md mx-auto">
                We apologize for the inconvenience. An unexpected error occurred while loading this content.
              </p>
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-left bg-card/50 rounded-lg p-4 mt-4">
                  <summary className="cursor-pointer text-sm font-medium text-white mb-2">
                    Error Details (Development)
                  </summary>
                  <pre className="text-xs text-red-400 overflow-auto">
                    {this.state.error.stack}
                  </pre>
                </details>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={this.handleReset}
                className="bg-primary hover:bg-primary/80"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={this.handleReload}
                className="border-border bg-card/50"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Reload Page
              </Button>
              <Button
                variant="ghost"
                onClick={() => window.location.href = '/'}
              >
                <Home className="mr-2 h-4 w-4" />
                Go Home
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

// Hook-based error boundary for functional components
export function withErrorBoundary<T extends object>(
  Component: React.ComponentType<T>,
  fallback?: ReactNode
) {
  return function WrappedComponent(props: T) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    )
  }
}