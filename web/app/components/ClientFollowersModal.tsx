'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clientsApi } from '../lib/api'
import { X } from 'lucide-react'

interface ClientFollowersModalProps {
  pageId: string
  pageUsername: string
  clientCount: number
}

export default function ClientFollowersModal({ pageId, pageUsername, clientCount }: ClientFollowersModalProps) {
  const [isOpen, setIsOpen] = useState(false)

  const { data: clients, isLoading } = useQuery({
    queryKey: ['page-followers', pageId],
    queryFn: async () => {
      // Get client_following records for this page
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'https://ig-follower-analyzer.onrender.com'}/api/pages/${pageId}/followers`
      )
      if (!response.ok) {
        throw new Error('Failed to fetch followers')
      }
      return response.json()
    },
    enabled: isOpen, // Only fetch when modal is open
  })

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
      >
        {clientCount} client{clientCount !== 1 ? 's' : ''}
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[80vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                Clients Following @{pageUsername}
              </h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-y-auto flex-1">
              {isLoading ? (
                <div className="text-center py-8 text-gray-500">
                  Loading clients...
                </div>
              ) : clients && clients.length > 0 ? (
                <div className="space-y-2">
                  {clients.map((client: any) => (
                    <div
                      key={client.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                    >
                      <div>
                        <div className="font-medium">@{client.ig_username}</div>
                        {client.full_name && (
                          <div className="text-sm text-gray-600">{client.full_name}</div>
                        )}
                      </div>
                      <a
                        href={`https://instagram.com/${client.ig_username}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        View →
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No clients found
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t bg-gray-50">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

