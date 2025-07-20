import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import DisputeWizardPage from '../DisputeWizardPage';
import { mockUser, mockTradeline, mockDisputeProfile, mockNegativeTradeline } from '../../test-utils';

// Mock the auth hook
jest.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    user: mockUser,
  }),
}));

// Mock the persistent hooks
jest.mock('@/hooks/usePersistentTradelines', () => ({
  usePersistentTradelines: () => ({
    tradelines: [mockTradeline, mockNegativeTradeline],
    loading: false,
    error: null,
    getNegativeTradelines: jest.fn(() => [mockNegativeTradeline]),
    refreshTradelines: jest.fn(),
  }),
}));

jest.mock('@/hooks/usePersistentProfile', () => ({
  usePersistentProfile: () => ({
    disputeProfile: mockDisputeProfile,
    loading: false,
    error: null,
    refreshProfile: jest.fn(),
    isProfileComplete: true,
    missingFields: [],
  }),
}));

// Mock the utils
jest.mock('@/utils/disputeUtils', () => ({
  generateDisputeLetters: jest.fn(),
  generatePDFPacket: jest.fn(),
  generateCompletePacket: jest.fn(),
}));

jest.mock('@/utils/documentPacketUtils', () => ({
  fetchUserDocuments: jest.fn(),
  downloadDocumentBlobs: jest.fn(),
  hasRequiredDocuments: jest.fn(),
  getMissingDocuments: jest.fn(),
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/dispute-wizard',
    search: '',
    hash: '',
    state: null,
  }),
  useNavigate: () => jest.fn(),
}));

