'use client'

import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '../api'
import { getCategoriesForSet } from '../categories'

export function useCategorySet() {
  const { data: preferences, isLoading } = useQuery({
    queryKey: ['settings', 'preferences'],
    queryFn: async () => {
      const response = await settingsApi.getPreferences()
      return response.data
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1,
  })

  const categorySet = preferences?.category_set || 'option1' // Default to option1
  const categories = getCategoriesForSet(categorySet)

  return {
    categorySet: categorySet as 'option1' | 'option2',
    categories,
    isLoading,
  }
}

