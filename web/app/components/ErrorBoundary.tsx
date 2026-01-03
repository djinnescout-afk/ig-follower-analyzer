'use client'

import { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    // If it's a chunk loading error, suggest reload
    if (error.message?.includes('chunk') || error.name === 'ChunkLoadError') {
      console.error('ChunkLoadError detected - this usually means the app was updated. Reloading...')
      // Auto-reload after a short delay
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    }
  }

  render() {
    if (this.state.hasError) {
      const isChunkError = this.state.error?.message?.includes('chunk') || this.state.error?.name === 'ChunkLoadError'
      
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center max-w-md mx-auto p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {isChunkError ? 'App Update Detected' : 'Something went wrong'}
            </h2>
            <p className="text-gray-600 mb-4">
              {isChunkError 
                ? 'The app has been updated. Reloading automatically...'
                : 'An error occurred. Please try refreshing the page.'}
            </p>
            {!isChunkError && (
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Reload Page
              </button>
            )}
            {!isChunkError && (
              <details className="mt-4 text-left">
                <summary className="text-sm text-gray-500 cursor-pointer">Error details</summary>
                <pre className="mt-2 text-xs text-red-600 bg-red-50 p-2 rounded overflow-auto">
                  {this.state.error?.message}
                </pre>
              </details>
            )}
          </div>
        </div>
      )
    }

    return this.props.children
  }
}


