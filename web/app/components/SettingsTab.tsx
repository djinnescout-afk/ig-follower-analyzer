'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../lib/api'
import { CATEGORY_SET_1, CATEGORY_SET_2 } from '../lib/categories'
import { Save, Check } from 'lucide-react'

export default function SettingsTab() {
  const queryClient = useQueryClient()
  const [selectedSet, setSelectedSet] = useState<'option1' | 'option2' | null>(null)
  const [showSet1, setShowSet1] = useState(false)
  const [showSet2, setShowSet2] = useState(false)

  // Fetch current preferences
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['settings', 'preferences'],
    queryFn: async () => {
      const response = await settingsApi.getPreferences()
      return response.data
    },
  })

  // Initialize selectedSet when preferences load
  useEffect(() => {
    if (preferences && selectedSet === null) {
      setSelectedSet(preferences.category_set)
    }
  }, [preferences, selectedSet])

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async (categorySet: 'option1' | 'option2') => {
      const response = await settingsApi.updatePreferences({ category_set: categorySet })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'preferences'] })
      queryClient.invalidateQueries({ queryKey: ['pages'] }) // Refresh pages to show new categories
    },
  })

  const handleSave = async () => {
    if (selectedSet) {
      await updateMutation.mutateAsync(selectedSet)
    }
  }

  const currentSet = preferences?.category_set || 'option1'
  const displaySet = selectedSet || currentSet

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading settings...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Category Set Preferences</h2>
        
        <div className="space-y-4 mb-6">
          <div className="flex items-center gap-4">
            <input
              type="radio"
              id="option1"
              name="categorySet"
              value="option1"
              checked={displaySet === 'option1'}
              onChange={() => setSelectedSet('option1')}
              className="w-5 h-5 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="option1" className="text-lg font-semibold text-gray-900 cursor-pointer">
              Option 1: Theme-based Categories (Default)
            </label>
            {currentSet === 'option1' && (
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                Current
              </span>
            )}
          </div>

          <div className="flex items-center gap-4">
            <input
              type="radio"
              id="option2"
              name="categorySet"
              value="option2"
              checked={displaySet === 'option2'}
              onChange={() => setSelectedSet('option2')}
              className="w-5 h-5 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="option2" className="text-lg font-semibold text-gray-900 cursor-pointer">
              Option 2: Current Categories
            </label>
            {currentSet === 'option2' && (
              <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                Current
              </span>
            )}
          </div>
        </div>

        {/* Category Set 1 Preview */}
        <div className="mb-6">
          <button
            onClick={() => setShowSet1(!showSet1)}
            className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg flex items-center justify-between"
          >
            <span className="font-medium text-gray-900">
              Option 1 Categories ({CATEGORY_SET_1.length} categories)
            </span>
            <span className="text-gray-500">{showSet1 ? '▼' : '▶'}</span>
          </button>
          {showSet1 && (
            <div className="mt-2 p-4 bg-gray-50 rounded-lg">
              <ul className="space-y-1">
                {CATEGORY_SET_1.map((category, idx) => (
                  <li key={idx} className="text-sm text-gray-700 py-1">
                    • {category}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Category Set 2 Preview */}
        <div className="mb-6">
          <button
            onClick={() => setShowSet2(!showSet2)}
            className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg flex items-center justify-between"
          >
            <span className="font-medium text-gray-900">
              Option 2 Categories ({CATEGORY_SET_2.length} categories)
            </span>
            <span className="text-gray-500">{showSet2 ? '▼' : '▶'}</span>
          </button>
          {showSet2 && (
            <div className="mt-2 p-4 bg-gray-50 rounded-lg">
              <ul className="space-y-1">
                {CATEGORY_SET_2.map((category, idx) => (
                  <li key={idx} className="text-sm text-gray-700 py-1">
                    • {category}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="flex items-center gap-4">
          <button
            onClick={handleSave}
            disabled={!selectedSet || selectedSet === currentSet || updateMutation.isPending}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-lg flex items-center gap-2"
          >
            {updateMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <Save size={20} />
                Save Preference
              </>
            )}
          </button>
          {updateMutation.isSuccess && (
            <div className="flex items-center gap-2 text-green-600">
              <Check size={20} />
              <span className="font-medium">Saved successfully!</span>
            </div>
          )}
          {updateMutation.isError && (
            <div className="text-red-600">
              Error: {updateMutation.error instanceof Error ? updateMutation.error.message : 'Failed to save'}
            </div>
          )}
        </div>

        {selectedSet && selectedSet !== currentSet && (
          <p className="mt-4 text-sm text-gray-600">
            You have unsaved changes. Click &quot;Save Preference&quot; to apply.
          </p>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">How it works:</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Your category set preference affects all categorization dropdowns</li>
          <li>• Option 1 (Default) uses theme-based categories</li>
          <li>• Option 2 uses the current category system</li>
          <li>• Changes take effect immediately after saving</li>
        </ul>
      </div>
    </div>
  )
}

