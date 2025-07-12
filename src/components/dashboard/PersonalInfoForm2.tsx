import { useState, useCallback, useMemo } from 'react'
import { User, MapPin, Phone, Loader2 } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { personalInfoSchema, PersonalInfoFormData, US_STATES, formatPhoneNumber, formatZipCode } from '../lib/validations'
import { useToast } from './ui/toast'

interface FormErrors {
  [key: string]: string
}

interface PersonalInfoFormProps {
  onSuccess?: (data: PersonalInfoFormData) => void
}

export const PersonalInfoForm = ({ onSuccess }: PersonalInfoFormProps) => {
  const [formData, setFormData] = useState<PersonalInfoFormData>({
    firstName: '',
    lastName: '',
    addressLine1: '',
    addressLine2: '',
    city: '',
    state: '',
    zipCode: '',
    phoneNumber: ''
  })
  
  const [errors, setErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { addToast, ToastContainer } = useToast()

  // Validate form data
  const validateForm = useCallback(() => {
    try {
      personalInfoSchema.parse(formData)
      setErrors({})
      return true
    } catch (error: any) {
      const fieldErrors: FormErrors = {}
      error.errors?.forEach((err: any) => {
        if (err.path) {
          fieldErrors[err.path[0]] = err.message
        }
      })
      setErrors(fieldErrors)
      return false
    }
  }, [formData])

  // Handle input changes with formatting
  const handleInputChange = useCallback((field: keyof PersonalInfoFormData, value: string) => {
    let formattedValue = value
    
    // Apply formatting based on field type
    if (field === 'phoneNumber') {
      formattedValue = formatPhoneNumber(value)
    } else if (field === 'zipCode') {
      formattedValue = formatZipCode(value)
    }
    
    setFormData(prev => ({
      ...prev,
      [field]: formattedValue
    }))
    
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }))
    }
  }, [errors])

  // Submit form to Supabase
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      addToast('Please fix the errors in the form', 'error')
      return
    }
    
    setIsSubmitting(true)
    
    try {
      // Prepare data for database
      const dbData = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        address_line_1: formData.addressLine1,
        address_line_2: formData.addressLine2 || null,
        city: formData.city,
        state: formData.state,
        zip_code: formData.zipCode,
        phone_number: formData.phoneNumber
      }
      
      // Try to upsert (insert or update if phone number exists)
      const { data, error } = await supabase
        .from('personal_info')
        .upsert(dbData, {
          onConflict: 'phone_number',
          ignoreDuplicates: false
        })
        .select()
      
      if (error) {
        console.error('Supabase error:', error)
        
        // Handle specific error cases
        if (error.code === '23505') {
          addToast('A record with this phone number already exists', 'error')
        } else {
          addToast('Failed to save information. Please try again.', 'error')
        }
        return
      }
      
      // Success
      addToast('Personal information saved successfully!', 'success')
      
      // Reset form
      setFormData({
        firstName: '',
        lastName: '',
        addressLine1: '',
        addressLine2: '',
        city: '',
        state: '',
        zipCode: '',
        phoneNumber: ''
      })
      
      // Call success callback if provided
      onSuccess?.(formData)
      
    } catch (error) {
      console.error('Unexpected error:', error)
      addToast('An unexpected error occurred. Please try again.', 'error')
    } finally {
      setIsSubmitting(false)
    }
  }, [formData, validateForm, addToast, onSuccess])

  // Memoized form fields for better performance
  const formFields = useMemo(() => [
    {
      label: 'First Name',
      field: 'firstName' as const,
      type: 'text',
      placeholder: 'Enter your first name',
      icon: User,
      required: true
    },
    {
      label: 'Last Name',
      field: 'lastName' as const,
      type: 'text',
      placeholder: 'Enter your last name',
      icon: User,
      required: true
    },
    {
      label: 'Address Line 1',
      field: 'addressLine1' as const,
      type: 'text',
      placeholder: 'Enter your street address',
      icon: MapPin,
      required: true
    },
    {
      label: 'Address Line 2',
      field: 'addressLine2' as const,
      type: 'text',
      placeholder: 'Apartment, suite, etc. (optional)',
      icon: MapPin,
      required: false
    },
    {
      label: 'City',
      field: 'city' as const,
      type: 'text',
      placeholder: 'Enter your city',
      icon: MapPin,
      required: true
    },
    {
      label: 'ZIP Code',
      field: 'zipCode' as const,
      type: 'text',
      placeholder: '12345',
      icon: MapPin,
      required: true,
      maxLength: 5
    },
    {
      label: 'Phone Number',
      field: 'phoneNumber' as const,
      type: 'tel',
      placeholder: '123-456-7890',
      icon: Phone,
      required: true,
      maxLength: 12
    }
  ], [])

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <ToastContainer />
      
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Personal Information</h2>
        <p className="text-gray-600">Please fill out your personal details below.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {formFields.slice(0, 2).map(({ label, field, type, placeholder, icon: Icon, required }) => (
            <div key={field}>
              <label htmlFor={field} className="block text-sm font-medium text-gray-700 mb-1">
                {label} {required && <span className="text-red-500">*</span>}
              </label>
              <div className="relative">
                <Icon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  id={field}
                  type={type}
                  value={formData[field]}
                  onChange={(e) => handleInputChange(field, e.target.value)}
                  placeholder={placeholder}
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    errors[field] ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={isSubmitting}
                />
              </div>
              {errors[field] && (
                <p className="mt-1 text-sm text-red-600">{errors[field]}</p>
              )}
            </div>
          ))}
        </div>

        {/* Address Fields */}
        <div className="space-y-4">
          {formFields.slice(2, 4).map(({ label, field, type, placeholder, icon: Icon, required }) => (
            <div key={field}>
              <label htmlFor={field} className="block text-sm font-medium text-gray-700 mb-1">
                {label} {required && <span className="text-red-500">*</span>}
              </label>
              <div className="relative">
                <Icon className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  id={field}
                  type={type}
                  value={formData[field]}
                  onChange={(e) => handleInputChange(field, e.target.value)}
                  placeholder={placeholder}
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                    errors[field] ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={isSubmitting}
                />
              </div>
              {errors[field] && (
                <p className="mt-1 text-sm text-red-600">{errors[field]}</p>
              )}
            </div>
          ))}
        </div>

        {/* City, State, ZIP Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* City */}
          <div>
            <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
              City <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                id="city"
                type="text"
                value={formData.city}
                onChange={(e) => handleInputChange('city', e.target.value)}
                placeholder="Enter your city"
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.city ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
            </div>
            {errors.city && (
              <p className="mt-1 text-sm text-red-600">{errors.city}</p>
            )}
          </div>

          {/* State */}
          <div>
            <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
              State <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <select
                id="state"
                value={formData.state}
                onChange={(e) => handleInputChange('state', e.target.value)}
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.state ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              >
                <option value="">Select State</option>
                {US_STATES.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>
            {errors.state && (
              <p className="mt-1 text-sm text-red-600">{errors.state}</p>
            )}
          </div>

          {/* ZIP Code */}
          <div>
            <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-1">
              ZIP Code <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                id="zipCode"
                type="text"
                value={formData.zipCode}
                onChange={(e) => handleInputChange('zipCode', e.target.value)}
                placeholder="12345"
                maxLength={5}
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                  errors.zipCode ? 'border-red-500' : 'border-gray-300'
                }`}
                disabled={isSubmitting}
              />
            </div>
            {errors.zipCode && (
              <p className="mt-1 text-sm text-red-600">{errors.zipCode}</p>
            )}
          </div>
        </div>

        {/* Phone Number */}
        <div>
          <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 mb-1">
            Phone Number <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              id="phoneNumber"
              type="tel"
              value={formData.phoneNumber}
              onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
              placeholder="123-456-7890"
              maxLength={12}
              className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
                errors.phoneNumber ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isSubmitting}
            />
          </div>
          {errors.phoneNumber && (
            <p className="mt-1 text-sm text-red-600">{errors.phoneNumber}</p>
          )}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            {isSubmitting ? 'Saving...' : 'Save Information'}
          </button>
        </div>
      </form>
    </div>
  )
}