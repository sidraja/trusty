import requests
import json
from typing import Dict, Any
from datetime import datetime
import logging
from .utils import setup_logging

logger = setup_logging()

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.agent_id = None
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def _update_auth_header(self):
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
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
                return response_data
            except ValueError as e:
                logger.error(f"Error parsing response: {str(e)}")
                logger.error(f"Raw response: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Request error: {str(e)}")
            return {}

    def test_registration(self) -> bool:
        logger.info("\n=== Testing User Registration ===")
        data = {
            "username": f"testuser_{int(datetime.now().timestamp())}",
            "email": f"test_{int(datetime.now().timestamp())}@example.com",
            "password": "TestPass123!"
        }
        
        response = self._make_request('POST', 'api/auth/register/', data)
        return 'user' in response and 'wallet_address' in response

    def test_token_obtain(self, username: str, password: str) -> bool:
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
        logger.info("\n=== Testing Agent Setup ===")
        data = {
            "template_id": 1,
            "constraints": {
                "max_price": 500,
                "categories": ["electronics"],
                "preferences": {"brand": "trusted"}
            },
            "max_budget": "1000.00",
            "allowed_merchants": ["Amazon", "BestBuy"],
            "bridge_wallet_address": "0x1234567890abcdef1234567890abcdef12345678"
        }
        
        response = self._make_request('POST', 'api/agents/setup/', data)
        if 'id' in response:
            self.agent_id = response['id']
            return True
        return False

    def test_agent_shopping(self) -> bool:
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
        logger.info("\n=== Testing Agent Status ===")
        if not self.agent_id:
            logger.warning("No agent ID available. Skipping test.")
            return False
            
        response = self._make_request('GET', f'api/agents/{self.agent_id}/status/')
        return 'status' in response and 'trust_score' in response

    def test_transaction_verification(self) -> bool:
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
    tester = APITester()
    
    # Generate unique username for this test run
    username = f"testuser_{int(datetime.now().timestamp())}"
    password = "TestPass123!"
    
    # Run all tests
    tests = [
        ("Registration", lambda: tester.test_registration()),
        ("Token Obtain", lambda: tester.test_token_obtain(username, password)),
        ("Agent Setup", lambda: tester.test_agent_setup()),
        ("Agent Shopping", lambda: tester.test_agent_shopping()),
        ("Agent Status", lambda: tester.test_agent_status()),
        ("Transaction Verification", lambda: tester.test_transaction_verification())
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    for test_name, success in results:
        status = "✅ Passed" if success else "❌ Failed"
        logger.info(f"{test_name}: {status}")

if __name__ == "__main__":
    main()