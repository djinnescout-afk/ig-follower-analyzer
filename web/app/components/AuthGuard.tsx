'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading, session } = useAuth()
  const router = useRouter()
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      // Wait for loading to complete
      if (loading) return

      // Wait for INITIAL_SESSION to fire (session restored from storage)
      // Check multiple times to catch the session when it's ready
      let attempts = 0
      const maxAttempts = 10
      
      const checkInterval = setInterval(async () => {
        attempts++
        const { data: { session: currentSession } } = await supabase.auth.getSession()
        
        console.log(`[AuthGuard] Attempt ${attempts}: session`, currentSession ? 'found' : 'not found', 'user:', user ? 'exists' : 'null')
        
        if (currentSession || user || session) {
          console.log('[AuthGuard] Session found, allowing access')
          setIsReady(true)
          clearInterval(checkInterval)
        } else if (attempts >= maxAttempts) {
          console.log('[AuthGuard] Max attempts reached, no session found, redirecting')
          setIsReady(true)
          clearInterval(checkInterval)
          router.push('/login')
        }
      }, 200) // Check every 200ms

      return () => clearInterval(checkInterval)
    }

    checkAuth()
  }, [loading, user, session, router])

  // Show loading while checking auth
  if (loading || !isReady) {
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

