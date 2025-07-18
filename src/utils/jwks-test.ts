/**
 * Frontend JWKS authentication test utilities
 * Tests JWT token validation and JWKS endpoint integration
 */

import { supabase, JWKS_URL, getSessionToken, validateToken } from '@/integrations/supabase/client';

export interface JWKSTestResult {
  testName: string;
  success: boolean;
  message: string;
  data?: any;
}

export class JWKSFrontendTester {
  private results: JWKSTestResult[] = [];

  private addResult(testName: string, success: boolean, message: string, data?: any): void {
    this.results.push({ testName, success, message, data });
    console.log(`${success ? '✅' : '❌'} ${testName}: ${message}`);
  }

  async testSupabaseClientConfiguration(): Promise<boolean> {
    try {
      // Test if Supabase client is properly configured
      const { data, error } = await supabase.auth.getSession();
      
      if (error) {
        this.addResult(
          'Supabase Client Configuration',
          false,
          `Session error: ${error.message}`
        );
        return false;
      }

      this.addResult(
        'Supabase Client Configuration',
        true,
        'Supabase client properly configured'
      );
      return true;
    } catch (error) {
      this.addResult(
        'Supabase Client Configuration',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async testJWKSEndpointAccess(): Promise<boolean> {
    try {
      const response = await fetch(JWKS_URL);
      
      if (!response.ok) {
        this.addResult(
          'JWKS Endpoint Access',
          false,
          `HTTP ${response.status}: ${response.statusText}`
        );
        return false;
      }

      const jwksData = await response.json();
      
      if (!jwksData.keys || !Array.isArray(jwksData.keys)) {
        this.addResult(
          'JWKS Endpoint Access',
          false,
          'Invalid JWKS format: missing or invalid keys array'
        );
        return false;
      }

      this.addResult(
        'JWKS Endpoint Access',
        true,
        `JWKS endpoint accessible with ${jwksData.keys.length} key(s)`,
        jwksData
      );
      return true;
    } catch (error) {
      this.addResult(
        'JWKS Endpoint Access',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async testSessionTokenRetrieval(): Promise<boolean> {
    try {
      const token = await getSessionToken();
      
      if (!token) {
        this.addResult(
          'Session Token Retrieval',
          true,
          'No active session (user not logged in)'
        );
        return true;
      }

      // Basic JWT format check
      const parts = token.split('.');
      if (parts.length !== 3) {
        this.addResult(
          'Session Token Retrieval',
          false,
          'Invalid JWT format (should have 3 parts)'
        );
        return false;
      }

      this.addResult(
        'Session Token Retrieval',
        true,
        'Session token retrieved successfully'
      );
      return true;
    } catch (error) {
      this.addResult(
        'Session Token Retrieval',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async testTokenValidation(): Promise<boolean> {
    try {
      const token = await getSessionToken();
      
      if (!token) {
        this.addResult(
          'Token Validation',
          true,
          'No token to validate (user not logged in)'
        );
        return true;
      }

      const validation = await validateToken(token);
      
      if (!validation.valid) {
        this.addResult(
          'Token Validation',
          false,
          `Token validation failed: ${validation.error}`
        );
        return false;
      }

      this.addResult(
        'Token Validation',
        true,
        'Token validation successful'
      );
      return true;
    } catch (error) {
      this.addResult(
        'Token Validation',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async testAuthenticationFlow(): Promise<boolean> {
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        this.addResult(
          'Authentication Flow',
          true,
          'No authenticated user (expected for logged-out state)'
        );
        return true;
      }

      // Test refresh token
      const { data, error } = await supabase.auth.refreshSession();
      
      if (error) {
        this.addResult(
          'Authentication Flow',
          false,
          `Token refresh failed: ${error.message}`
        );
        return false;
      }

      this.addResult(
        'Authentication Flow',
        true,
        'Authentication flow working correctly'
      );
      return true;
    } catch (error) {
      this.addResult(
        'Authentication Flow',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async testEnvironmentVariables(): Promise<boolean> {
    try {
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

      if (!supabaseUrl) {
        this.addResult(
          'Environment Variables',
          false,
          'VITE_SUPABASE_URL not set'
        );
        return false;
      }

      if (!supabaseAnonKey) {
        this.addResult(
          'Environment Variables',
          false,
          'VITE_SUPABASE_ANON_KEY not set'
        );
        return false;
      }

      this.addResult(
        'Environment Variables',
        true,
        'All required environment variables are set'
      );
      return true;
    } catch (error) {
      this.addResult(
        'Environment Variables',
        false,
        `Exception: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      return false;
    }
  }

  async runAllTests(): Promise<boolean> {
    console.log('🧪 Starting Frontend JWKS Authentication Tests');
    console.log('=' * 50);

    const tests = [
      this.testEnvironmentVariables,
      this.testSupabaseClientConfiguration,
      this.testJWKSEndpointAccess,
      this.testSessionTokenRetrieval,
      this.testTokenValidation,
      this.testAuthenticationFlow,
    ];

    let passed = 0;
    const total = tests.length;

    for (const test of tests) {
      try {
        if (await test.call(this)) {
          passed++;
        }
      } catch (error) {
        console.error(`Test ${test.name} failed with exception:`, error);
      }
    }

    console.log('=' * 50);
    console.log(`🏁 Frontend Test Results: ${passed}/${total} tests passed`);

    if (passed === total) {
      console.log('✅ All frontend tests passed! JWKS authentication is working correctly.');
    } else {
      console.warn(`❌ ${total - passed} tests failed. Please check the implementation.`);
    }

    return passed === total;
  }

  getResults(): JWKSTestResult[] {
    return this.results;
  }

  printSummary(): void {
    console.log('\n' + '='.repeat(60));
    console.log('FRONTEND JWKS AUTHENTICATION TEST SUMMARY');
    console.log('='.repeat(60));

    for (const result of this.results) {
      const status = result.success ? '✅ PASS' : '❌ FAIL';
      console.log(`${status} ${result.testName}`);
      console.log(`    ${result.message}`);
    }

    const passed = this.results.filter(r => r.success).length;
    const total = this.results.length;
    console.log(`\nOverall: ${passed}/${total} tests passed`);
  }
}

// Export function for easy testing in browser console
export const testJWKSAuthentication = async (): Promise<void> => {
  const tester = new JWKSFrontendTester();
  await tester.runAllTests();
  tester.printSummary();
};

// Auto-run tests in development mode
if (import.meta.env.DEV) {
  console.log('JWKS Frontend Tester loaded. Run testJWKSAuthentication() to test authentication.');
}