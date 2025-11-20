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

// Client API
export const clientsApi = {
  list: () => api.get<Client[]>('/clients'),
  get: (id: string) => api.get<Client>(`/clients/${id}`),
  create: (data: { name: string; ig_username: string }) => 
    api.post<Client>('/clients', data),
  delete: (id: string) => api.delete(`/clients/${id}`),
}

// Pages API
export const pagesApi = {
  list: (params?: { min_client_count?: number; limit?: number; offset?: number }) => 
    api.get<Page[]>('/pages', { params }),
  get: (id: string) => api.get<Page>(`/pages/${id}`),
  getProfile: (id: string) => api.get<PageProfile>(`/pages/${id}/profile`),
  update: (id: string, data: any) => api.patch(`/pages/${id}`, data),
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

