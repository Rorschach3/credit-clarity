import { useEffect } from 'react';

const useActivityMonitoring = (activity: string) => {
  useEffect(() => {
    console.log('Activity:', activity);
    // TODO: Implement anomaly detection logic here
  }, [activity]);
};

export default useActivityMonitoring;