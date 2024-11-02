# External API Tests for Trusty

This directory contains external test scripts for testing the Trusty API endpoints.

## Setup

1. Install requirements: 
```bash
pip install -r requirements.txt
```

2. Make sure the Trusty server is running:
```bash
cd /path/to/trusty
python manage.py runserver
```

3. Run the tests:
```bash
python -m api_tests.test_api_endpoints
```

## Test Coverage

The test suite covers:
- User registration
- Token authentication
- Agent setup
- Agent shopping
- Agent status
- Transaction verification

## Configuration

By default, the tests run against `http://localhost:8000`. To use a different URL:

```python
tester = APITester(base_url="http://your-server-url")
```

## Adding New Tests

To add new test cases:
1. Add a new test method to the APITester class
2. Add the test to the `tests` list in the main() function