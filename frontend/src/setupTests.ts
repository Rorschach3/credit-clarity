import '@testing-library/jest-dom';
import React from 'react';

// Global test environment setup
beforeEach(() => {
  jest.clearAllMocks();
  // Reset console mocks but allow real console in development
  if (process.env.NODE_ENV === 'test') {
    jest.clearAllMocks();
  }
});

afterEach(() => {
  // Clean up any remaining timers
  jest.useRealTimers();
});

// Browser API Mocks
// ===================

// Mock IntersectionObserver with proper callback support
class MockIntersectionObserver implements IntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = '0px';
  readonly thresholds: ReadonlyArray<number> = [];
  
  private callback: IntersectionObserverCallback;
  private elements = new Set<Element>();

  constructor(callback: IntersectionObserverCallback, options?: IntersectionObserverInit) {
    this.callback = callback;
  }
  
  observe(element: Element): void {
    this.elements.add(element);
    // Simulate immediate intersection for testing
    setTimeout(() => {
      this.callback([{
        target: element,
        isIntersecting: true,
        intersectionRatio: 1,
        boundingClientRect: element.getBoundingClientRect(),
        intersectionRect: element.getBoundingClientRect(),
        rootBounds: null,
        time: Date.now()
      }], this);
    }, 0);
  }
  
  unobserve(element: Element): void {
    this.elements.delete(element);
  }
  
  disconnect(): void {
    this.elements.clear();
  }

  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

global.IntersectionObserver = MockIntersectionObserver;

// Mock ResizeObserver with proper callback support
class MockResizeObserver implements ResizeObserver {
  private callback: ResizeObserverCallback;
  private elements = new Set<Element>();

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }
  
  observe(element: Element): void {
    this.elements.add(element);
    // Simulate immediate resize for testing
    setTimeout(() => {
      this.callback([{
        target: element,
        contentRect: {
          width: 100,
          height: 100,
          top: 0,
          left: 0,
          bottom: 100,
          right: 100,
          x: 0,
          y: 0
        } as DOMRectReadOnly,
        borderBoxSize: [] as ReadonlyArray<ResizeObserverSize>,
        contentBoxSize: [] as ReadonlyArray<ResizeObserverSize>,
        devicePixelContentBoxSize: [] as ReadonlyArray<ResizeObserverSize>
      }], this);
    }, 0);
  }
  
  unobserve(element: Element): void {
    this.elements.delete(element);
  }
  
  disconnect(): void {
    this.elements.clear();
  }
}

global.ResizeObserver = MockResizeObserver;

// Enhanced matchMedia mock with query support
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => {
    const mediaQuery = {
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(), // Deprecated
      removeListener: jest.fn(), // Deprecated
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    };

    // Add some common media query matches for testing
    if (query.includes('max-width: 768px')) {
      mediaQuery.matches = false; // Default to desktop
    }
    if (query.includes('prefers-color-scheme: dark')) {
      mediaQuery.matches = false; // Default to light mode
    }

    return mediaQuery;
  }),
});

// Mock scrollIntoView with options support
Element.prototype.scrollIntoView = jest.fn((options?: boolean | ScrollIntoViewOptions) => {
  // Mock implementation that respects options
  if (options && typeof options === 'object') {
    // Handle behavior, block, inline options
  }
});

// Enhanced File API Mocks
// ========================

