'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Only check after loading completes
    if (loading) return

    // Wait a moment for React state to update after loading completes
    const timer = setTimeout(() => {
      console.log('[AuthGuard] Final check - user:', user ? 'exists' : 'null', 'session:', session ? 'exists' : 'null')
      
      // Only redirect if we're absolutely sure there's no session
      if (!user && !session) {
        console.log('[AuthGuard] No user or session after loading, redirecting to login')
        router.push('/login')
      }
    }, 500) // Wait 500ms after loading completes for state to update

    return () => clearTimeout(timer)
  }, [loading, user, session, router])

  // Show loading while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // If we have a user or session, show content
  if (user || session) {
    return <>{children}</>
  }

  // If no user after loading, don't render (redirect will happen)
  return null
}

