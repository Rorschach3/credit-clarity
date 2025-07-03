// Re-export everything from the new modular structure
export * from './tradeline/types';
export * from './tradeline/parser';
export { saveTradelinesToDatabase as saveTradelinesToDatabase, fetchUserTradelines } from './tradeline/database';

// Keep the main parsing function for backward compatibility
export { parseTradelinesFromText } from './tradeline/parser';
