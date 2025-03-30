from api import call_api
from api_config import ApiService, API_BASE_URLS, API_ENDPOINTS, API_PARAMS
from data_utils import extract_items_from_response, clean_hospital_dataframe


# Function to check API parameters
def get_api_data(service_enum, endpoint_key, user_params):
    endpoint = API_ENDPOINTS[service_enum][endpoint_key]
    base_url = API_BASE_URLS[service_enum]
    user_params["_type"] = "json"
    return call_api(service_enum.value, endpoint, user_params)

# Step 1: Get basic hospital info API
service = ApiService.HOSP_BASIC
endpoint_key = "LIST"
endpoint = API_ENDPOINTS[service][endpoint_key]
base_url = API_BASE_URLS[service]

params = {
    "pageNo": 1,
    "numOfRows": 10,
    "_type": "json"
}

response = call_api(
    base_url=base_url,
    endpoint=endpoint,
    params=params
)

# Step 2: Extract and clean
df = extract_items_from_response(response)
df_clean = clean_hospital_dataframe(df)

print(df_clean.head(20))

# Step 3: get hospital detail info
service = ApiService.HOSP_DETAIL
endpoint_key = "SPECIALIST_COUNT_BY_DEPARTMENT"
endpoint = API_ENDPOINTS[service][endpoint_key]
base_url = API_BASE_URLS[service]

params = {
    "ykiho": "JDQ4MTg4MSM1MSMkMSMkMCMkODkkMzgxMzUxIzExIyQxIyQzIyQ2MiQ0NjEwMDIjNjEjJDEjJDAjJDgz",
    "pageNo": 1,
    "numOfRows": 10,
    "_type": "json"
}

response = call_api(
    base_url=base_url,
    endpoint=endpoint,
    params=params
)

print(response)