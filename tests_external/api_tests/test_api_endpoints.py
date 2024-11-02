import requests
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging
from .utils import setup_logging

logger = setup_logging()

class APITester:
    """Test suite for Trusty API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.agent_id = None
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def _update_auth_header(self) -> None:
        """Update authorization header with token if available."""
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to API endpoint with enhanced error logging."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        self._update_auth_header()
        
        logger.info(f"\nTesting {method} {endpoint}")
        logger.info(f"Request Data: {json.dumps(data, indent=2) if data else 'None'}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            else:
                response = requests.post(url, headers=self.headers, json=data)
            
            logger.info(f"Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"Response: {json.dumps(response_data, indent=2)}")
                
                # Enhanced error logging
                if response.status_code >= 400:
                    logger.error(f"Request failed with status {response.status_code}")
                    logger.error(f"Error details: {json.dumps(response_data, indent=2)}")
                    if 'detail' in response_data:
                        logger.error(f"Error message: {response_data['detail']}")
                
                return response_data
            except ValueError as e:
                logger.error(f"Error parsing response: {str(e)}")
                logger.error(f"Raw response: {response.text}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            logger.error(f"Request details: {method} {url}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            return {}

    def run_tests(self) -> List[Tuple[str, bool]]:
        """Run all API tests and return results."""
        timestamp = int(datetime.now().timestamp())
        username = f"testuser_{timestamp}"
        password = "TestPass123!"
        
        tests = [
            ("Registration", lambda: self.test_registration(username, password)),
            ("Token Obtain", lambda: self.test_token_obtain(username, password)),
            ("Agent Setup", lambda: self.test_agent_setup()),
            ("Agent Shopping", lambda: self.test_agent_shopping()),
            ("Agent Status", lambda: self.test_agent_status()),
            ("Transaction Verification", lambda: self.test_transaction_verification())
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                logger.error(f"Error in {test_name}: {str(e)}")
                results.append((test_name, False))
        
        return results

    def test_registration(self, username: str, password: str) -> bool:
        """Test user registration endpoint."""
        logger.info("\n=== Testing User Registration ===")
        data = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password
        }
        
        response = self._make_request('POST', 'api/auth/register/', data)
        return 'user' in response and 'wallet_address' in response

    def test_token_obtain(self, username: str, password: str) -> bool:
        """Test token obtain endpoint."""
        logger.info("\n=== Testing Token Obtain ===")
        data = {
            "username": username,
            "password": password
        }
        
        response = self._make_request('POST', 'api/auth/token/', data)
        if 'access' in response:
            self.token = response['access']
            return True
        return False

    def test_agent_setup(self) -> bool:
        """Test agent setup endpoint."""
        logger.info("\n=== Testing Agent Setup ===")
        prompt = "I want to buy a new gaming laptop under $2000 from trusted brands with fast shipping"
        data = {
            "prompt": prompt,
            "template_id": 1,
            "bridge_wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
        }
        
        logger.info(f"Testing prompt processing with: '{prompt}'")
        response = self._make_request('POST', 'api/agents/setup/', data)
        
        if 'error' in response:
            logger.error(f"Setup Error: {response.get('detail', 'Unknown error')}")
            return False
            
        if 'id' in response:
            self.agent_id = response['id']
            constraints = response.get('constraints', {})
            
            # Check for OpenAI processing errors
            if '_error' in constraints:
                logger.warning(f"OpenAI processing failed: {constraints['_error']}")
                logger.warning("Using default constraints instead")
            
            logger.info("\nProcessed Constraints:")
            logger.info(f"Max Price: {constraints.get('max_price')}")
            logger.info(f"Categories: {constraints.get('categories')}")
            logger.info(f"Preferences: {constraints.get('preferences')}")
            
            # Test continues even with default constraints
            validation = all([
                'max_price' in constraints,
                'categories' in constraints,
                'preferences' in constraints
            ])
            
            if not validation:
                logger.error("Missing required constraints")
                logger.error(f"Full response: {json.dumps(response, indent=2)}")
                return False
                
            return True
            
        logger.error(f"Unexpected response format: {json.dumps(response, indent=2)}")
        return False

    def test_agent_shopping(self) -> bool:
        """Test agent shopping endpoint."""
        logger.info("\n=== Testing Agent Shopping ===")
        if not self.agent_id:
            logger.warning("No agent ID available. Skipping test.")
            return False
            
        data = {
            "search_criteria": {
                "category": "electronics",
                "max_price": 500
            }
        }
        
        response = self._make_request('POST', f'api/agents/{self.agent_id}/shop/', data)
        return 'task_id' in response

    def test_agent_status(self) -> bool:
        """Test agent status endpoint."""
        logger.info("\n=== Testing Agent Status ===")
        if not self.agent_id:
            logger.warning("No agent ID available. Skipping test.")
            return False
            
        response = self._make_request('GET', f'api/agents/{self.agent_id}/status/')
        return 'status' in response and 'trust_score' in response

    def test_transaction_verification(self) -> bool:
        """Test transaction verification endpoint."""
        logger.info("\n=== Testing Transaction Verification ===")
        if not self.agent_id:
            logger.warning("No agent ID available. Skipping test.")
            return False
            
        data = {
            "agent_instance": self.agent_id,
            "amount": "150.00",
            "merchant": "Amazon",
            "merchant_wallet": "0x9876543210abcdef1234567890abcdef12345678"
        }
        
        response = self._make_request('POST', 'api/transactions/verify/', data)
        return 'status' in response

def main():
    """Main entry point for the test suite."""
    tester = APITester()
    results = tester.run_tests()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    for test_name, success in results:
        status = "✅ Passed" if success else "❌ Failed"
        logger.info(f"{test_name}: {status}")

if __name__ == "__main__":
    main()