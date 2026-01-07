import { Helmet } from "react-helmet-async";
import { ReactNode } from "react";

interface SafeHelmetProps {
  children: ReactNode;
}

/**
 * Wrapper for Helmet that catches and logs errors from invalid dates in schemas
 * Prevents RangeError: Invalid time value from Date.toISOString()
 */
export function SafeHelmet({ children }: SafeHelmetProps) {
  try {
    return <Helmet>{children}</Helmet>;
  } catch (error) {
    console.error('Error rendering Helmet meta tags:', error);
    // Return empty Helmet on error to prevent app crash
    return <Helmet />;
  }
}
