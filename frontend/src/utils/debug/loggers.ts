// Debug utilities (conditionally enabled)
const DEBUG_MODE = import.meta.env.DEV;

export function logModuleLoad(moduleName: string) {
  if (!DEBUG_MODE) return;
  console.debug(`[DEBUG] Module loaded: ${moduleName}`);
}

export function logRouteValidation(route: string, isValid: boolean) {
  if (!DEBUG_MODE) return;
  console.debug(`[DEBUG] Route validation: ${route} - ${isValid ? 'VALID' : 'INVALID'}`);
}

// New safety filter logger
export function logSafetyFilterBlock(reason: string, inputSample: string) {
  if (!DEBUG_MODE) return;
  console.warn(`🚫 Safety Filter Triggered: ${reason}`);
  console.debug(`Input sample: ${inputSample.substring(0, 100)}...`);
}

// Sanitization metrics logger
export function logSanitizationMetrics(originalLength: number, sanitizedLength: number, removedPatterns: Record<string, number>) {
  if (!DEBUG_MODE) return;
  console.info(`📊 Sanitization Metrics:`);
  console.info(`Original chars: ${originalLength}, Sanitized chars: ${sanitizedLength}`);
  console.info(`Reduction: ${((1 - sanitizedLength/originalLength)*100).toFixed(1)}%`);
  console.info("Patterns removed:");
  Object.entries(removedPatterns).forEach(([pattern, count]) => {
    console.info(`- ${pattern}: ${count}`);
  });
}