// Category Set 1 (Option 1 - Default): Theme-based categories
export const CATEGORY_SET_1 = [
  'Theme page (General)',
  'BUSINESS Theme Page',
  'FITNESS Theme Page',
  'AI Theme Page',
  'MASCULINITY Theme Page',
  'QUOTES Theme Page',
  'HEALTH Theme Page',
  'CHRISTIAN Theme Page',
  'MODELS/OF Theme Page',
  'WOMEN\'S Theme Page',
  'POLITICAL Theme Page',
  'SPIRITUAL Theme Page',
  'FASHION Theme Page',
  'LUXURY Theme Page',
  'NATURE/ANIMALS Theme Page',
  'COUPLES Theme Page',
  'PHILOSOPHY Theme Page',
  'TRAVEL Theme Page',
  'CARS/BIKES Theme Page',
  'ART Theme Page',
  'MISCELLANEOUS Theme Page',
  'Celebrity',
  'Non-Celebrity Public Figure',
  'Entrepreneur',
  'Other (Miscellaneous)',
  'Extra category A (optional use)',
  'Extra category B (optional use)',
  'Extra category C (optional use)',
] as const

// Category Set 2 (Option 2 - Current): Existing categories
export const CATEGORY_SET_2 = [
  'Black Theme Page',
  'Mixed Theme Page',
  'White Theme Page',
  'Ethnic (Other) Theme Page',
  'Text only Theme Page',
  'Black BG White Text Theme Page',
  'Black Personal Brand Entrepreneur',
  'White Personal Brand Entrepreneur',
  'Other Personal Brand Entrepreneur',
  'Black Celebrity',
  'White Celebrity',
  'Ethnic (All Others) Celebrity',
  'Black Figure',
  'Other Figure',
  'Black Other',
  'Other',
] as const

// Legacy export for backward compatibility (defaults to Option 2 for now)
// Components should use useCategorySet() hook instead
export const CATEGORIES = CATEGORY_SET_2

export type Category = typeof CATEGORY_SET_1[number] | typeof CATEGORY_SET_2[number]

// Get categories for a specific set
export function getCategoriesForSet(set: 'option1' | 'option2'): readonly string[] {
  return set === 'option1' ? CATEGORY_SET_1 : CATEGORY_SET_2
}

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
// Tier 1 (Highest): Hotlist + 2+ clients + 50k+ followers
// Tier 2: Hotlist + 1 client + 50k+ followers
// Tier 3: Non-hotlist + 2+ clients
// Tier 4 (Lowest): Non-hotlist + 1 client OR hotlist with <50k followers
export function getPriorityTier(username: string, fullName: string | null | undefined, clientCount: number, followerCount?: number): number {
  const isHotlist = matchesHotlist(username, fullName)
  const hasEnoughFollowers = !followerCount || followerCount >= 50000 // Null/0 treated as "unknown" - allow through
  
  // Hotlist pages with <50k followers get demoted to Tier 4
  if (isHotlist && followerCount && followerCount < 50000) return 4
  
  if (isHotlist && hasEnoughFollowers && clientCount >= 2) return 1
  if (isHotlist && hasEnoughFollowers && clientCount === 1) return 2
  if (!isHotlist && clientCount >= 2) return 3
  return 4
}

export const TIER_LABELS = {
  1: '🔥 TIER 1: Hotlist + 2+ Clients + 50k+ Followers (HIGHEST PRIORITY)',
  2: '⭐ TIER 2: Hotlist + 1 Client + 50k+ Followers',
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
  { value: 'unlikely', label: 'Unlikely' },
  { value: 'not_open', label: 'Not Open' },
  { value: 'accepted', label: 'Accepted' },
] as const

export type PromoStatus = typeof PROMO_STATUSES[number]['value']

