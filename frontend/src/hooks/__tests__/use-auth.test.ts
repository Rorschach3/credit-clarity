import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../use-auth';

// Mock Supabase client
const mockSupabase = {
  auth: {
    getSession: jest.fn(),
    getUser: jest.fn(),
    signInWithPassword: jest.fn(),
    signUp: jest.fn(),
    signOut: jest.fn(),
    onAuthStateChange: jest.fn(),
  },
};

jest.mock('@/integrations/supabase/client', () => ({
  supabase: mockSupabase,
}));

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with null user and loading state', () => {
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(true);
  });

  it('should set user when session exists', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
      user_metadata: {
        firstName: 'John',
        lastName: 'Doe',
      },
    };

    const mockSession = {
      user: mockUser,
      access_token: 'mock-token',
      refresh_token: 'mock-refresh-token',
    };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: mockSession },
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      // Simulate immediate callback with session
      setTimeout(() => callback('SIGNED_IN', mockSession), 0);
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    // Wait for async operations to complete
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.loading).toBe(false);
  });

  it('should handle sign in successfully', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
    };

    const mockSession = {
      user: mockUser,
      access_token: 'mock-token',
      refresh_token: 'mock-refresh-token',
    };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.signInWithPassword.mockResolvedValue({
      data: { user: mockUser, session: mockSession },
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signIn('test@example.com', 'password123');
      expect(response).toEqual({ user: mockUser, error: null });
    });

    expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should handle sign in error', async () => {
    const mockError = { message: 'Invalid credentials' };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.signInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: mockError,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signIn('test@example.com', 'wrongpassword');
      expect(response).toEqual({ user: null, error: mockError });
    });
  });

  it('should handle sign up successfully', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
    };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.signUp.mockResolvedValue({
      data: { user: mockUser, session: null },
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signUp('test@example.com', 'password123');
      expect(response).toEqual({ user: mockUser, error: null });
    });

    expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should handle sign up error', async () => {
    const mockError = { message: 'Email already registered' };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.signUp.mockResolvedValue({
      data: { user: null, session: null },
      error: mockError,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signUp('test@example.com', 'password123');
      expect(response).toEqual({ user: null, error: mockError });
    });
  });

  it('should handle sign out successfully', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
    };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: { user: mockUser } },
      error: null,
    });

    mockSupabase.auth.signOut.mockResolvedValue({
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signOut();
      expect(response).toEqual({ error: null });
    });

    expect(mockSupabase.auth.signOut).toHaveBeenCalled();
  });

  it('should handle sign out error', async () => {
    const mockError = { message: 'Sign out failed' };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.signOut.mockResolvedValue({
      error: mockError,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const response = await result.current.signOut();
      expect(response).toEqual({ error: mockError });
    });
  });

  it('should update user state on auth state change', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
    };

    const mockSession = {
      user: mockUser,
      access_token: 'mock-token',
      refresh_token: 'mock-refresh-token',
    };

    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    let authStateCallback: (event: string, session: any) => void;
    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      authStateCallback = callback;
      return { data: { subscription: { unsubscribe: jest.fn() } } };
    });

    const { result } = renderHook(() => useAuth());

    // Simulate auth state change
    await act(async () => {
      authStateCallback('SIGNED_IN', mockSession);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.loading).toBe(false);

    // Simulate sign out
    await act(async () => {
      authStateCallback('SIGNED_OUT', null);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should cleanup subscription on unmount', () => {
    const mockUnsubscribe = jest.fn();
    
    mockSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
      error: null,
    });

    mockSupabase.auth.onAuthStateChange.mockImplementation((callback) => {
      return { data: { subscription: { unsubscribe: mockUnsubscribe } } };
    });

    const { unmount } = renderHook(() => useAuth());

    unmount();

    expect(mockUnsubscribe).toHaveBeenCalled();
  });
});