// Create a proper FileReader mock that matches the expected interface
const MockFileReader = class {
  result: string | ArrayBuffer | null = null;
  error: DOMException | null = null;
  readyState: number = 0;
  onabort: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onerror: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onload: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadend: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onloadstart: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;
  onprogress: ((this: FileReader, ev: ProgressEvent<FileReader>) => any) | null = null;

  static readonly EMPTY = 0;
  static readonly LOADING = 1;
  static readonly DONE = 2;

  readonly EMPTY = 0;
  readonly LOADING = 1;
  readonly DONE = 2;

  addEventListener = jest.fn();
  removeEventListener = jest.fn();
  dispatchEvent = jest.fn();

  constructor() {
    // Initialize event handlers
  }

  readAsArrayBuffer(blob: Blob): void {
    this.readyState = 1; // LOADING
    
    setTimeout(() => {
      this.result = new ArrayBuffer(blob.size || 8);
      this.readyState = 2; // DONE
      if (this.onload) {
        this.onload.call(this as any, new Event('load') as any);
      }
    }, 0);
  }

  readAsText(blob: Blob, _encoding: string = 'UTF-8'): void {
    this.readyState = 1; // LOADING
    
    setTimeout(() => {
      this.result = 'mock file content';
      this.readyState = 2; // DONE
      if (this.onload) {
        this.onload.call(this as any, new Event('load') as any);
      }
    }, 0);
  }

  readAsDataURL(blob: Blob): void {
    this.readyState = 1; // LOADING
    
    setTimeout(() => {
      const mimeType = blob.type || 'application/octet-stream';
      this.result = `data:${mimeType};base64,bW9jayBmaWxlIGNvbnRlbnQ=`;
      this.readyState = 2; // DONE
      if (this.onload) {
        this.onload.call(this as any, new Event('load') as any);
      }
    }, 0);
  }

  readAsBinaryString(_blob: Blob): void {
    this.readyState = 1; // LOADING
    
    setTimeout(() => {
      this.result = 'mock binary content';
      this.readyState = 2; // DONE
      if (this.onload) {
        this.onload.call(this as any, new Event('load') as any);
      }
    }, 0);
  }

  abort(): void {
    this.readyState = 2; // DONE
    if (this.onabort) {
      this.onabort.call(this as any, new Event('abort') as any);
    }
  }
} as any;

// Assign the static properties to match FileReader interface
Object.defineProperty(MockFileReader, 'EMPTY', { value: 0, writable: false });
Object.defineProperty(MockFileReader, 'LOADING', { value: 1, writable: false });
Object.defineProperty(MockFileReader, 'DONE', { value: 2, writable: false });

global.FileReader = MockFileReader;

// Enhanced URL mocks
const mockObjectUrls = new Set();
global.URL.createObjectURL = jest.fn((blob) => {
  const url = `mock-object-url-${Date.now()}-${Math.random()}`;
  mockObjectUrls.add(url);
  return url;
});

global.URL.revokeObjectURL = jest.fn((url) => {
  mockObjectUrls.delete(url);
});

// Enhanced crypto mock
Object.defineProperty(global, 'crypto', {
  value: {
    getRandomValues: jest.fn((arr) => {
      for (let i = 0; i < arr.length; i++) {
        arr[i] = Math.floor(Math.random() * 256);
      }
      return arr;
    }),
    randomUUID: jest.fn(() => 'mock-uuid-' + Math.random().toString(36).substr(2, 9)),
    subtle: {
      digest: jest.fn(() => Promise.resolve(new ArrayBuffer(32))),
    }
  },
});

// Third-Party Library Mocks
// ==========================

// Enhanced Supabase mock with realistic return values
jest.mock('@/integrations/supabase/client', () => ({
  supabase: {
    auth: {
      getUser: jest.fn(() => Promise.resolve({ 
        data: { user: { id: 'mock-user-id', email: 'test@example.com' } }, 
        error: null 
      })),
      getSession: jest.fn(() => Promise.resolve({ 
        data: { session: { access_token: 'mock-token' } }, 
        error: null 
      })),
      signInWithPassword: jest.fn(() => Promise.resolve({ 
        data: { user: { id: 'mock-user-id' }, session: {} }, 
        error: null 
      })),
      signUp: jest.fn(() => Promise.resolve({ 
        data: { user: { id: 'mock-user-id' }, session: {} }, 
        error: null 
      })),
      signOut: jest.fn(() => Promise.resolve({ error: null })),
      onAuthStateChange: jest.fn((callback: (event: string, session: any) => void) => {
        // Simulate initial auth state
        setTimeout(() => callback('SIGNED_IN', { user: { id: 'mock-user-id' } }), 0);
        return {
          data: { subscription: { unsubscribe: jest.fn() } }
        };
      }),
    },
    from: jest.fn((_table: string) => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          single: jest.fn(() => Promise.resolve({ data: {}, error: null })),
          execute: jest.fn(() => Promise.resolve({ data: [], error: null })),
        })),
        limit: jest.fn(() => Promise.resolve({ data: [], error: null })),
        order: jest.fn(() => Promise.resolve({ data: [], error: null })),
      })),
      insert: jest.fn(() => ({
        select: jest.fn(() => Promise.resolve({ data: [{}], error: null })),
        execute: jest.fn(() => Promise.resolve({ data: [{}], error: null })),
      })),
      update: jest.fn(() => ({
        eq: jest.fn(() => ({
          select: jest.fn(() => Promise.resolve({ data: [{}], error: null })),
          execute: jest.fn(() => Promise.resolve({ data: [{}], error: null })),
        })),
      })),
      delete: jest.fn(() => ({
        eq: jest.fn(() => ({
          execute: jest.fn(() => Promise.resolve({ data: null, error: null })),
        })),
      })),
    })),
    storage: {
      from: jest.fn((_bucket: string) => ({
        upload: jest.fn(() => Promise.resolve({ 
          data: { path: 'mock-path/file.jpg' }, 
          error: null 
        })),
        download: jest.fn(() => Promise.resolve({ 
          data: new Blob(['mock-data']), 
          error: null 
        })),
        remove: jest.fn(() => Promise.resolve({ data: null, error: null })),
        list: jest.fn(() => Promise.resolve({ data: [], error: null })),
      })),
    },
  },
}));

