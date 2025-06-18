import requests
from requests.exceptions import Timeout, HTTPError, RequestException

# --- Configuration ---

# SERVICE_KEY = "GTDvWSPwxWuonrDpSoJFdpfsGL10NYvxqG3hCEwNTdMp39xqNkgVUXR7+ywZsErmVoAtkLW18guG1SgF6Dcnaw==" # old
SERVICE_KEY = "Fbq4OmxpKYD/RUVgN0+nZgm02P3BojouPbc4z3JApBzD39BllVOYadxrCb8evD0XHNbQUSSt8nwZanr5Vw7qDQ==" # new

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
    timeout = 60 # seconds
    try:
        url = f"{base_url}{endpoint}"
        params["ServiceKey"] = SERVICE_KEY
        params["_type"] = "json"

        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json() if return_json else response.text
    except Timeout:
        # caller can catch this specifically if desired
        raise RuntimeError(f"Timeout ({timeout}s) calling {url}")
    except HTTPError as he:
        # 4xx, 5xx responses
        status = he.response.status_code if he.response else "?"
        text   = he.response.text       if he.response else ""
        raise RuntimeError(f"HTTP {status} calling {url}: {text}") from he
    except RequestException as re:
        # includes ConnectionError, TooManyRedirects, etc.
        raise RuntimeError(f"Request failed calling {url}: {re}") from re