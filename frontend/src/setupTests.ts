// src/setupTests.ts

// This file is executed automatically by Jest (setupFilesAfterEnv) before each test suite.
// It sets up any global test utilities and extends Jest with additional matchers.

// Adds custom jest matchers from jest-dom
import '@testing-library/jest-dom';

// Optionally, you can configure any global mocks or setup here.
// For example, to mock window.matchMedia:

if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},  // Deprecated
      removeListener: () => {},  // Deprecated
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

// You can also set up global fetch mocks or other test-level configurations here.
