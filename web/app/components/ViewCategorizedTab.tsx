'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { pagesApi, Page } from '../lib/api'
import { CATEGORIES } from '../lib/categories'
import { Users, DollarSign, Phone, Calendar } from 'lucide-react'

export default function ViewCategorizedTab() {
  const [selectedCategory, setSelectedCategory] = useState<string>('')

  // Fetch categorized pages for selected category with batch loading
  const { data: pages, isLoading } = useQuery({
    queryKey: ['pages', 'categorized', selectedCategory],
    queryFn: async () => {
      const allPages: Page[] = []
      let offset = 0
      const limit = 5000

      while (true) {
        const response = await pagesApi.list({
          categorized: true,
          category: selectedCategory || undefined,
          limit: limit,
          offset: offset,
        })
        
        const batch = response.data || []
        allPages.push(...batch)

        if (batch.length < limit) {
          break
        }
        offset += limit
      }

      return allPages
    },
    enabled: !!selectedCategory,
  })

  // Count pages by category with batch loading
  const { data: categoryCounts } = useQuery({
    queryKey: ['pages', 'category-counts'],
    queryFn: async () => {
      const counts: Record<string, number> = {}
      
      // Fetch pages for each category with batch loading
      await Promise.all(
        CATEGORIES.map(async (category) => {
          let total = 0
          let offset = 0
          const limit = 5000

          while (true) {
            const response = await pagesApi.list({
              categorized: true,
              category,
              limit: limit,
              offset: offset,
            })
            
            const batch = response.data || []
            total += batch.length

            if (batch.length < limit) {
              break
            }
            offset += limit
          }

          counts[category] = total
        })
      )
      
      return counts
    },
  })

  return (
    <div className="space-y-6">
      {/* Category Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Select Category</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {CATEGORIES.map((category) => {
            const count = categoryCounts?.[category] || 0
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedCategory === category
                    ? 'border-blue-600 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
              >
                <div className="font-medium text-sm mb-1">{category}</div>
                <div className="text-2xl font-bold text-gray-700">{count}</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Pages List */}
      {selectedCategory && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold">
              {selectedCategory} ({pages?.length || 0} pages)
            </h2>
          </div>

          {isLoading ? (
            <div className="text-center py-12 text-gray-500">Loading pages...</div>
          ) : pages && pages.length > 0 ? (
            <div className="divide-y">
              {pages.map((page) => (
                <div key={page.id} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex gap-6">
                    {/* Left: Basic Info */}
                    <div className="flex-1">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-lg font-semibold">
                            @{page.ig_username}
                            {page.is_verified && (
                              <span className="ml-2 text-blue-600 text-sm">✓</span>
                            )}
                          </h3>
                          <p className="text-gray-600">{page.full_name || 'N/A'}</p>
                        </div>
                        <a
                          href={`https://instagram.com/${page.ig_username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-sm"
                        >
                          View on IG →
                        </a>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div className="flex items-center gap-2 text-gray-700">
                          <Users size={16} />
                          <span className="font-semibold">
                            {page.follower_count ? page.follower_count.toLocaleString() : '0'} followers
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Users size={16} />
                          <span className="font-medium text-blue-600">
                            {page.client_count} client{page.client_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                        {page.promo_price && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <DollarSign size={16} />
                            <span>${page.promo_price.toLocaleString()}</span>
                          </div>
                        )}
                        {page.current_main_contact_method && (
                          <div className="flex items-center gap-2 text-gray-600">
                            <Phone size={16} />
                            <span>{page.current_main_contact_method}</span>
                          </div>
                        )}
                      </div>

                      {/* Contact Info */}
                      {(page.known_contact_methods && page.known_contact_methods.length > 0) && (
                        <div className="mt-3 text-sm text-gray-600">
                          <span className="font-medium">Known methods:</span>{' '}
                          {page.known_contact_methods.join(', ')}
                        </div>
                      )}

                      {page.ig_account_for_dm && (
                        <div className="mt-2 text-sm text-gray-600">
                          <span className="font-medium">IG DM from:</span> {page.ig_account_for_dm}
                        </div>
                      )}

                      {page.website_url && (
                        <div className="mt-2">
                          <a
                            href={page.website_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline"
                          >
                            🌐 Website
                          </a>
                        </div>
                      )}

                      {/* VA Notes */}
                      {page.va_notes && (
                        <div className="mt-3 p-3 bg-yellow-50 rounded text-sm">
                          <span className="font-medium">Notes:</span> {page.va_notes}
                        </div>
                      )}

                      {/* Last Reviewed */}
                      {page.last_reviewed_at && (
                        <div className="mt-3 text-xs text-gray-500 flex items-center gap-2">
                          <Calendar size={14} />
                          <span>
                            Reviewed {new Date(page.last_reviewed_at).toLocaleDateString()}
                            {page.last_reviewed_by && ` by ${page.last_reviewed_by}`}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No pages found in this category
            </div>
          )}
        </div>
      )}

      {!selectedCategory && (
        <div className="text-center py-12 text-gray-500">
          Select a category above to view pages
        </div>
      )}
    </div>
  )
}


