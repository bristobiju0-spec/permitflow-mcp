import requests
import sys

def test_render_health():
    # Attempting to ping the Render root endpoint
    url = "https://sales-agent-pro.onrender.com/"
    print(f"Pinging Render root endpoint: {url}...")
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"Success! Status Code: {response.status_code}")
            print(f"Response Body: {response.json()}")
            return response.json().get("status") == "online"
        else:
            print(f"Failed! Status Code: {response.status_code}")
            print(f"Response Body: {response.text}")
            return False
    except Exception as e:
        print(f"Error during connection test: {e}")
        return False

if __name__ == "__main__":
    if test_render_health():
        print("Render server is ALIVE and healthy.")
        sys.exit(0)
    else:
        print("Render server is NOT responding or unhealthy.")
        sys.exit(1)
