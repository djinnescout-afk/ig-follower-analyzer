'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsApi, scrapesApi, BulkClientResult } from '../lib/api'
import { format } from 'date-fns'
import { UserPlus, RefreshCw, Trash2, Users } from 'lucide-react'

export default function ClientsTab() {
  const queryClient = useQueryClient()
  const [isAddingClient, setIsAddingClient] = useState(false)
  const [isBulkImporting, setIsBulkImporting] = useState(false)
  const [newClient, setNewClient] = useState({ name: '', ig_username: '' })
  const [bulkInput, setBulkInput] = useState('')
  const [bulkResult, setBulkResult] = useState<BulkClientResult | null>(null)
  const [selectedClients, setSelectedClients] = useState<string[]>([])

  // Fetch clients
  const { data: clients, isLoading } = useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await clientsApi.list()
      return response.data
    },
  })

  // Add client mutation
  const addClientMutation = useMutation({
    mutationFn: clientsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      setNewClient({ name: '', ig_username: '' })
      setIsAddingClient(false)
    },
  })

  // Bulk import mutation
  const bulkImportMutation = useMutation({
    mutationFn: clientsApi.createBulk,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      setBulkResult(data.data)
    },
  })

  // Delete client mutation
  const deleteClientMutation = useMutation({
    mutationFn: clientsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })

  // Trigger scrape mutation
  const scrapeMutation = useMutation({
    mutationFn: scrapesApi.triggerClientFollowing,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrapes'] })
      setSelectedClients([])
      alert('Scrape jobs queued successfully!')
    },
  })

  const handleAddClient = (e: React.FormEvent) => {
    e.preventDefault()
    if (newClient.name && newClient.ig_username) {
      addClientMutation.mutate(newClient)
    }
  }

  const handleBulkImport = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Parse input: each line should be "Name, @username" or "Name, username"
    const lines = bulkInput.split('\n').filter(line => line.trim())
    const clients = lines.map(line => {
      const parts = line.split(',').map(p => p.trim())
      if (parts.length >= 2) {
        const name = parts[0]
        let username = parts[1]
        // Remove @ if present
        username = username.replace('@', '')
        return { name, ig_username: username }
      }
      // If no comma, assume the whole line is the username and use it as name too
      const username = line.trim().replace('@', '')
      return { name: username, ig_username: username }
    }).filter(c => c.ig_username) // Filter out empty lines
    
    if (clients.length > 0) {
      bulkImportMutation.mutate(clients)
    }
  }

  const closeBulkModal = () => {
    setIsBulkImporting(false)
    setBulkInput('')
    setBulkResult(null)
  }

  const handleScrapeSelected = () => {
    if (selectedClients.length > 0) {
      scrapeMutation.mutate(selectedClients)
    }
  }

  const toggleClientSelection = (clientId: string) => {
    setSelectedClients(prev =>
      prev.includes(clientId)
        ? prev.filter(id => id !== clientId)
        : [...prev, clientId]
    )
  }

  if (isLoading) {
    return <div className="text-center py-8">Loading clients...</div>
  }

  return (
    <div className="space-y-6">
      {/* Add Client Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Clients</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setIsBulkImporting(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <Users size={16} />
              Bulk Import
            </button>
            <button
              onClick={() => setIsAddingClient(!isAddingClient)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <UserPlus size={16} />
              Add Client
            </button>
          </div>
        </div>

        {isAddingClient && (
          <form onSubmit={handleAddClient} className="mb-6 p-4 bg-gray-50 rounded-md">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Client Name
                </label>
                <input
                  type="text"
                  value={newClient.name}
                  onChange={(e) => setNewClient({ ...newClient, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="John Smith"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Instagram Username
                </label>
                <input
                  type="text"
                  value={newClient.ig_username}
                  onChange={(e) => setNewClient({ ...newClient, ig_username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  placeholder="johnsmith123"
                  required
                />
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="submit"
                disabled={addClientMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {addClientMutation.isPending ? 'Adding...' : 'Add Client'}
              </button>
              <button
                type="button"
                onClick={() => setIsAddingClient(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Bulk Actions */}
        {selectedClients.length > 0 && (
          <div className="mb-4 p-3 bg-blue-50 rounded-md flex items-center justify-between">
            <span className="text-sm text-blue-900">
              {selectedClients.length} client(s) selected
            </span>
            <button
              onClick={handleScrapeSelected}
              disabled={scrapeMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              <RefreshCw size={16} />
              {scrapeMutation.isPending ? 'Queueing...' : 'Scrape Selected'}
            </button>
          </div>
        )}

        {/* Clients Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedClients(clients?.map(c => c.id) || [])
                      } else {
                        setSelectedClients([])
                      }
                    }}
                    checked={selectedClients.length === clients?.length && clients.length > 0}
                  />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Instagram
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Following Count
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Last Scraped
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {clients?.map((client) => (
                <tr key={client.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <input
                      type="checkbox"
                      checked={selectedClients.includes(client.id)}
                      onChange={() => toggleClientSelection(client.id)}
                    />
                  </td>
                  <td className="px-4 py-4 text-sm font-medium text-gray-900">
                    {client.name}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    @{client.ig_username}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {client.following_count > 0 ? client.following_count.toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {client.last_scraped
                      ? format(new Date(client.last_scraped), 'MMM d, yyyy')
                      : 'Never'}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <button
                      onClick={() => {
                        if (confirm(`Delete client ${client.name}?`)) {
                          deleteClientMutation.mutate(client.id)
                        }
                      }}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {clients?.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No clients yet. Add your first client to get started!
            </div>
          )}
        </div>
      </div>

      {/* Bulk Import Modal */}
      {isBulkImporting && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold">Bulk Import Clients</h3>
              <button
                onClick={closeBulkModal}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            {!bulkResult ? (
              <form onSubmit={handleBulkImport}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Enter clients (one per line)
                  </label>
                  <p className="text-xs text-gray-500 mb-2">
                    Format: <code>Name, @username</code> or just <code>@username</code>
                  </p>
                  <p className="text-xs text-gray-500 mb-3">
                    Example:<br />
                    <code>John Doe, @johndoe</code><br />
                    <code>Jane Smith, janesmith</code><br />
                    <code>@example_user</code>
                  </p>
                  <textarea
                    value={bulkInput}
                    onChange={(e) => setBulkInput(e.target.value)}
                    rows={12}
                    placeholder="John Doe, @johndoe&#10;Jane Smith, janesmith&#10;@example_user"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    required
                  />
                </div>

                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={closeBulkModal}
                    className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={bulkImportMutation.isPending}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {bulkImportMutation.isPending ? 'Importing...' : 'Import'}
                  </button>
                </div>
              </form>
            ) : (
              <div>
                {/* Success Results */}
                {bulkResult.success.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-green-600 mb-2">
                      ✅ Successfully Imported ({bulkResult.success.length})
                    </h4>
                    <div className="bg-green-50 rounded-md p-4 max-h-64 overflow-y-auto">
                      {bulkResult.success.map((client) => (
                        <div key={client.id} className="text-sm py-1">
                          {client.name} (@{client.ig_username})
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Failed Results */}
                {bulkResult.failed.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-lg font-semibold text-red-600 mb-2">
                      ❌ Failed ({bulkResult.failed.length})
                    </h4>
                    <div className="bg-red-50 rounded-md p-4 max-h-64 overflow-y-auto">
                      {bulkResult.failed.map((failed, idx) => (
                        <div key={idx} className="text-sm py-2 border-b border-red-100 last:border-0">
                          <div className="font-medium">{failed.name} (@{failed.ig_username})</div>
                          <div className="text-red-600 text-xs">{failed.reason}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex justify-end">
                  <button
                    onClick={closeBulkModal}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

