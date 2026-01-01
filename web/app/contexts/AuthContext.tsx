'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User, Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error: any }>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let hasReceivedInitialSession = false

    // Listen for auth changes - this is the reliable way to get the session
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      console.log('[AuthContext] Auth state changed:', event, session ? 'has session' : 'no session')
      setSession(session)
      setUser(session?.user ?? null)
      
      // INITIAL_SESSION is the key event - session restored from storage
      if (event === 'INITIAL_SESSION') {
        hasReceivedInitialSession = true
        setLoading(false)
        console.log('[AuthContext] INITIAL_SESSION received, loading complete')
      } else if (event === 'SIGNED_IN' || event === 'SIGNED_OUT') {
        // For sign in/out, also stop loading
        setLoading(false)
      } else if (!hasReceivedInitialSession) {
        // If we haven't received INITIAL_SESSION yet, keep loading
        // This prevents premature checks
      }
    })

    // Don't call getSession() - it's unreliable. Wait for INITIAL_SESSION event instead.
    // Set a timeout as fallback in case INITIAL_SESSION never fires
    const fallbackTimer = setTimeout(() => {
      if (!hasReceivedInitialSession) {
        console.log('[AuthContext] Fallback: INITIAL_SESSION never fired, checking session directly')
        supabase.auth.getSession().then(({ data: { session } }) => {
          setSession(session)
          setUser(session?.user ?? null)
          setLoading(false)
        })
      }
    }, 3000) // 3 second fallback

    return () => {
      subscription.unsubscribe()
      clearTimeout(fallbackTimer)
    }
  }, [])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { error }
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

