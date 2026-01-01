'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()
  const [hasStabilized, setHasStabilized] = useState(false)

  useEffect(() => {
    // Wait for loading to complete
    if (loading) {
      setHasStabilized(false)
      return
    }

    // Wait a bit for auth state to stabilize after loading completes
    const timer = setTimeout(() => {
      setHasStabilized(true)
      console.log('[AuthGuard] Auth stabilized - user:', user ? 'exists' : 'null', 'session:', session ? 'exists' : 'null')
    }, 1000) // Wait 1 second after loading completes

    return () => clearTimeout(timer)
  }, [loading, user, session])

  useEffect(() => {
    // Only redirect after auth has stabilized
    if (!hasStabilized || loading) return

    if (!user && !session) {
      console.log('[AuthGuard] No user or session after stabilization, redirecting to login')
      router.push('/login')
    }
  }, [hasStabilized, user, session, loading, router])

  // Show loading while checking auth
  if (loading || !hasStabilized) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // If no user after stabilization, don't render (redirect will happen)
  if (!user && !session) {
    return null
  }

  return <>{children}</>
}

