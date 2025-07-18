#!/usr/bin/env python3
"""
Test script for JWKS authentication implementation
Tests both frontend and backend JWT validation
"""

import asyncio
import json
import logging
from typing import Dict, Any
import aiohttp
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from utils.jwks_auth import JWKSAuthenticator, get_authenticator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JWKSAuthTester:
    """Test suite for JWKS authentication"""
    
    def __init__(self):
        self.supabase_url = "https://gywohmbqohytziwsjrps.supabase.co"
        self.jwks_url = f"{self.supabase_url}/auth/v1/.well-known/jwks.json"
        self.authenticator = JWKSAuthenticator(self.supabase_url)
        self.test_results = []
        
    def log_test_result(self, test_name: str, success: bool, message: str):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })
    
    async def test_jwks_endpoint_accessibility(self) -> bool:
        """Test if JWKS endpoint is accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.jwks_url) as response:
                    if response.status == 200:
                        jwks_data = await response.json()
                        keys_count = len(jwks_data.get("keys", []))
                        self.log_test_result(
                            "JWKS Endpoint Accessibility",
                            True,
                            f"Endpoint accessible with {keys_count} keys"
                        )
                        return True
                    else:
                        self.log_test_result(
                            "JWKS Endpoint Accessibility",
                            False,
                            f"HTTP {response.status}"
                        )
                        return False
        except Exception as e:
            self.log_test_result(
                "JWKS Endpoint Accessibility",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_jwks_data_structure(self) -> bool:
        """Test JWKS data structure validity"""
        try:
            jwks_data = await self.authenticator._fetch_jwks()
            
            # Check required fields
            if "keys" not in jwks_data:
                self.log_test_result(
                    "JWKS Data Structure",
                    False,
                    "Missing 'keys' field"
                )
                return False
            
            keys = jwks_data["keys"]
            if not isinstance(keys, list) or len(keys) == 0:
                self.log_test_result(
                    "JWKS Data Structure",
                    False,
                    "Keys field is not a non-empty list"
                )
                return False
            
            # Check first key structure
            key = keys[0]
            required_fields = ["kid", "kty", "use", "alg"]
            missing_fields = [field for field in required_fields if field not in key]
            
            if missing_fields:
                self.log_test_result(
                    "JWKS Data Structure",
                    False,
                    f"Missing required fields: {missing_fields}"
                )
                return False
            
            self.log_test_result(
                "JWKS Data Structure",
                True,
                f"Valid structure with {len(keys)} keys"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "JWKS Data Structure",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_jwks_caching(self) -> bool:
        """Test JWKS caching mechanism"""
        try:
            # First fetch - should hit the API
            start_time = asyncio.get_event_loop().time()
            await self.authenticator._fetch_jwks()
            first_fetch_time = asyncio.get_event_loop().time() - start_time
            
            # Second fetch - should use cache
            start_time = asyncio.get_event_loop().time()
            await self.authenticator._fetch_jwks()
            second_fetch_time = asyncio.get_event_loop().time() - start_time
            
            # Cache should be significantly faster
            if second_fetch_time < first_fetch_time * 0.5:
                self.log_test_result(
                    "JWKS Caching",
                    True,
                    f"Cache working (first: {first_fetch_time:.3f}s, second: {second_fetch_time:.3f}s)"
                )
                return True
            else:
                self.log_test_result(
                    "JWKS Caching",
                    False,
                    f"Cache not working effectively (first: {first_fetch_time:.3f}s, second: {second_fetch_time:.3f}s)"
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "JWKS Caching",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_invalid_token_handling(self) -> bool:
        """Test handling of invalid JWT tokens"""
        invalid_tokens = [
            "invalid.token.here",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.invalid_signature",
            "",
            "not_a_jwt_at_all"
        ]
        
        for token in invalid_tokens:
            try:
                await self.authenticator.verify_jwt_token(token)
                self.log_test_result(
                    f"Invalid Token Handling ({token[:20]}...)",
                    False,
                    "Should have thrown exception"
                )
                return False
            except Exception:
                # This is expected
                pass
        
        self.log_test_result(
            "Invalid Token Handling",
            True,
            "All invalid tokens properly rejected"
        )
        return True
    
    async def test_key_lookup(self) -> bool:
        """Test key lookup functionality"""
        try:
            jwks_data = await self.authenticator._fetch_jwks()
            keys = jwks_data.get("keys", [])
            
            if not keys:
                self.log_test_result(
                    "Key Lookup",
                    False,
                    "No keys available for testing"
                )
                return False
            
            # Test finding existing key
            existing_kid = keys[0]["kid"]
            found_key = self.authenticator._find_key(jwks_data, existing_kid)
            
            if found_key is None:
                self.log_test_result(
                    "Key Lookup",
                    False,
                    f"Could not find existing key {existing_kid}"
                )
                return False
            
            # Test finding non-existent key
            non_existent_key = self.authenticator._find_key(jwks_data, "non-existent-kid")
            if non_existent_key is not None:
                self.log_test_result(
                    "Key Lookup",
                    False,
                    "Found non-existent key"
                )
                return False
            
            self.log_test_result(
                "Key Lookup",
                True,
                "Key lookup working correctly"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Key Lookup",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def test_environment_configuration(self) -> bool:
        """Test environment configuration"""
        try:
            # Test SUPABASE_URL
            supabase_url = os.getenv("SUPABASE_URL")
            if not supabase_url:
                self.log_test_result(
                    "Environment Configuration",
                    False,
                    "SUPABASE_URL not set"
                )
                return False
            
            # Test SUPABASE_ANON_KEY
            anon_key = os.getenv("SUPABASE_ANON_KEY")
            if not anon_key:
                self.log_test_result(
                    "Environment Configuration",
                    False,
                    "SUPABASE_ANON_KEY not set"
                )
                return False
            
            self.log_test_result(
                "Environment Configuration",
                True,
                "All required environment variables set"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "Environment Configuration",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🧪 Starting JWKS Authentication Tests")
        logger.info("=" * 50)
        
        tests = [
            self.test_environment_configuration,
            self.test_jwks_endpoint_accessibility,
            self.test_jwks_data_structure,
            self.test_jwks_caching,
            self.test_invalid_token_handling,
            self.test_key_lookup,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
        
        # Cleanup
        await self.authenticator.close()
        
        logger.info("=" * 50)
        logger.info(f"🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("✅ All tests passed! JWKS authentication is working correctly.")
        else:
            logger.warning(f"❌ {total - passed} tests failed. Please check the implementation.")
        
        return passed == total
    
    def print_summary(self):
        """Print detailed test summary"""
        print("\n" + "=" * 60)
        print("JWKS AUTHENTICATION TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test']}")
            print(f"    {result['message']}")
        
        passed = sum(1 for r in self.test_results if r["success"])
        total = len(self.test_results)
        print(f"\nOverall: {passed}/{total} tests passed")

async def main():
    """Main test runner"""
    tester = JWKSAuthTester()
    
    try:
        success = await tester.run_all_tests()
        tester.print_summary()
        
        if success:
            print("\n🎉 JWKS authentication is ready for production!")
            return 0
        else:
            print("\n🔧 JWKS authentication needs fixes before production use.")
            return 1
            
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)