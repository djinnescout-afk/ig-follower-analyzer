'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [hasChecked, setHasChecked] = useState(false)

  useEffect(() => {
    // Wait a bit for session to load from storage
    if (!loading) {
      setHasChecked(true)
      console.log('[AuthGuard] Loading complete, user:', user ? 'exists' : 'null')
      if (!user) {
        console.log('[AuthGuard] No user, redirecting to login')
        router.push('/login')
      }
    }
  }, [user, loading, router])

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
  if (!user) {
    return null
  }

  return <>{children}</>
}

