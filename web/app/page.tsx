'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { clientsApi, pagesApi, scrapesApi } from './lib/api'
import { useAuth } from './contexts/AuthContext'
import { AuthGuard } from './components/AuthGuard'
import ClientsTab from './components/ClientsTab'
import CategorizeTab from './components/CategorizeTab'
import EditPageTab from './components/EditPageTab'
import ViewCategorizedTab from './components/ViewCategorizedTab'
import PagesTab from './components/PagesTab'
import ScrapesTab from './components/ScrapesTab'
import AdminTab from './components/AdminTab'

function DashboardContent() {
  const [activeTab, setActiveTab] = useState<'clients' | 'categorize' | 'edit' | 'view-categorized' | 'pages' | 'scrapes' | 'admin'>('clients')
  const { user, signOut } = useAuth()

  const handleSignOut = async () => {
    await signOut()
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                IG Follower Analyzer
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                VA Dashboard - Add clients, scrape profiles, categorize pages, and track outreach
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 overflow-x-auto">
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
              onClick={() => setActiveTab('categorize')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'categorize'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Categorize
            </button>
            <button
              onClick={() => setActiveTab('edit')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'edit'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Edit Page
            </button>
            <button
              onClick={() => setActiveTab('view-categorized')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'view-categorized'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              View Categorized
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
              All Pages
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
            <button
              onClick={() => setActiveTab('admin')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === 'admin'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              Admin
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="mt-6 pb-12">
          {activeTab === 'clients' && <ClientsTab />}
          {activeTab === 'categorize' && <CategorizeTab />}
          {activeTab === 'edit' && <EditPageTab />}
          {activeTab === 'view-categorized' && <ViewCategorizedTab />}
          {activeTab === 'pages' && <PagesTab />}
          {activeTab === 'scrapes' && <ScrapesTab />}
          {activeTab === 'admin' && <AdminTab />}
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  )
}

