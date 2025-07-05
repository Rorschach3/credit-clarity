import type { JestConfigWithTsJest } from 'ts-jest';

const config: JestConfigWithTsJest = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transform: {
    "^.+\\.(ts|tsx|js|jsx)$": "ts-jest",
  },
  transformIgnorePatterns: [
    "/node_modules/(?!(@supabase|@supabase/supabase-js|@supabase/realtime-js)/)"
  ]
};

export default config;