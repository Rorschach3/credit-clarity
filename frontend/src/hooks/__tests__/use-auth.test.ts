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
    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(true);
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

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      // @ts-expect-error
      const { onAuthStateChange } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      onAuthStateChange.mock.calls('SIGNED_IN', mockSession);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isLoading).toBe(false);
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

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      const { signInWithPassword } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signInWithPassword.mockResolvedValue({ data: { user: mockUser, session: mockSession }, error: null });
      await result.current.login('test@example.com', 'password123');
    });

    const { signInWithPassword } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
    expect(signInWithPassword).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should handle sign in error', async () => {
    const mockError = { message: 'Invalid credentials' };

    const { result } = renderHook(() => useAuth());

    await act(async () => {

      const { signInWithPassword } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signInWithPassword.mockResolvedValue({ data: { user: null, session: null }, error: mockError });
      const response = await result.current.login('test@example.com', 'wrongpassword');
      expect(response).toEqual({ user: null, error: mockError });
    });
  });

  it('should handle sign up successfully', async () => {
    const mockUser = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
    };

    const { result } = renderHook(() => useAuth());

    await act(async () => {

      const { signUp } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signUp.mockResolvedValue({ data: { user: mockUser, session: null }, error: null });
      const response = await result.current.signup('test@example.com', 'password123');
      expect(response).toEqual({ user: mockUser, error: null });
    });


    const { signUp } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
    expect(signUp).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123',
    });
  });

  it('should handle sign up error', async () => {
    const mockError = { message: 'Email already registered' };

    const { result } = renderHook(() => useAuth());

    await act(async () => {

      const { signUp } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signUp.mockResolvedValue({ data: { user: null, session: null }, error: mockError });
      const response = await result.current.signup('test@example.com', 'password123');
      expect(response).toEqual({ user: null, error: mockError });
    });
  });

  it('should handle sign out successfully', async () => {
    const { result } = renderHook(() => useAuth());

    await act(async () => {

      const { signOut } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signOut.mockResolvedValue({ error: null });
      const response = await result.current.logout();
      expect(response).toEqual({ error: null });
    });

    // @ts-expect-error sign in process
    const { signOut } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
    expect(signOut).toHaveBeenCalled();
  });

  it('should handle sign out error', async () => {
    const mockError = { message: 'Sign out failed' };

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      // @ts-expect-error sign out process
      const { signOut } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      signOut.mockResolvedValue({ error: mockError });
      const response = await result.current.logout();
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

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      // @ts-expect-error supabase integration
      const { onAuthStateChange } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      onAuthStateChange.mock.calls('SIGNED_IN', mockSession);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isLoading).toBe(false);

    await act(async () => {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-expect-error
      const { onAuthStateChange } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
      onAuthStateChange.mock.calls('SIGNED_OUT', null);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should cleanup subscription on unmount', () => {
    const mockUnsubscribe = jest.fn();
    // @ts-expect-error subscription error
    const { onAuthStateChange } = jest.requireMock('@/integrations/supabase/client').supabase.auth;
    onAuthStateChange.mockReturnValue({ data: { subscription: { unsubscribe: mockUnsubscribe } } });

    const { unmount } = renderHook(() => useAuth());

    unmount();

    expect(mockUnsubscribe).toHaveBeenCalled();
  });
});