// Toast notifications mock
jest.mock('sonner', () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    promise: jest.fn(),
    dismiss: jest.fn(),
  },
  Toaster: () => null,
}));

// Enhanced React Router mock
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({ 
    pathname: '/', 
    search: '', 
    hash: '', 
    state: null,
    key: 'default'
  }),
  useParams: () => ({}),
  useSearchParams: () => [new URLSearchParams(), jest.fn()],
  BrowserRouter: ({ children }) => children,
  MemoryRouter: ({ children }) => children,
}));

// Comprehensive Lucide React icons mock - using function approach
jest.mock('lucide-react', () => {
  const mockIcon = (name: string) => {
    const IconComponent = React.forwardRef<any, any>((props, ref) => {
      return React.createElement('div', {
        'data-testid': `icon-${name.toLowerCase()}`,
        ref,
        ...props
      }, name);
    });
    IconComponent.displayName = name;
    return IconComponent;
  };

  // Create a comprehensive list of common Lucide icons
  const icons: Record<string, any> = {};
  const iconNames = [
    'MessageCircle', 'X', 'Loader2', 'Info', 'AlertCircle', 'ArrowRight',
    'Upload', 'Download', 'Edit', 'Trash2', 'Plus', 'Minus', 'Check',
    'User', 'CreditCard', 'FileText', 'Settings', 'LogOut', 'Home', 'Menu',
    'Search', 'Bell', 'Mail', 'Phone', 'Calendar', 'Clock', 'Star',
    'Heart', 'Share', 'Copy', 'Save', 'Print', 'Eye', 'EyeOff'
  ];

  iconNames.forEach(name => {
    icons[name] = mockIcon(name);
  });

  // Return a proxy that falls back to creating new icons for any missing ones
  return new Proxy(icons, {
    get: (target, prop) => {
      if (typeof prop === 'string' && !target[prop]) {
        target[prop] = mockIcon(prop);
      }
      return target[prop];
    }
  });
});

// Enhanced Framer Motion mock with animation support
jest.mock('framer-motion', () => ({
  motion: new Proxy({} as any, {
    get: (_target, prop) => {
      if (typeof prop !== 'string') return undefined;
      
      const MotionComponent = React.forwardRef<any, any>(({ children, animate, initial, exit, ...props }, ref) => {
        const elementProps = {
          ...props,
          'data-testid': props['data-testid'] || `motion-${prop}`,
          ref
        };
        
        return React.createElement(prop, elementProps, children);
      });
      
      MotionComponent.displayName = `motion.${prop}`;
      return MotionComponent;
    }
  }),
  AnimatePresence: React.forwardRef<any, any>(({ children, mode, ...props }, ref) => {
    return React.createElement('div', { 
      'data-testid': 'animate-presence', 
      ref,
      ...props 
    }, children);
  }),
  useAnimation: () => ({
    start: jest.fn(() => Promise.resolve()),
    stop: jest.fn(),
    set: jest.fn(),
  }),
  useMotionValue: (initial: any) => ({
    get: () => initial,
    set: jest.fn(),
    on: jest.fn(),
  }),
}));

// Enhanced PDF library mocks
jest.mock('jspdf', () => {
  return jest.fn().mockImplementation(() => ({
    internal: {
      pageSize: { height: 792, width: 612 },
      scaleFactor: 1.33,
    },
    setFontSize: jest.fn().mockReturnThis(),
    setFont: jest.fn().mockReturnThis(),
    setTextColor: jest.fn().mockReturnThis(),
    text: jest.fn().mockReturnThis(),
    addPage: jest.fn().mockReturnThis(),
    splitTextToSize: jest.fn((text: string | string[], _width: number) => 
      Array.isArray(text) ? text : text.split('\n')
    ),
    getTextWidth: jest.fn(() => 100),
    output: jest.fn((type?: string) => {
      if (type === 'blob') {
        return new Blob(['mock-pdf'], { type: 'application/pdf' });
      }
      return 'mock-pdf-string';
    }),
    save: jest.fn(),
  }));
});

