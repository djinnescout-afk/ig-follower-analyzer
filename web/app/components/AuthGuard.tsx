'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()
  const [hasChecked, setHasChecked] = useState(false)

  useEffect(() => {
    // Wait for loading to complete (INITIAL_SESSION has fired)
    if (loading) {
      setHasChecked(false)
      return
    }

    // After loading completes, wait a moment for state to update
    const timer = setTimeout(() => {
      setHasChecked(true)
      console.log('[AuthGuard] Check complete - user:', user ? 'exists' : 'null', 'session:', session ? 'exists' : 'null')
      
      // Only redirect if we're absolutely sure there's no session
      if (!user && !session) {
        console.log('[AuthGuard] No user or session, redirecting to login')
        router.push('/login')
      }
    }, 300) // Small delay to let React state update

    return () => clearTimeout(timer)
  }, [loading, user, session, router])

  // Show loading while checking auth
  if (loading || !hasChecked) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // If no user after checking, don't render (redirect will happen)
  if (!user && !session) {
    return null
  }

  return <>{children}</>
}

