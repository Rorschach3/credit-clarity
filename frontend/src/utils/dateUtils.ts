/**
 * Safely convert a value to ISO string format
 * Returns current date as fallback if invalid
 */
export function safeToISOString(date?: Date | string | number | null): string {
  try {
    if (!date) {
      return new Date().toISOString();
    }
    
    const dateObj = date instanceof Date ? date : new Date(date);
    
    // Check if date is valid
    if (isNaN(dateObj.getTime())) {
      console.warn('Invalid date provided to safeToISOString:', date);
      return new Date().toISOString();
    }
    
    return dateObj.toISOString();
  } catch (error) {
    console.error('Error in safeToISOString:', error, 'Input:', date);
    return new Date().toISOString();
  }
}

/**
 * Safely convert a value to ISO date string (YYYY-MM-DD)
 * Returns current date as fallback if invalid
 */
export function safeToISODateString(date?: Date | string | number | null): string {
  return safeToISOString(date).split('T')[0];
}

/**
 * Check if a date is valid
 */
export function isValidDate(date: any): boolean {
  if (!date) return false;
  const dateObj = date instanceof Date ? date : new Date(date);
  return !isNaN(dateObj.getTime());
}
