import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Client {
  id: string
  name: string
  ig_username: string
  following_count: number
  last_scraped?: string
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
  last_scraped?: string
  last_scrape_status?: 'success' | 'failed'
  last_scrape_error?: string
  // VA Categorization fields
  category?: string
  known_contact_methods?: string[]
  successful_contact_method?: string
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
export interface BulkClientResult {
  success: Client[]
  failed: Array<{ name: string; ig_username: string; reason: string }>
}

export const clientsApi = {
  list: () => api.get<Client[]>('/clients'),
  get: (id: string) => api.get<Client>(`/clients/${id}`),
  create: (data: { name: string; ig_username: string }) => 
    api.post<Client>('/clients', data),
  createBulk: (clients: Array<{ name: string; ig_username: string }>) =>
    api.post<BulkClientResult>('/clients/bulk', { clients }),
  delete: (id: string) => api.delete(`/clients/${id}`),
}

// Pages API
export const pagesApi = {
  list: (params?: { 
    min_client_count?: number
    categorized?: boolean
    category?: string
    sort_by?: string
    order?: 'asc' | 'desc'
    limit?: number
    offset?: number 
  }) => api.get<Page[]>('/pages', { params }),
  get: (id: string) => api.get<Page>(`/pages/${id}`),
  getProfile: (id: string) => api.get<PageProfile>(`/pages/${id}/profile`),
  update: (id: string, data: any) => api.put(`/pages/${id}`, data),
  getCount: (params?: {
    min_client_count?: number
    categorized?: boolean
    category?: string
  }) => api.get<{ count: number }>('/pages/count', { params }),
  getCategoryCounts: () => api.get<Record<string, number>>('/pages/category-counts'),
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

