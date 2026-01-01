'use client'

import { useState } from 'react'

export type DateRangePreset = 'all_time' | 'this_month' | 'last_month' | 'custom'

export interface DateRange {
  from: string | null
  to: string | null
  preset: DateRangePreset
}

interface DateRangePickerProps {
  value: DateRange
  onChange: (range: DateRange) => void
  className?: string
}

export function DateRangePicker({ value, onChange, className = '' }: DateRangePickerProps) {
  const [showCustom, setShowCustom] = useState(value.preset === 'custom')

  const handlePresetChange = (preset: DateRangePreset) => {
    let from: string | null = null
    let to: string | null = null

    if (preset === 'this_month') {
      const now = new Date()
      from = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split('T')[0]
      to = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split('T')[0]
    } else if (preset === 'last_month') {
      const now = new Date()
      const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)
      from = new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1).toISOString().split('T')[0]
      to = new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0).toISOString().split('T')[0]
    } else if (preset === 'all_time') {
      from = null
      to = null
    }

    setShowCustom(preset === 'custom')
    onChange({ from, to, preset })
  }

  const handleCustomDateChange = (field: 'from' | 'to', dateValue: string) => {
    const newRange = { ...value }
    if (field === 'from') {
      newRange.from = dateValue || null
    } else {
      newRange.to = dateValue || null
    }
    newRange.preset = 'custom'
    onChange(newRange)
  }

  const formatDateRange = () => {
    if (value.preset === 'all_time') {
      return 'All Time'
    } else if (value.preset === 'this_month') {
      const date = new Date(value.from!)
      return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    } else if (value.preset === 'last_month') {
      const date = new Date(value.from!)
      return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    } else if (value.from && value.to) {
      const fromDate = new Date(value.from)
      const toDate = new Date(value.to)
      return `${fromDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - ${toDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    } else if (value.from) {
      const fromDate = new Date(value.from)
      return `From ${fromDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    } else if (value.to) {
      const toDate = new Date(value.to)
      return `Until ${toDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    }
    return 'Select date range'
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => handlePresetChange('all_time')}
          className={`px-3 py-1 text-sm rounded-md ${
            value.preset === 'all_time'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          All Time
        </button>
        <button
          type="button"
          onClick={() => handlePresetChange('this_month')}
          className={`px-3 py-1 text-sm rounded-md ${
            value.preset === 'this_month'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          This Month
        </button>
        <button
          type="button"
          onClick={() => handlePresetChange('last_month')}
          className={`px-3 py-1 text-sm rounded-md ${
            value.preset === 'last_month'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Last Month
        </button>
        <button
          type="button"
          onClick={() => handlePresetChange('custom')}
          className={`px-3 py-1 text-sm rounded-md ${
            value.preset === 'custom'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          Custom Range
        </button>
      </div>

      {showCustom && (
        <div className="flex gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From</label>
            <input
              type="date"
              value={value.from || ''}
              onChange={(e) => handleCustomDateChange('from', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To</label>
            <input
              type="date"
              value={value.to || ''}
              onChange={(e) => handleCustomDateChange('to', e.target.value)}
              min={value.from || undefined}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      )}

      {value.preset !== 'all_time' && (value.from || value.to) && (
        <p className="text-sm text-gray-600">
          Showing: <span className="font-medium">{formatDateRange()}</span>
        </p>
      )}
    </div>
  )
}

