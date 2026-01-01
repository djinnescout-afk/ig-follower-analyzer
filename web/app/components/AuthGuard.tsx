'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()
  const [hasChecked, setHasChecked] = useState(false)

  useEffect(() => {
    // Wait for auth to finish loading
    if (loading) return

    // Give it a moment for session to be restored
    const timer = setTimeout(() => {
      setHasChecked(true)
      console.log('[AuthGuard] Check complete - user:', user ? 'exists' : 'null', 'session:', session ? 'exists' : 'null')
      
      // Only redirect if we're sure there's no session
      if (!user && !session) {
        console.log('[AuthGuard] No user or session, redirecting to login')
        router.push('/login')
      }
    }, 500) // Wait 500ms for session to restore

    return () => clearTimeout(timer)
  }, [user, session, loading, router])

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

  // If no user after loading, don't render (redirect will happen)
  if (!user && !session) {
    return null
  }

  return <>{children}</>
}

