'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pagesApi, outreachApi, Page } from '../lib/api'
import { CATEGORIES, CONTACT_METHODS, OUTREACH_STATUSES } from '../lib/categories'
import { Search, Save } from 'lucide-react'

export default function EditPageTab() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPageId, setSelectedPageId] = useState<string | null>(null)
  const [formData, setFormData] = useState<any>({})
  const queryClient = useQueryClient()

  // Fetch all pages
  const { data: pages, isLoading: pagesLoading } = useQuery({
    queryKey: ['pages', 'all'],
    queryFn: async () => {
      const response = await pagesApi.list({
        min_client_count: 1,
        limit: 10000,
      })
      return response.data
    },
  })

  // Filter pages by search query
  const filteredPages = pages?.filter((page) => {
    const query = searchQuery.toLowerCase()
    return (
      page.ig_username.toLowerCase().includes(query) ||
      page.full_name?.toLowerCase().includes(query)
    )
  })

  const selectedPage = pages?.find((p) => p.id === selectedPageId)

  // Fetch profile for selected page
  const { data: profile } = useQuery({
    queryKey: ['page-profile', selectedPageId],
    queryFn: async () => {
      if (!selectedPageId) return null
      try {
        const response = await pagesApi.getProfile(selectedPageId)
        return response.data
      } catch (error) {
        return null
      }
    },
    enabled: !!selectedPageId,
  })

  // Fetch outreach tracking
  const { data: outreach } = useQuery({
    queryKey: ['outreach', selectedPageId],
    queryFn: async () => {
      if (!selectedPageId) return null
      try {
        const response = await outreachApi.get(selectedPageId)
        return response.data
      } catch (error) {
        return null
      }
    },
    enabled: !!selectedPageId,
  })

  // Initialize form data when page changes
  useEffect(() => {
    if (selectedPage) {
      setFormData({
        category: selectedPage.category || '',
        known_contact_methods: selectedPage.known_contact_methods || [],
        successful_contact_method: selectedPage.successful_contact_method || '',
        current_main_contact_method: selectedPage.current_main_contact_method || '',
        ig_account_for_dm: selectedPage.ig_account_for_dm || '',
        promo_price: selectedPage.promo_price || '',
        website_url: selectedPage.website_url || '',
        va_notes: selectedPage.va_notes || '',
        outreach_status: outreach?.status || 'not_contacted',
        date_contacted: outreach?.date_contacted
          ? new Date(outreach.date_contacted).toISOString().split('T')[0]
          : '',
        follow_up_date: outreach?.follow_up_date
          ? new Date(outreach.follow_up_date).toISOString().split('T')[0]
          : '',
        outreach_notes: outreach?.notes || '',
      })
    }
  }, [selectedPage, outreach])

  // Update page mutation
  const updatePageMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!selectedPageId) return
      await pagesApi.update(selectedPageId, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
      alert('Page updated successfully!')
    },
  })

  // Update outreach mutation
  const updateOutreachMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!selectedPageId) return
      if (outreach) {
        await outreachApi.update(selectedPageId, data)
      } else {
        await outreachApi.create({ page_id: selectedPageId, ...data })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outreach'] })
    },
  })

  const handleSave = async () => {
    try {
      // Extract page fields
      const pageData = {
        category: formData.category || null,
        known_contact_methods:
          formData.known_contact_methods.length > 0
            ? formData.known_contact_methods
            : null,
        successful_contact_method: formData.successful_contact_method || null,
        current_main_contact_method: formData.current_main_contact_method || null,
        ig_account_for_dm: formData.ig_account_for_dm || null,
        promo_price: formData.promo_price ? parseFloat(formData.promo_price) : null,
        website_url: formData.website_url || null,
        va_notes: formData.va_notes || null,
        last_reviewed_by: 'VA', // TODO: Get from auth
        last_reviewed_at: new Date().toISOString(),
      }

      // Extract outreach fields
      const outreachData = {
        status: formData.outreach_status || 'not_contacted',
        date_contacted: formData.date_contacted
          ? new Date(formData.date_contacted).toISOString()
          : null,
        follow_up_date: formData.follow_up_date
          ? new Date(formData.follow_up_date).toISOString()
          : null,
        notes: formData.outreach_notes || null,
      }

      await Promise.all([
        updatePageMutation.mutateAsync(pageData),
        updateOutreachMutation.mutateAsync(outreachData),
      ])
    } catch (error) {
      console.error('Error saving:', error)
      alert('Failed to save. Please try again.')
    }
  }

  if (pagesLoading) {
    return <div className="text-center py-8">Loading pages...</div>
  }

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-4">
          <Search size={20} className="text-gray-400" />
          <input
            type="text"
            placeholder="Search by username or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-600">
            {filteredPages?.length || 0} pages found
          </span>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Search Results */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h2 className="font-semibold">Search Results</h2>
            </div>
            <div className="divide-y max-h-[600px] overflow-y-auto">
              {filteredPages && filteredPages.length > 0 ? (
                filteredPages.map((page) => (
                  <div
                    key={page.id}
                    onClick={() => setSelectedPageId(page.id)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 ${
                      selectedPageId === page.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="font-medium">@{page.ig_username}</div>
                    {page.full_name && (
                      <div className="text-sm text-gray-600">{page.full_name}</div>
                    )}
                    <div className="text-xs text-gray-500 mt-1">
                      {page.client_count} client{page.client_count !== 1 ? 's' : ''} •{' '}
                      {page.category || 'Uncategorized'}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-gray-500">
                  {searchQuery ? 'No pages found' : 'Enter a search query'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Edit Form */}
        <div className="lg:col-span-2">
          {!selectedPage ? (
            <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
              Search and select a page to edit
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-bold">@{selectedPage.ig_username}</h2>
                <p className="text-gray-600">{selectedPage.full_name || 'N/A'}</p>
                <div className="mt-2 text-sm text-gray-500">
                  {selectedPage.follower_count.toLocaleString()} followers •{' '}
                  {selectedPage.client_count} client{selectedPage.client_count !== 1 ? 's' : ''}
                </div>
              </div>

              {/* Same form as CategorizeTab */}
              <div className="space-y-4">
                {/* Category */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Category
                  </label>
                  <select
                    value={formData.category || ''}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select a category...</option>
                    {CATEGORIES.map((cat) => (
                      <option key={cat} value={cat}>
                        {cat}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Contact Methods */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Known Contact Methods
                  </label>
                  <div className="space-y-2">
                    {CONTACT_METHODS.map((method) => (
                      <label key={method} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.known_contact_methods?.includes(method) || false}
                          onChange={(e) => {
                            const methods = formData.known_contact_methods || []
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                known_contact_methods: [...methods, method],
                              })
                            } else {
                              setFormData({
                                ...formData,
                                known_contact_methods: methods.filter((m: string) => m !== method),
                              })
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm">{method}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Successful Contact Method */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Successful Contact Method
                  </label>
                  <select
                    value={formData.successful_contact_method || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, successful_contact_method: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">None yet</option>
                    {CONTACT_METHODS.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Current Main Contact Method */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Current Main Contact Method
                  </label>
                  <select
                    value={formData.current_main_contact_method || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, current_main_contact_method: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    <option value="">Select...</option>
                    {CONTACT_METHODS.map((method) => (
                      <option key={method} value={method}>
                        {method}
                      </option>
                    ))}
                  </select>
                </div>

                {/* IG Account for DM */}
                {(formData.known_contact_methods?.includes('IG DM') ||
                  formData.current_main_contact_method === 'IG DM') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Which IG Account Did You Use for DM?
                    </label>
                    <input
                      type="text"
                      value={formData.ig_account_for_dm || ''}
                      onChange={(e) =>
                        setFormData({ ...formData, ig_account_for_dm: e.target.value })
                      }
                      placeholder="e.g., @your_account"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                )}

                {/* Promo Price */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Promo Price ($)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.promo_price || ''}
                    onChange={(e) => setFormData({ ...formData, promo_price: e.target.value })}
                    placeholder="0.00"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Website URL */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Website URL
                  </label>
                  <input
                    type="url"
                    value={formData.website_url || ''}
                    onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                    placeholder="https://example.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Outreach Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Outreach Status
                  </label>
                  <select
                    value={formData.outreach_status || 'not_contacted'}
                    onChange={(e) =>
                      setFormData({ ...formData, outreach_status: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  >
                    {OUTREACH_STATUSES.map((status) => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Date Contacted */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Date Contacted
                  </label>
                  <input
                    type="date"
                    value={formData.date_contacted || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, date_contacted: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Follow-up Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Date
                  </label>
                  <input
                    type="date"
                    value={formData.follow_up_date || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, follow_up_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* VA Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    VA Notes
                  </label>
                  <textarea
                    value={formData.va_notes || ''}
                    onChange={(e) => setFormData({ ...formData, va_notes: e.target.value })}
                    rows={3}
                    placeholder="Any additional notes..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Outreach Notes */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Outreach Notes
                  </label>
                  <textarea
                    value={formData.outreach_notes || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, outreach_notes: e.target.value })
                    }
                    rows={3}
                    placeholder="Notes about outreach attempts..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Save Button */}
                <button
                  onClick={handleSave}
                  disabled={updatePageMutation.isPending || updateOutreachMutation.isPending}
                  className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2"
                >
                  <Save size={20} />
                  {updatePageMutation.isPending || updateOutreachMutation.isPending
                    ? 'Saving...'
                    : 'Save Changes'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

