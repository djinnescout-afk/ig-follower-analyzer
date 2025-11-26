'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { scrapesApi, clientsApi, pagesApi } from '../lib/api'
import { format } from 'date-fns'
import { CheckCircle, XCircle, Clock, Loader, ChevronDown, ChevronUp } from 'lucide-react'

export default function ScrapesTab() {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set())

  const toggleExpanded = (jobId: string) => {
    const newExpanded = new Set(expandedJobs)
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId)
    } else {
      newExpanded.add(jobId)
    }
    setExpandedJobs(newExpanded)
  }
  // Fetch scrape runs
  const { data: scrapes, isLoading } = useQuery({
    queryKey: ['scrapes'],
    queryFn: async () => {
      const response = await scrapesApi.list({ limit: 50 })
      return response.data
    },
    refetchInterval: 5000, // Refresh every 5 seconds to show real-time status
  })

  // Fetch all clients for lookups
  const { data: clients } = useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await clientsApi.list()
      return response.data
    },
  })

  // Fetch all pages for lookups (only when needed)
  const { data: pages } = useQuery({
    queryKey: ['pages', 'all'],
    queryFn: async () => {
      const response = await pagesApi.list({ limit: 10000 })
      return response.data
    },
    enabled: !!scrapes?.some(s => s.page_ids && s.page_ids.length > 0),
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading scrape jobs...</div>
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={20} className="text-green-500" />
      case 'failed':
        return <XCircle size={20} className="text-red-500" />
      case 'processing':
        return <Loader size={20} className="text-blue-500 animate-spin" />
      case 'pending':
        return <Clock size={20} className="text-gray-400" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-3 py-1 rounded-full text-xs font-medium'
    switch (status) {
      case 'completed':
        return `${baseClasses} bg-green-100 text-green-800`
      case 'failed':
        return `${baseClasses} bg-red-100 text-red-800`
      case 'processing':
        return `${baseClasses} bg-blue-100 text-blue-800`
      case 'pending':
        return `${baseClasses} bg-gray-100 text-gray-800`
      default:
        return baseClasses
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Scrape Jobs ({scrapes?.length || 0})
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Automatically refreshing every 5 seconds
          </p>
        </div>

        <div className="divide-y">
          {scrapes?.map((scrape) => (
            <div key={scrape.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-start gap-4">
                <div className="mt-1">{getStatusIcon(scrape.status)}</div>

                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-gray-900">
                      {scrape.scrape_type === 'client_following'
                        ? 'Client Following Scrape'
                        : 'Profile Scrape'}
                    </span>
                    <span className={getStatusBadge(scrape.status)}>
                      {scrape.status}
                    </span>
                  </div>

                  <div className="mt-2 text-sm text-gray-600 space-y-1">
                    <p>Created: {format(new Date(scrape.created_at), 'MMM d, yyyy HH:mm:ss')}</p>
                    {scrape.started_at && (
                      <p>Started: {format(new Date(scrape.started_at), 'MMM d, yyyy HH:mm:ss')}</p>
                    )}
                    {scrape.completed_at && (
                      <p>
                        Completed: {format(new Date(scrape.completed_at), 'MMM d, yyyy HH:mm:ss')}
                      </p>
                    )}
                    
                    {/* Show which clients/pages were attempted */}
                    {scrape.client_id && clients && (
                      <p>
                        <span className="font-medium">Client:</span>{' '}
                        {clients.find(c => c.id === scrape.client_id)?.name || scrape.client_id}
                        {' (@'}
                        {clients.find(c => c.id === scrape.client_id)?.ig_username || 'unknown'}
                        {')'}
                      </p>
                    )}
                    {scrape.page_ids && scrape.page_ids.length > 0 && (
                      <div>
                        <p><span className="font-medium">Pages attempted:</span> {scrape.page_ids.length}</p>
                        {pages && expandedJobs.has(scrape.id) && (
                          <ul className="mt-1 ml-4 text-xs space-y-0.5">
                            {scrape.page_ids.slice(0, 10).map((pageId: string) => {
                              const page = pages.find(p => p.id === pageId)
                              return (
                                <li key={pageId}>
                                  • @{page?.ig_username || pageId}
                                </li>
                              )
                            })}
                            {scrape.page_ids.length > 10 && (
                              <li className="text-gray-500">... and {scrape.page_ids.length - 10} more</li>
                            )}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Results */}
                  {scrape.result && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-md">
                      <button
                        onClick={() => toggleExpanded(scrape.id)}
                        className="flex items-center gap-2 text-sm font-medium text-gray-900 w-full hover:text-blue-600"
                      >
                        {expandedJobs.has(scrape.id) ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                        <span>Results & Details</span>
                      </button>

                      {expandedJobs.has(scrape.id) && (
                        <div className="mt-3 space-y-3">
                          {scrape.status === 'completed' && scrape.scrape_type === 'client_following' && (
                        <div className="text-sm text-gray-700 space-y-1">
                          <p>
                            Accounts scraped: {scrape.result.accounts_scraped?.toLocaleString() || 0}
                          </p>
                          {scrape.result.expected_count && (
                            <p>
                              Expected: {scrape.result.expected_count.toLocaleString()}
                            </p>
                          )}
                          {scrape.result.coverage_percent && (
                            <p className="flex items-center gap-2">
                              Coverage:{' '}
                              <span
                                className={`font-medium ${
                                  scrape.result.coverage_percent >= 95
                                    ? 'text-green-600'
                                    : scrape.result.coverage_percent >= 90
                                    ? 'text-yellow-600'
                                    : 'text-red-600'
                                }`}
                              >
                                {scrape.result.coverage_percent.toFixed(1)}%
                              </span>
                              {scrape.result.coverage_percent >= 95 && (
                                <span className="text-green-600 text-xs">✅ Excellent</span>
                              )}
                              {scrape.result.coverage_percent < 90 && (
                                <span className="text-red-600 text-xs">⚠️ Poor</span>
                              )}
                            </p>
                          )}
                          {scrape.result.failed_usernames &&
                            scrape.result.failed_usernames.length > 0 && (
                              <p className="text-red-600">
                                Failed: {scrape.result.failed_usernames.join(', ')}
                              </p>
                            )}
                        </div>
                      )}

                      {scrape.status === 'completed' && scrape.scrape_type === 'profile_scrape' && (
                        <div className="text-sm text-gray-700 space-y-1">
                          <p>
                            Success: {scrape.result.success_count || 0} / {scrape.result.total_pages || 0}
                          </p>
                          {scrape.result.failed_usernames &&
                            scrape.result.failed_usernames.length > 0 && (
                              <p className="text-red-600">
                                Failed: {scrape.result.failed_usernames.join(', ')}
                              </p>
                            )}
                        </div>
                      )}

                          {scrape.status === 'failed' && scrape.result.error && (
                            <div className="bg-red-50 border border-red-200 rounded p-3">
                              <h5 className="text-sm font-medium text-red-900 mb-2">Error Details:</h5>
                              <pre className="text-xs text-red-700 whitespace-pre-wrap font-mono overflow-x-auto">
                                {typeof scrape.result.error === 'string' 
                                  ? scrape.result.error 
                                  : JSON.stringify(scrape.result.error, null, 2)}
                              </pre>
                            </div>
                          )}

                          {/* Show full result object for debugging */}
                          <details className="mt-2">
                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                              Raw result data (for debugging)
                            </summary>
                            <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">
                              {JSON.stringify(scrape.result, null, 2)}
                            </pre>
                          </details>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {scrapes?.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No scrape jobs yet. Start scraping client following lists to see jobs here!
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

