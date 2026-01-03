'use client'

import { useQuery } from '@tanstack/react-query'
import { accountApi } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'

export function AccountStatusGuard({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()

  // Fetch account status
  const { data: accountStatus, isLoading } = useQuery({
    queryKey: ['account', 'status'],
    queryFn: async () => {
      const response = await accountApi.getStatus()
      return response.data
    },
    enabled: !!user, // Only fetch if user is logged in
    retry: 1,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  })

  // Show loading while checking account status
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  // If account is paused, show blocked message
  if (accountStatus?.account_state === 'paused') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center px-6">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="mb-4">
              <svg
                className="mx-auto h-16 w-16 text-yellow-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Account Paused
            </h1>
            <p className="text-gray-600 mb-6">
              Your account has been paused. Please contact support to reactivate your account.
            </p>
            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-500">
              <p>If you believe this is an error, please reach out to our support team.</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Account is active, show content
  return <>{children}</>
}

