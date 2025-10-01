import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8001"
    
    endpoints = [
        "/api/weather/sources",
        "/api/weather/data?hours=24",
        "/health"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\nTesting: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                except:
                    print(f"Response (text): {response.text[:200]}...")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("Connection Error: Backend server might not be running")
        except requests.exceptions.Timeout:
            print("Timeout: Server took too long to respond")
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_api_endpoints()