import requests

# --- Configuration ---
SERVICE_KEY = "ejSxZH1i9X9Btaga5Oom/AZiuOcUNR2v9FgYwhDM3gaerP1EZGAlxYqFpS4fYMCKq4SIbfRZJvi45+e8LjEZzw==" # Decoding 

# --- Helper Function to Make API Call ---
def call_api(base_url: str, endpoint: str, params: dict, return_json=True):
    """
    Calls the specified API service and endpoint with parameters.
    
    :param base_url: API base URL (e.g., "http://apis.data.go.kr/B551182/hospInfoServicev2")
    :param endpoint: API endpoint string (e.g., "/getHospBasisList")
    :param params: Dictionary of query parameters
    :param return_json: Whether to parse response as JSON
    :return: Parsed response or raw text
    """

    url = f"{base_url}{endpoint}"
    params["ServiceKey"] = SERVICE_KEY
    params["_type"] = "json"

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json() if return_json else response.text
    else:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")