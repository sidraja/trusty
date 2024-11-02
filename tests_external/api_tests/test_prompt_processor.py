import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptProcessorTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/api/prompt/process/"
    
    def test_prompt(self, prompt: str, scenario_name: str, expected_structure: str) -> None:
        """Test prompt processing with given input."""
        print(f"\n=== Testing Scenario: {scenario_name} ===")
        print(f"Expected Constraints: {expected_structure}")
        print(f"Prompt: '{prompt}'")
        
        try:
            response = requests.post(
                self.endpoint,
                headers={'Content-Type': 'application/json'},
                json={'prompt': prompt}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.ok:
                result = response.json()
                print("\nGenerated Constraints:")
                print(json.dumps(result, indent=2))
            else:
                print(f"\nError Response: {response.text}")
                
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    """Test various shopping scenarios."""
    tester = PromptProcessorTester()
    
    # Test scenarios with expected constraint structures
    scenarios = [
        {
            "name": "Gaming Setup Bundle",
            "prompt": "I need a complete gaming setup with a high-end PC (around $2500), "
                     "a 4K monitor (under $800), gaming chair (about $300), and peripherals "
                     "from Razer or Logitech. Everything should have at least 4-star ratings "
                     "and fast shipping. Prefer new items only.",
            "expected": "Multiple categories, high budget, specific brands, rating requirements"
        },
        {
            "name": "Smart Home Starter Kit",
            "prompt": "Looking to make my apartment smart. Need compatible devices: "
                     "smart thermostat (preferably Nest or Ecobee), doorbell camera, "
                     "smart lights for 3 rooms, and a hub. Total budget is $1000. "
                     "Want everything to work with Alexa. Prime shipping preferred.",
            "expected": "IoT category, brand compatibility, ecosystem requirements"
        },
        {
            "name": "Professional Photography Kit",
            "prompt": "Need a mirrorless camera setup for professional photography. "
                     "Looking at Sony or Fujifilm, budget around $3500 for body and lenses. "
                     "Need a 35mm prime lens and a zoom lens. Must be new, from authorized dealers only. "
                     "Include a camera bag and extra battery. Shipping insurance required.",
            "expected": "Photography gear, authorized sellers, accessories, shipping requirements"
        },
        {
            "name": "Home Gym Equipment",
            "prompt": "Setting up a home gym in my garage. Need a power rack with pull-up bar, "
                     "Olympic barbell set with weights (preferably Rogue or Rep Fitness), "
                     "adjustable bench, and rubber flooring. Max budget $3000. "
                     "Can handle used equipment if in excellent condition. Need freight shipping.",
            "expected": "Fitness equipment, heavy items, specific brands, condition flexibility"
        },
        {
            "name": "Mobile Office Setup",
            "prompt": "Building a portable office setup. Need a lightweight laptop (MacBook Air or Dell XPS), "
                     "portable 15\" monitor, noise-cancelling headphones (Sony or Bose), and a compact "
                     "wireless keyboard/mouse combo. Everything needs to fit in a carry-on. "
                     "Budget is $2800. Need extended warranty where available.",
            "expected": "Portable electronics, size constraints, warranty requirements"
        },
        {
            "name": "Kitchen Remodel Appliances",
            "prompt": "Renovating kitchen with all new appliances. Need smart fridge with water dispenser, "
                     "dual-fuel range (prefer Wolf or Viking), dishwasher, and microwave drawer. "
                     "All in stainless steel finish. Budget up to $15000. White glove delivery required. "
                     "Energy Star certified only.",
            "expected": "Appliances, finish matching, delivery requirements, energy specifications"
        }
    ]
    
    for scenario in scenarios:
        tester.test_prompt(
            prompt=scenario["prompt"],
            scenario_name=scenario["name"],
            expected_structure=scenario["expected"]
        )

if __name__ == "__main__":
    main()