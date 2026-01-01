'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()
  const hasRedirected = useRef(false)

  useEffect(() => {
    // Only check after loading completes
    if (loading) {
      hasRedirected.current = false
      return
    }

    // Wait a moment for React state to update after loading completes
    const timer = setTimeout(() => {
      console.log('[AuthGuard] Final check - user:', user ? 'exists' : 'null', 'session:', session ? 'exists' : 'null')
      
      // Only redirect if we're absolutely sure there's no session AND we haven't redirected yet
      if (!user && !session && !hasRedirected.current) {
        console.log('[AuthGuard] No user or session after loading, redirecting to login')
        hasRedirected.current = true
        router.push('/login')
      }
    }, 800) // Wait 800ms after loading completes for state to update

    return () => clearTimeout(timer)
  }, [loading, user, session, router])

  // Show loading while checking auth (with timeout fallback)
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
          <p className="mt-2 text-xs text-gray-400">Initializing authentication...</p>
        </div>
      </div>
    )
  }

  // If we have a user or session, show content (this is the key check)
  if (user || session) {
    console.log('[AuthGuard] Render: User or session exists, showing content')
    return <>{children}</>
  }

  // If no user after loading, show nothing (redirect will happen via useEffect)
  console.log('[AuthGuard] Render: No user or session, waiting for redirect')
  return null
}

