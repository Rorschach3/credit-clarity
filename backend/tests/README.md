# Backend Test Suite

## Overview

This directory contains the test suite for the Credit Clarity backend API. Tests are organized by functionality and use pytest as the test runner.

## Test Structure

```
tests/
├── README.md                           # This file
├── conftest.py                         # Shared fixtures and test configuration
├── pytest.ini                          # Pytest configuration (in backend/)
├── test_basic_api.py                   # ✅ Basic API and utility tests (14 passed)
│
├── unit/                               # Unit tests for individual components
│   ├── test_api_health.py             # Health check endpoints
│   └── test_tradelines_api.py         # Tradeline API endpoints
│
├── integration/                        # Integration tests
│   └── test_api_integration.py        # Full API integration tests
│
├── advanced_parsing/                   # Tests for parsing accuracy
│   ├── test_parsing_accuracy.py
│   ├── test_real_world_validation.py
│   └── run_tests.py
│
├── test_fixtures/                      # Test data and fixtures
│   └── tradeline_test_data.py
│
├── test_api_endpoints.py              # API endpoint tests
├── test_negative_account_extraction.py # Negative account parsing
├── test_pdf_chunker.py                # PDF chunking service
├── test_pdf_extractor.py              # PDF extraction
├── test_tradeline_extraction_pipeline.py # Full extraction pipeline
└── test_tradeline_parser.py           # Tradeline parsing logic
```

## Running Tests

### All Tests
```bash
cd backend
source ../venv/bin/activate
pytest -v
```

### Specific Test File
```bash
pytest tests/test_basic_api.py -v
```

### With Coverage
```bash
pytest --cov=. --cov-report=html
```

### By Marker
```bash
pytest -m unit              # Run only unit tests
pytest -m integration       # Run only integration tests
pytest -m "not slow"        # Skip slow tests
```

## Test Status

### ✅ Working Tests (test_basic_api.py)
- **14 passed, 2 skipped** in 0.23s
- Basic endpoints (health check, CORS)
- Utility imports (field validator, tradeline normalizer)
- PDF processing (chunker initialization)
- Classifier functionality
- Configuration and environment
- Async functionality
- Security utilities
- Pydantic data models

### ⚠️ Legacy Tests (Require Refactoring)
The following test files reference `main_modular` which has been consolidated into `main.py`:
- `tests/unit/test_api_health.py`
- `tests/unit/test_tradelines_api.py`
- `tests/integration/test_api_integration.py`
- Other test files in root tests/

**Status:** Fixed in `conftest.py` but individual tests may still need updates.

## Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
asyncio_mode = auto
addopts = -v --tb=short --strict-markers --disable-warnings
```

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.requires_db` - Tests requiring database
- `@pytest.mark.requires_api` - Tests requiring external API

## Writing New Tests

### Basic Test Template
```python
import pytest
from fastapi.testclient import TestClient

def test_my_feature(client):
    """Test description."""
    response = client.get("/api/endpoint")
    assert response.status_code == 200
    assert "expected_key" in response.json()
```

### Async Test Template
```python
@pytest.mark.asyncio
async def test_async_feature(async_client):
    """Test async functionality."""
    response = await async_client.get("/api/endpoint")
    assert response.status_code == 200
```

### Using Fixtures
```python
def test_with_auth(client, auth_headers):
    """Test with authentication."""
    response = client.get(
        "/api/protected",
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Dependencies

Test dependencies are in `requirements-test.txt`:
- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- pytest-cov>=4.1.0
- httpx>=0.24.0

## CI/CD Integration

Tests run automatically in GitHub Actions CI workflow:
- On push to main/master
- On pull requests
- Backend tests run with Python 3.11
- Frontend tests run separately

See: `.github/workflows/ci.yml`

## Next Steps

1. ✅ Basic test suite created and passing
2. ⏭️ Update legacy tests to use `main` instead of `main_modular`
3. ⏭️ Add more comprehensive API endpoint tests
4. ⏭️ Add tradeline extraction pipeline tests
5. ⏭️ Increase test coverage to 80%+

## Troubleshooting

### Import Errors
Make sure you're in the backend directory and virtual environment is activated:
```bash
cd backend
source ../venv/bin/activate
```

### Module Not Found
Add backend to Python path in test file:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
```

### Async Tests Not Running
Ensure pytest-asyncio is installed and `asyncio_mode = auto` is in pytest.ini

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
