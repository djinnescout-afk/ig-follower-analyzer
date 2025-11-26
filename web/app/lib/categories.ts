export const CATEGORIES = [
  'Black Theme Page',
  'Mixed Theme Page',
  'White Theme Page',
  'Text only Theme Page',
  'Black BG White Text Theme Page',
  'Black Personal Brand Entrepreneur',
  'White Personal Brand Entrepreneur',
  'Other Personal Brand Entrepreneur',
  'Black Celebrity',
  'White Celebrity',
  'Ethnic (All Others) Celebrity',
  'Black Other',
  'Other',
] as const

export type Category = typeof CATEGORIES[number]

// Hotlist keywords for priority categorization
// Note: Uses partial matching - "black" matches "blacksuccess", "hustl" matches "hustlersimage"
export const HOTLIST_KEYWORDS = [
  'hustl',      // Matches: hustlersimage, hustlingquiet, etc.
  'afri',       // Matches: african, afro-american, etc.
  'afro',       // Matches: afro-american, etc.
  'black',      // Matches: blacksuccess, blackbillionaire, etc.
  'melanin',    // Matches: melaninmagic, melaninpoppin, etc.
  'blvck',      // Alternative spelling of black
  'culture',    // Matches: culture, cultural, etc.
  'kulture',    // Alternative spelling of culture
  'brown',      // Matches: brownskin, brownbeauty, brownsuccess, etc.
  'noir',       // French for black, used in some contexts
  'ebony',      // Another term for black/dark
]

// Check if page matches hotlist keywords
export function matchesHotlist(username: string, fullName: string | null | undefined): boolean {
  const text = `${username} ${fullName || ''}`.toLowerCase()
  return HOTLIST_KEYWORDS.some(keyword => text.includes(keyword.toLowerCase()))
}

// Calculate priority tier for a page
// Tier 1 (Highest): Hotlist + 2+ clients
// Tier 2: Hotlist + 1 client
// Tier 3: Non-hotlist + 2+ clients
// Tier 4 (Lowest): Non-hotlist + 1 client
export function getPriorityTier(username: string, fullName: string | null | undefined, clientCount: number): number {
  const isHotlist = matchesHotlist(username, fullName)
  
  if (isHotlist && clientCount >= 2) return 1
  if (isHotlist && clientCount === 1) return 2
  if (!isHotlist && clientCount >= 2) return 3
  return 4
}

export const TIER_LABELS = {
  1: '🔥 TIER 1: Hotlist + 2+ Clients (HIGHEST PRIORITY)',
  2: '⭐ TIER 2: Hotlist + 1 Client',
  3: '📊 TIER 3: Non-Hotlist + 2+ Clients',
  4: '📄 TIER 4: Non-Hotlist + 1 Client',
}

export const TIER_COLORS = {
  1: 'bg-red-50 border-red-500 text-red-900',
  2: 'bg-orange-50 border-orange-500 text-orange-900',
  3: 'bg-blue-50 border-blue-500 text-blue-900',
  4: 'bg-gray-50 border-gray-500 text-gray-900',
}

export const CONTACT_METHODS = [
  'IG DM',
  'Email',
  'Phone',
  'WhatsApp',
  'Telegram',
  'Other',
] as const

export type ContactMethod = typeof CONTACT_METHODS[number]

export const OUTREACH_STATUSES = [
  { value: 'not_contacted', label: 'Not Contacted' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'responded', label: 'Responded' },
  { value: 'negotiating', label: 'Negotiating' },
  { value: 'booked', label: 'Booked' },
  { value: 'declined', label: 'Declined' },
] as const

export type OutreachStatus = typeof OUTREACH_STATUSES[number]['value']

export const PROMO_STATUSES = [
  { value: 'unknown', label: 'Unknown' },
  { value: 'warm', label: 'Warm' },
  { value: 'not_open', label: 'Not Open' },
  { value: 'accepted', label: 'Accepted' },
] as const

export type PromoStatus = typeof PROMO_STATUSES[number]['value']

