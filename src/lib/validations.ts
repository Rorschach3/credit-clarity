import { z } from 'zod'

// Zod schema for personal information form
export const personalInfoSchema = z.object({
  firstName: z.string().min(1, 'First Name is required'),
  lastName: z.string().min(1, 'Last Name is required'),
  address1: z.string().min(1, 'Address Line 1 is required'),
  address2: z.string().optional().nullable(),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(1, 'State is required'),
  zipCode: z.string().regex(/^\d{5}$/, 'Invalid ZIP Code. Must be 5 digits.'),
  phoneNumber: z.string().regex(/^\d{3}-\d{3}-\d{4}$/, 'Invalid Phone Number. Format: 123-456-7890'),
  lastFourOfSsn: z.string().optional().nullable(),
  dob: z.string().optional().nullable(),
})

// Type definition for form data
export type PersonalInfoFormData = z.infer<typeof personalInfoSchema>

// List of US States (simplified for example)
export const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

// Utility function to format phone number
export const formatPhoneNumber = (value: string): string => {
  if (!value) return ''
  const phoneNumber = value.replace(/[^\d]/g, '')
  const phoneNumberLength = phoneNumber.length
  if (phoneNumberLength < 4) return phoneNumber
  if (phoneNumberLength < 7) {
    return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3)}`
  }
  return `${phoneNumber.slice(0, 3)}-${phoneNumber.slice(3, 6)}-${phoneNumber.slice(6, 10)}`
}

// Utility function to format ZIP code
export const formatZipCode = (value: string): string => {
  if (!value) return ''
  const zipCode = value.replace(/[^\d]/g, '')
  return zipCode.slice(0, 5)
}