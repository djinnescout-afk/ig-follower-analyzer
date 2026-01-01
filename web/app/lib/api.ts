import axios from 'axios'
import { supabase } from './supabase'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout for Render wake-up
})

// Add request interceptor to include JWT token
api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Add response interceptor to handle Render wake-up errors and auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // If it's a network error (Render waking up), provide helpful message
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
      console.error('[API] Connection failed. The server may be waking up (Render free tier).')
      error.message = 'API server is waking up. Please wait 30 seconds and try again.'
    }
    
    // If unauthorized, check if we actually have a session before redirecting
    if (error.response?.status === 401) {
      console.error('[API] 401 Unauthorized error:', {
        url: error.config?.url,
        method: error.config?.method,
        hasAuthHeader: !!error.config?.headers?.Authorization,
      })
      
      // Check if we have a valid session before redirecting
      const { data: { session } } = await supabase.auth.getSession()
      
      if (!session) {
        console.log('[API] No session found, redirecting to login')
        // Only redirect if we're not already on the login page
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      } else {
        console.warn('[API] 401 error but session exists - this might be a backend JWT verification issue')
        console.warn('[API] Session details:', {
          user_id: session.user?.id,
          expires_at: session.expires_at,
          token_length: session.access_token?.length,
        })
        // Don't redirect if we have a session - might be a backend issue
        // Just log the error and let the component handle it
      }
    }
    
    return Promise.reject(error)
  }
)

// Types
export interface Client {
  id: string
  name: string
  ig_username: string
  following_count: number
  last_scraped?: string
  date_closed?: string
  created_at: string
}

export interface Page {
  id: string
  ig_username: string
  full_name?: string
  follower_count: number
  is_verified: boolean
  is_private: boolean
  client_count: number
  followers_per_client?: number
  last_scraped?: string
  last_scrape_status?: string
  // VA Categorization fields
  category?: string
  manual_promo_status?: string
  known_contact_methods?: string[]
  attempted_contact_methods?: string[]
  successful_contact_methods?: string[]
  current_main_contact_method?: string
  ig_account_for_dm?: string
  promo_price?: number
  website_url?: string
  va_notes?: string
  last_reviewed_by?: string
  last_reviewed_at?: string
  // Contact detail fields
  contact_email?: string
  contact_phone?: string
  contact_whatsapp?: string
  contact_telegram?: string
  contact_other?: string
  // Outreach tracking fields
  outreach_status?: string
  outreach_date_contacted?: string
  outreach_follow_up_date?: string
}

export interface ScrapeRun {
  id: string
  scrape_type: 'client_following' | 'profile_scrape'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  client_id?: string
  page_ids?: string[]
  result?: any
  created_at: string
  started_at?: string
  completed_at?: string
}

export interface PageProfile {
  page_id: string
  profile_pic_base64?: string
  profile_pic_mime_type?: string
  bio?: string
  posts?: any[]
  promo_status?: string
  promo_indicators?: string[]
  contact_email?: string
  scraped_at: string
}

export interface OutreachTracking {
  id: string
  page_id: string
  status: 'not_contacted' | 'contacted' | 'responded' | 'negotiating' | 'booked' | 'declined'
  date_contacted?: string
  follow_up_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

// Client API
export const clientsApi = {
  list: () => api.get<Client[]>('/clients'),
  get: (id: string) => api.get<Client>(`/clients/${id}`),
  create: (data: { name: string; ig_username: string; date_closed?: string }) => 
    api.post<Client>('/clients', data),
  bulkCreate: (clients: Array<{ name: string; ig_username: string; date_closed?: string }>) =>
    api.post<Client[]>('/clients/bulk', clients),
  delete: (id: string) => api.delete(`/clients/${id}`),
}

// Pages API
export const pagesApi = {
  list: (params?: { 
    min_client_count?: number
    categorized?: boolean
    category?: string
    search?: string
    sort_by?: string
    order?: string
    limit?: number
    offset?: number
    include_archived?: boolean
    client_date_from?: string
    client_date_to?: string
  }) => api.get<Page[]>('/pages', { params }),
  get: (id: string) => api.get<Page>(`/pages/${id}`),
  getProfile: (id: string) => api.get<PageProfile>(`/pages/${id}/profile`),
  update: (id: string, data: any) => api.put(`/pages/${id}`, data),
  archive: (id: string) => api.put(`/pages/${id}`, { archived: true }),
  getPageFollowers: (id: string) => api.get<any[]>(`/pages/${id}/followers`),
  getCategoryCounts: (params?: {
    client_date_from?: string
    client_date_to?: string
  }) => api.get<Record<string, number>>('/pages/category-counts', { params }),
  getCount: (params?: {
    categorized?: boolean
    category?: string
    search?: string
    include_archived?: boolean
    client_date_from?: string
    client_date_to?: string
  }) => api.get<{ count: number }>('/pages/count', { params }),
}

// Scrapes API
export const scrapesApi = {
  list: (params?: { limit?: number; offset?: number }) => 
    api.get<ScrapeRun[]>('/scrapes', { params }),
  get: (id: string) => api.get<ScrapeRun>(`/scrapes/${id}`),
  triggerClientFollowing: (clientIds: string[]) => 
    api.post('/scrapes/client-following', { client_ids: clientIds }),
  triggerProfileScrape: (pageIds: string[]) => 
    api.post('/scrapes/profile-scrape', { page_ids: pageIds }),
}

// Outreach API
export const outreachApi = {
  get: (pageId: string) => api.get<OutreachTracking>(`/outreach/${pageId}`),
  create: (data: { 
    page_id: string
    status: string
    date_contacted?: string
    follow_up_date?: string
    notes?: string 
  }) => api.post<OutreachTracking>('/outreach', data),
  update: (pageId: string, data: {
    status?: string
    date_contacted?: string
    follow_up_date?: string
    notes?: string
  }) => api.put<OutreachTracking>(`/outreach/${pageId}`, data),
}

// Concentration calculation utilities
export function calculateConcentration(page: Page): number | null {
  if (!page.client_count || page.client_count === 0) return null
  return page.follower_count / page.client_count
}

export function calculateConcentrationPerDollar(page: Page): number | null {
  if (!page.promo_price || page.promo_price === 0) return null
  const conc = calculateConcentration(page)
  if (conc === null) return null
  return conc / page.promo_price / 1000000
}

export function calculateQuartiles(values: number[]): { q25: number; q50: number; q75: number } {
  if (values.length === 0) return { q25: 0, q50: 0, q75: 0 }
  const sorted = [...values].sort((a, b) => a - b)
  const q25 = sorted[Math.floor(sorted.length * 0.25)]
  const q50 = sorted[Math.floor(sorted.length * 0.50)]
  const q75 = sorted[Math.floor(sorted.length * 0.75)]
  return { q25, q50, q75 }
}

export function getConcentrationTier(
  value: number | null, 
  quartiles: { q25: number; q50: number; q75: number }
): 'A' | 'B' | 'C' | 'D' | 'unknown' {
  if (value === null) return 'unknown'
  // INVERTED: Lower concentration = better (more targeted)
  // Tier A = Bottom 25% (most concentrated/best)
  // Tier D = Top 25% (least concentrated/worst)
  if (value <= quartiles.q25) return 'A'
  if (value <= quartiles.q50) return 'B'
  if (value <= quartiles.q75) return 'C'
  return 'D'
}

