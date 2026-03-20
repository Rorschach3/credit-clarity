import { useEffect, useRef } from 'react';

const WINDOW_MS = 60_000;
const MAX_EVENTS = 10;
const RAPID_THRESHOLD_MS = 500;
const RAPID_COUNT = 5;

const useActivityMonitoring = (activity: string) => {
  const timestamps = useRef<number[]>([]);
  const rapidCount = useRef(0);
  const lastActivityTime = useRef(0);

  useEffect(() => {
    if (!activity) return;
    const now = Date.now();

    // Detect rapid repeated actions
    if (now - lastActivityTime.current < RAPID_THRESHOLD_MS) {
      rapidCount.current += 1;
    } else {
      rapidCount.current = 0;
    }
    lastActivityTime.current = now;

    // Rolling window: keep only events within last 60s
    timestamps.current = [...timestamps.current.filter(t => now - t < WINDOW_MS), now];

    // Anomaly checks
    if (timestamps.current.length > MAX_EVENTS) {
      console.warn(`[ActivityMonitor] Anomaly: "${activity}" triggered ${timestamps.current.length}x in 60s`);
      // Reset to avoid repeated warnings
      timestamps.current = [];
    }

    if (rapidCount.current >= RAPID_COUNT) {
      console.warn(`[ActivityMonitor] Anomaly: rapid repeated "${activity}" detected`);
      rapidCount.current = 0;
    }
  }, [activity]);
};

export default useActivityMonitoring;
