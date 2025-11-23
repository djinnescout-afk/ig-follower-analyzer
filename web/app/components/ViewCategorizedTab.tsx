'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { pagesApi, Page } from '../lib/api'
import { CATEGORIES } from '../lib/categories'
import { useDebounce } from '../lib/hooks/useDebounce'

export default function ViewCategorizedTab() {
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(100)
  const [searchQuery, setSearchQuery] = useState('')
  
  // Debounce search query to reduce API calls (500ms delay)
  const debouncedSearch = useDebounce(searchQuery, 500)

  // Efficient category counts using SQL aggregation
  const { data: categoryCounts } = useQuery({
    queryKey: ['pages', 'category-counts'],
    queryFn: async () => {
      console.log('[ViewCategorized] Fetching category counts (efficient)...')
      const response = await pagesApi.getCategoryCounts()
      console.log('[ViewCategorized] Category counts:', response.data)
      return response.data
    },
    staleTime: 30000, // Cache for 30 seconds
    refetchOnMount: true,
  })

  // Get total count for selected category
  const { data: totalCountData } = useQuery({
    queryKey: ['pages', 'count', selectedCategory, debouncedSearch],
    queryFn: async () => {
      const response = await pagesApi.getCount({
        categorized: true,
        category: selectedCategory || undefined,
        search: debouncedSearch || undefined,
      })
      return response.data
    },
    enabled: !!selectedCategory,
  })

  const totalPages = Math.ceil((totalCountData?.count || 0) / pageSize)

  // Fetch paginated pages for selected category
  const { data: pages, isLoading } = useQuery({
    queryKey: ['pages', 'categorized', selectedCategory, page, pageSize, debouncedSearch],
    queryFn: async () => {
      console.log('[ViewCategorized] Fetching pages for category:', selectedCategory, 'page:', page, 'search:', debouncedSearch)
      const response = await pagesApi.list({
        categorized: true,
        category: selectedCategory || undefined,
        search: debouncedSearch || undefined,
        sort_by: 'client_count',
        order: 'desc',
        limit: pageSize,
        offset: page * pageSize,
      })
      console.log('[ViewCategorized] Response data:', response.data)
      console.log('[ViewCategorized] Found', response.data.length, 'pages')
      return response.data
    },
    enabled: !!selectedCategory,
  })

  // Reset to page 0 when category changes
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category)
    setPage(0)
  }

  // Reset to page 0 when search changes
  const handleSearchChange = (query: string) => {
    setSearchQuery(query)
    setPage(0)
  }

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
                onClick={() => handleCategoryChange(category)}
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

      {/* Pages Table */}
      {selectedCategory && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-6 border-b space-y-4">
            <h2 className="text-lg font-semibold">
              {selectedCategory} ({totalCountData?.count || 0} pages)
            </h2>
            {/* Search Box */}
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Search by username or name..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {searchQuery && (
                <button
                  onClick={() => handleSearchChange('')}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {isLoading ? (
            <div className="text-center py-12 text-gray-500">Loading pages...</div>
          ) : pages && pages.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-gray-50">
                  <tr className="border-b-2 border-gray-300">
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Handle
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Followers
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Clients
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Contact Methods
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Contact Details
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Price
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Notes
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                      Last Reviewed
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white">
                  {pages.map((page) => (
                    <tr key={page.id} className="border-b border-gray-200 hover:bg-gray-50">
                      {/* Name */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-sm font-medium text-gray-900">
                          {page.full_name || 'N/A'}
                        </div>
                      </td>

                      {/* Handle */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-sm text-gray-900">
                          @{page.ig_username}
                          {page.is_verified && (
                            <span className="ml-1 text-blue-600">✓</span>
                          )}
                        </div>
                      </td>

                      {/* Followers */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-sm text-gray-900">
                          {page.follower_count.toLocaleString()}
                        </div>
                      </td>

                      {/* Clients */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <span className="inline-flex px-2 py-1 text-xs font-bold rounded bg-blue-100 text-blue-800">
                          {page.client_count}
                        </span>
                      </td>

                      {/* Contact Methods */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-sm text-gray-900">
                          {page.known_contact_methods && page.known_contact_methods.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {page.known_contact_methods.map((method) => (
                                <span
                                  key={method}
                                  className="inline-block px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                                >
                                  {method}
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                          {page.current_main_contact_method && (
                            <div className="mt-1 text-xs text-blue-600 font-medium">
                              Main: {page.current_main_contact_method}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Contact Details */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-xs space-y-1">
                          {page.contact_email && (
                            <div>
                              📧 <a href={`mailto:${page.contact_email}`} className="text-blue-600 hover:underline">
                                {page.contact_email}
                              </a>
                            </div>
                          )}
                          {page.contact_phone && (
                            <div>
                              📞 <a href={`tel:${page.contact_phone}`} className="text-blue-600 hover:underline">
                                {page.contact_phone}
                              </a>
                            </div>
                          )}
                          {page.contact_whatsapp && (
                            <div>
                              💬 <a
                                href={`https://wa.me/${page.contact_whatsapp.replace(/[^0-9]/g, '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                {page.contact_whatsapp}
                              </a>
                            </div>
                          )}
                          {page.contact_telegram && (
                            <div>
                              ✈️ <a
                                href={`https://t.me/${page.contact_telegram.replace('@', '')}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                {page.contact_telegram}
                              </a>
                            </div>
                          )}
                          {page.contact_other && (
                            <div>📝 {page.contact_other}</div>
                          )}
                          {page.ig_account_for_dm && (
                            <div className="text-gray-600">
                              DM: {page.ig_account_for_dm}
                            </div>
                          )}
                          {page.website_url && (
                            <div>
                              🌐 <a
                                href={page.website_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                Website
                              </a>
                            </div>
                          )}
                          {!page.contact_email && !page.contact_phone && !page.contact_whatsapp && 
                           !page.contact_telegram && !page.contact_other && !page.ig_account_for_dm && 
                           !page.website_url && (
                            <span className="text-gray-400">—</span>
                          )}
                        </div>
                      </td>

                      {/* Price */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-sm text-gray-900">
                          {page.promo_price ? (
                            <span className="font-medium text-green-700">
                              ${page.promo_price.toLocaleString()}
                            </span>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </div>
                      </td>

                      {/* Notes */}
                      <td className="px-4 py-5 max-w-xs border-r border-gray-200">
                        <div className="text-xs text-gray-700">
                          {page.va_notes ? (
                            <div className="truncate max-w-xs" title={page.va_notes}>
                              {page.va_notes}
                            </div>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                          {page.last_scrape_status === 'failed' && (
                            <div className="mt-1 text-red-600 font-medium">
                              ⚠️ Scrape failed
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Last Reviewed */}
                      <td className="px-4 py-5 border-r border-gray-200">
                        <div className="text-xs text-gray-500">
                          {page.last_reviewed_at ? (
                            <>
                              <div>{new Date(page.last_reviewed_at).toLocaleDateString()}</div>
                              {page.last_reviewed_by && (
                                <div className="text-gray-400">{page.last_reviewed_by}</div>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-5">
                        <a
                          href={`https://instagram.com/${page.ig_username}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          View IG →
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No pages found in this category
            </div>
          )}

          {/* Pagination Controls */}
          {pages && pages.length > 0 && (
            <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-sm text-gray-700">
                  Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, totalCountData?.count || 0)} of {totalCountData?.count || 0} pages
                </div>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value))
                    setPage(0)
                  }}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={50}>50 per page</option>
                  <option value={100}>100 per page</option>
                  <option value={250}>250 per page</option>
                  <option value={500}>500 per page</option>
                </select>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => setPage(0)}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  First
                </button>
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 0}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <div className="px-3 py-1 text-sm">
                  Page {page + 1} of {totalPages}
                </div>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages - 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
                <button
                  onClick={() => setPage(totalPages - 1)}
                  disabled={page >= totalPages - 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Last
                </button>
              </div>
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