jest.mock('pdf-lib', () => ({
  PDFDocument: {
    create: jest.fn(() => Promise.resolve({
      addPage: jest.fn(() => ({
        getSize: jest.fn(() => ({ width: 612, height: 792 })),
        drawText: jest.fn(),
        drawImage: jest.fn(),
        setFont: jest.fn(),
        setFontSize: jest.fn(),
      })),
      copyPages: jest.fn(() => Promise.resolve([])),
      save: jest.fn(() => Promise.resolve(new Uint8Array([1, 2, 3, 4]))),
      embedJpg: jest.fn(() => Promise.resolve({})),
      embedPng: jest.fn(() => Promise.resolve({})),
      embedFont: jest.fn(() => Promise.resolve({})),
      getPages: jest.fn(() => []),
    })),
    load: jest.fn(() => Promise.resolve({
      getPages: jest.fn(() => []),
      copyPages: jest.fn(() => Promise.resolve([])),
    })),
  },
  StandardFonts: {
    Helvetica: 'Helvetica',
    TimesRoman: 'Times-Roman',
  },
  rgb: jest.fn((r: number, g: number, b: number) => ({ r: r/255, g: g/255, b: b/255 })),
  degrees: jest.fn((deg: number) => deg * Math.PI / 180),
}));

// Console Management
// ==================

// Store original console methods
const originalConsole = { ...global.console };

// Create mock console that can be toggled
const createMockConsole = () => ({
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
  info: jest.fn(),
  debug: jest.fn(),
  trace: jest.fn(),
  table: jest.fn(),
  group: jest.fn(),
  groupEnd: jest.fn(),
  groupCollapsed: jest.fn(),
  clear: jest.fn(),
  count: jest.fn(),
  countReset: jest.fn(),
  time: jest.fn(),
  timeEnd: jest.fn(),
  timeLog: jest.fn(),
  assert: jest.fn(),
  dir: jest.fn(),
  dirxml: jest.fn(),
});

// Apply console mocking based on environment
if (process.env.NODE_ENV === 'test' && process.env.MOCK_CONSOLE !== 'false') {
  Object.assign(global.console, createMockConsole());
}

// Utility function to restore real console for specific tests
global.restoreConsole = () => {
  Object.assign(global.console, originalConsole);
};

global.mockConsole = () => {
  Object.assign(global.console, createMockConsole());
};

// Global test utilities with proper typing
// =====================

interface GlobalTestUtils {
  waitFor: (ms?: number) => Promise<void>;
  triggerResize: (element: Element, dimensions?: { width: number; height: number }) => void;
  cleanupMockUrls: () => void;
  suppressReactErrorLogging: () => jest.SpyInstance;
  restoreConsole: () => void;
  mockConsole: () => void;
}

// Helper to wait for async operations
(global as any).waitFor = (ms: number = 0): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

// Helper to trigger ResizeObserver
(global as any).triggerResize = (element: Element, dimensions = { width: 100, height: 100 }): void => {
  const resizeObservers = (element as any)._resizeObservers || [];
  resizeObservers.forEach((observer: any) => {
    if (observer.callback) {
      observer.callback([{
        target: element,
        contentRect: dimensions
      }]);
    }
  });
};

// Helper to clean up mocked URLs
(global as any).cleanupMockUrls = (): void => {
  mockObjectUrls.clear();
};

// Error boundary for tests
(global as any).suppressReactErrorLogging = (): jest.SpyInstance => {
  const spy = jest.spyOn(console, 'error');
  spy.mockImplementation(() => {});
  return spy;
};

// Console restoration utilities
(global as any).restoreConsole = (): void => {
  Object.assign(global.console, originalConsole);
};

(global as any).mockConsole = (): void => {
  Object.assign(global.console, createMockConsole());
};

// Export types for test files
declare global {
  var waitFor: (ms?: number) => Promise<void>;
  var triggerResize: (element: Element, dimensions?: { width: number; height: number }) => void;
  var cleanupMockUrls: () => void;
  var suppressReactErrorLogging: () => jest.SpyInstance;
  var restoreConsole: () => void;
  var mockConsole: () => void;
}