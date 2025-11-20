export const CATEGORIES = [
  'Black Theme Page',
  'Mixed Theme Page',
  'White Theme Page',
  'Text only Theme Page',
  'Black BG White Text Theme Page',
  'Personal Brand Entrepreneur',
  'Black Celebrity',
  'White Celebrity',
  'Ethnic (All Others) Celebrity',
  'Other',
] as const

export type Category = typeof CATEGORIES[number]

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

