'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { adminApi, AdminUser } from '../lib/api'
import { format } from 'date-fns'
import { Mail, ExternalLink, RefreshCw, Pause, Play } from 'lucide-react'

export default function AdminTab() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null)
  const [generatedLink, setGeneratedLink] = useState<string | null>(null)
  const [generatedLinkEmail, setGeneratedLinkEmail] = useState<string | null>(null)

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
      // Always use the current production URL, never localhost
      const redirectTo = window.location.origin
      console.log('[AdminTab] Generating magic link with redirectTo:', redirectTo)
      const response = await adminApi.generateMagicLink(userId, redirectTo)
      return response.data
    },
    onSuccess: (data) => {
      // Store the link for copying instead of auto-opening
      setGeneratedLink(data.magic_link)
      setGeneratedLinkEmail(data.user_email)
    },
    onError: (error: any) => {
      if (error.response?.status === 403) {
        alert('You do not have admin access. Contact your administrator.')
      } else {
        alert(`Error generating magic link: ${error.response?.data?.detail || error.message}`)
      }
    },
  })

  // Set account state mutation
  const setAccountStateMutation = useMutation({
    mutationFn: async ({ userId, state }: { userId: string; state: 'active' | 'paused' }) => {
      const response = await adminApi.setAccountState(userId, state)
      return response.data
    },
    onSuccess: () => {
      // Refetch users to update the list
      refetch()
    },
    onError: (error: any) => {
      if (error.response?.status === 403) {
        alert('You do not have admin access. Contact your administrator.')
      } else {
        alert(`Error updating account state: ${error.response?.data?.detail || error.message}`)
      }
    },
  })

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      alert('Magic link copied to clipboard!')
    } catch (err) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
      alert('Magic link copied to clipboard!')
    }
  }

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
      {/* Generated Link Display */}
      {generatedLink && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-blue-900 mb-1">
                Magic Link Generated
              </h3>
              <p className="text-xs text-blue-700">
                For: {generatedLinkEmail}
              </p>
            </div>
            <button
              onClick={() => {
                setGeneratedLink(null)
                setGeneratedLinkEmail(null)
              }}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              ✕
            </button>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={generatedLink}
              className="flex-1 px-3 py-2 bg-white border border-blue-300 rounded-md text-sm font-mono text-gray-700"
              onClick={(e) => (e.target as HTMLInputElement).select()}
            />
            <button
              onClick={() => copyToClipboard(generatedLink)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Copy Link
            </button>
          </div>
          <p className="text-xs text-blue-600 mt-2">
            Copy this link and open it in an incognito/private window to sign in as this user.
          </p>
        </div>
      )}

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
          Manage user accounts: generate magic links for debugging, or pause/activate accounts.
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
                  Account State
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
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      (user.account_state || 'active') === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {(user.account_state || 'active') === 'active' ? 'Active' : 'Paused'}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => generateLinkMutation.mutate(user.id)}
                        disabled={generateLinkMutation.isPending && selectedUserId === user.id}
                        className="flex items-center gap-1 px-2 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
                      >
                        {generateLinkMutation.isPending && selectedUserId === user.id ? (
                          <>
                            <RefreshCw size={12} className="animate-spin" />
                            Generating...
                          </>
                        ) : (
                          <>
                            <Mail size={12} />
                            Sign In
                          </>
                        )}
                      </button>
                      {(user.account_state || 'active') === 'active' ? (
                        <button
                          onClick={() => {
                            if (confirm(`Pause account for ${user.email}? They will lose access to all features.`)) {
                              setAccountStateMutation.mutate({ userId: user.id, state: 'paused' })
                            }
                          }}
                          disabled={setAccountStateMutation.isPending}
                          className="flex items-center gap-1 px-2 py-1 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
                          title="Pause account"
                        >
                          <Pause size={12} />
                          Pause
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            if (confirm(`Activate account for ${user.email}?`)) {
                              setAccountStateMutation.mutate({ userId: user.id, state: 'active' })
                            }
                          }}
                          disabled={setAccountStateMutation.isPending}
                          className="flex items-center gap-1 px-2 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-xs"
                          title="Activate account"
                        >
                          <Play size={12} />
                          Activate
                        </button>
                      )}
                    </div>
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

