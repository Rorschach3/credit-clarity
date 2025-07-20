import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import ChatbotWidget from '../ChatbotWidget';

// Mock the auth hook
const mockUser = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  email: 'test@example.com',
};

jest.mock('@/hooks/use-auth', () => ({
  useAuth: () => ({
    user: mockUser,
  }),
}));

// Mock toast notifications
jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
    info: jest.fn(),
  },
}));

// Mock fetch for API calls
global.fetch = jest.fn();

describe('ChatbotWidget', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });

  it('renders chat button when closed', () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    expect(chatButton).toBeInTheDocument();
    expect(chatButton).toHaveAttribute('disabled', 'false');
  });

  it('opens chat window when button is clicked', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    expect(screen.getByText('Credit Clarity AI')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask about credit, disputes, or your report/)).toBeInTheDocument();
  });

  it('displays welcome message when opened', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    expect(screen.getByText(/Hello! I'm Credit Clarity AI/)).toBeInTheDocument();
  });

  it('allows user to type and send messages', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        response: 'Thank you for your question about credit scores.',
        timestamp: new Date().toISOString(),
      }),
    });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'What is a good credit score?');
    await userEvent.click(sendButton);
    
    expect(global.fetch).toHaveBeenCalledWith('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId: mockUser.id,
        message: 'What is a good credit score?',
        conversationHistory: expect.any(Array),
      }),
    });
  });

  it('displays user message immediately after sending', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        response: 'Thank you for your question.',
        timestamp: new Date().toISOString(),
      }),
    });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'Test message');
    await userEvent.click(sendButton);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('displays bot response after successful API call', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        response: 'A good credit score is typically 700 or above.',
        timestamp: new Date().toISOString(),
      }),
    });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'What is a good credit score?');
    await userEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('A good credit score is typically 700 or above.')).toBeInTheDocument();
    });
  });

  it('shows loading state while waiting for response', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(
      () => new Promise(resolve => setTimeout(resolve, 1000))
    );

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'Test message');
    await userEvent.click(sendButton);
    
    expect(screen.getByText('Credit Clarity AI is thinking...')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'Test message');
    await userEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/I apologize, but I'm experiencing technical difficulties/)).toBeInTheDocument();
    });
  });

  it('disables send button when message is empty', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when message is typed', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    await userEvent.type(textArea, 'Test message');
    
    expect(sendButton).not.toBeDisabled();
  });

  it('sends message when Enter key is pressed', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        response: 'Thank you for your question.',
        timestamp: new Date().toISOString(),
      }),
    });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    
    await userEvent.type(textArea, 'Test message');
    await userEvent.keyboard('{Enter}');
    
    expect(global.fetch).toHaveBeenCalledWith('/api/chat', expect.any(Object));
  });

  it('does not send message when Shift+Enter is pressed', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const textArea = screen.getByPlaceholderText(/Ask about credit, disputes, or your report/);
    
    await userEvent.type(textArea, 'Test message');
    await userEvent.keyboard('{Shift>}{Enter}{/Shift}');
    
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('loads conversation history when opened', async () => {
    const mockHistory = [
      { role: 'user', content: 'Previous question' },
      { role: 'assistant', content: 'Previous answer' },
    ];

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        success: true,
        history: mockHistory,
      }),
    });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(`/api/chat/history/${mockUser.id}?limit=10`);
    });
  });

  it('loads credit suggestions when opened', async () => {
    const mockSuggestions = [
      {
        type: 'dispute',
        priority: 'high',
        title: 'Dispute Negative Items',
        description: 'You have accounts with negative marks that could be disputed.',
        action: 'Review and dispute inaccurate negative items',
      },
    ];

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        json: async () => ({ success: true, history: [] }),
      })
      .mockResolvedValueOnce({
        json: async () => ({
          success: true,
          suggestions: mockSuggestions,
        }),
      });

    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(`/api/chat/suggestions/${mockUser.id}`);
    });
  });

  it('closes chat window when close button is clicked', async () => {
    render(<ChatbotWidget />);
    
    const chatButton = screen.getByRole('button');
    await userEvent.click(chatButton);
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    await userEvent.click(closeButton);
    
    expect(screen.queryByText('Credit Clarity AI')).not.toBeInTheDocument();
  });
});