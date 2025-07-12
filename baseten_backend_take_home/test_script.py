#!/usr/bin/env python
import httpx
import json

def test_invoke_endpoint():
    """Test script to make a POST request to /invoke endpoint"""
    
    # Define the endpoint URL
    url = "http://localhost:8000/invoke"
    
    # Define the request payload based on the InvokeRequest model
    payload = {
        "worklet_input": {
            "model_id": "test_model_123",
            "input": [1, 2, 3, 4, 5]
        }
    }
    
    # Set headers
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("Making POST request to:", url)
        print("Payload:", json.dumps(payload, indent=2))
        print("-" * 50)
        
        # Make the POST request
        response = httpx.post(url, json=payload, headers=headers)
        
        print("Response Status Code:", response.status_code)
        print("-" * 50)
        
        if response.status_code == 200:
            print("Success! Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error Response:")
            print("Status Code:", response.status_code)
            print("Response Text:", response.text)
            
    except httpx.ConnectError:
        print("Error: Could not connect to the server. Make sure the server is running on localhost:8000")
    except httpx.RequestError as e:
        print(f"Request failed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_invoke_endpoint()
