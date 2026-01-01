'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { adminApi, AdminUser } from '../lib/api'
import { format } from 'date-fns'
import { Mail, ExternalLink, RefreshCw } from 'lucide-react'

export default function AdminTab() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)

  // Test admin access first
  const { data: testData } = useQuery({
    queryKey: ['admin', 'test'],
    queryFn: async () => {
      const response = await adminApi.testAdminAccess()
      return response.data
    },
    retry: false,
  })

  // Fetch all users
  const { data: usersData, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: async () => {
      const response = await adminApi.listUsers()
      return response.data
    },
    retry: false, // Don't retry on 403 (not admin)
  })

  // Generate magic link mutation
  const generateLinkMutation = useMutation({
    mutationFn: async (userId: string) => {
      setSelectedUserId(userId)
      const redirectTo = window.location.origin
      const response = await adminApi.generateMagicLink(userId, redirectTo)
      return response.data
    },
    onSuccess: (data) => {
      // Open magic link in new tab
      window.open(data.magic_link, '_blank')
      alert(`Magic link generated for ${data.user_email}. Opening in new tab...`)
    },
    onError: (error: any) => {
      if (error.response?.status === 403) {
        alert('You do not have admin access. Contact your administrator.')
      } else {
        alert(`Error generating magic link: ${error.response?.data?.detail || error.message}`)
      }
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading users...</div>
  }

  // Show debug info if test data is available
  if (testData) {
    console.log('[AdminTab] Admin test data:', testData)
  }

  if (!usersData) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">Unable to load users. You may not have admin access.</p>
        {testData && (
          <div className="mb-4 p-4 bg-gray-100 rounded-md text-left max-w-2xl mx-auto">
            <h3 className="font-semibold mb-2">Debug Info:</h3>
            <pre className="text-xs overflow-auto">
              {JSON.stringify(testData, null, 2)}
            </pre>
          </div>
        )}
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <RefreshCw size={16} className="inline mr-2" />
          Retry
        </button>
      </div>
    )
  }

  const users = usersData.users

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        <p className="text-sm text-gray-600 mb-4">
          Generate magic links to sign in as any user for debugging purposes.
        </p>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Email
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Created At
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Last Sign In
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Email Confirmed
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm font-medium text-gray-900">
                    {user.email}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {user.created_at
                      ? format(new Date(user.created_at), 'MMM d, yyyy HH:mm')
                      : '-'}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {user.last_sign_in_at
                      ? format(new Date(user.last_sign_in_at), 'MMM d, yyyy HH:mm')
                      : 'Never'}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {user.email_confirmed_at ? (
                      <span className="text-green-600">✓ Confirmed</span>
                    ) : (
                      <span className="text-yellow-600">Not confirmed</span>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <button
                      onClick={() => generateLinkMutation.mutate(user.id)}
                      disabled={generateLinkMutation.isPending && selectedUserId === user.id}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
                    >
                      {generateLinkMutation.isPending && selectedUserId === user.id ? (
                        <>
                          <RefreshCw size={14} className="animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Mail size={14} />
                          Sign In As User
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {users.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No users found.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

