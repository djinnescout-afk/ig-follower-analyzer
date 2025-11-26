'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pagesApi, outreachApi, Page, PageProfile, OutreachTracking } from '../lib/api'
import { CATEGORIES, CONTACT_METHODS, OUTREACH_STATUSES, PROMO_STATUSES, getPriorityTier, TIER_LABELS, TIER_COLORS } from '../lib/categories'
import { ChevronLeft, ChevronRight, Save, SkipForward } from 'lucide-react'

export default function CategorizeTab() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [formData, setFormData] = useState<any>({})
  const queryClient = useQueryClient()

  // Fetch uncategorized pages
  const { data: pages, isLoading: pagesLoading } = useQuery({
    queryKey: ['pages', 'uncategorized'],
    queryFn: async () => {
      const response = await pagesApi.list({ 
        categorized: false, 
        min_client_count: 1,
        limit: 10000 
      })
      
      // Sort by priority tier, then by client_count, then by follower_count
      const sorted = response.data.sort((a, b) => {
        const tierA = getPriorityTier(a.ig_username, a.full_name, a.client_count)
        const tierB = getPriorityTier(b.ig_username, b.full_name, b.client_count)
        
        if (tierA !== tierB) return tierA - tierB // Lower tier number = higher priority
        if (a.client_count !== b.client_count) return b.client_count - a.client_count
        return b.follower_count - a.follower_count
      })
      
      return sorted
    },
  })

  const currentPage = pages?.[currentIndex]

  // Fetch profile for current page
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ['page-profile', currentPage?.id],
    queryFn: async () => {
      if (!currentPage) return null
      try {
        const response = await pagesApi.getProfile(currentPage.id)
        return response.data
      } catch (error) {
        return null
      }
    },
    enabled: !!currentPage,
  })

  // Fetch outreach tracking
  const { data: outreach } = useQuery({
    queryKey: ['outreach', currentPage?.id],
    queryFn: async () => {
      if (!currentPage) return null
      try {
        const response = await outreachApi.get(currentPage.id)
        return response.data
      } catch (error) {
        return null
      }
    },
    enabled: !!currentPage,
  })

  // Initialize form data when page changes
  useEffect(() => {
    if (currentPage) {
      setFormData({
        category: currentPage.category || '',
        manual_promo_status: currentPage.manual_promo_status || '',
        known_contact_methods: currentPage.known_contact_methods || [],
        successful_contact_method: currentPage.successful_contact_method || '',
        current_main_contact_method: currentPage.current_main_contact_method || '',
        ig_account_for_dm: currentPage.ig_account_for_dm || '',
        promo_price: currentPage.promo_price || '',
        website_url: currentPage.website_url || '',
        va_notes: currentPage.va_notes || '',
        outreach_status: outreach?.status || 'not_contacted',
        date_contacted: outreach?.date_contacted ? new Date(outreach.date_contacted).toISOString().split('T')[0] : '',
        follow_up_date: outreach?.follow_up_date ? new Date(outreach.follow_up_date).toISOString().split('T')[0] : '',
        outreach_notes: outreach?.notes || '',
      })
    }
  }, [currentPage, outreach])

  // Update page mutation
  const updatePageMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!currentPage) return
      await pagesApi.update(currentPage.id, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pages'] })
    },
  })

  // Update outreach mutation
  const updateOutreachMutation = useMutation({
    mutationFn: async (data: any) => {
      if (!currentPage) return
      if (outreach) {
        await outreachApi.update(currentPage.id, data)
      } else {
        await outreachApi.create({ page_id: currentPage.id, ...data })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outreach'] })
    },
  })

  const handleSaveAndNext = async () => {
    try {
      // Extract page fields
      const pageData = {
        category: formData.category || null,
        manual_promo_status: formData.manual_promo_status || null,
        known_contact_methods: formData.known_contact_methods.length > 0 ? formData.known_contact_methods : null,
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
        date_contacted: formData.date_contacted ? new Date(formData.date_contacted).toISOString() : null,
        follow_up_date: formData.follow_up_date ? new Date(formData.follow_up_date).toISOString() : null,
        notes: formData.outreach_notes || null,
      }

      await Promise.all([
        updatePageMutation.mutateAsync(pageData),
        updateOutreachMutation.mutateAsync(outreachData),
      ])

      // Move to next page
      if (currentIndex < (pages?.length || 0) - 1) {
        setCurrentIndex(currentIndex + 1)
      }
    } catch (error) {
      console.error('Error saving:', error)
      alert('Failed to save. Please try again.')
    }
  }

  const handleSkip = () => {
    if (currentIndex < (pages?.length || 0) - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  if (pagesLoading) {
    return <div className="text-center py-8">Loading uncategorized pages...</div>
  }

  if (!pages || pages.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">🎉 All Done!</h2>
        <p className="text-gray-600">No uncategorized pages found.</p>
      </div>
    )
  }

  if (!currentPage) {
    return <div className="text-center py-8">No page selected</div>
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-lg font-semibold">
            Page {currentIndex + 1} of {pages.length}
          </span>
          <div className="space-x-2">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center gap-2"
            >
              <ChevronLeft size={16} /> Previous
            </button>
            <button
              onClick={handleSkip}
              disabled={currentIndex >= pages.length - 1}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed rounded flex items-center gap-2"
            >
              Skip <SkipForward size={16} />
            </button>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${((currentIndex + 1) / pages.length) * 100}%` }}
          />
        </div>
        {/* Priority Tier Badge */}
        {currentPage && (
          <div className={`px-4 py-2 rounded-lg border-2 font-semibold text-sm ${TIER_COLORS[getPriorityTier(currentPage.ig_username, currentPage.full_name, currentPage.client_count) as keyof typeof TIER_COLORS]}`}>
            {TIER_LABELS[getPriorityTier(currentPage.ig_username, currentPage.full_name, currentPage.client_count) as keyof typeof TIER_LABELS]}
          </div>
        )}
      </div>

      {/* Page Display */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Profile & Posts */}
        <div className="space-y-6">
          {/* Profile Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex gap-4">
              {/* Profile Pic */}
              <div className="flex-shrink-0">
                {profile?.profile_pic_base64 ? (
                  <img
                    src={`data:${profile.profile_pic_mime_type};base64,${profile.profile_pic_base64}`}
                    alt={currentPage.ig_username}
                    className="w-24 h-24 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-full bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-400">No pic</span>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1">
                <h2 className="text-2xl font-bold">@{currentPage.ig_username}</h2>
                <p className="text-gray-600">{currentPage.full_name || 'N/A'}</p>
                <div className="mt-2 flex gap-4 text-sm text-gray-600">
                  <span>{currentPage.follower_count ? currentPage.follower_count.toLocaleString() : '0'} followers</span>
                  <span>{currentPage.client_count} client{currentPage.client_count !== 1 ? 's' : ''}</span>
                  {currentPage.is_verified && <span className="text-blue-600">✓ Verified</span>}
                </div>
                <a
                  href={`https://instagram.com/${currentPage.ig_username}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-sm mt-2 inline-block"
                >
                  View on Instagram →
                </a>
              </div>
            </div>

            {/* Bio */}
            {profile?.bio && (
              <div className="mt-4 pt-4 border-t">
                <h3 className="font-semibold mb-2">Bio</h3>
                <p className="text-sm whitespace-pre-wrap">{profile.bio}</p>
              </div>
            )}
          </div>

          {/* Recent Posts */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="font-semibold mb-4">Recent Posts</h3>
            {profileLoading ? (
              <div className="text-center py-8 text-gray-500">Loading posts...</div>
            ) : profile?.posts && profile.posts.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {profile.posts.slice(0, 9).map((post: any, idx: number) => (
                  <div key={idx} className="aspect-square bg-gray-100 rounded overflow-hidden">
                    {post.images && post.images[0] ? (
                      <img
                        src={`data:${post.images[0].mime_type};base64,${post.images[0].image_base64}`}
                        alt="Post"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
                        No image
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No posts scraped yet. Run profile scraper first.
              </div>
            )}
          </div>
        </div>

        {/* Right: Categorization Form */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-semibold mb-6">Categorization</h3>

            {/* Category */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                value={formData.category || ''}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select a category...</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Promo Status */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Promo Status
              </label>
              <select
                value={formData.manual_promo_status || ''}
                onChange={(e) => setFormData({ ...formData, manual_promo_status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select status...</option>
                {PROMO_STATUSES.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Contact Methods */}
            <div className="mb-4">
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
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Successful Contact Method
              </label>
              <select
                value={formData.successful_contact_method || ''}
                onChange={(e) =>
                  setFormData({ ...formData, successful_contact_method: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Main Contact Method
              </label>
              <select
                value={formData.current_main_contact_method || ''}
                onChange={(e) =>
                  setFormData({ ...formData, current_main_contact_method: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              <div className="mb-4">
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {/* Promo Price */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Promo Price ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.promo_price || ''}
                onChange={(e) => setFormData({ ...formData, promo_price: e.target.value })}
                placeholder="0.00"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Website URL */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Website URL
              </label>
              <input
                type="url"
                value={formData.website_url || ''}
                onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                placeholder="https://example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Outreach Status */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Outreach Status
              </label>
              <select
                value={formData.outreach_status || 'not_contacted'}
                onChange={(e) =>
                  setFormData({ ...formData, outreach_status: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {OUTREACH_STATUSES.map((status) => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Date Contacted */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date Contacted
              </label>
              <input
                type="date"
                value={formData.date_contacted || ''}
                onChange={(e) =>
                  setFormData({ ...formData, date_contacted: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Follow-up Date */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Follow-up Date
              </label>
              <input
                type="date"
                value={formData.follow_up_date || ''}
                onChange={(e) =>
                  setFormData({ ...formData, follow_up_date: e.target.value })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* VA Notes */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                VA Notes
              </label>
              <textarea
                value={formData.va_notes || ''}
                onChange={(e) => setFormData({ ...formData, va_notes: e.target.value })}
                rows={3}
                placeholder="Any additional notes..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Outreach Notes */}
            <div className="mb-6">
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
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Save Button */}
            <button
              onClick={handleSaveAndNext}
              disabled={!formData.category || updatePageMutation.isPending || updateOutreachMutation.isPending}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center justify-center gap-2"
            >
              <Save size={20} />
              {updatePageMutation.isPending || updateOutreachMutation.isPending
                ? 'Saving...'
                : currentIndex < pages.length - 1
                ? 'Save & Next'
                : 'Save & Finish'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

