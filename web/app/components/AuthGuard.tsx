'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../lib/supabase'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const checkAuth = async () => {
      // Wait for initial load
      if (loading) return

      // Double-check session directly from Supabase
      const { data: { session } } = await supabase.auth.getSession()
      console.log('[AuthGuard] Direct session check:', session ? 'found' : 'not found')
      
      setChecking(false)
      
      if (!session && !user) {
        console.log('[AuthGuard] No session or user, redirecting to login')
        router.push('/login')
      }
    }

    checkAuth()
  }, [user, loading, router])

  // Show loading while checking auth
  if (loading || checking) {
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

