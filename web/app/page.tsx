'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clientsApi, pagesApi, scrapesApi } from './lib/api'
import ClientsTab from './components/ClientsTab'
import PagesTab from './components/PagesTab'
import ScrapesTab from './components/ScrapesTab'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<'clients' | 'pages' | 'scrapes'>('clients')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            IG Follower Analyzer
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            VA Dashboard - Manage clients, scrape following lists, and categorize pages
          </p>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('clients')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'clients'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Clients
            </button>
            <button
              onClick={() => setActiveTab('pages')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'pages'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Pages
            </button>
            <button
              onClick={() => setActiveTab('scrapes')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'scrapes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Scrape Jobs
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6 pb-12">
          {activeTab === 'clients' && <ClientsTab />}
          {activeTab === 'pages' && <PagesTab />}
          {activeTab === 'scrapes' && <ScrapesTab />}
        </div>
      </div>
    </div>
  )
}

