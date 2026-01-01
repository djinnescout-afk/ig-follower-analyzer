'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientsApi, scrapesApi } from '../lib/api'
import { format } from 'date-fns'
import { UserPlus, RefreshCw, Trash2 } from 'lucide-react'

export default function ClientsTab() {
  const queryClient = useQueryClient()
  const [isAddingClient, setIsAddingClient] = useState(false)
  const [isBulkAdding, setIsBulkAdding] = useState(false)
  const [newClient, setNewClient] = useState({ name: '', ig_username: '', date_closed: '' })
  const [bulkClients, setBulkClients] = useState({ text: '', date_closed: '' })
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
      setNewClient({ name: '', ig_username: '', date_closed: '' })
      setIsAddingClient(false)
    },
  })

  // Bulk add clients mutation
  const bulkAddMutation = useMutation({
    mutationFn: clientsApi.bulkCreate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      setBulkClients({ text: '', date_closed: '' })
      setIsBulkAdding(false)
      alert('Clients added successfully!')
    },
    onError: (error: any) => {
      alert(`Error adding clients: ${error.response?.data?.detail?.message || error.message}`)
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
      const payload: any = {
        name: newClient.name,
        ig_username: newClient.ig_username,
      }
      if (newClient.date_closed) {
        payload.date_closed = newClient.date_closed
      }
      addClientMutation.mutate(payload)
    }
  }

  const handleBulkAdd = (e: React.FormEvent) => {
    e.preventDefault()
    if (!bulkClients.text.trim()) {
      alert('Please enter client data')
      return
    }

    // Parse bulk text: one client per line, format: "Name,username"
    const lines = bulkClients.text.trim().split('\n').filter(line => line.trim())
    const clients = lines.map(line => {
      const parts = line.split(',').map(p => p.trim())
      if (parts.length < 2) {
        throw new Error(`Invalid format: "${line}". Expected "Name,username"`)
      }
      const payload: any = {
        name: parts[0],
        ig_username: parts[1],
      }
      if (bulkClients.date_closed) {
        payload.date_closed = bulkClients.date_closed
      }
      return payload
    })

    bulkAddMutation.mutate(clients)
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
              onClick={() => {
                setIsBulkAdding(false)
                setIsAddingClient(!isAddingClient)
              }}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <UserPlus size={16} />
              Add Client
            </button>
            <button
              onClick={() => {
                setIsAddingClient(false)
                setIsBulkAdding(!isBulkAdding)
              }}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
              title="Add multiple clients at once"
            >
              <UserPlus size={16} />
              Bulk Add Clients
            </button>
          </div>
        </div>

        {isAddingClient && (
          <form onSubmit={handleAddClient} className="mb-6 p-4 bg-gray-50 rounded-md">
            <div className="grid grid-cols-3 gap-4">
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
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date Closed (optional)
                </label>
                <input
                  type="date"
                  value={newClient.date_closed}
                  onChange={(e) => setNewClient({ ...newClient, date_closed: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <p className="text-xs text-gray-500 mt-1">Defaults to today if not set</p>
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

        {isBulkAdding && (
          <form onSubmit={handleBulkAdd} className="mb-6 p-4 bg-gray-50 rounded-md">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Clients (one per line: Name,username)
                </label>
                <textarea
                  value={bulkClients.text}
                  onChange={(e) => setBulkClients({ ...bulkClients, text: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-sm"
                  rows={8}
                  placeholder="John Smith,johnsmith123&#10;Jane Doe,janedoe456&#10;Bob Johnson,bobjohnson789"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Format: Client Name,Instagram Username (one per line)
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date Closed (optional - applies to all clients)
                </label>
                <input
                  type="date"
                  value={bulkClients.date_closed}
                  onChange={(e) => setBulkClients({ ...bulkClients, date_closed: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
                <p className="text-xs text-gray-500 mt-1">
                  If set, all clients will have this date_closed. Otherwise defaults to today.
                </p>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                type="submit"
                disabled={bulkAddMutation.isPending}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {bulkAddMutation.isPending ? 'Adding...' : 'Add All Clients'}
              </button>
              <button
                type="button"
                onClick={() => setIsBulkAdding(false)}
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
                  Date Closed
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
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {client.date_closed
                      ? format(new Date(client.date_closed), 'MMM d, yyyy')
                      : '-'}
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
    </div>
  )
}

