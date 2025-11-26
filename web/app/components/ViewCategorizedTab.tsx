'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { pagesApi, Page } from '../lib/api'
import { CATEGORIES } from '../lib/categories'
import { Users, DollarSign, Phone, Calendar } from 'lucide-react'

export default function ViewCategorizedTab() {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(0)
  const [goToPageInput, setGoToPageInput] = useState('')
  const [allPages, setAllPages] = useState<Page[]>([])
  
  const pageSize = 100 // Display 100 pages at a time

  // Fetch ALL categorized pages for selected category
  const { data: fetchedPages, isLoading } = useQuery({
    queryKey: ['pages', 'categorized', selectedCategory],
    queryFn: async () => {
      if (!selectedCategory) return []
      
      try {
        const allFetched: Page[] = []
        let offset = 0
        const batchSize = 1000 // Fetch in batches of 1000

        while (true) {
          const response = await pagesApi.list({
            categorized: true,
            category: selectedCategory,
            limit: batchSize,
            offset: offset,
          })
          
          const batch = response.data || []
          allFetched.push(...batch)
          
          // Stop if we got less than batchSize (no more pages)
          if (batch.length < batchSize) {
            break
          }
          
          offset += batchSize
        }
        
        return allFetched
      } catch (error) {
        console.error('Error fetching categorized pages:', error)
        return []
      }
    },
    enabled: !!selectedCategory,
  })
  
  // Update allPages when fetch completes
  if (fetchedPages && fetchedPages !== allPages) {
    setAllPages(fetchedPages)
    setCurrentPage(0) // Reset to first page when category changes
  }
  
  // Paginate the allPages array client-side
  const totalPages = Math.ceil((allPages?.length || 0) / pageSize)
  const paginatedPages = allPages?.slice(currentPage * pageSize, (currentPage + 1) * pageSize) || []

  // Don't pre-count categories - too expensive for backend
  // Show counts after user selects a category
  const categoryCounts: Record<string, number> = {}

  return (
    <div className="space-y-6">
      {/* Category Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Select Category</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
          {CATEGORIES.map((category) => {
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
                <div className="font-medium text-sm">{category}</div>
                <div className="text-xs text-gray-500 mt-1">Click to view</div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Pages List */}
      {selectedCategory && (
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                {selectedCategory} ({allPages?.length || 0} total pages)
              </h2>
              
              {/* Pagination Controls */}
              {!isLoading && allPages && allPages.length > pageSize && (
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                    disabled={currentPage === 0}
                    className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ← Prev
                  </button>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-600">Page</span>
                    <input
                      type="number"
                      min="1"
                      max={totalPages}
                      value={goToPageInput || currentPage + 1}
                      onChange={(e) => setGoToPageInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && goToPageInput) {
                          const pageNum = parseInt(goToPageInput) - 1
                          if (pageNum >= 0 && pageNum < totalPages) {
                            setCurrentPage(pageNum)
                            setGoToPageInput('')
                          }
                        }
                      }}
                      onBlur={() => {
                        if (goToPageInput) {
                          const pageNum = parseInt(goToPageInput) - 1
                          if (pageNum >= 0 && pageNum < totalPages) {
                            setCurrentPage(pageNum)
                          }
                          setGoToPageInput('')
                        }
                      }}
                      className="w-16 px-2 py-1 border border-gray-300 rounded text-center text-sm"
                    />
                    <span className="text-sm text-gray-600">of {totalPages}</span>
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                    disabled={currentPage >= totalPages - 1}
                    className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next →
                  </button>
                </div>
              )}
            </div>
            
            {!isLoading && allPages && allPages.length > 0 && (
              <div className="mt-2 text-sm text-gray-500">
                Showing {currentPage * pageSize + 1}-{Math.min((currentPage + 1) * pageSize, allPages.length)} of {allPages.length}
              </div>
            )}
          </div>

          {isLoading ? (
            <div className="text-center py-12 text-gray-500">Loading pages...</div>
          ) : paginatedPages && paginatedPages.length > 0 ? (
            <div className="divide-y">
              {paginatedPages.map((page) => (
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


