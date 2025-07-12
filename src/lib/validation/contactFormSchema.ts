import { z } from 'zod';

export const contactFormSchema = z.object({
  first_name: z.string().min(2, 'Name is required').max(50, 'Name is too long'),
  last_name: z.string().min(2, 'Name is required').max(50, 'Name is too long'),
  email: z.string().email('Invalid email address'),
  phone_number: z.string().optional(),
  address1: z.string().min(5, 'Address is required').max(100, 'Address is too long'),
  address2: z.string().optional(),
  city: z.string().min(2, 'City is required').max(50, 'City is too long'),
  state: z.string().length(2, 'State must be 2 characters').refine((val) => {
    const US_STATES = [
      'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
      'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
      'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
      'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
      'SD', 'TN', 'TX', 'UT', 'VT', 'VA',
      'WA', 'WV', 'WI', 'WY'
    ];
    return US_STATES.includes(val);
  }, 'Please select a valid state'),
  zip_code: z.string().regex(/^\d{5}$/, 'ZIP code must be exactly 5 digits'),
  dob: z.string().optional(),
  last_four_of_ssn: z.string().optional(),
});

export type ContactFormInputs = z.infer<typeof contactFormSchema>;

// US States for dropdown
export const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

// Validation schema for personal information form
export const personalInfoSchema = z.object({
  firstName: z.string()
    .min(1, 'First name is required')
    .min(2, 'First name must be at least 2 characters')
    .max(50, 'First name must be less than 50 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'First name can only contain letters, spaces, hyphens, and apostrophes'),
  
  lastName: z.string()
    .min(1, 'Last name is required')
    .min(2, 'Last name must be at least 2 characters')
    .max(50, 'Last name must be less than 50 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'Last name can only contain letters, spaces, hyphens, and apostrophes'),
  
  addressLine1: z.string()
    .min(1, 'Address line 1 is required')
    .min(5, 'Address must be at least 5 characters')
    .max(100, 'Address must be less than 100 characters'),
  
  addressLine2: z.string()
    .max(100, 'Address line 2 must be less than 100 characters')
    .optional(),
  
  city: z.string()
    .min(1, 'City is required')
    .min(2, 'City must be at least 2 characters')
    .max(50, 'City must be less than 50 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'City can only contain letters, spaces, hyphens, and apostrophes'),
  
  state: z.string()
    .min(1, 'State is required')
    .length(2, 'State must be 2 characters')
    .refine((val) => US_STATES.includes(val), 'Please select a valid state'),
  
  zipCode: z.string()
    .min(1, 'ZIP code is required')
    .regex(/^\d{5}$/, 'ZIP code must be exactly 5 digits'),
  
  phoneNumber: z.string()
    .min(1, 'Phone number is required')
    .regex(/^\d{3}-\d{3}-\d{4}$/, 'Phone number must be in format: ###-###-####')
})

export type PersonalInfoFormData = z.infer<typeof personalInfoSchema>

// Helper function to format phone number as user types
export const formatPhoneNumber = (value: string): string => {
  const cleaned = value.replace(/\D/g, '')
  const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,4})$/)
  
  if (!match) return value
  
  const [, area, exchange, number] = match
  
  if (number) {
    return `${area}-${exchange}-${number}`
  } else if (exchange) {
    return `${area}-${exchange}`
  } else if (area) {
    return area
  }
  
  return ''
}

// Helper function to format ZIP code
export const formatZipCode = (value: string): string => {
  return value.replace(/\D/g, '').slice(0, 5)
}