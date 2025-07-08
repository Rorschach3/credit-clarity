import { useAuth } from "./use-auth";
import { toast } from 'sonner';

export const useAuthGuard = () => {
  const { user, isLoading } = useAuth();

  const requireAuth = (operation: string = "perform this action"): boolean => {
    if (isLoading) {
      toast.error("Authentication is still loading. Please wait.");
      return false;
    }

    if (!user) {
      toast.error(`You must be logged in to ${operation}.`);
      return false;
    }

    if (!user.id) {
      toast.error("Invalid user session. Please log in again.");
      return false;
    }

    return true;
  };

  const withAuthGuard = <T extends any[], R>(
    fn: (...args: T) => R | Promise<R>,
    operation?: string
  ) => {
    return (...args: T): R | Promise<R> | null => {
      if (!requireAuth(operation)) {
        return null as R;
      }
      return fn(...args);
    };
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user && !!user.id,
    requireAuth,
    withAuthGuard
  };
};