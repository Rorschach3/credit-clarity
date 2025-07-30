import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options });

// Create mock user data
export const mockUser = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
  user_metadata: {
    firstName: 'John',
    lastName: 'Doe',
  },
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
};

// Create mock tradeline data
export const mockTradeline = {
  id: 'tradeline-1',
  user_id: mockUser.id,
  creditor_name: 'Test Bank',
  account_number: '****1234',
  date_opened: '01/01/2020',
  account_status: 'Open',
  account_type: 'Credit Card',
  account_balance: '$1,000',
  credit_limit: '$5,000',
  monthly_payment: '$100',
  credit_bureau: 'Experian',
  is_negative: false,
  dispute_count: 0,
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
};

// Create mock negative tradeline data
export const mockNegativeTradeline = {
  ...mockTradeline,
  id: 'tradeline-2',
  account_status: 'Charged Off',
  is_negative: true,
  creditor_name: 'Collection Agency',
};

// Create mock dispute profile data
export const mockDisputeProfile = {
  id: 'profile-1',
  user_id: mockUser.id,
  firstName: 'John',
  lastName: 'Doe',
  address: '123 Main St',
  city: 'Anytown',
  state: 'CA',
  zipCode: '12345',
  dateOfBirth: '01/01/1990',
  ssn: '123456789',
  phone: '555-1234',
  email: 'john.doe@example.com',
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
};

// Create mock dispute letter data
export const mockDisputeLetter = {
  id: 'letter-1',
  creditBureau: 'Experian',
  tradelines: [mockTradeline],
  letterContent: 'Sample dispute letter content...',
  disputeCount: 1,
  isEdited: false,
};

// Create mock document data
export const mockDocument = {
  id: 'doc-1',
  user_id: mockUser.id,
  document_type: 'photo_id',
  file_name: 'drivers_license.jpg',
  file_path: '/documents/drivers_license.jpg',
  created_at: '2023-01-01T00:00:00.000Z',
};

// Create mock chat message data
export const mockChatMessage = {
  id: 'msg-1',
  user_id: mockUser.id,
  user_message: 'What is a good credit score?',
  ai_response: 'A good credit score is typically 700 or above.',
  session_id: 'session-1',
  created_at: '2023-01-01T00:00:00.000Z',
  updated_at: '2023-01-01T00:00:00.000Z',
};

// Create mock credit suggestions data
export const mockCreditSuggestions = [
  {
    type: 'dispute',
    priority: 'high' as const,
    title: 'Dispute Negative Items',
    description: 'You have accounts with negative marks that could be disputed.',
    action: 'Review and dispute inaccurate negative items',
  },
  {
    type: 'credit_building',
    priority: 'medium' as const,
    title: 'Build Credit Mix',
    description: 'Consider adding a credit card to improve your credit mix.',
    action: 'Apply for a secured or starter credit card',
  },
];

// Helper function to create mock fetch responses
export const mockFetchResponse = (data: any, ok: boolean = true) => {
  return Promise.resolve({
    ok,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response);
};

// Helper function to create mock error responses
export const mockFetchError = (message: string) => {
  return Promise.reject(new Error(message));
};

// Helper function to wait for async operations
export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { customRender as render };