describe('DisputeWizardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the dispute wizard page', () => {
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Credit Dispute Wizard')).toBeInTheDocument();
    expect(screen.getByText('Profile Requirements')).toBeInTheDocument();
    expect(screen.getByText('Tradeline Selection')).toBeInTheDocument();
  });

  it('displays profile status correctly', () => {
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Profile Complete')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('123 Main St')).toBeInTheDocument();
  });

  it('displays tradelines status correctly', () => {
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('2 tradelines loaded')).toBeInTheDocument();
    expect(screen.getByText('1 negative tradeline found')).toBeInTheDocument();
  });

  it('shows tradeline selection section', () => {
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Collection Agency')).toBeInTheDocument();
    expect(screen.getByText('Charged Off')).toBeInTheDocument();
    expect(screen.getByText('Select All')).toBeInTheDocument();
    expect(screen.getByText('Deselect All')).toBeInTheDocument();
  });

  it('allows selecting and deselecting tradelines', async () => {
    render(<DisputeWizardPage />);
    
    const selectAllButton = screen.getByText('Select All');
    const deselectAllButton = screen.getByText('Deselect All');
    
    await userEvent.click(selectAllButton);
    // Check that tradelines are selected (this would be implementation-specific)
    
    await userEvent.click(deselectAllButton);
    // Check that tradelines are deselected (this would be implementation-specific)
  });

  it('shows generate dispute letters button when ready', () => {
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Generate Dispute Letters')).toBeInTheDocument();
  });

  it('generates dispute letters when button is clicked', async () => {
    const mockGenerateDisputeLetters = require('@/utils/disputeUtils').generateDisputeLetters;
    const mockGeneratePDFPacket = require('@/utils/disputeUtils').generatePDFPacket;
    
    mockGenerateDisputeLetters.mockResolvedValue([
      {
        id: 'letter-1',
        creditBureau: 'Experian',
        tradelines: [mockNegativeTradeline],
        letterContent: 'Sample dispute letter content...',
        disputeCount: 1,
        isEdited: false,
      },
    ]);
    
    mockGeneratePDFPacket.mockResolvedValue(new Blob(['pdf content'], { type: 'application/pdf' }));
    
    render(<DisputeWizardPage />);
    
    const generateButton = screen.getByText('Generate Dispute Letters');
    await userEvent.click(generateButton);
    
    await waitFor(() => {
      expect(mockGenerateDisputeLetters).toHaveBeenCalledWith(
        expect.any(Array),
        expect.any(Array),
        mockDisputeProfile,
        expect.any(Function)
      );
    });
  });

  it('shows loading state during letter generation', async () => {
    const mockGenerateDisputeLetters = require('@/utils/disputeUtils').generateDisputeLetters;
    
    // Mock a delayed response
    mockGenerateDisputeLetters.mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );
    
    render(<DisputeWizardPage />);
    
    const generateButton = screen.getByText('Generate Dispute Letters');
    await userEvent.click(generateButton);
    
    expect(screen.getByText('Generating...')).toBeInTheDocument();
    expect(screen.getByText('Initializing dispute letter generation')).toBeInTheDocument();
  });

  it('handles letter generation errors', async () => {
    const mockGenerateDisputeLetters = require('@/utils/disputeUtils').generateDisputeLetters;
    
    mockGenerateDisputeLetters.mockRejectedValue(new Error('Generation failed'));
    
    render(<DisputeWizardPage />);
    
    const generateButton = screen.getByText('Generate Dispute Letters');
    await userEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to generate dispute letters')).toBeInTheDocument();
    });
  });

  it('shows document upload section after letters are generated', async () => {
    const mockGenerateDisputeLetters = require('@/utils/disputeUtils').generateDisputeLetters;
    const mockGeneratePDFPacket = require('@/utils/disputeUtils').generatePDFPacket;
    
    mockGenerateDisputeLetters.mockResolvedValue([
      {
        id: 'letter-1',
        creditBureau: 'Experian',
        tradelines: [mockNegativeTradeline],
        letterContent: 'Sample dispute letter content...',
        disputeCount: 1,
        isEdited: false,
      },
    ]);
    
    mockGeneratePDFPacket.mockResolvedValue(new Blob(['pdf content'], { type: 'application/pdf' }));
    
    render(<DisputeWizardPage />);
    
    const generateButton = screen.getByText('Generate Dispute Letters');
    await userEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Required Identity Documents')).toBeInTheDocument();
      expect(screen.getByText('Government-Issued Photo ID')).toBeInTheDocument();
      expect(screen.getByText('Social Security Card')).toBeInTheDocument();
      expect(screen.getByText('Utility Bill or Proof of Address')).toBeInTheDocument();
    });
  });

  it('shows mailing instructions after letters are generated', async () => {
    const mockGenerateDisputeLetters = require('@/utils/disputeUtils').generateDisputeLetters;
    const mockGeneratePDFPacket = require('@/utils/disputeUtils').generatePDFPacket;
    
    mockGenerateDisputeLetters.mockResolvedValue([
      {
        id: 'letter-1',
        creditBureau: 'Experian',
        tradelines: [mockNegativeTradeline],
        letterContent: 'Sample dispute letter content...',
        disputeCount: 1,
        isEdited: false,
      },
    ]);
    
    mockGeneratePDFPacket.mockResolvedValue(new Blob(['pdf content'], { type: 'application/pdf' }));
    
    render(<DisputeWizardPage />);
    
    const generateButton = screen.getByText('Generate Dispute Letters');
    await userEvent.click(generateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Mailing Instructions')).toBeInTheDocument();
      expect(screen.getByText('Print and mail your dispute letters')).toBeInTheDocument();
    });
  });

  it('renders the chatbot widget', () => {
    render(<DisputeWizardPage />);
    
    // The chatbot widget should be rendered (it's a separate component)
    expect(screen.getByRole('button', { name: /chat/i })).toBeInTheDocument();
  });

  it('handles profile navigation', async () => {
    const mockNavigate = jest.fn();
    
    jest.mocked(require('react-router-dom').useNavigate).mockReturnValue(mockNavigate);
    
    render(<DisputeWizardPage />);
    
    const editProfileButton = screen.getByText('Edit Profile');
    await userEvent.click(editProfileButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/profile');
  });

  it('shows error state when profile is incomplete', () => {
    jest.mocked(require('@/hooks/usePersistentProfile').usePersistentProfile).mockReturnValue({
      disputeProfile: null,
      loading: false,
      error: null,
      refreshProfile: jest.fn(),
      isProfileComplete: false,
      missingFields: ['firstName', 'lastName'],
    });
    
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Profile Incomplete')).toBeInTheDocument();
    expect(screen.getByText('Complete your profile to proceed')).toBeInTheDocument();
  });

  it('shows error state when no tradelines are found', () => {
    jest.mocked(require('@/hooks/usePersistentTradelines').usePersistentTradelines).mockReturnValue({
      tradelines: [],
      loading: false,
      error: null,
      getNegativeTradelines: jest.fn(() => []),
      refreshTradelines: jest.fn(),
    });
    
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('No tradelines found')).toBeInTheDocument();
    expect(screen.getByText('Upload a credit report to get started')).toBeInTheDocument();
  });

  it('handles loading state correctly', () => {
    jest.mocked(require('@/hooks/usePersistentProfile').usePersistentProfile).mockReturnValue({
      disputeProfile: null,
      loading: true,
      error: null,
      refreshProfile: jest.fn(),
      isProfileComplete: false,
      missingFields: [],
    });
    
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Loading your profile and credit data...')).toBeInTheDocument();
  });

  it('handles route state with initial tradelines', () => {
    const mockTradelines = [mockNegativeTradeline];
    
    jest.mocked(require('react-router-dom').useLocation).mockReturnValue({
      pathname: '/dispute-wizard',
      search: '',
      hash: '',
      state: { initialSelectedTradelines: mockTradelines },
    });
    
    render(<DisputeWizardPage />);
    
    expect(screen.getByText('Loaded 1 tradeline(s) from tradelines page')).toBeInTheDocument();
  });
});