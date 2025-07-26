import { useEffect, useRef, useCallback } from 'react';

interface CleanupFunction {
  (): void;
}

export const useMemoryCleanup = () => {
  const cleanupFunctions = useRef<CleanupFunction[]>([]);
  const objectUrls = useRef<string[]>([]);
  const timeouts = useRef<number[]>([]);
  const intervals = useRef<number[]>([]);

  const addCleanup = useCallback((fn: CleanupFunction) => {
    cleanupFunctions.current.push(fn);
  }, []);

  const trackObjectUrl = useCallback((url: string) => {
    objectUrls.current.push(url);
    return url;
  }, []);

  const trackTimeout = useCallback((timeout: number) => {
    timeouts.current.push(timeout);
    return timeout;
  }, []);

  const trackInterval = useCallback((interval: number) => {
    intervals.current.push(interval);
    return interval;
  }, []);

  const cleanup = useCallback(() => {
    // Clean up custom functions
    cleanupFunctions.current.forEach(fn => {
      try {
        fn();
      } catch (error) {
        console.warn('Cleanup function error:', error);
      }
    });
    cleanupFunctions.current = [];

    // Clean up object URLs
    objectUrls.current.forEach(url => {
      try {
        URL.revokeObjectURL(url);
      } catch (error) {
        console.warn('Failed to revoke object URL:', error);
      }
    });
    objectUrls.current = [];

    // Clear timeouts
    timeouts.current.forEach(timeout => {
      try {
        clearTimeout(timeout);
      } catch (error) {
        console.warn('Failed to clear timeout:', error);
      }
    });
    timeouts.current = [];

    // Clear intervals
    intervals.current.forEach(interval => {
      try {
        clearInterval(interval);
      } catch (error) {
        console.warn('Failed to clear interval:', error);
      }
    });
    intervals.current = [];
  }, []);

  // Auto cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  return {
    addCleanup,
    trackObjectUrl,
    trackTimeout,
    trackInterval,
    cleanup
  };
};