'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { pagesApi } from '../lib/api'
import { CheckCircle, Users, Eye } from 'lucide-react'

export default function PagesTab() {
  const [minClientCount, setMinClientCount] = useState(2)
  const [selectedPage, setSelectedPage] = useState<string | null>(null)

  // Fetch pages
  const { data: pages, isLoading } = useQuery({
    queryKey: ['pages', minClientCount],
    queryFn: async () => {
      const response = await pagesApi.list({ min_client_count: minClientCount })
      return response.data
    },
  })

  // Fetch selected page profile
  const { data: profile } = useQuery({
    queryKey: ['page-profile', selectedPage],
    queryFn: async () => {
      if (!selectedPage) return null
      const response = await pagesApi.getProfile(selectedPage)
      return response.data
    },
    enabled: !!selectedPage,
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading pages...</div>
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">
            Minimum Clients Following:
          </label>
          <input
            type="number"
            min="1"
            value={minClientCount}
            onChange={(e) => setMinClientCount(parseInt(e.target.value) || 1)}
            className="w-24 px-3 py-2 border border-gray-300 rounded-md"
          />
          <span className="text-sm text-gray-600">
            Showing pages followed by {minClientCount}+ clients
          </span>
        </div>
      </div>

      {/* Pages Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pages List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900">
              Pages ({pages?.length || 0})
            </h2>
          </div>
          <div className="divide-y max-h-[600px] overflow-y-auto">
            {pages?.map((page) => (
              <div
                key={page.id}
                onClick={() => setSelectedPage(page.id)}
                className={`p-4 cursor-pointer hover:bg-gray-50 ${
                  selectedPage === page.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        @{page.ig_username}
                      </span>
                      {page.is_verified && (
                        <CheckCircle size={16} className="text-blue-500" />
                      )}
                    </div>
                    {page.full_name && (
                      <p className="text-sm text-gray-600 mt-1">{page.full_name}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Users size={14} />
                        {page.follower_count.toLocaleString()} followers
                      </span>
                      <span className="font-medium text-blue-600">
                        {page.client_count} client{page.client_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>
                  <button className="text-blue-600 hover:text-blue-800">
                    <Eye size={18} />
                  </button>
                </div>
              </div>
            ))}

            {pages?.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No pages found. Scrape client following lists first!
              </div>
            )}
          </div>
        </div>

        {/* Page Details */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Page Details</h2>
          </div>
          <div className="p-6">
            {!selectedPage && (
              <div className="text-center py-12 text-gray-500">
                Select a page to view details
              </div>
            )}

            {selectedPage && profile && (
              <div className="space-y-4">
                {/* Profile Picture */}
                {profile.profile_pic_base64 && (
                  <div className="flex justify-center">
                    <img
                      src={`data:${profile.profile_pic_mime_type};base64,${profile.profile_pic_base64}`}
                      alt="Profile"
                      className="w-32 h-32 rounded-full object-cover"
                    />
                  </div>
                )}

                {/* Bio */}
                {profile.bio && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Bio</h3>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {profile.bio}
                    </p>
                  </div>
                )}

                {/* Contact Info */}
                {profile.contact_email && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Contact</h3>
                    <a
                      href={`mailto:${profile.contact_email}`}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {profile.contact_email}
                    </a>
                  </div>
                )}

                {/* Promo Status */}
                {profile.promo_status && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Promo Status</h3>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm ${
                        profile.promo_status === 'warm'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {profile.promo_status}
                    </span>
                    {profile.promo_indicators && profile.promo_indicators.length > 0 && (
                      <ul className="mt-2 text-sm text-gray-600 list-disc list-inside">
                        {profile.promo_indicators.map((indicator, idx) => (
                          <li key={idx}>{indicator}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Recent Posts */}
                {profile.posts && profile.posts.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Recent Posts</h3>
                    <div className="grid grid-cols-3 gap-2">
                      {profile.posts.slice(0, 9).map((post: any, idx) => (
                        <div key={idx} className="aspect-square bg-gray-100 rounded">
                          {post.images && post.images[0] && (
                            <img
                              src={`data:${post.images[0].mime_type};base64,${post.images[0].image_base64}`}
                              alt="Post"
                              className="w-full h-full object-cover rounded"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {selectedPage && !profile && (
              <div className="text-center py-12 text-gray-500">
                Profile not scraped yet. Trigger a profile scrape to see details.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

